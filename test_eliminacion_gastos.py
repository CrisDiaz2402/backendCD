import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://localhost:8000"

def test_eliminacion_gastos():
    """
    Script de prueba para los endpoints de eliminación de gastos
    """
    
    print("=== PRUEBAS DE ENDPOINTS DE ELIMINACIÓN DE GASTOS ===\n")
    
    # 1. Crear usuario de prueba
    print("1. Preparando datos de prueba...")
    usuario_data = {
        "nombre": "Usuario Test Eliminación",
        "email": "test_delete@ejemplo.com",
        "password": "123456",
        "telefono": "1234567890"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=usuario_data)
        if response.status_code == 200:
            usuario = response.json()
            usuario_id = usuario["id"]
            print(f"✓ Usuario creado con ID: {usuario_id}")
        else:
            # Usuario ya existe
            usuario_id = 2  # Usar ID alternativo
            print(f"Usuario ya existe, usando ID: {usuario_id}")
    except Exception as e:
        print(f"Error creando usuario: {e}")
        usuario_id = 2
    
    # 2. Crear gastos de prueba para eliminar
    print("\n2. Creando gastos de prueba...")
    
    gastos_prueba = [
        {"descripcion": "Test Comida 1", "monto": 15.50, "categoria": "COMIDA", "usuario_id": usuario_id},
        {"descripcion": "Test Comida 2", "monto": 25.00, "categoria": "COMIDA", "usuario_id": usuario_id},
        {"descripcion": "Test Transporte 1", "monto": 10.00, "categoria": "TRANSPORTE", "usuario_id": usuario_id},
        {"descripcion": "Test Transporte 2", "monto": 12.50, "categoria": "TRANSPORTE", "usuario_id": usuario_id},
        {"descripcion": "Test Varios 1", "monto": 8.75, "categoria": "VARIOS", "usuario_id": usuario_id},
        {"descripcion": "Test Varios 2", "monto": 20.00, "categoria": "VARIOS", "usuario_id": usuario_id}
    ]
    
    gastos_ids = []
    for gasto in gastos_prueba:
        try:
            response = requests.post(f"{BASE_URL}/gastos/", json=gasto)
            if response.status_code == 200:
                gasto_creado = response.json()
                gastos_ids.append(gasto_creado["id"])
                print(f"✓ Gasto creado: {gasto['descripcion']} (ID: {gasto_creado['id']})")
        except Exception as e:
            print(f"✗ Error creando gasto: {e}")
    
    print(f"Total gastos creados: {len(gastos_ids)}")
    
    # 3. Probar eliminación de gasto individual
    print("\n3. Probando eliminación de gasto individual...")
    
    if gastos_ids:
        gasto_a_eliminar = gastos_ids[0]
        try:
            # Eliminar con validación de usuario
            response = requests.delete(
                f"{BASE_URL}/gastos/{gasto_a_eliminar}",
                params={"usuario_id": usuario_id}
            )
            
            if response.status_code == 200:
                resultado = response.json()
                print(f"✓ Gasto eliminado: {resultado['mensaje']}")
                print(f"  - Gasto: {resultado['gasto_eliminado']['descripcion']}")
                print(f"  - Monto: ${resultado['gasto_eliminado']['monto']}")
                gastos_ids.remove(gasto_a_eliminar)  # Remover de la lista
            else:
                print(f"✗ Error eliminando gasto: {response.text}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # 4. Probar eliminación múltiple
    print("\n4. Probando eliminación múltiple...")
    
    if len(gastos_ids) >= 2:
        gastos_a_eliminar = gastos_ids[:2]  # Tomar los primeros 2
        try:
            # Método usando parámetros en la URL (simulando form data)
            params_string = "&".join([f"gastos_ids={id}" for id in gastos_a_eliminar])
            params_string += f"&usuario_id={usuario_id}"
            
            response = requests.delete(
                f"{BASE_URL}/gastos/batch?{params_string}"
            )
            
            if response.status_code == 200:
                resultado = response.json()
                print(f"✓ Eliminación múltiple exitosa: {resultado['mensaje']}")
                print(f"  - Gastos eliminados: {resultado['gastos_eliminados']}")
                print(f"  - Monto total: ${resultado['monto_total_eliminado']}")
                
                # Remover de la lista
                for id_eliminado in gastos_a_eliminar:
                    if id_eliminado in gastos_ids:
                        gastos_ids.remove(id_eliminado)
            else:
                print(f"✗ Error eliminación múltiple: {response.text}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # 5. Crear más gastos para probar eliminación por categoría
    print("\n5. Creando más gastos para prueba de eliminación por categoría...")
    
    mas_gastos_comida = [
        {"descripcion": "Comida para eliminar 1", "monto": 30.00, "categoria": "COMIDA", "usuario_id": usuario_id},
        {"descripcion": "Comida para eliminar 2", "monto": 35.00, "categoria": "COMIDA", "usuario_id": usuario_id}
    ]
    
    for gasto in mas_gastos_comida:
        try:
            response = requests.post(f"{BASE_URL}/gastos/", json=gasto)
            if response.status_code == 200:
                print(f"✓ Gasto adicional creado: {gasto['descripcion']}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # 6. Probar eliminación por categoría
    print("\n6. Probando eliminación por categoría...")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/gastos/usuario/{usuario_id}/categoria/COMIDA",
            params={"confirmar": "true"}
        )
        
        if response.status_code == 200:
            resultado = response.json()
            print(f"✓ Eliminación por categoría exitosa: {resultado['mensaje']}")
            print(f"  - Categoría: {resultado['categoria']}")
            print(f"  - Gastos eliminados: {resultado['gastos_eliminados']}")
            print(f"  - Monto total: ${resultado['monto_total_eliminado']}")
        else:
            print(f"✗ Error eliminación por categoría: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 7. Probar casos de error
    print("\n7. Probando casos de error...")
    
    # Eliminar gasto inexistente
    try:
        response = requests.delete(f"{BASE_URL}/gastos/99999")
        if response.status_code == 404:
            print("✓ Error 404 para gasto inexistente manejado correctamente")
        else:
            print(f"✗ Respuesta inesperada: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Eliminar sin confirmación
    try:
        response = requests.delete(f"{BASE_URL}/gastos/usuario/{usuario_id}/categoria/TRANSPORTE")
        if response.status_code == 400:
            print("✓ Error 400 para falta de confirmación manejado correctamente")
        else:
            print(f"✗ Respuesta inesperada: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 8. Verificar estado final
    print("\n8. Verificando estado final...")
    
    try:
        response = requests.get(f"{BASE_URL}/gastos/", params={"usuario_id": usuario_id})
        if response.status_code == 200:
            gastos_restantes = response.json()
            print(f"✓ Gastos restantes del usuario: {len(gastos_restantes)}")
            
            if gastos_restantes:
                print("Gastos restantes por categoría:")
                categorias = {}
                for gasto in gastos_restantes:
                    cat = gasto.get('categoria', 'SIN_CATEGORIA')
                    if cat not in categorias:
                        categorias[cat] = 0
                    categorias[cat] += 1
                
                for cat, count in categorias.items():
                    print(f"  - {cat}: {count} gastos")
        else:
            print(f"✗ Error verificando estado: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 9. Probar eliminación total (comentado por seguridad)
    print("\n9. Información sobre eliminación total...")
    print("⚠️  Endpoint para eliminación total disponible:")
    print(f"   DELETE /gastos/usuario/{usuario_id}/todos?confirmar=true&confirmar_todos=true")
    print("   (Requiere doble confirmación por ser operación destructiva)")
    
    print("\n=== PRUEBAS DE ELIMINACIÓN COMPLETADAS ===")
    print("\nEndpoints de eliminación implementados:")
    print("- DELETE /gastos/{gasto_id} - Eliminar gasto individual")
    print("- DELETE /gastos/batch - Eliminar múltiples gastos")
    print("- DELETE /gastos/usuario/{usuario_id}/categoria/{categoria} - Eliminar por categoría")
    print("- DELETE /gastos/usuario/{usuario_id}/todos - Eliminar todos los gastos (destructivo)")
    
    print("\nCaracterísticas de seguridad:")
    print("- Validación de existencia de gastos y usuarios")
    print("- Confirmación requerida para operaciones destructivas")
    print("- Doble confirmación para eliminación total")
    print("- Información detallada de gastos eliminados")
    print("- Manejo de errores y casos extremos")

def test_casos_especiales():
    """Pruebas adicionales para casos especiales"""
    print("\n=== CASOS ESPECIALES ===")
    
    # Prueba de eliminación con lista vacía
    try:
        response = requests.delete(f"{BASE_URL}/gastos/batch", params={"gastos_ids": ""})
        print(f"Eliminación con lista vacía: {response.status_code}")
    except Exception as e:
        print(f"Error esperado con lista vacía: {e}")
    
    # Prueba de eliminación de usuario inexistente
    try:
        response = requests.delete(
            f"{BASE_URL}/gastos/usuario/99999/categoria/COMIDA",
            params={"confirmar": "true"}
        )
        if response.status_code == 404:
            print("✓ Usuario inexistente manejado correctamente")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_eliminacion_gastos()
    test_casos_especiales()
