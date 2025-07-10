#!/bin/bash

# Configuración para producción en Render
echo "🚀 Iniciando Money Manager G5 API en producción..."
echo "Puerto: 10000"
echo "Host: 0.0.0.0"
echo "Entorno: Producción"

# Inicializar base de datos si es necesario
echo "📊 Verificando base de datos..."
python -c "
import sys
sys.path.append('.')
try:
    from database import engine
    from models import Base
    Base.metadata.create_all(bind=engine)
    print('✅ Base de datos verificada')
except Exception as e:
    print(f'⚠️ Advertencia DB: {e}')
"

echo "🎯 Iniciando servidor..."
uvicorn main:app --host 0.0.0.0 --port 10000