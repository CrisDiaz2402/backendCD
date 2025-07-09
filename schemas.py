from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from models import CategoriaGasto, TipoPatron
import enum

# Esquemas base
class UsuarioBase(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = None
    presupuesto_diario: Optional[float] = 0.0

class UsuarioCreate(UsuarioBase):
    pass

class Usuario(UsuarioBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Gastos
class GastoBase(BaseModel):
    descripcion: str
    monto: float
    categoria: Optional[CategoriaGasto] = None
    subcategoria: Optional[str] = None
    ubicacion: Optional[str] = None
    metodo_pago: Optional[str] = None

class GastoCreate(GastoBase):
    usuario_id: int
    
    @validator('monto')
    def validar_monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v

class GastoUpdate(BaseModel):
    descripcion: Optional[str] = None
    monto: Optional[float] = None
    categoria: Optional[CategoriaGasto] = None
    subcategoria: Optional[str] = None
    metodo_pago: Optional[str] = None

class Gasto(GastoBase):
    id: int
    usuario_id: int
    fecha: datetime
    dia_semana: Optional[int] = None
    hora_gasto: Optional[int] = None
    es_fin_semana: Optional[bool] = False
    patron_temporal: Optional[str] = None
    frecuencia_descripcion: Optional[int] = 1
    es_recurrente: Optional[bool] = False
    confianza_categoria: Optional[float] = 0.0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Patrones ML
class PatronGastoBase(BaseModel):
    patron_tipo: TipoPatron
    descripcion_patron: str
    categoria_asociada: Optional[CategoriaGasto] = None
    frecuencia: float
    monto_promedio: float
    confianza: float

class PatronGastoCreate(PatronGastoBase):
    usuario_id: int

class PatronGasto(PatronGastoBase):
    id: int
    usuario_id: int
    monto_minimo: Optional[float] = None
    monto_maximo: Optional[float] = None
    dias_semana: Optional[str] = None
    horas_preferidas: Optional[str] = None
    activo: bool = True
    veces_recomendado: int = 0
    veces_aceptado: int = 0
    efectividad: float = 0.0
    ultima_actualizacion: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Transportes Predefinidos
class TransportePredefinidoBase(BaseModel):
    descripcion: str
    monto: float

class TransportePredefinidoCreate(TransportePredefinidoBase):
    usuario_id: int

class TransportePredefinido(TransportePredefinidoBase):
    id: int
    usuario_id: int
    frecuencia_uso: int = 0
    ultima_vez_usado: Optional[datetime] = None
    activo: bool = True
    
    class Config:
        from_attributes = True

# Esquemas para ML y Análisis
class AnalisisRequest(BaseModel):
    usuario_id: int
    tipo_analisis: str
    parametros: Optional[dict] = None

class AnalisisResponse(BaseModel):
    tipo_analisis: str
    resultado: dict
    confianza: float
    accion_recomendada: Optional[str] = None
    fecha_analisis: datetime

class RecomendacionML(BaseModel):
    descripcion: str
    categoria: CategoriaGasto
    monto_estimado: float
    confianza: float
    razon: str

class AnomaliaDetectada(BaseModel):
    gasto_id: int
    descripcion: str
    monto: float
    monto_esperado: float
    categoria: CategoriaGasto
    nivel_anomalia: float  # 0.0 - 1.0
    razon: str

class PrediccionGasto(BaseModel):
    categoria: CategoriaGasto
    monto_predicho: float
    fecha_estimada: datetime
    confianza: float
    factores: List[str]

# Esquemas para respuestas de estadísticas
class EstadisticasUsuario(BaseModel):
    total_gastos: float
    gastos_por_categoria: dict
    promedio_diario: float
    gastos_recurrentes: int
    precisión_clasificacion: float
    
class ResumenML(BaseModel):
    patrones_detectados: int
    gastos_clasificados_automaticamente: int
    anomalias_detectadas: int
    precisión_modelo: float
    ultima_actualizacion: datetime

# Esquemas para feedback
class FeedbackML(BaseModel):
    analisis_id: int
    fue_util: bool
    comentario: Optional[str] = None

class ModeloInfo(BaseModel):
    nombre_modelo: str
    version: str
    metricas: dict
    fecha_entrenamiento: datetime
    esta_activo: bool
    dataset_size: int
