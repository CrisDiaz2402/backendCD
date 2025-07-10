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
    GastoCreate, GastoUpdate, Gasto as GastoSchema,
    UsuarioCreate, UsuarioResponse, UsuarioLogin, UsuarioUpdate, Token, TokenWithUser,
    EliminacionResponse, EliminacionCategoriaResponse, EliminacionTotalResponse
)
from auth import (
    authenticate_user, create_access_token, create_user,
    get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

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
# ENDPOINTS DE USUARIOS (LEGACY - Para compatibilidad)
# ========================

@app.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtener usuario por ID"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@app.get("/usuarios/", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    """Listar todos los usuarios"""
    return db.query(Usuario).all()

# ========================
# ENDPOINTS DE GASTOS
# ========================

@app.post("/gastos/", response_model=GastoSchema)
def crear_gasto(
    gasto: Optional[GastoCreate] = None,
    descripcion: Optional[str] = None,
    monto: Optional[float] = None,
    categoria: Optional[CategoriaGasto] = None,
    usuario_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Crear un nuevo gasto"""
    # Determinar origen de datos
    if gasto:
        # Datos desde objeto GastoCreate (uso API)
        gasto_data = {
            "descripcion": gasto.descripcion,
            "monto": gasto.monto,
            "categoria": gasto.categoria,
            "usuario_id": gasto.usuario_id
        }
    elif descripcion and monto is not None and categoria and usuario_id:
        # Datos desde parámetros individuales (uso frontend)
        gasto_data = {
            "descripcion": descripcion,
            "monto": monto,
            "categoria": categoria,
            "usuario_id": usuario_id
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar un objeto GastoCreate o los parámetros: descripcion, monto, categoria, usuario_id"
        )
    
    # Validaciones básicas
    if gasto_data["monto"] <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser positivo")
    
    if not gasto_data["descripcion"] or not gasto_data["descripcion"].strip():
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
    
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == gasto_data["usuario_id"]).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Crear gasto
    db_gasto = Gasto(
        usuario_id=gasto_data["usuario_id"],
        descripcion=gasto_data["descripcion"],
        monto=gasto_data["monto"],
        categoria=gasto_data["categoria"],
        fecha=datetime.now()
    )
    
    # Guardar en base de datos
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    
    return db_gasto

@app.get("/gastos/", response_model=List[GastoSchema])
def listar_gastos(
    usuario_id: Optional[int] = None,
    categoria: Optional[CategoriaGasto] = None,
    limite: int = 100,
    db: Session = Depends(get_db)
):
    """Listar gastos con filtros opcionales"""
    query = db.query(Gasto)
    
    if usuario_id:
        query = query.filter(Gasto.usuario_id == usuario_id)
    if categoria:
        query = query.filter(Gasto.categoria == categoria)
    
    return query.order_by(Gasto.fecha.desc()).limit(limite).all()

@app.get("/gastos/{gasto_id}", response_model=GastoSchema)
def obtener_gasto(gasto_id: int, db: Session = Depends(get_db)):
    """Obtener gasto por ID"""
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    return gasto

