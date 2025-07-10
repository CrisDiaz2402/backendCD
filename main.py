from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from typing import List, Optional

# Importaciones locales
from database import SessionLocal, engine, Base
from models import (
    Gasto, Usuario, PatronGasto, TransportePredefinido, 
    AnalisisGasto, ModeloML, CategoriaGasto, TipoPatron
)
from schemas import (
    GastoCreate, GastoUpdate, Gasto as GastoSchema,
    UsuarioCreate, UsuarioResponse, UsuarioLogin, Token,
    PatronGasto as PatronGastoSchema,
    TransportePredefinidoCreate, TransportePredefinido as TransportePredefinidoSchema,
    AnalisisRequest, AnalisisResponse, RecomendacionML, AnomaliaDetectada,
    PrediccionGasto, EstadisticasUsuario, FeedbackML, ResumenML
)
from ml_services import clasificador_gastos, detector_anomalias, analizador_patrones
from ml_utils import (
    procesar_gasto_para_ml, calcular_estadisticas_usuario, 
    validar_gasto_anomalo, crear_directorio_modelos
)
from auth import (
    authenticate_user, create_access_token, create_user,
    get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Crear directorio para modelos ML
crear_directorio_modelos()

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

@app.post("/auth/login-json", response_model=Token)
def login_usuario_json(usuario_login: UsuarioLogin, db: Session = Depends(get_db)):
    """Login de usuario con JSON (para apps móviles)"""
    user = authenticate_user(db, usuario_login.email, usuario_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
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

@app.get("/auth/me", response_model=UsuarioResponse)
def obtener_usuario_actual(current_user: Usuario = Depends(get_current_active_user)):
    """Obtener información del usuario autenticado"""
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
    # Parámetros simples para frontend
    descripcion: Optional[str] = None,
    monto: Optional[float] = None,
    categoria: Optional[CategoriaGasto] = None,
    usuario_id: Optional[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo gasto - Acepta tanto objeto GastoCreate como parámetros individuales
    Uso desde frontend: POST /gastos/ con parámetros form-data o query params
    Uso desde API: POST /gastos/ con JSON body
    """
    
    # Determinar origen de datos
    if gasto:
        # Datos desde objeto GastoCreate (uso API)
        gasto_data = gasto.dict()
        usar_ml_completo = True
    elif descripcion and monto is not None and categoria and usuario_id:
        # Datos desde parámetros individuales (uso frontend)
        gasto_data = {
            "descripcion": descripcion,
            "monto": monto,
            "categoria": categoria,
            "usuario_id": usuario_id
        }
        usar_ml_completo = False
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
    
    # Obtener fecha actual
    fecha_actual = datetime.now()
    gasto_data['fecha'] = fecha_actual
    
    # Funciones auxiliares para procesamiento básico
    def obtener_patron_temporal(hora: int) -> str:
        if 6 <= hora < 12:
            return "mañana"
        elif 12 <= hora < 18:
            return "tarde"
        else:
            return "noche"
    
    def calcular_confianza_inicial(descripcion: str, categoria: CategoriaGasto) -> float:
        desc_lower = descripcion.lower().strip()
        
        if categoria == CategoriaGasto.TRANSPORTE:
            if any(word in desc_lower for word in ["uber", "taxi", "bus", "metro", "transporte"]):
                return 0.9
        elif categoria == CategoriaGasto.COMIDA:
            if any(word in desc_lower for word in ["comida", "restaurante", "almuerzo", "cena", "desayuno"]):
                return 0.9
        elif categoria == CategoriaGasto.VARIOS:
            return 0.7
        
        return 0.5
    
    # Procesar según el tipo de uso
    if usar_ml_completo:
        # Procesamiento ML completo para uso API
        gasto_procesado = procesar_gasto_para_ml(gasto_data, db, gasto_data["usuario_id"])
        
        # La categoría ya viene del frontend, no necesitamos predicción
        gasto_procesado['categoria'] = gasto_data["categoria"]
        gasto_procesado['confianza_categoria'] = calcular_confianza_inicial(
            gasto_data["descripcion"], gasto_data["categoria"]
        )
        
        # Crear gasto con procesamiento ML completo
        db_gasto = Gasto(
            usuario_id=gasto_data["usuario_id"],
            descripcion=gasto_data["descripcion"],
            monto=gasto_data["monto"],
            categoria=gasto_procesado['categoria'],
            fecha=fecha_actual,
            texto_normalizado=gasto_procesado['texto_normalizado'],
            dia_semana=gasto_procesado['dia_semana'],
            hora_gasto=gasto_procesado['hora_gasto'],
            es_fin_semana=gasto_procesado['es_fin_semana'],
            patron_temporal=gasto_procesado['patron_temporal'],
            frecuencia_descripcion=gasto_procesado['frecuencia_descripcion'],
            confianza_categoria=gasto_procesado['confianza_categoria']
        )
    else:
        # Procesamiento básico para uso frontend
        db_gasto = Gasto(
            usuario_id=gasto_data["usuario_id"],
            descripcion=gasto_data["descripcion"],
            monto=gasto_data["monto"],
            categoria=gasto_data["categoria"],
            fecha=fecha_actual,
            # Campos ML básicos
            texto_normalizado=gasto_data["descripcion"].lower().strip(),
            dia_semana=fecha_actual.weekday(),
            hora_gasto=fecha_actual.hour,
            es_fin_semana=fecha_actual.weekday() >= 5,
            patron_temporal=obtener_patron_temporal(fecha_actual.hour),
            frecuencia_descripcion=1,
            confianza_categoria=calcular_confianza_inicial(gasto_data["descripcion"], gasto_data["categoria"]),
            es_recurrente=False
        )
    
    # Guardar en base de datos
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    
    # Analizar patrones y anomalías en segundo plano
    background_tasks.add_task(analizar_gasto_anomalo, db_gasto.id, gasto_data["usuario_id"])
    
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
def actualizar_gasto(gasto_id: int, gasto_update: GastoUpdate, db: Session = Depends(get_db)):
    """Actualizar un gasto existente"""
    db_gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not db_gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    # Actualizar campos proporcionados
    for field, value in gasto_update.dict(exclude_unset=True).items():
        setattr(db_gasto, field, value)
    
    db_gasto.updated_at = datetime.now()
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

@app.delete("/gastos/{gasto_id}")
def eliminar_gasto(gasto_id: int, db: Session = Depends(get_db)):
    """Eliminar un gasto"""
    db_gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not db_gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    db.delete(db_gasto)
    db.commit()
    return {"mensaje": "Gasto eliminado correctamente"}

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
# ENDPOINTS DE MACHINE LEARNING
# ========================

@app.post("/ml/entrenar-clasificador/")
def entrenar_clasificador(usuario_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Entrenar el clasificador de gastos"""
    resultado = clasificador_gastos.entrenar(db, usuario_id)
    
    if resultado["status"] == "success":
        # Guardar información del modelo en BD
        modelo_ml = ModeloML(
            nombre_modelo="clasificador_gastos",
            version="1.0",
            metricas=json.dumps(resultado["reporte"]),
            esta_activo=True,
            dataset_size=resultado["gastos_entrenamiento"]
        )
        db.add(modelo_ml)
        db.commit()
    
    return resultado

@app.post("/ml/entrenar-detector-anomalias/")
def entrenar_detector_anomalias(usuario_id: int, db: Session = Depends(get_db)):
    """Entrenar el detector de anomalías para un usuario"""
    resultado = detector_anomalias.entrenar(db, usuario_id)
    return resultado

@app.get("/ml/predecir-categoria/")
def predecir_categoria(descripcion: str, monto: float = 0, db: Session = Depends(get_db)):
    """Predecir la categoría de un gasto"""
    if not clasificador_gastos.modelo_entrenado:
        clasificador_gastos.cargar_modelo()
    
    categoria, confianza = clasificador_gastos.predecir_categoria(descripcion, monto)
    
    return {
        "categoria": categoria,
        "confianza": confianza,
        "descripcion": descripcion,
        "monto": monto
    }

@app.get("/ml/recomendaciones/{usuario_id}", response_model=List[RecomendacionML])
def obtener_recomendaciones(usuario_id: int, db: Session = Depends(get_db)):
    """Obtener recomendaciones ML para un usuario"""
    recomendaciones = analizador_patrones.generar_recomendaciones(db, usuario_id)
    
    return [
        RecomendacionML(
            descripcion=rec["descripcion"],
            categoria=CategoriaGasto(rec["categoria"]),
            monto_estimado=rec["monto_estimado"],
            confianza=rec["confianza"],
            razon=rec["razon"]
        )
        for rec in recomendaciones
    ]

@app.get("/ml/detectar-anomalias/{usuario_id}")
def detectar_anomalias_usuario(usuario_id: int, dias: int = 30, db: Session = Depends(get_db)):
    """Detectar gastos anómalos para un usuario"""
    from datetime import timedelta
    
    fecha_limite = datetime.now() - timedelta(days=dias)
    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.fecha >= fecha_limite
    ).all()
    
    anomalias = []
    estadisticas = calcular_estadisticas_usuario(db, usuario_id, dias)
    
    for gasto in gastos:
        es_anomalo, razon = validar_gasto_anomalo(gasto, estadisticas)
        if es_anomalo:
            anomalias.append({
                "gasto_id": gasto.id,
                "descripcion": gasto.descripcion,
                "monto": gasto.monto,
                "categoria": gasto.categoria.value if gasto.categoria else "VARIOS",
                "fecha": gasto.fecha,
                "razon": razon
            })
    
    return {
        "anomalias_detectadas": len(anomalias),
        "total_gastos_analizados": len(gastos),
        "anomalias": anomalias
    }

@app.get("/ml/patrones/{usuario_id}")
def analizar_patrones_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Analizar patrones de gasto de un usuario"""
    patrones = analizador_patrones.analizar_patrones_temporales(db, usuario_id)
    
    # Guardar patrones en BD
    for patron in patrones:
        db_patron = PatronGasto(
            usuario_id=usuario_id,
            patron_tipo=TipoPatron(patron["tipo"]),
            descripcion_patron=patron["descripcion"],
            categoria_asociada=CategoriaGasto(patron["categoria"]),
            frecuencia=patron["frecuencia"],
            monto_promedio=patron["monto_promedio"],
            confianza=patron["confianza"],
            dias_semana=json.dumps(patron.get("datos", {}))
        )
        db.add(db_patron)
    
    try:
        db.commit()
    except:
        db.rollback()  # En caso de patrones duplicados
    
    return {
        "patrones_detectados": len(patrones),
        "patrones": patrones
    }

@app.get("/ml/estadisticas/{usuario_id}", response_model=EstadisticasUsuario)
def obtener_estadisticas_ml(usuario_id: int, dias: int = 30, db: Session = Depends(get_db)):
    """Obtener estadísticas ML del usuario"""
    stats = calcular_estadisticas_usuario(db, usuario_id, dias)
    
    # Calcular precisión de clasificación
    gastos_clasificados = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.confianza_categoria > 0.7
    ).count()
    
    total_gastos = db.query(Gasto).filter(Gasto.usuario_id == usuario_id).count()
    precision_clasificacion = gastos_clasificados / max(1, total_gastos)
    
    return EstadisticasUsuario(
        total_gastos=stats["total_gastos"],
        gastos_por_categoria=stats["gastos_por_categoria"],
        promedio_diario=stats["promedio_diario"],
        gastos_recurrentes=stats["gastos_recurrentes"],
        precisión_clasificacion=precision_clasificacion
    )

# ========================
# ENDPOINTS DE TRANSPORTES PREDEFINIDOS
# ========================

@app.post("/transportes/", response_model=TransportePredefinidoSchema)
def crear_transporte_predefinido(transporte: TransportePredefinidoCreate, db: Session = Depends(get_db)):
    """Crear un transporte predefinido"""
    db_transporte = TransportePredefinido(**transporte.dict())
    db.add(db_transporte)
    db.commit()
    db.refresh(db_transporte)
    return db_transporte

@app.get("/transportes/{usuario_id}", response_model=List[TransportePredefinidoSchema])
def listar_transportes_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Listar transportes predefinidos de un usuario"""
    return db.query(TransportePredefinido).filter(
        TransportePredefinido.usuario_id == usuario_id,
        TransportePredefinido.activo == True
    ).order_by(TransportePredefinido.frecuencia_uso.desc()).all()

@app.post("/transportes/{transporte_id}/usar")
def usar_transporte_predefinido(transporte_id: int, db: Session = Depends(get_db)):
    """Marcar un transporte como usado (para ML)"""
    transporte = db.query(TransportePredefinido).filter(
        TransportePredefinido.id == transporte_id
    ).first()
    
    if not transporte:
        raise HTTPException(status_code=404, detail="Transporte no encontrado")
    
    transporte.frecuencia_uso += 1
    transporte.ultima_vez_usado = datetime.now()
    db.commit()
    
    return {"mensaje": "Transporte marcado como usado"}

# ========================
# ENDPOINTS DE FEEDBACK Y UTILIDADES
# ========================

@app.post("/ml/feedback/")
def enviar_feedback_ml(feedback: FeedbackML, db: Session = Depends(get_db)):
    """Enviar feedback sobre análisis ML"""
    analisis = db.query(AnalisisGasto).filter(
        AnalisisGasto.id == feedback.analisis_id
    ).first()
    
    if not analisis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    
    analisis.fue_util = feedback.fue_util
    db.commit()
    
    return {"mensaje": "Feedback registrado correctamente"}

@app.get("/ml/resumen/", response_model=ResumenML)
def obtener_resumen_ml(db: Session = Depends(get_db)):
    """Obtener resumen del estado de ML"""
    patrones_detectados = db.query(PatronGasto).filter(
        PatronGasto.activo == True
    ).count()
    
    gastos_clasificados = db.query(Gasto).filter(
        Gasto.confianza_categoria > 0.7
    ).count()
    
    # Simular datos para el ejemplo
    return ResumenML(
        patrones_detectados=patrones_detectados,
        gastos_clasificados_automaticamente=gastos_clasificados,
        anomalias_detectadas=0,  # Se calculará con el detector real
        precisión_modelo=0.85,   # Se calculará con métricas reales
        ultima_actualizacion=datetime.now()
    )

@app.get("/")
def root():
    """Endpoint raíz de la API"""
    return {
        "mensaje": "Money Manager G5 API con Machine Learning",
        "version": "1.0.0",
        "endpoints": {
            "usuarios": "/usuarios/",
            "gastos": "/gastos/",
            "ml": "/ml/",
            "transportes": "/transportes/",
            "docs": "/docs"
        }
    }

# ========================
# FUNCIONES DE BACKGROUND
# ========================

def analizar_gasto_anomalo(gasto_id: int, usuario_id: int):
    """Función para analizar gastos anómalos en segundo plano"""
    try:
        db = SessionLocal()
        gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
        
        if gasto and detector_anomalias.modelo_entrenado:
            es_anomalo, nivel, razon = detector_anomalias.detectar_anomalia(gasto)
            
            if es_anomalo:
                # Guardar análisis de anomalía
                analisis = AnalisisGasto(
                    usuario_id=usuario_id,
                    tipo_analisis="anomalia",
                    resultado=json.dumps({
                        "gasto_id": gasto_id,
                        "nivel_anomalia": nivel,
                        "razon": razon
                    }),
                    confianza=nivel
                )
                db.add(analisis)
                db.commit()
        
        db.close()
    except Exception as e:
        print(f"Error en análisis de anomalía: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)