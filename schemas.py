from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from models import CategoriaGasto
import enum

# Esquemas base
class UsuarioBase(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = None
    presupuesto_diario: Optional[float] = 0.0

class UsuarioCreate(UsuarioBase):
    password: str  # Contraseña en texto plano (se hasheará)
    
    @validator('password')
    def validar_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
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
    usuario_id: int
    total_gastos_eliminados: int
    monto_total_eliminado: float
    estadisticas_por_categoria: dict
    fecha_eliminacion: str
    advertencia: str