@app.put("/gastos/{gasto_id}", response_model=GastoSchema)
def actualizar_gasto(
    gasto_id: int, 
    gasto_update: GastoUpdate, 
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """Actualizar un gasto existente con validación de usuario"""
    # Buscar el gasto y verificar que pertenece al usuario
    db_gasto = db.query(Gasto).filter(
        Gasto.id == gasto_id,
        Gasto.usuario_id == usuario_id
    ).first()
    
    if not db_gasto:
        raise HTTPException(
            status_code=404, 
            detail="Gasto no encontrado o no pertenece al usuario especificado"
        )
    
    # Actualizar campos proporcionados
    for field, value in gasto_update.dict(exclude_unset=True).items():
        setattr(db_gasto, field, value)
    
    db_gasto.updated_at = datetime.now()
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

@app.delete("/gastos/{gasto_id}")
def eliminar_gasto(
    gasto_id: int, 
    usuario_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Eliminar un gasto específico
    
    Args:
        gasto_id: ID del gasto a eliminar
        usuario_id: ID del usuario (opcional, para validación adicional de seguridad)
    
    Returns:
        Mensaje de confirmación con detalles del gasto eliminado
    """
    # Buscar el gasto
    query = db.query(Gasto).filter(Gasto.id == gasto_id)
    
    # Si se proporciona usuario_id, validar que el gasto pertenece a ese usuario
    if usuario_id:
        query = query.filter(Gasto.usuario_id == usuario_id)
    
    db_gasto = query.first()
    
    if not db_gasto:
        if usuario_id:
            raise HTTPException(
                status_code=404, 
                detail="Gasto no encontrado o no pertenece al usuario especificado"
            )
        else:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    # Guardar información del gasto antes de eliminarlo (para el log)
    gasto_info = {
        "id": db_gasto.id,
        "descripcion": db_gasto.descripcion,
        "monto": db_gasto.monto,
        "categoria": db_gasto.categoria.value if db_gasto.categoria else None,
        "fecha": db_gasto.fecha.isoformat(),
        "usuario_id": db_gasto.usuario_id
    }
    
    # Eliminar el gasto
    db.delete(db_gasto)
    db.commit()
    
    return {
        "mensaje": "Gasto eliminado correctamente",
        "gasto_eliminado": gasto_info
    }

@app.delete("/gastos/batch", response_model=EliminacionResponse)
def eliminar_gastos_multiples(
    gastos_ids: List[int],
    usuario_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Eliminar múltiples gastos por sus IDs
    
    Args:
        gastos_ids: Lista de IDs de gastos a eliminar
        usuario_id: ID del usuario (opcional, para validación de seguridad)
    
    Returns:
        Resumen de la operación de eliminación
    """
    if not gastos_ids:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un ID de gasto")
    
    if len(gastos_ids) > 100:
        raise HTTPException(status_code=400, detail="No se pueden eliminar más de 100 gastos a la vez")
    
    # Buscar gastos existentes
    query = db.query(Gasto).filter(Gasto.id.in_(gastos_ids))
    
    if usuario_id:
        query = query.filter(Gasto.usuario_id == usuario_id)
    
    gastos_encontrados = query.all()
    
    if not gastos_encontrados:
        raise HTTPException(status_code=404, detail="No se encontraron gastos con los IDs proporcionados")
    
    # Información de gastos antes de eliminar
    gastos_eliminados = []
    monto_total_eliminado = 0.0
    
    for gasto in gastos_encontrados:
        gastos_eliminados.append({
            "id": gasto.id,
            "descripcion": gasto.descripcion,
            "monto": gasto.monto,
            "categoria": gasto.categoria.value if gasto.categoria else None,
            "fecha": gasto.fecha.isoformat()
        })
        monto_total_eliminado += gasto.monto
        
        # Eliminar el gasto
        db.delete(gasto)
    
    db.commit()
    
    ids_no_encontrados = set(gastos_ids) - set(g.id for g in gastos_encontrados)
    
    return {
        "mensaje": f"Eliminados {len(gastos_eliminados)} gastos correctamente",
        "gastos_eliminados": len(gastos_eliminados),
        "monto_total_eliminado": round(monto_total_eliminado, 2),
        "gastos_eliminados_detalle": gastos_eliminados,
        "ids_solicitados": len(gastos_ids),
        "ids_no_encontrados": list(ids_no_encontrados) if ids_no_encontrados else []
    }

@app.get("/gastos/usuario/{usuario_id}/categoria/{categoria}", response_model=List[GastoSchema])
def obtener_gastos_usuario_por_categoria(
    usuario_id: int, 
    categoria: CategoriaGasto,
    limite: int = 100,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Obtener todos los gastos de un usuario específico filtrados por categoría
    
    Args:
        usuario_id: ID del usuario
        categoria: Categoría de gastos a filtrar (COMIDA, TRANSPORTE, VARIOS)
        limite: Número máximo de gastos a retornar (default: 100)
        fecha_desde: Fecha inicial para filtrar (opcional)
        fecha_hasta: Fecha final para filtrar (opcional)
    
    Returns:
        Lista de gastos del usuario en la categoría especificada
    """
    
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Construir query base
    query = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.categoria == categoria
    )
    
    # Aplicar filtros de fecha si se proporcionan
    if fecha_desde:
        query = query.filter(Gasto.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Gasto.fecha <= fecha_hasta)
    
    # Obtener gastos ordenados por fecha descendente
    gastos = query.order_by(Gasto.fecha.desc()).limit(limite).all()
    
    return gastos

@app.get("/gastos/usuario/{usuario_id}/categoria/{categoria}/estadisticas")
def obtener_estadisticas_gastos_por_categoria(
    usuario_id: int,
    categoria: CategoriaGasto,
    dias: int = 30,
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de gastos de un usuario en una categoría específica
    
    Args:
        usuario_id: ID del usuario
        categoria: Categoría de gastos a analizar
        dias: Número de días hacia atrás para el análisis (default: 30)
    
    Returns:
        Estadísticas detalladas de gastos en la categoría
    """
    
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Calcular fecha límite
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    # Obtener gastos de la categoría en el período
    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.categoria == categoria,
        Gasto.fecha >= fecha_limite
    ).all()
    
    if not gastos:
        return {
            "usuario_id": usuario_id,
            "categoria": categoria.value,
            "periodo_dias": dias,
            "total_gastos": 0,
            "monto_total": 0.0,
            "monto_promedio": 0.0,
            "monto_minimo": 0.0,
            "monto_maximo": 0.0,
            "gastos_por_dia": 0.0,
            "gastos": []
        }
    
    # Calcular estadísticas
    montos = [gasto.monto for gasto in gastos]
    total_gastos = len(gastos)
    monto_total = sum(montos)
    monto_promedio = monto_total / total_gastos
    monto_minimo = min(montos)
    monto_maximo = max(montos)
    gastos_por_dia = total_gastos / dias
    
    # Agrupar gastos por día para análisis temporal
    gastos_por_fecha = {}
    for gasto in gastos:
        fecha_str = gasto.fecha.strftime("%Y-%m-%d")
        if fecha_str not in gastos_por_fecha:
            gastos_por_fecha[fecha_str] = []
        gastos_por_fecha[fecha_str].append({
            "id": gasto.id,
            "descripcion": gasto.descripcion,
            "monto": gasto.monto,
            "hora": gasto.fecha.strftime("%H:%M")
        })
    
    return {
        "usuario_id": usuario_id,
        "categoria": categoria.value,
        "periodo_dias": dias,
        "total_gastos": total_gastos,
        "monto_total": round(monto_total, 2),
        "monto_promedio": round(monto_promedio, 2),
        "monto_minimo": round(monto_minimo, 2),
        "monto_maximo": round(monto_maximo, 2),
        "gastos_por_dia": round(gastos_por_dia, 2),
        "gastos_por_fecha": gastos_por_fecha,
        "gastos": [
            {
                "id": gasto.id,
                "descripcion": gasto.descripcion,
                "monto": gasto.monto,
                "fecha": gasto.fecha,
                "confianza_categoria": gasto.confianza_categoria
            }
            for gasto in gastos
        ]
    }

# ========================
# ENDPOINTS DE FEEDBACK Y UTILIDADES
# ========================

@app.get("/")
def root():
    """Endpoint raíz de la API"""
    return {
        "mensaje": "Money Manager G5 API",
        "version": "1.0.0",
        "endpoints": {
            "usuarios": "/usuarios/",
            "gastos": "/gastos/",
            "auth": "/auth/",
            "docs": "/docs"
        }
    }

@app.delete("/gastos/usuario/{usuario_id}/todos")
def eliminar_todos_gastos_usuario(
    usuario_id: int,
    confirmar: bool = False,
    confirmar_todos: bool = False,
    db: Session = Depends(get_db)
):
    """
    Eliminar TODOS los gastos de un usuario (operación destructiva)
    
    Args:
        usuario_id: ID del usuario
        confirmar: Primera confirmación requerida
        confirmar_todos: Segunda confirmación requerida (doble confirmación)
    
    Returns:
        Resumen completo de eliminación
    """
    # Verificar doble confirmación
    if not (confirmar and confirmar_todos):
        raise HTTPException(
            status_code=400, 
            detail="Operación destructiva requiere doble confirmación: confirmar=true&confirmar_todos=true"
        )
    
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener todos los gastos del usuario
    gastos = db.query(Gasto).filter(Gasto.usuario_id == usuario_id).all()
    
    if not gastos:
        return {
            "mensaje": "El usuario no tiene gastos registrados",
            "usuario_id": usuario_id,
            "gastos_eliminados": 0,
            "monto_total_eliminado": 0.0
        }
    
    # Calcular estadísticas por categoría
    estadisticas_por_categoria = {}
    monto_total = 0.0
    
    for gasto in gastos:
        categoria = gasto.categoria.value if gasto.categoria else "SIN_CATEGORIA"
        
        if categoria not in estadisticas_por_categoria:
            estadisticas_por_categoria[categoria] = {
                "cantidad": 0,
                "monto_total": 0.0,
                "gastos": []
            }
        
        estadisticas_por_categoria[categoria]["cantidad"] += 1
        estadisticas_por_categoria[categoria]["monto_total"] += gasto.monto
        estadisticas_por_categoria[categoria]["gastos"].append({
            "id": gasto.id,
            "descripcion": gasto.descripcion,
            "monto": gasto.monto,
            "fecha": gasto.fecha.isoformat()
        })
        
        monto_total += gasto.monto
        db.delete(gasto)
    
    db.commit()
    
    # Redondear montos
    for categoria in estadisticas_por_categoria:
        estadisticas_por_categoria[categoria]["monto_total"] = round(
            estadisticas_por_categoria[categoria]["monto_total"], 2
        )
    
    return {
        "mensaje": f"TODOS los gastos del usuario {usuario_id} han sido eliminados",
        "usuario_id": usuario_id,
        "total_gastos_eliminados": len(gastos),
        "monto_total_eliminado": round(monto_total, 2),
        "estadisticas_por_categoria": estadisticas_por_categoria,
        "fecha_eliminacion": datetime.now().isoformat(),
        "advertencia": "Esta acción no se puede deshacer"
    }

@app.get("/usuarios/{usuario_id}/gastos", response_model=List[GastoSchema])
def obtener_gastos_usuario(
    usuario_id: int,
    limite: int = 100,
    offset: int = 0,
    categoria: Optional[CategoriaGasto] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los gastos de un usuario específico con filtros opcionales"""
    
    # Verificar que el usuario está accediendo a sus propios gastos
    if current_user.id != usuario_id:
        raise HTTPException(
            status_code=403, 
            detail="Solo puedes acceder a tus propios gastos"
        )
    
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Construir query base
    query = db.query(Gasto).filter(Gasto.usuario_id == usuario_id)
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)