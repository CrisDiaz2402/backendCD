"""
Script de pruebas para la API de Money Manager G5
Demuestra todas las funcionalidades de Machine Learning
"""
import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

def probar_crear_usuario():
    """Probar creación de usuario"""
    print("🧪 Probando creación de usuario...")
    
    usuario_data = {
        "nombre": "Juan Pérez",
        "email": "juan.perez@email.com",
        "telefono": "123-456-7890",
        "presupuesto_diario": 50.0
    }
    
    response = requests.post(f"{BASE_URL}/usuarios/", 
                           json=usuario_data, headers=headers)
    
    if response.status_code == 200:
        usuario = response.json()
        print(f"✅ Usuario creado: ID {usuario['id']}")
        return usuario['id']
    else:
        print(f"❌ Error creando usuario: {response.text}")
        return None

def probar_crear_gastos(usuario_id):
    """Probar creación de gastos con clasificación automática"""
    print("\n🧪 Probando creación de gastos con ML...")
    
    gastos_prueba = [
        {"descripcion": "Almuerzo en restaurante", "monto": 15.50},
        {"descripcion": "Taxi al trabajo", "monto": 8.00},
        {"descripcion": "Compra supermercado", "monto": 45.20},
        {"descripcion": "Uber a casa", "monto": 12.50},
        {"descripcion": "Cena pizza delivery", "monto": 18.90},
        {"descripcion": "Bus al centro", "monto": 1.50},
        {"descripcion": "Café y tostadas", "monto": 6.50},
        {"descripcion": "Entrada cine", "monto": 12.00}
    ]
    
    gastos_creados = []
    
    for gasto_data in gastos_prueba:
        gasto_data["usuario_id"] = usuario_id
        
        response = requests.post(f"{BASE_URL}/gastos/", 
                               json=gasto_data, headers=headers)
        
        if response.status_code == 200:
            gasto = response.json()
            categoria = gasto.get('categoria', 'No clasificado')
            confianza = gasto.get('confianza_categoria', 0)
            print(f"✅ Gasto: '{gasto['descripcion']}' → {categoria} (confianza: {confianza:.2f})")
            gastos_creados.append(gasto['id'])
        else:
            print(f"❌ Error creando gasto: {response.text}")
    
    return gastos_creados

def probar_clasificacion_automatica():
    """Probar clasificación automática sin crear gastos"""
    print("\n🧪 Probando clasificación automática...")
    
    textos_prueba = [
        {"descripcion": "Hamburguesa McDonald's", "monto": 9.50},
        {"descripcion": "Metro línea 1", "monto": 1.20},
        {"descripcion": "Regalo cumpleaños", "monto": 25.00},
        {"descripcion": "Gasolina estación", "monto": 40.00}
    ]
    
    for texto in textos_prueba:
        response = requests.get(f"{BASE_URL}/ml/predecir-categoria/", 
                              params=texto)
        
        if response.status_code == 200:
            prediccion = response.json()
            print(f"✅ '{texto['descripcion']}' → {prediccion['categoria']} (confianza: {prediccion['confianza']:.2f})")
        else:
            print(f"❌ Error en predicción: {response.text}")

def probar_recomendaciones(usuario_id):
    """Probar recomendaciones ML"""
    print(f"\n🧪 Probando recomendaciones ML para usuario {usuario_id}...")
    
    response = requests.get(f"{BASE_URL}/ml/recomendaciones/{usuario_id}")
    
    if response.status_code == 200:
        recomendaciones = response.json()
        print(f"✅ {len(recomendaciones)} recomendaciones encontradas:")
        for rec in recomendaciones:
            print(f"   - {rec['descripcion']} ({rec['categoria']}) - ${rec['monto_estimado']:.2f}")
    else:
        print(f"❌ Error obteniendo recomendaciones: {response.text}")

def probar_deteccion_anomalias(usuario_id):
    """Probar detección de anomalías"""
    print(f"\n🧪 Probando detección de anomalías para usuario {usuario_id}...")
    
    response = requests.get(f"{BASE_URL}/ml/detectar-anomalias/{usuario_id}")
    
    if response.status_code == 200:
        resultado = response.json()
        print(f"✅ Análisis completado: {resultado['anomalias_detectadas']} anomalías de {resultado['total_gastos_analizados']} gastos")
        
        if resultado['anomalias']:
            print("   Anomalías detectadas:")
            for anomalia in resultado['anomalias'][:3]:  # Mostrar solo las primeras 3
                print(f"   - {anomalia['descripcion']}: ${anomalia['monto']} - {anomalia['razon']}")
    else:
        print(f"❌ Error detectando anomalías: {response.text}")

