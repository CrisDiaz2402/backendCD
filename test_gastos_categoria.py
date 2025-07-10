import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://localhost:8000"

def test_gastos_por_categoria():
    """
    Script de prueba para los nuevos endpoints de gastos por categoría
    """
    
    print("=== PRUEBAS DE ENDPOINTS DE GASTOS POR CATEGORÍA ===\n")
    
    # 1. Crear un usuario de prueba
    print("1. Creando usuario de prueba...")
    usuario_data = {
        "nombre": "Usuario Test",
        "email": "test@ejemplo.com",
        "password": "123456",
        "telefono": "1234567890",
        "presupuesto_diario": 100.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=usuario_data)
        if response.status_code == 200:
            usuario = response.json()
            usuario_id = usuario["id"]
            print(f"✓ Usuario creado con ID: {usuario_id}")
        else:
            # El usuario ya existe, intentar obtener ID
            print("Usuario ya existe, usando ID 1 para pruebas")
            usuario_id = 1
    except Exception as e:
        print(f"Error creando usuario: {e}")
        usuario_id = 1
    
    # 2. Crear gastos de prueba en diferentes categorías
    print("\n2. Creando gastos de prueba...")
    
    gastos_prueba = [
        {"descripcion": "Almuerzo restaurante", "monto": 25.50, "categoria": "COMIDA", "usuario_id": usuario_id},
        {"descripcion": "Uber al trabajo", "monto": 12.00, "categoria": "TRANSPORTE", "usuario_id": usuario_id},
        {"descripcion": "Cena familiar", "monto": 45.00, "categoria": "COMIDA", "usuario_id": usuario_id},
        {"descripcion": "Metro", "monto": 2.50, "categoria": "TRANSPORTE", "usuario_id": usuario_id},
        {"descripcion": "Compra farmacia", "monto": 15.75, "categoria": "VARIOS", "usuario_id": usuario_id},
        {"descripcion": "Desayuno café", "monto": 8.00, "categoria": "COMIDA", "usuario_id": usuario_id},
        {"descripcion": "Taxi aeropuerto", "monto": 35.00, "categoria": "TRANSPORTE", "usuario_id": usuario_id}
    ]
    
    gastos_creados = []
    for gasto in gastos_prueba:
        try:
            response = requests.post(f"{BASE_URL}/gastos/", json=gasto)
            if response.status_code == 200:
                gasto_creado = response.json()
                gastos_creados.append(gasto_creado)
                print(f"✓ Gasto creado: {gasto['descripcion']} - {gasto['categoria']}")
            else:
                print(f"✗ Error creando gasto: {response.text}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print(f"Total gastos creados: {len(gastos_creados)}")
    
    # 3. Probar endpoint de gastos por categoría
    print("\n3. Probando endpoint de gastos por categoría...")
    
    categorias = ["COMIDA", "TRANSPORTE", "VARIOS"]
    
    for categoria in categorias:
        try:
            print(f"\n--- Probando categoría: {categoria} ---")
            response = requests.get(f"{BASE_URL}/gastos/usuario/{usuario_id}/categoria/{categoria}")
            
            if response.status_code == 200:
                gastos = response.json()
                print(f"✓ Gastos encontrados en {categoria}: {len(gastos)}")
                
                if gastos:
                    print("Detalles de gastos:")
                    for gasto in gastos:
                        print(f"  - {gasto['descripcion']}: ${gasto['monto']} ({gasto['fecha'][:10]})")
                else:
                    print("  No hay gastos en esta categoría")
            else:
                print(f"✗ Error obteniendo gastos: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # 4. Probar endpoint de estadísticas por categoría
    print("\n4. Probando endpoint de estadísticas por categoría...")
    
    for categoria in categorias:
        try:
            print(f"\n--- Estadísticas para {categoria} ---")
            response = requests.get(f"{BASE_URL}/gastos/usuario/{usuario_id}/categoria/{categoria}/estadisticas")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✓ Estadísticas obtenidas para {categoria}:")
                print(f"  - Total gastos: {stats['total_gastos']}")
                print(f"  - Monto total: ${stats['monto_total']}")
                print(f"  - Monto promedio: ${stats['monto_promedio']}")
                print(f"  - Monto mínimo: ${stats['monto_minimo']}")
                print(f"  - Monto máximo: ${stats['monto_maximo']}")
                print(f"  - Gastos por día: {stats['gastos_por_dia']}")
                
                if stats['gastos_por_fecha']:
                    print("  - Gastos por fecha:")
                    for fecha, gastos_fecha in stats['gastos_por_fecha'].items():
                        total_fecha = sum(g['monto'] for g in gastos_fecha)
                        print(f"    {fecha}: {len(gastos_fecha)} gastos, ${total_fecha:.2f}")
            else:
                print(f"✗ Error obteniendo estadísticas: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # 5. Probar filtros de fecha
    print("\n5. Probando filtros de fecha...")
    
    try:
        # Filtrar últimos 7 días
        fecha_hace_7_dias = (datetime.now() - timedelta(days=7)).isoformat()
        response = requests.get(
            f"{BASE_URL}/gastos/usuario/{usuario_id}/categoria/COMIDA",
            params={"fecha_desde": fecha_hace_7_dias}
        )
        
        if response.status_code == 200:
            gastos_recientes = response.json()
            print(f"✓ Gastos de COMIDA en últimos 7 días: {len(gastos_recientes)}")
        else:
            print(f"✗ Error con filtro de fecha: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 6. Probar casos de error
    print("\n6. Probando casos de error...")
    
    # Usuario inexistente
    try:
        response = requests.get(f"{BASE_URL}/gastos/usuario/99999/categoria/COMIDA")
        if response.status_code == 404:
            print("✓ Error 404 para usuario inexistente manejado correctamente")
        else:
            print(f"✗ Respuesta inesperada para usuario inexistente: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Categoría inválida
    try:
        response = requests.get(f"{BASE_URL}/gastos/usuario/{usuario_id}/categoria/INVALIDA")
        if response.status_code == 422:
            print("✓ Error 422 para categoría inválida manejado correctamente")
        else:
            print(f"✗ Respuesta inesperada para categoría inválida: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n=== PRUEBAS COMPLETADAS ===")
    print(f"Usuario de prueba ID: {usuario_id}")
    print(f"Gastos creados: {len(gastos_creados)}")
    print("\nEndpoints implementados:")
    print(f"- GET /gastos/usuario/{{usuario_id}}/categoria/{{categoria}}")
    print(f"- GET /gastos/usuario/{{usuario_id}}/categoria/{{categoria}}/estadisticas")

if __name__ == "__main__":
    test_gastos_por_categoria()
