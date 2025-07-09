"""
Script de inicialización para Money Manager G5
Prepara la base de datos y los modelos de Machine Learning
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base, engine, SessionLocal
from models import Usuario, Gasto, CategoriaGasto
from ml_services import clasificador_gastos, detector_anomalias
from ml_utils import crear_directorio_modelos, normalizar_texto

def crear_tablas():
    """Crear todas las tablas en la base de datos"""
    print("Creando tablas de la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas correctamente")

def crear_usuario_demo(db):
    """Crear un usuario demo para pruebas"""
    print("Creando usuario demo...")
    
    usuario_demo = Usuario(
        nombre="Usuario Demo",
        email="demo@moneymanager.com",
        telefono="123-456-7890",
        presupuesto_diario=50.0
    )
    
    db.add(usuario_demo)
    db.commit()
    db.refresh(usuario_demo)
    print(f"✓ Usuario demo creado con ID: {usuario_demo.id}")
    
    return usuario_demo

def crear_gastos_demo(db, usuario_id):
    """Crear gastos demo para entrenamiento ML"""
    print("Creando gastos demo para entrenamiento ML...")
    
    gastos_demo = [
        # Gastos de COMIDA
        {"descripcion": "Desayuno en cafetería", "monto": 8.50, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Almuerzo restaurante", "monto": 15.00, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Cena pizza", "monto": 12.00, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Compra supermercado", "monto": 45.00, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Hamburguesa fast food", "monto": 9.50, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Sushi delivery", "monto": 25.00, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Café y tostadas", "monto": 6.00, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Panadería", "monto": 4.50, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Mercado frutas", "monto": 12.50, "categoria": CategoriaGasto.COMIDA},
        {"descripcion": "Cena restaurante", "monto": 35.00, "categoria": CategoriaGasto.COMIDA},
        
        # Gastos de TRANSPORTE
        {"descripcion": "Pasaje bus", "monto": 1.20, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Taxi al trabajo", "monto": 8.50, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Uber viaje", "monto": 12.00, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Metro", "monto": 1.50, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Gasolina", "monto": 45.00, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Parking centro", "monto": 5.00, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Cabify", "monto": 9.50, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Autobus interurbano", "monto": 3.50, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Estacionamiento", "monto": 3.00, "categoria": CategoriaGasto.TRANSPORTE},
        {"descripcion": "Combustible moto", "monto": 15.00, "categoria": CategoriaGasto.TRANSPORTE},
        
        # Gastos VARIOS
        {"descripcion": "Cine", "monto": 10.00, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Regalo cumpleaños", "monto": 25.00, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Farmacia medicinas", "monto": 18.50, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Ropa tienda", "monto": 65.00, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Libro", "monto": 15.00, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Juego videojuego", "monto": 30.00, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Diversión bar", "monto": 20.00, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Compra electronico", "monto": 120.00, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Peluquería", "monto": 25.00, "categoria": CategoriaGasto.VARIOS},
        {"descripcion": "Gimnasio mensual", "monto": 40.00, "categoria": CategoriaGasto.VARIOS}
    ]
    
    # Crear gastos con fechas variadas
    for i, gasto_data in enumerate(gastos_demo):
        # Distribuir gastos en los últimos 30 días
        fecha_gasto = datetime.now() - timedelta(days=random.randint(0, 30))
        
        # Agregar características temporales
        dia_semana = fecha_gasto.weekday()
        hora_gasto = random.randint(7, 22)  # Entre 7 AM y 10 PM
        es_fin_semana = dia_semana >= 5
        
        # Determinar patrón temporal
        if hora_gasto < 12:
            patron_temporal = "mañana"
        elif hora_gasto < 18:
            patron_temporal = "tarde"
        else:
            patron_temporal = "noche"
        
        gasto = Gasto(
            usuario_id=usuario_id,
            descripcion=gasto_data["descripcion"],
            monto=gasto_data["monto"],
            categoria=gasto_data["categoria"],
            fecha=fecha_gasto,
            texto_normalizado=normalizar_texto(gasto_data["descripcion"]),
            dia_semana=dia_semana,
            hora_gasto=hora_gasto,
            es_fin_semana=es_fin_semana,
            patron_temporal=patron_temporal,
            frecuencia_descripcion=1
        )
        
        db.add(gasto)
    
    db.commit()
    print(f"✓ Creados {len(gastos_demo)} gastos demo")

def entrenar_modelos_iniciales(db, usuario_id):
    """Entrenar modelos ML con datos demo"""
    print("Entrenando modelos de Machine Learning...")
    
    # Entrenar clasificador
    print("  - Entrenando clasificador de gastos...")
    resultado_clasificador = clasificador_gastos.entrenar(db, usuario_id)
    if resultado_clasificador["status"] == "success":
        print(f"  ✓ Clasificador entrenado con accuracy: {resultado_clasificador['accuracy']:.2f}")
    else:
        print(f"  ✗ Error entrenando clasificador: {resultado_clasificador['mensaje']}")
    
    # Entrenar detector de anomalías
    print("  - Entrenando detector de anomalías...")
    resultado_detector = detector_anomalias.entrenar(db, usuario_id)
    if resultado_detector["status"] == "success":
        print("  ✓ Detector de anomalías entrenado")
    else:
        print(f"  ✗ Error entrenando detector: {resultado_detector['mensaje']}")

def mostrar_resumen_inicializacion(db):
    """Mostrar resumen de la inicialización"""
    print("\n" + "="*50)
    print("RESUMEN DE INICIALIZACIÓN")
    print("="*50)
    
    usuarios_count = db.query(Usuario).count()
    gastos_count = db.query(Gasto).count()
    
    print(f"Usuarios creados: {usuarios_count}")
    print(f"Gastos creados: {gastos_count}")
    
    print("\nCategorías de gastos disponibles:")
    for categoria in CategoriaGasto:
        count = db.query(Gasto).filter(Gasto.categoria == categoria).count()
        print(f"  - {categoria.value}: {count} gastos")
    
    print("\nModelos ML:")
    print(f"  - Clasificador entrenado: {'Sí' if clasificador_gastos.modelo_entrenado else 'No'}")
    print(f"  - Detector anomalías entrenado: {'Sí' if detector_anomalias.modelo_entrenado else 'No'}")
    
    print("\nEndpoints principales disponibles:")
    print("  - POST /usuarios/ - Crear usuario")
    print("  - POST /gastos/ - Crear gasto (con ML automático)")
    print("  - GET /ml/recomendaciones/{usuario_id} - Obtener recomendaciones")
    print("  - GET /ml/detectar-anomalias/{usuario_id} - Detectar anomalías")
    print("  - GET /ml/patrones/{usuario_id} - Analizar patrones")
    print("  - GET /docs - Documentación interactiva")
    
    print("\nPara iniciar el servidor:")
    print("  uvicorn main:app --reload")
    print("="*50)

def main():
    """Función principal de inicialización"""
    print("Iniciando configuración de Money Manager G5")
    print("="*50)
    
    # Crear directorio para modelos
    crear_directorio_modelos()
    
    # Crear tablas
    crear_tablas()
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        # Verificar si ya existe el usuario demo
        usuario_existente = db.query(Usuario).filter(Usuario.email == "demo@moneymanager.com").first()
        
        if usuario_existente:
            print("Usuario demo ya existe, usando datos existentes...")
            usuario_demo = usuario_existente
        else:
            # Crear usuario demo
            usuario_demo = crear_usuario_demo(db)
            
            # Crear gastos demo
            crear_gastos_demo(db, usuario_demo.id)
        
        # Entrenar modelos ML
        entrenar_modelos_iniciales(db, usuario_demo.id)
        
        # Mostrar resumen
        mostrar_resumen_inicializacion(db)
        
        print("\n🎉 Inicialización completada exitosamente!")
        print(f"Usuario demo ID: {usuario_demo.id}")
        print("Puedes usar este ID para probar los endpoints de ML")
        
    except Exception as e:
        print(f"Error durante la inicialización: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