def probar_analisis_patrones(usuario_id):
    """Probar análisis de patrones"""
    print(f"\n🧪 Probando análisis de patrones para usuario {usuario_id}...")
    
    response = requests.get(f"{BASE_URL}/ml/patrones/{usuario_id}")
    
    if response.status_code == 200:
        resultado = response.json()
        print(f"✅ {resultado['patrones_detectados']} patrones detectados:")
        
        for patron in resultado['patrones'][:3]:  # Mostrar solo los primeros 3
            print(f"   - {patron['descripcion']} (confianza: {patron['confianza']:.2f})")
    else:
        print(f"❌ Error analizando patrones: {response.text}")

def probar_estadisticas(usuario_id):
    """Probar estadísticas ML"""
    print(f"\n🧪 Probando estadísticas ML para usuario {usuario_id}...")
    
    response = requests.get(f"{BASE_URL}/ml/estadisticas/{usuario_id}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Estadísticas obtenidas:")
        print(f"   - Total gastado: ${stats['total_gastos']:.2f}")
        print(f"   - Promedio diario: ${stats['promedio_diario']:.2f}")
        print(f"   - Gastos recurrentes: {stats['gastos_recurrentes']}")
        print(f"   - Precisión clasificación: {stats['precisión_clasificacion']:.2%}")
        
        print(f"   - Gastos por categoría:")
        for categoria, monto in stats['gastos_por_categoria'].items():
            print(f"     * {categoria}: ${monto:.2f}")
    else:
        print(f"❌ Error obteniendo estadísticas: {response.text}")

def probar_transportes_predefinidos(usuario_id):
    """Probar transportes predefinidos"""
    print(f"\n🧪 Probando transportes predefinidos para usuario {usuario_id}...")
    
    # Crear transportes predefinidos
    transportes = [
        {"descripcion": "Bus urbano", "monto": 1.50},
        {"descripcion": "Metro", "monto": 1.20},
        {"descripcion": "Taxi corto", "monto": 8.00}
    ]
    
    for transporte_data in transportes:
        transporte_data["usuario_id"] = usuario_id
        response = requests.post(f"{BASE_URL}/transportes/", 
                               json=transporte_data, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Transporte creado: {transporte_data['descripcion']}")
    
    # Listar transportes
    response = requests.get(f"{BASE_URL}/transportes/{usuario_id}")
    if response.status_code == 200:
        transportes = response.json()
        print(f"✅ {len(transportes)} transportes predefinidos disponibles")

def probar_resumen_sistema():
    """Probar resumen del sistema ML"""
    print("\n🧪 Probando resumen del sistema ML...")
    
    response = requests.get(f"{BASE_URL}/ml/resumen/")
    
    if response.status_code == 200:
        resumen = response.json()
        print(f"✅ Resumen del sistema:")
        print(f"   - Patrones detectados: {resumen['patrones_detectados']}")
        print(f"   - Gastos clasificados automáticamente: {resumen['gastos_clasificados_automaticamente']}")
        print(f"   - Precisión del modelo: {resumen['precisión_modelo']:.2%}")
    else:
        print(f"❌ Error obteniendo resumen: {response.text}")

def verificar_servidor():
    """Verificar que el servidor esté funcionando"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Servidor funcionando correctamente")
            return True
        else:
            print(f"❌ Servidor responde con error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
        print("   Asegúrate de que el servidor esté ejecutándose con:")
        print("   uvicorn main:app --reload")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Money Manager G5 - Pruebas de API con Machine Learning")
    print("=" * 60)
    
    # Verificar servidor
    if not verificar_servidor():
        return
    
    # Ejecutar pruebas
    usuario_id = probar_crear_usuario()
    if not usuario_id:
        print("❌ No se pudo crear usuario, abortando pruebas")
        return
    
    # Pruebas de funcionalidades ML
    gastos_ids = probar_crear_gastos(usuario_id)
    probar_clasificacion_automatica()
    probar_recomendaciones(usuario_id)
    probar_deteccion_anomalias(usuario_id)
    probar_analisis_patrones(usuario_id)
    probar_estadisticas(usuario_id)
    probar_transportes_predefinidos(usuario_id)
    probar_resumen_sistema()
    
    print("\n" + "=" * 60)
    print("🎉 ¡Todas las pruebas completadas!")
    print(f"Usuario de prueba creado con ID: {usuario_id}")
    print("Puedes continuar probando en: http://localhost:8000/docs")
    print("=" * 60)

if __name__ == "__main__":
    main()
