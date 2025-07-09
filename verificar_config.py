"""
Script de verificación de la configuración de Money Manager G5
"""
import sys
import os

def verificar_dependencias():
    """Verificar que todas las dependencias estén instaladas"""
    dependencias = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'pandas', 'numpy', 
        'sklearn', 'nltk', 'textblob', 'joblib', 'pydantic'
    ]
    
    print("Verificando dependencias de Python...")
    faltantes = []
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} - FALTANTE")
            faltantes.append(dep)
    
    if faltantes:
        print(f"\nDependencias faltantes: {', '.join(faltantes)}")
        print("Ejecuta: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ Todas las dependencias están instaladas")
        return True

def verificar_estructura_archivos():
    """Verificar que todos los archivos necesarios existan"""
    archivos_requeridos = [
        'main.py', 'models.py', 'schemas.py', 'database.py',
        'ml_services.py', 'ml_utils.py', 'requirements.txt',
        'init_setup.py', '.env.example'
    ]
    
    print("\nVerificando estructura de archivos...")
    faltantes = []
    
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            print(f"✓ {archivo}")
        else:
            print(f"✗ {archivo} - FALTANTE")
            faltantes.append(archivo)
    
    if faltantes:
        print(f"\nArchivos faltantes: {', '.join(faltantes)}")
        return False
    else:
        print("\n✓ Todos los archivos están presentes")
        return True

def verificar_configuracion():
    """Verificar configuración del entorno"""
    print("\nVerificando configuración...")
    
    # Verificar Python version
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}")
    else:
        print(f"✗ Python {version.major}.{version.minor} - Se requiere 3.8+")
        return False
    
    # Verificar archivo .env
    if os.path.exists('.env'):
        print("✓ Archivo .env encontrado")
    else:
        print("⚠ Archivo .env no encontrado")
        print("  Copia .env.example a .env y configura tu base de datos")
    
    # Verificar directorio models
    if not os.path.exists('models'):
        os.makedirs('models')
        print("✓ Directorio models/ creado")
    else:
        print("✓ Directorio models/ existe")
    
    return True

def mostrar_siguiente_pasos():
    """Mostrar los siguientes pasos"""
    print("\n" + "="*60)
    print("SIGUIENTES PASOS PARA COMPLETAR LA CONFIGURACIÓN")
    print("="*60)
    
    print("\n1. Configurar Base de Datos:")
    print("   - Copia .env.example a .env")
    print("   - Configura DATABASE_URL con tus credenciales de PostgreSQL")
    print("   - Ejemplo: postgresql://usuario:password@localhost:5432/money_manager_g5")
    
    print("\n2. Inicializar la Base de Datos:")
    print("   python init_setup.py")
    
    print("\n3. Iniciar el Servidor:")
    print("   uvicorn main:app --reload")
    
    print("\n4. Acceder a la Documentación:")
    print("   http://localhost:8000/docs")
    
    print("\n5. Probar los Endpoints ML:")
    print("   - POST /usuarios/ (crear usuario)")
    print("   - POST /gastos/ (crear gasto con ML automático)")
    print("   - GET /ml/recomendaciones/{usuario_id}")
    print("   - GET /ml/detectar-anomalias/{usuario_id}")
    
    print("\n" + "="*60)
    print("¡Money Manager G5 con Machine Learning está listo! 🚀")
    print("="*60)

def main():
    """Función principal"""
    print("Money Manager G5 - Verificación de Configuración")
    print("="*50)
    
    dependencias_ok = verificar_dependencias()
    archivos_ok = verificar_estructura_archivos()
    config_ok = verificar_configuracion()
    
    print("\n" + "="*50)
    print("RESUMEN DE VERIFICACIÓN")
    print("="*50)
    
    if dependencias_ok and archivos_ok and config_ok:
        print("✅ CONFIGURACIÓN COMPLETA")
        print("El proyecto está listo para usar")
        mostrar_siguiente_pasos()
    else:
        print("❌ CONFIGURACIÓN INCOMPLETA")
        print("Revisa los errores arriba y corrígelos antes de continuar")
    
    return dependencias_ok and archivos_ok and config_ok

if __name__ == "__main__":
    main()
