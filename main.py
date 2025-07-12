from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from typing import List, Optional

# Importaciones locales
from database import SessionLocal, engine, Base
from models import Gasto, Usuario, CategoriaGasto
from schemas import (
    Gasto as GastoSchema,
    UsuarioCreate, UsuarioResponse, UsuarioLogin, UsuarioUpdate, Token, TokenWithUser,
    SugerenciaRequest, SugerenciaResponse,
    GastoConDecision
)
from auth import (
    authenticate_user, create_access_token, create_user,
    get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from ml_service import ml_service

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Money Manager G5 API",
    description="API para gestión de gastos con Machine Learning",
    version="1.0.0"
)

# Dependencia para sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================
# ENDPOINTS DE AUTENTICACIÓN
# ========================

# Nuevo endpoint POST para modificar datos del usuario autenticado
@app.post("/auth/update-profile", response_model=UsuarioResponse)
async def actualizar_perfil_usuario_post(
    usuario_update: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar los datos del usuario autenticado (POST).
    Solo se modifican los campos enviados en el body.
    """
    try:
        update_data = usuario_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(current_user, field, value)
        current_user.updated_at = datetime.now()
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/register", response_model=UsuarioResponse)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""
    # Verificar si el email ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(
            status_code=400, 
            detail="El email ya está registrado"
        )
    
    # Crear usuario con contraseña hasheada
    db_usuario = create_user(db, usuario.dict())
    return db_usuario

@app.post("/auth/login", response_model=Token)
def login_usuario(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login de usuario y generación de token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/auth/login-json", response_model=TokenWithUser)
def login_usuario_json(usuario_login: UsuarioLogin, db: Session = Depends(get_db)):
    """Login de usuario con JSON (para apps móviles) - Devuelve token + información del usuario"""
    user = authenticate_user(db, usuario_login.email, usuario_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    # Actualizar último login
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@app.get("/auth/me", response_model=UsuarioResponse)
def obtener_usuario_actual(current_user: Usuario = Depends(get_current_active_user)):
    """Obtener información del usuario autenticado"""
    return current_user

@app.patch("/auth/me", response_model=UsuarioResponse)
def actualizar_perfil_usuario(
    usuario_update: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar perfil del usuario autenticado (PATCH - solo campos enviados)"""
    
    # Actualizar solo los campos proporcionados (exclude_unset=True)
    update_data = usuario_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            setattr(current_user, field, value)
    
    # Actualizar timestamp
    current_user.updated_at = datetime.now()
    
    # Guardar cambios
    db.commit()
    db.refresh(current_user)
    
    return current_user







# ========================
# ENDPOINTS DE UTILIDADES
# ========================

# Endpoint para editar un gasto del usuario autenticado
from fastapi import Body
from schemas import GastoUpdate

@app.post("/auth/gastos/update", response_model=GastoSchema)
def editar_gasto_usuario(
    gasto_id: int = Body(..., embed=True, description="ID del gasto a editar"),
    gasto_update: GastoUpdate = Body(...),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Editar un gasto del usuario autenticado. Solo se modifican los campos enviados.
    """
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id, Gasto.usuario_id == current_user.id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    update_data = gasto_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(gasto, field, value)
    gasto.updated_at = datetime.now()
    db.commit()
    db.refresh(gasto)
    return gasto

# Endpoint para eliminar un gasto del usuario autenticado
@app.post("/auth/gastos/delete")
def eliminar_gasto_usuario(
    gasto_id: int = Body(..., embed=True, description="ID del gasto a eliminar"),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar un gasto del usuario autenticado por su ID.
    """
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id, Gasto.usuario_id == current_user.id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    db.delete(gasto)
    db.commit()
    return {"message": "Gasto eliminado exitosamente", "id": gasto_id}

@app.get("/")
def root():
    """Endpoint raíz de la API"""
    return {
        "mensaje": "Money Manager G5 API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth/*",
            "flujo_gastos": [
                "POST /ml/verificar-categoria",
                "POST /gastos/crear-con-decision"
            ],
            "consultas": "GET /auth/me/gastos",
            "utilidades": "GET /ml/estado",
            "docs": "/docs"
        }
    }

@app.get("/auth/me/gastos", response_model=List[GastoSchema])
def obtener_mis_gastos(
    limite: int = 100,
    offset: int = 0,
    categoria: Optional[CategoriaGasto] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los gastos del usuario autenticado con filtros opcionales"""
    
    # Construir query base
    query = db.query(Gasto).filter(Gasto.usuario_id == current_user.id)
    
    # Aplicar filtros opcionales
    if categoria:
        query = query.filter(Gasto.categoria == categoria)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
            query = query.filter(Gasto.fecha >= fecha_desde_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha_desde inválido. Use ISO format")
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
            query = query.filter(Gasto.fecha <= fecha_hasta_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha_hasta inválido. Use ISO format")
    
    # Ordenar por fecha descendente y aplicar límites
    gastos = query.order_by(Gasto.fecha.desc()).offset(offset).limit(limite).all()
    
    return gastos

# ========================
# ENDPOINTS DE MACHINE LEARNING
# ========================



@app.get("/ml/estado")
def obtener_estado_ml():
    """
    Verificar el estado del servicio de Machine Learning
    """
    try:
        estado = ml_service.probar_conexion()
        return {
            "servicio_ml": "activo" if estado["disponible"] else "inactivo",
            "modelo": estado["modelo"],
            "detalles": estado
        }
    except Exception as e:
        return {
            "servicio_ml": "error",
            "modelo": ml_service.model_space if ml_service else "N/A",
            "error": str(e)
        }

# ========================
# ENDPOINTS SEGÚN IDEA ORIGINAL - 2 PASOS SEPARADOS
# ========================

@app.post("/ml/verificar-categoria", response_model=SugerenciaResponse)
def verificar_categoria_con_ml(
    datos: SugerenciaRequest,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    🔍 PASO 1: Verificar categoría con ML (cuando usuario hace clic en "Guardar")
    
    El usuario envía la categoría elegida y el backend verifica con el modelo ML
    si es consistente. Devuelve sugerencia si encuentra una mejor opción.
    
    Flujo:
    1. Usuario llena formulario y hace clic en "Guardar"
    2. Frontend llama este endpoint
    3. ML verifica si la categoría es apropiada
    4. Si hay sugerencia diferente, frontend muestra modal "¿Cambiar a COMIDA?"
    5. Si coincide, frontend procede directo al paso 2
    """
    try:
        # Convertir enum a string para el modelo
        categoria_str = datos.categoria_usuario.value
        
        # Obtener sugerencia del modelo ML
        resultado = ml_service.obtener_sugerencia_categoria(
            descripcion=datos.descripcion,
            categoria_usuario=categoria_str
        )
        
        return resultado
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al verificar categoría con ML: {str(e)}"
        )

@app.post("/gastos/crear-con-decision", response_model=GastoSchema)
def crear_gasto_con_decision_final(
    datos: GastoConDecision,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    💾 PASO 2: Crear gasto con decisión del usuario (cuando hace clic en "Aceptar" o "Ignorar")
    
    Después de que el usuario ve la sugerencia del ML y decide, este endpoint
    crea el registro con la categoría final elegida por el usuario.
    
    Flujo:
    1. Usuario ve modal con sugerencia del ML
    2. Hace clic en "Aceptar Sugerencia" o "Ignorar y Mantener Original"
    3. Frontend llama este endpoint con la decisión
    4. Se crea el gasto con la categoría final
    """
    try:
        # Determinar categoría final basada en la decisión del usuario
        if datos.acepta_sugerencia and datos.categoria_sugerida:
            # Usuario ACEPTA la sugerencia del ML
            try:
                categoria_final = CategoriaGasto(datos.categoria_sugerida.value)
            except (ValueError, AttributeError):
                # Si hay error con la categoría sugerida, usar original
                categoria_final = datos.categoria_original
        else:
            # Usuario IGNORA la sugerencia y mantiene la original
            categoria_final = datos.categoria_original
        
        # Crear el gasto con la categoría final elegida
        nuevo_gasto = Gasto(
            descripcion=datos.descripcion,
            monto=datos.monto,
            categoria=categoria_final,
            usuario_id=current_user.id,  # Usuario autenticado automáticamente
            fecha=datetime.now()
        )
        
        # Guardar en base de datos
        db.add(nuevo_gasto)
        db.commit()
        db.refresh(nuevo_gasto)
        
        return nuevo_gasto
        
    except HTTPException:
        # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear gasto con decisión: {str(e)}"
        )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)