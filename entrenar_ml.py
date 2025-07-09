"""
Script para entrenar los modelos de Machine Learning con datos realistas
"""
import requests
import json
import random
from datetime import datetime, timedelta

# Para desarrollo local
BASE_URL = "http://localhost:8000"

# Para producción (usar esta URL en tu app móvil)
# BASE_URL = "https://tu-dominio-render.com"
headers = {"Content-Type": "application/json"}

def crear_gastos_entrenamiento(usuario_id):
    """Crear gastos con categorías específicas para entrenar el modelo"""
    print("🎯 Creando gastos de entrenamiento con categorías específicas...")
    
    gastos_entrenamiento = [
        # COMIDA - 15 gastos
        {"descripcion": "Desayuno cafetería", "monto": 8.50, "categoria": "comida"},
        {"descripcion": "Almuerzo restaurante", "monto": 15.00, "categoria": "comida"},
        {"descripcion": "Cena pizza", "monto": 12.00, "categoria": "comida"},
        {"descripcion": "Supermercado compra", "monto": 45.00, "categoria": "comida"},
        {"descripcion": "Hamburguesa fast food", "monto": 9.50, "categoria": "comida"},
        {"descripcion": "Sushi delivery", "monto": 25.00, "categoria": "comida"},
        {"descripcion": "Café y tostadas", "monto": 6.00, "categoria": "comida"},
        {"descripcion": "Panadería pan", "monto": 4.50, "categoria": "comida"},
        {"descripcion": "Mercado frutas", "monto": 12.50, "categoria": "comida"},
        {"descripcion": "Restaurante cena", "monto": 35.00, "categoria": "comida"},
        {"descripcion": "McDonald's almuerzo", "monto": 8.90, "categoria": "comida"},
        {"descripcion": "Pollo asado", "monto": 16.50, "categoria": "comida"},
        {"descripcion": "Tienda comida", "monto": 22.00, "categoria": "comida"},
        {"descripcion": "Comida china", "monto": 18.50, "categoria": "comida"},
        {"descripcion": "Desayuno hotel", "monto": 12.00, "categoria": "comida"},
        
        # TRANSPORTE - 15 gastos
        {"descripcion": "Pasaje bus", "monto": 1.20, "categoria": "transporte"},
        {"descripcion": "Taxi trabajo", "monto": 8.50, "categoria": "transporte"},
        {"descripcion": "Uber viaje", "monto": 12.00, "categoria": "transporte"},
        {"descripcion": "Metro pasaje", "monto": 1.50, "categoria": "transporte"},
        {"descripcion": "Gasolina auto", "monto": 45.00, "categoria": "transporte"},
        {"descripcion": "Parking centro", "monto": 5.00, "categoria": "transporte"},
        {"descripcion": "Cabify casa", "monto": 9.50, "categoria": "transporte"},
        {"descripcion": "Autobus interurbano", "monto": 3.50, "categoria": "transporte"},
        {"descripcion": "Estacionamiento", "monto": 3.00, "categoria": "transporte"},
        {"descripcion": "Combustible moto", "monto": 15.00, "categoria": "transporte"},
        {"descripcion": "Bus urbano", "monto": 1.80, "categoria": "transporte"},
        {"descripcion": "Taxi aeropuerto", "monto": 25.00, "categoria": "transporte"},
        {"descripcion": "Metro línea 2", "monto": 1.50, "categoria": "transporte"},
        {"descripcion": "Uber pool", "monto": 6.50, "categoria": "transporte"},
        {"descripcion": "Gasolina estación", "monto": 40.00, "categoria": "transporte"},
        
        # VARIOS - 15 gastos
        {"descripcion": "Entrada cine", "monto": 10.00, "categoria": "varios"},
        {"descripcion": "Regalo cumpleaños", "monto": 25.00, "categoria": "varios"},
        {"descripcion": "Farmacia medicina", "monto": 18.50, "categoria": "varios"},
        {"descripcion": "Ropa tienda", "monto": 65.00, "categoria": "varios"},
        {"descripcion": "Libro librería", "monto": 15.00, "categoria": "varios"},
        {"descripcion": "Videojuego", "monto": 30.00, "categoria": "varios"},
        {"descripcion": "Bar diversión", "monto": 20.00, "categoria": "varios"},
        {"descripcion": "Electrónico tienda", "monto": 120.00, "categoria": "varios"},
        {"descripcion": "Peluquería corte", "monto": 25.00, "categoria": "varios"},
        {"descripcion": "Gimnasio mensual", "monto": 40.00, "categoria": "varios"},
        {"descripcion": "Cine IMAX", "monto": 15.00, "categoria": "varios"},
        {"descripcion": "Regalo día madre", "monto": 35.00, "categoria": "varios"},
        {"descripcion": "Medicina gripe", "monto": 12.50, "categoria": "varios"},
        {"descripcion": "Zapatos nuevos", "monto": 80.00, "categoria": "varios"},
        {"descripcion": "Entretenimiento", "monto": 22.50, "categoria": "varios"}
    ]
    
    gastos_creados = 0
    
    for i, gasto_data in enumerate(gastos_entrenamiento):
        # Crear fechas variadas en los últimos 60 días
        dias_atras = random.randint(0, 60)
        fecha_gasto = datetime.now() - timedelta(days=dias_atras)
        
        gasto_data["usuario_id"] = usuario_id
        
        response = requests.post(f"{BASE_URL}/gastos/", 
                               json=gasto_data, headers=headers)
        
        if response.status_code == 200:
            gasto = response.json()
            gastos_creados += 1
            if gastos_creados % 10 == 0:
                print(f"   ✅ {gastos_creados} gastos creados...")
        else:
            print(f"   ❌ Error creando gasto: {gasto_data['descripcion']}")
            print(f"      Detalle: {response.text}")
            # Mostrar solo los primeros 3 errores para no saturar la salida
            if gastos_creados < 3:
                print(f"      Datos enviados: {gasto_data}")
    
    print(f"✅ Total gastos de entrenamiento creados: {gastos_creados}")
    return gastos_creados

