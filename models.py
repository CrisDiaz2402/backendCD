from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class CategoriaGasto(enum.Enum):
    COMIDA = "comida"
    TRANSPORTE = "transporte"
    VARIOS = "varios"

class PeriodoPresupuesto(enum.Enum):
    DIARIO = "diario"
    SEMANAL = "semanal"
    MENSUAL = "mensual"

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    telefono = Column(String, nullable=True)  # Opcional
    presupuesto = Column(Float, nullable=True, default=None)  # Opcional
    periodo_presupuesto = Column(Enum(PeriodoPresupuesto), nullable=True, default=None)  # Opcional
    
    # Campos de autenticación
    password_hash = Column(String, nullable=False)  # Contraseña hasheada
    is_active = Column(Boolean, default=True)       # Usuario activo/inactivo
    last_login = Column(DateTime, nullable=True)    # Último login
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    gastos = relationship("Gasto", back_populates="usuario")

class Gasto(Base):
    __tablename__ = "gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    descripcion = Column(String, index=True)
    monto = Column(Float, index=True)
    categoria = Column(Enum(CategoriaGasto), index=True)
    fecha = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Campos de auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="gastos")