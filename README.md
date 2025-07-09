# Money Manager G5 - Backend con Machine Learning

Una API REST completa para gestión de gastos personales con capacidades avanzadas de Machine Learning.

## 🚀 Características Principales

### Machine Learning Integrado
- **Clasificación Automática**: Clasifica gastos automáticamente usando NLP y Random Forest
- **Detección de Anomalías**: Identifica gastos inusuales usando clustering y análisis estadístico
- **Análisis de Patrones**: Detecta patrones temporales y recurrentes en los gastos
- **Recomendaciones Inteligentes**: Sugiere gastos probables basados en historial

### Funcionalidades Core
- Gestión completa de usuarios y gastos
- Categorización automática (Comida, Transporte, Varios)
- Transportes predefinidos con frecuencia de uso
- Análisis temporal avanzado (día de semana, hora, patrones estacionales)
- Feedback para mejorar modelos ML

## 📊 Arquitectura de Base de Datos

### Estructura Optimizada para ML

```
Usuarios
├── Gastos (tabla principal unificada)
│   ├── Campos básicos: descripción, monto, categoría
│   ├── Campos ML: texto_normalizado, dia_semana, hora_gasto
│   ├── Patrones: es_fin_semana, patron_temporal, frecuencia_descripcion
│   └── Confianza: confianza_categoria, es_recurrente
├── PatronGasto (patrones detectados por ML)
├── TransportePredefinido (recomendaciones de transporte)
├── ModeloML (versionado de modelos)
└── AnalisisGasto (resultados y feedback ML)
```

### ¿Por qué Esta Estructura?

1. **Tabla Unificada**: Un solo modelo `Gasto` para todos los tipos permite:
   - Análisis de patrones globales
   - Clasificación automática consistente
   - Detección de anomalías en todos los tipos de gasto
   - Facilita el entrenamiento de modelos ML

2. **Campos ML Específicos**: Campos como `texto_normalizado`, `dia_semana`, `patron_temporal` optimizan:
   - Velocidad de procesamiento ML
   - Calidad de predicciones
   - Análisis temporal preciso

3. **Separación de Metadatos ML**: Tablas como `PatronGasto` y `ModeloML` permiten:
   - Versionado de modelos
   - Tracking de efectividad
   - Mejora continua

## 🛠️ Instalación

### Prerrequisitos
- Python 3.8+
- PostgreSQL
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd MoneyManagerG5/backend
```

2. **Crear entorno virtual**
```bash
python -m venv env
# Windows
env\Scripts\activate
# Linux/Mac
source env/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**
```bash
# Crear archivo .env basado en .env.example
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL
```

5. **Inicializar la aplicación**
```bash
python init_setup.py
```

6. **Ejecutar el servidor**
```bash
uvicorn main:app --reload
```

## 📱 Integración con App Móvil

### Endpoints Principales

#### Gestión de Gastos
```http
POST /gastos/
{
  "usuario_id": 1,
  "descripcion": "Almuerzo restaurante",
  "monto": 15.50,
  "categoria": "COMIDA"  // Opcional - se predice automáticamente
}
```

#### Machine Learning
```http
GET /ml/recomendaciones/{usuario_id}     # Recomendaciones inteligentes
GET /ml/detectar-anomalias/{usuario_id}  # Gastos anómalos
GET /ml/patrones/{usuario_id}            # Análisis de patrones
GET /ml/predecir-categoria/?descripcion="taxi"&monto=10
```

#### Pantallas de la App

**Pantalla "Varios"**:
- `POST /gastos/` con `categoria: "VARIOS"`
- `GET /ml/recomendaciones/{usuario_id}` para sugerencias

**Pantalla "Transporte"**:
- `GET /transportes/{usuario_id}` para opciones predefinidas
- `POST /transportes/{transporte_id}/usar` para tracking ML

**Pantalla "Comida"**:
- `POST /gastos/` con clasificación automática
- Detección de patrones de comida por horarios

## 🤖 Modelos de Machine Learning

### 1. Clasificador de Gastos
- **Algoritmo**: Random Forest + TF-IDF
- **Entrada**: Descripción, monto, hora, día de semana
- **Salida**: Categoría + confianza
- **Entrenamiento**: Automático con gastos etiquetados

### 2. Detector de Anomalías
- **Algoritmo**: K-Means + Análisis estadístico
- **Entrada**: Monto, patrones temporales, categoría
- **Salida**: Es anómalo + nivel + razón
- **Umbral**: 2 desviaciones estándar por categoría

### 3. Analizador de Patrones
- **Tipos**: Recurrente, Estacional, Tendencia
- **Análisis**: Frecuencia, días preferidos, montos típicos
- **Recomendaciones**: Basadas en patrones históricos

## 📈 Métricas y Monitoreo

### Métricas de ML Disponibles
- Accuracy del clasificador
- Gastos clasificados automáticamente
- Patrones detectados activos
- Efectividad de recomendaciones
- Feedback de usuarios

### Endpoints de Estadísticas
```http
GET /ml/estadisticas/{usuario_id}  # Estadísticas personales
GET /ml/resumen/                   # Resumen global del sistema
```

## 🔧 Configuración Avanzada

### Variables de Entorno (.env)
```
DATABASE_URL=postgresql://user:pass@localhost:5432/money_manager
ML_MODEL_PATH=./models/
ML_UPDATE_INTERVAL=3600
SECRET_KEY=your-secret-key
```

### Reentrenamiento de Modelos
```bash
# Manual
curl -X POST "http://localhost:8000/ml/entrenar-clasificador/"

# Automático (cada 1 hora según ML_UPDATE_INTERVAL)
```

## 📚 Documentación de API

Una vez ejecutando el servidor, visita:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚀 Despliegue en Producción

### Usando Docker (Recomendado)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Variables de Producción
- Configurar `DATABASE_URL` con PostgreSQL en producción
- Usar Redis para Celery (procesamiento en background)
- Configurar logging adecuado

## 🤝 Contribución

1. Fork el proyecto
2. Crear branch para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.

## 🙋‍♂️ Soporte

- **Issues**: GitHub Issues
- **Email**: support@moneymanager.com
- **Docs**: http://localhost:8000/docs

---

**Money Manager G5** - Gestión inteligente de gastos con Machine Learning 🤖💰