def entrenar_clasificador():
    """Entrenar el clasificador con los datos creados"""
    print("\n🤖 Entrenando clasificador de gastos...")
    
    response = requests.post(f"{BASE_URL}/ml/entrenar-clasificador/")
    
    if response.status_code == 200:
        resultado = response.json()
        if resultado["status"] == "success":
            print(f"✅ Clasificador entrenado exitosamente!")
            print(f"   - Accuracy: {resultado['accuracy']:.2%}")
            print(f"   - Gastos de entrenamiento: {resultado['gastos_entrenamiento']}")
        else:
            print(f"❌ Error entrenando: {resultado['mensaje']}")
    else:
        print(f"❌ Error en request: {response.text}")

def entrenar_detector_anomalias(usuario_id):
    """Entrenar el detector de anomalías"""
    print(f"\n🔍 Entrenando detector de anomalías para usuario {usuario_id}...")
    
    response = requests.post(f"{BASE_URL}/ml/entrenar-detector-anomalias/", 
                           json={"usuario_id": usuario_id})
    
    if response.status_code == 200:
        resultado = response.json()
        if resultado["status"] == "success":
            print(f"✅ Detector de anomalías entrenado!")
        else:
            print(f"❌ Error entrenando detector: {resultado['mensaje']}")
    else:
        print(f"❌ Error en request: {response.text}")

def probar_clasificacion_mejorada():
    """Probar clasificación después del entrenamiento"""
    print("\n🧪 Probando clasificación mejorada...")
    
    textos_prueba = [
        {"descripcion": "Pizza delivery casa", "monto": 18.50},
        {"descripcion": "Uber al centro", "monto": 12.00},
        {"descripcion": "Entrada teatro", "monto": 15.00},
        {"descripcion": "Desayuno café", "monto": 7.50},
        {"descripcion": "Bus al trabajo", "monto": 1.50},
        {"descripcion": "Farmacia aspirinas", "monto": 8.00}
    ]
    
    for texto in textos_prueba:
        response = requests.get(f"{BASE_URL}/ml/predecir-categoria/", 
                              params=texto)
        
        if response.status_code == 200:
            prediccion = response.json()
            print(f"✅ '{texto['descripcion']}' → {prediccion['categoria']} (confianza: {prediccion['confianza']:.2f})")
        else:
            print(f"❌ Error en predicción: {response.text}")

def probar_gastos_nuevos_con_ml(usuario_id):
    """Crear gastos nuevos para ver la clasificación automática"""
    print(f"\n🎯 Probando gastos nuevos con ML entrenado (Usuario {usuario_id})...")
    
    gastos_nuevos = [
        {"descripcion": "Hamburguesa McDonald's", "monto": 9.50},
        {"descripcion": "Metro línea azul", "monto": 1.20},
        {"descripcion": "Cine con palomitas", "monto": 18.00},
        {"descripcion": "Sushi para llevar", "monto": 22.50},
        {"descripcion": "Taxi nocturno", "monto": 15.00}
    ]
    
    for gasto_data in gastos_nuevos:
        gasto_data["usuario_id"] = usuario_id
        
        response = requests.post(f"{BASE_URL}/gastos/", 
                               json=gasto_data, headers=headers)
        
        if response.status_code == 200:
            gasto = response.json()
            categoria = gasto.get('categoria', 'No clasificado')
            confianza = gasto.get('confianza_categoria', 0)
            print(f"✅ '{gasto['descripcion']}' → {categoria} (confianza: {confianza:.2f})")
        else:
            print(f"❌ Error: {response.text}")

def main():
    """Función principal para entrenar ML"""
    print("🎓 Money Manager G5 - Entrenamiento de Machine Learning")
    print("=" * 65)
    
    # Usar el usuario existente (ID 2)
    usuario_id = 2
    
    # Crear datos de entrenamiento
    gastos_creados = crear_gastos_entrenamiento(usuario_id)
    
    if gastos_creados >= 30:  # Necesitamos suficientes datos
        # Entrenar modelos
        entrenar_clasificador()
        entrenar_detector_anomalias(usuario_id)
        
        # Probar clasificación mejorada
        probar_clasificacion_mejorada()
        
        # Probar con gastos nuevos
        probar_gastos_nuevos_con_ml(usuario_id)
        
        print("\n" + "=" * 65)
        print("🎉 ¡Entrenamiento de ML completado!")
        print("Ahora la clasificación automática debería funcionar mucho mejor.")
        print(f"Puedes probar más funciones en: {BASE_URL}/docs")
        print("=" * 65)
    else:
        print("❌ No se crearon suficientes gastos para entrenar")

if __name__ == "__main__":
    main()
