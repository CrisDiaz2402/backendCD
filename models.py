from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class CategoriaGasto(enum.Enum):
    COMIDA = "comida"
    TRANSPORTE = "transporte"
    VARIOS = "varios"

class TipoPatron(enum.Enum):
    RECURRENTE = "recurrente"
    ANOMALO = "anomalo"
    ESTACIONAL = "estacional"
    TENDENCIA = "tendencia"

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    telefono = Column(String)
    presupuesto_diario = Column(Float, default=0.0)
    
    # Campos de autenticación
    password_hash = Column(String, nullable=False)  # Contraseña hasheada
    is_active = Column(Boolean, default=True)       # Usuario activo/inactivo
    last_login = Column(DateTime, nullable=True)    # Último login
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    gastos = relationship("Gasto", back_populates="usuario")
    patrones = relationship("PatronGasto", back_populates="usuario")
    transportes_predefinidos = relationship("TransportePredefinido", back_populates="usuario")

class Gasto(Base):
    __tablename__ = "gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    descripcion = Column(String, index=True)
    monto = Column(Float, index=True)
    categoria = Column(Enum(CategoriaGasto), index=True)
    fecha = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Campos para Machine Learning
    texto_normalizado = Column(String, index=True)  # Descripción procesada para NLP
    dia_semana = Column(Integer, index=True)  # 0-6 (Lunes-Domingo)
    hora_gasto = Column(Integer, index=True)  # 0-23
    es_fin_semana = Column(Boolean, default=False, index=True)
    patron_temporal = Column(String)  # "mañana", "tarde", "noche"
    frecuencia_descripcion = Column(Integer, default=1)  # Frecuencia de esta descripción
    distancia_promedio_gastos = Column(Float, default=0.0)  # Para análisis geográfico
    es_recurrente = Column(Boolean, default=False, index=True)
    confianza_categoria = Column(Float, default=0.0)  # Confianza del modelo ML
    
    # Campos de auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="gastos")

class PatronGasto(Base):
    """Tabla para almacenar patrones detectados por Machine Learning"""
    __tablename__ = "patrones_gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    patron_tipo = Column(Enum(TipoPatron), index=True)
    descripcion_patron = Column(String)
    categoria_asociada = Column(Enum(CategoriaGasto))
    frecuencia = Column(Float)  # Frecuencia del patrón (días/semanas/meses)
    monto_promedio = Column(Float)
    monto_minimo = Column(Float)
    monto_maximo = Column(Float)
    confianza = Column(Float)  # Confianza del modelo ML (0.0 - 1.0)
    dias_semana = Column(String)  # JSON con días preferidos
    horas_preferidas = Column(String)  # JSON con horas preferidas
    activo = Column(Boolean, default=True, index=True)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Campos para recomendaciones
    veces_recomendado = Column(Integer, default=0)
    veces_aceptado = Column(Integer, default=0)
    efectividad = Column(Float, default=0.0)  # aceptado/recomendado
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="patrones")

class TransportePredefinido(Base):
    """Gastos de transporte predefinidos para recomendaciones ML"""
    __tablename__ = "transportes_predefinidos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    descripcion = Column(String, index=True)
    monto = Column(Float)
    frecuencia_uso = Column(Integer, default=0)  # Para ML de recomendaciones
    ultima_vez_usado = Column(DateTime, nullable=True)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="transportes_predefinidos")

class ModeloML(Base):
    """Tabla para versioning y metadata de modelos ML"""
    __tablename__ = "modelos_ml"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_modelo = Column(String, index=True)  # "clasificador_gastos", "detector_anomalias", etc.
    version = Column(String, index=True)
    path_modelo = Column(String)  # Ruta al archivo del modelo
    metricas = Column(String)  # JSON con métricas del modelo
    fecha_entrenamiento = Column(DateTime, default=datetime.utcnow)
    esta_activo = Column(Boolean, default=False)
    parametros = Column(String)  # JSON con hiperparámetros
    dataset_size = Column(Integer)  # Tamaño del dataset de entrenamiento
    
class AnalisisGasto(Base):
    """Tabla para almacenar análisis y predicciones ML"""
    __tablename__ = "analisis_gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    fecha_analisis = Column(DateTime, default=datetime.utcnow, index=True)
    tipo_analisis = Column(String, index=True)  # "prediccion", "anomalia", "recomendacion"
    resultado = Column(String)  # JSON con resultados del análisis
    confianza = Column(Float)
    accion_recomendada = Column(String, nullable=True)
    fue_util = Column(Boolean, nullable=True)  # Feedback del usuario