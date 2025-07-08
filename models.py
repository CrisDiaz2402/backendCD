from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class Gasto(Base):
    __tablename__ = "gastos"
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String, index=True)
    monto = Column(Float)
    fecha = Column(DateTime, default=datetime.utcnow)