"""
Script para probar el sistema de autenticación de Money Manager G5
"""
import requests
import json

BASE_URL = "https://backendcd.onrender.com"
headers = {"Content-Type": "application/json"}

def test_registro_usuario():
    """Probar registro de usuario"""
    print("🔐 Probando registro de usuario...")
    
    usuario_data = {
        "nombre": "Juan Pérez",
        "email": "juan.perez@test.com",
        "telefono": "+1234567890",
        "presupuesto_diario": 50.0,
        "password": "mipassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", 
                           json=usuario_data, headers=headers)
    
    if response.status_code == 200:
        usuario = response.json()
        print(f"✅ Usuario registrado exitosamente!")
        print(f"   - ID: {usuario['id']}")
        print(f"   - Nombre: {usuario['nombre']}")
        print(f"   - Email: {usuario['email']}")
        print(f"   - Activo: {usuario['is_active']}")
        return usuario
    else:
        print(f"❌ Error en registro: {response.text}")
        return None

def test_login_usuario(email, password):
    """Probar login de usuario"""
    print(f"\n🔑 Probando login para: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login-json", 
                           json=login_data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Login exitoso!")
        print(f"   - Token: {token_data['access_token'][:50]}...")
        print(f"   - User ID: {token_data['user_id']}")
        print(f"   - Expira en: {token_data['expires_in']} segundos")
        return token_data
    else:
        print(f"❌ Error en login: {response.text}")
        return None

def test_usuario_autenticado(token):
    """Probar acceso con token de autenticación"""
    print(f"\n👤 Probando acceso autenticado...")
    
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=auth_headers)
    
    if response.status_code == 200:
        usuario = response.json()
        print(f"✅ Acceso autenticado exitoso!")
        print(f"   - Nombre: {usuario['nombre']}")
        print(f"   - Email: {usuario['email']}")
        print(f"   - Último login: {usuario['last_login']}")
        return usuario
    else:
        print(f"❌ Error en acceso autenticado: {response.text}")
        return None

def test_crear_gasto_autenticado(token, usuario_id):
    """Probar crear gasto con autenticación"""
    print(f"\n💰 Probando crear gasto autenticado...")
    
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    gasto_data = {
        "usuario_id": usuario_id,
        "descripcion": "Almuerzo con autenticación",
        "monto": 25.50,
        "categoria": "comida"
    }
    
    response = requests.post(f"{BASE_URL}/gastos/", 
                           json=gasto_data, headers=auth_headers)
    
    if response.status_code == 200:
        gasto = response.json()
        print(f"✅ Gasto creado exitosamente!")
        print(f"   - ID: {gasto['id']}")
        print(f"   - Descripción: {gasto['descripcion']}")
        print(f"   - Monto: ${gasto['monto']}")
        print(f"   - Categoría: {gasto['categoria']}")
        return gasto
    else:
        print(f"❌ Error creando gasto: {response.text}")
        return None

def main():
    """Función principal para probar autenticación"""
    print("🔐 Money Manager G5 - Prueba de Sistema de Autenticación")
    print("=" * 65)
    
    # 1. Registrar usuario
    usuario = test_registro_usuario()
    
    if usuario:
        # 2. Hacer login
        token_data = test_login_usuario(usuario['email'], "mipassword123")
        
        if token_data:
            token = token_data['access_token']
            
            # 3. Probar acceso autenticado
            usuario_auth = test_usuario_autenticado(token)
            
            if usuario_auth:
                # 4. Crear gasto autenticado
                test_crear_gasto_autenticado(token, usuario['id'])
        
        print("\n" + "=" * 65)
        print("🎉 ¡Pruebas de autenticación completadas!")
        print("Ahora puedes usar estos endpoints en tu app móvil:")
        print(f"   - Registro: POST {BASE_URL}/auth/register")
        print(f"   - Login: POST {BASE_URL}/auth/login-json")
        print(f"   - Perfil: GET {BASE_URL}/auth/me")
        print("=" * 65)

if __name__ == "__main__":
    main()
