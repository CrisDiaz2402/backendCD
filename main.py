from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine, Base
from models import Gasto

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependencia para sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Esquema para input
class GastoCreate(BaseModel):
    descripcion: str
    monto: float

@app.post("/gastos/")
def crear_gasto(gasto: GastoCreate, db: Session = Depends(get_db)):
    db_gasto = Gasto(descripcion=gasto.descripcion, monto=gasto.monto)
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

@app.get("/gastos/")
def leer_gastos(db: Session = Depends(get_db)):
    return db.query(Gasto).all()