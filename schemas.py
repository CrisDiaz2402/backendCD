from pydantic import BaseModel, validator
from typing import Optional, List, Any
from datetime import datetime
from models import CategoriaGasto, PeriodoPresupuesto
import enum
import re

# Esquemas base
class UsuarioBase(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = None
    presupuesto: Optional[float] = None
    periodo_presupuesto: Optional[PeriodoPresupuesto] = None

class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str  # Solo campos obligatorios para registro
    
    @validator('password')
    def validar_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v
    
    @validator('email')
    def validar_email(cls, v):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Email no válido')
        return v.lower()

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    presupuesto: Optional[float] = None
    periodo_presupuesto: Optional[PeriodoPresupuesto] = None
    
    @validator('telefono')
    def validar_telefono(cls, v):
        if v is not None:
            # Eliminar espacios y caracteres no numéricos
            telefono_limpio = re.sub(r'[^\d]', '', v)
            if len(telefono_limpio) != 10:
                raise ValueError('El teléfono debe tener exactamente 10 dígitos')
            if not telefono_limpio.isdigit():
                raise ValueError('El teléfono debe contener solo números')
            return telefono_limpio
        return v
    
    @validator('presupuesto')
    def validar_presupuesto_positivo(cls, v):
        if v is not None and v < 0:
            raise ValueError('El presupuesto debe ser positivo o cero')
        return v

class UsuarioLogin(BaseModel):
    email: str
    password: str

class UsuarioResponse(UsuarioBase):
    id: int
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Para compatibilidad con código existente
class Usuario(UsuarioResponse):
    pass

# Esquemas de autenticación
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    expires_in: int

class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    expires_in: int
    user: UsuarioResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    
    class Config:
        from_attributes = True

# Esquemas para Gastos
class GastoBase(BaseModel):
    descripcion: str
    monto: float
    categoria: CategoriaGasto  # Ahora es obligatorio

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

class Gasto(GastoBase):
    id: int
    usuario_id: int
    fecha: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas para eliminación de gastos
class EliminacionGastoRequest(BaseModel):
    gastos_ids: List[int]
    usuario_id: Optional[int] = None
    
    @validator('gastos_ids')
    def validar_lista_ids(cls, v):
        if not v:
            raise ValueError('Debe proporcionar al menos un ID de gasto')
        if len(v) > 100:
            raise ValueError('No se pueden eliminar más de 100 gastos a la vez')
        return v

class GastoEliminado(BaseModel):
    id: int
    descripcion: str
    monto: float
    categoria: Optional[str] = None
    fecha: str

class EliminacionResponse(BaseModel):
    mensaje: str
    gastos_eliminados: int
    monto_total_eliminado: float
    gastos_eliminados_detalle: List[GastoEliminado]
    ids_no_encontrados: List[int] = []

class EliminacionCategoriaResponse(BaseModel):
    mensaje: str
    usuario_id: int
    categoria: str
    gastos_eliminados: int
    monto_total_eliminado: float
    rango_fechas: dict
    gastos_eliminados_detalle: List[GastoEliminado]

class EstadisticasEliminacion(BaseModel):
    cantidad: int
    monto_total: float
    gastos: List[GastoEliminado]

class EliminacionTotalResponse(BaseModel):
    mensaje: str
    gastos_eliminados: int
    usuario_id: int
    monto_total_eliminado: float

# Esquemas para ML y sugerencias
class SugerenciaRequest(BaseModel):
    descripcion: str
    categoria_usuario: CategoriaGasto
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        if len(v.strip()) < 3:
            raise ValueError('La descripción debe tener al menos 3 caracteres')
        return v.strip()

class RecomendacionCategoria(BaseModel):
    categoria_sugerida: str
    categoria_original: str
    coincide: bool
    mensaje: str

class SugerenciaResponse(BaseModel):
    exito: bool
    prediccion_modelo: Optional[Any] = None
    categoria_original: str
    descripcion: str
    recomendacion: RecomendacionCategoria
    confianza: float
    error: Optional[str] = None

# Esquemas para decisión del usuario
class GastoConDecision(BaseModel):
    descripcion: str
    monto: float
    categoria_original: CategoriaGasto  # La que eligió inicialmente el usuario
    categoria_sugerida: Optional[CategoriaGasto] = None  # La que sugirió el ML
    acepta_sugerencia: bool  # True = acepta ML, False = mantiene original
    usuario_id: int
    
    @validator('monto')
    def validar_monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        if len(v.strip()) < 3:
            raise ValueError('La descripción debe tener al menos 3 caracteres')
        return v.strip()

class FeedbackML(BaseModel):
    categoria_original: str
    categoria_sugerida: Optional[str] = None
    categoria_final: str
    usuario_acepto_sugerencia: bool
    timestamp: str

class RespuestaGastoConDecision(BaseModel):
    gasto: Gasto
    decision_usuario: str  # "acepto_sugerencia" o "mantuvo_original"
    categoria_final: CategoriaGasto
    feedback_ml: FeedbackML

# Esquema unificado para crear gastos (con ML opcional)
class GastoCreateUnificado(BaseModel):
    descripcion: str
    monto: float
    categoria: CategoriaGasto
    usar_ml: Optional[bool] = True  # Si debe usar ML para sugerencias
    acepta_sugerencia: Optional[bool] = None  # Solo se usa si usar_ml=True y hay sugerencia diferente
    
    @validator('monto')
    def validar_monto_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        if len(v.strip()) < 3:
            raise ValueError('La descripción debe tener al menos 3 caracteres')
        return v.strip()

class RespuestaGastoUnificado(BaseModel):
    gasto: Optional[Gasto] = None  # Puede ser None si aún no se crea
    ml_usado: bool
    sugerencia_ml: Optional[SugerenciaResponse] = None
    decision_usuario: Optional[str] = None  # "acepto_sugerencia", "mantuvo_original", "sin_sugerencia"
    categoria_final: CategoriaGasto
    feedback_ml: Optional[FeedbackML] = None
