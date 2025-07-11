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
    EliminacionResponse, EliminacionCategoriaResponse, EliminacionTotalResponse,
    SugerenciaRequest, SugerenciaResponse,
    GastoConDecision, RespuestaGastoConDecision, FeedbackML,
    GastoCreateUnificado, RespuestaGastoUnificado
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

@app.post("/gastos/", response_model=RespuestaGastoUnificado)
def crear_gasto_unificado(
    gasto_data: GastoCreateUnificado,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    🔄 ENDPOINT UNIFICADO - Crear gasto con autenticación y ML integrado
    
    Este es el único endpoint que necesitas para crear gastos. Combina:
    ✅ Autenticación JWT automática
    ✅ Inteligencia artificial opcional
    ✅ Manejo de decisiones del usuario
    
    Flujos soportados:
    1. ML Automático: usar_ml=True, acepta_sugerencia=None → Si ML sugiere diferente, retorna sugerencia
    2. ML con Decisión: usar_ml=True, acepta_sugerencia=True/False → Crea gasto con decisión
    3. Sin ML: usar_ml=False → Crea gasto directo con categoría del usuario
    
    Ejemplos de uso:
    
    📱 Frontend Mobile (2 pasos):
    Paso 1: { "descripcion": "Almuerzo", "monto": 25, "categoria": "VARIOS", "usar_ml": true }
    Respuesta: Si ML sugiere "COMIDA", retorna sugerencia sin crear gasto
    Paso 2: { ...mismo_data..., "acepta_sugerencia": true } → Crea con "COMIDA"
    
    💻 Desktop/Web (1 paso):
    { "descripcion": "Gasolina", "monto": 50, "categoria": "TRANSPORTE", "usar_ml": false }
    Respuesta: Crea gasto directo con "TRANSPORTE"
    """
    try:
        categoria_original = gasto_data.categoria
        categoria_final = categoria_original
        sugerencia_ml = None
        ml_usado = False
        decision_usuario = "sin_ml"
        feedback_ml = None
        
        # Paso 1: Obtener sugerencia del ML si está habilitado
        if gasto_data.usar_ml:
            try:
                # Obtener sugerencia del modelo ML
                resultado_ml = ml_service.obtener_sugerencia_categoria(
                    descripcion=gasto_data.descripcion,
                    categoria_usuario=categoria_original.value
                )
                
                sugerencia_ml = resultado_ml
                ml_usado = True
                
                # Verificar si la sugerencia es diferente
                if not resultado_ml.recomendacion.coincide:
                    # Hay una sugerencia diferente
                    if gasto_data.acepta_sugerencia is None:
                        # Frontend necesita mostrar la decisión al usuario
                        return RespuestaGastoUnificado(
                            gasto=None,  # No se crea aún
                            ml_usado=True,
                            sugerencia_ml=sugerencia_ml,
                            decision_usuario="pendiente_decision",
                            categoria_final=categoria_original,
                            feedback_ml=None
                        )
                    elif gasto_data.acepta_sugerencia:
                        # Usuario acepta la sugerencia del ML
                        try:
                            categoria_sugerida = CategoriaGasto(resultado_ml.recomendacion.categoria_sugerida.upper())
                            categoria_final = categoria_sugerida
                            decision_usuario = "acepto_sugerencia"
                        except ValueError:
                            # Si la categoría sugerida no es válida, mantener original
                            categoria_final = categoria_original
                            decision_usuario = "error_sugerencia_mantiene_original"
                    else:
                        # Usuario mantiene la categoría original
                        categoria_final = categoria_original
                        decision_usuario = "mantuvo_original"
                else:
                    # ML sugiere la misma categoría
                    categoria_final = categoria_original
                    decision_usuario = "coincide_con_ml"
                    
            except Exception as e:
                # Si falla el ML, continuar sin él
                print(f"Error en ML service: {str(e)}")
                ml_usado = False
                decision_usuario = "error_ml_sin_sugerencia"
        
        # Paso 2: Crear el gasto con la categoría final
        nuevo_gasto = Gasto(
            descripcion=gasto_data.descripcion,
            monto=gasto_data.monto,
            categoria=categoria_final,
            usuario_id=current_user.id,  # Usar usuario autenticado
            fecha=datetime.now()
        )
        
        db.add(nuevo_gasto)
        db.commit()
        db.refresh(nuevo_gasto)
        
        # Paso 3: Crear feedback para analytics si se usó ML
        if ml_usado and sugerencia_ml:
            feedback_ml = FeedbackML(
                categoria_original=categoria_original.value,
                categoria_sugerida=sugerencia_ml.recomendacion.categoria_sugerida if sugerencia_ml.recomendacion else None,
                categoria_final=categoria_final.value,
                usuario_acepto_sugerencia=gasto_data.acepta_sugerencia or False,
                timestamp=datetime.now().isoformat()
            )
        
        return RespuestaGastoUnificado(
            gasto=nuevo_gasto,
            ml_usado=ml_usado,
            sugerencia_ml=sugerencia_ml,
            decision_usuario=decision_usuario,
            categoria_final=categoria_final,
            feedback_ml=feedback_ml
        )
        
    except HTTPException:
        # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear gasto: {str(e)}"
        )

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

# ========================
# ENDPOINTS DE MACHINE LEARNING
# ========================

@app.post("/ml/sugerencia", response_model=SugerenciaResponse)
def obtener_sugerencia_categoria(sugerencia: SugerenciaRequest):
    """
    Obtener sugerencia de categoría del modelo ML sin crear un gasto
    
    Este endpoint permite probar qué categoría sugiere el modelo para una descripción
    antes de crear realmente el gasto.
    """
    try:
        # Convertir enum a string para el modelo
        categoria_str = sugerencia.categoria_usuario.value
        
        # Obtener sugerencia del modelo
        resultado = ml_service.obtener_sugerencia_categoria(
            descripcion=sugerencia.descripcion,
            categoria_usuario=categoria_str
        )
        
        return resultado
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener sugerencia: {str(e)}"
        )

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

# ========================
# ENDPOINT DE COMPATIBILIDAD (LEGACY)
# ========================

@app.post("/gastos/simple", response_model=GastoSchema)
def crear_gasto_simple(
    gasto: GastoCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crear gasto simple sin ML (para compatibilidad con código anterior)
    DEPRECATED: Usar POST /gastos/ con usar_ml=False
    """
    # Crear gasto directamente sin ML
    nuevo_gasto = Gasto(
        descripcion=gasto.descripcion,
        monto=gasto.monto,
        categoria=gasto.categoria,
        usuario_id=current_user.id,
        fecha=datetime.now()
    )
    
    db.add(nuevo_gasto)
    db.commit()
    db.refresh(nuevo_gasto)
    
    return nuevo_gasto

@app.post("/gastos/crear-directo", response_model=GastoSchema)
def crear_gasto_directo(
    gasto_data: GastoCreateUnificado,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    💾 CREAR DIRECTO: Para casos donde no se usa ML o coincide la categoría
    
    Este endpoint se usa cuando:
    1. El ML sugiere la misma categoría (coincide)
    2. El usuario desactiva el ML
    3. Como fallback si hay problemas con ML
    """
    try:
        # Crear gasto directamente con la categoría enviada
        nuevo_gasto = Gasto(
            descripcion=gasto_data.descripcion,
            monto=gasto_data.monto,
            categoria=gasto_data.categoria,
            usuario_id=current_user.id,
            fecha=datetime.now()
        )
        
        db.add(nuevo_gasto)
        db.commit()
        db.refresh(nuevo_gasto)
        
        return nuevo_gasto
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear gasto directo: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)