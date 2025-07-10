# API de Gastos por Categoría - Money Manager G5

## Nuevos Endpoints Implementados

Se han implementado dos nuevos endpoints para obtener gastos de usuarios filtrados por categoría, así como estadísticas detalladas.

### 1. Obtener Gastos por Usuario y Categoría

**Endpoint:** `GET /gastos/usuario/{usuario_id}/categoria/{categoria}`

**Descripción:** Obtiene todos los gastos de un usuario específico filtrados por categoría.

**Parámetros de Ruta:**
- `usuario_id` (int): ID del usuario
- `categoria` (string): Categoría de gastos. Valores válidos:
  - `COMIDA`
  - `TRANSPORTE` 
  - `VARIOS`

**Parámetros de Query (Opcionales):**
- `limite` (int): Número máximo de gastos a retornar (default: 100)
- `fecha_desde` (datetime): Fecha inicial para filtrar gastos
- `fecha_hasta` (datetime): Fecha final para filtrar gastos

**Ejemplo de Uso:**
```bash
# Obtener gastos de comida del usuario 1
GET /gastos/usuario/1/categoria/COMIDA

# Obtener gastos de transporte con límite
GET /gastos/usuario/1/categoria/TRANSPORTE?limite=50

# Obtener gastos de comida en un rango de fechas
GET /gastos/usuario/1/categoria/COMIDA?fecha_desde=2025-07-01T00:00:00&fecha_hasta=2025-07-10T23:59:59
```

**Respuesta Exitosa (200):**
```json
[
  {
    "id": 1,
    "usuario_id": 1,
    "descripcion": "Almuerzo restaurante",
    "monto": 25.50,
    "categoria": "COMIDA",
    "fecha": "2025-07-10T12:30:00",
    "dia_semana": 3,
    "hora_gasto": 12,
    "es_fin_semana": false,
    "patron_temporal": "tarde",
    "frecuencia_descripcion": 1,
    "es_recurrente": false,
    "confianza_categoria": 0.9,
    "created_at": "2025-07-10T12:30:00",
    "updated_at": "2025-07-10T12:30:00"
  }
]
```

**Errores:**
- `404`: Usuario no encontrado
- `422`: Categoría inválida

### 2. Obtener Estadísticas de Gastos por Categoría

**Endpoint:** `GET /gastos/usuario/{usuario_id}/categoria/{categoria}/estadisticas`

**Descripción:** Obtiene estadísticas detalladas de los gastos de un usuario en una categoría específica.

**Parámetros de Ruta:**
- `usuario_id` (int): ID del usuario
- `categoria` (string): Categoría de gastos (COMIDA, TRANSPORTE, VARIOS)

**Parámetros de Query (Opcionales):**
- `dias` (int): Número de días hacia atrás para el análisis (default: 30)

**Ejemplo de Uso:**
```bash
# Estadísticas de gastos de comida del último mes
GET /gastos/usuario/1/categoria/COMIDA/estadisticas

# Estadísticas de gastos de transporte de los últimos 7 días
GET /gastos/usuario/1/categoria/TRANSPORTE/estadisticas?dias=7
```

**Respuesta Exitosa (200):**
```json
{
  "usuario_id": 1,
  "categoria": "COMIDA",
  "periodo_dias": 30,
  "total_gastos": 15,
  "monto_total": 385.50,
  "monto_promedio": 25.70,
  "monto_minimo": 8.00,
  "monto_maximo": 65.00,
  "gastos_por_dia": 0.50,
  "gastos_por_fecha": {
    "2025-07-10": [
      {
        "id": 1,
        "descripcion": "Almuerzo restaurante",
        "monto": 25.50,
        "hora": "12:30"
      }
    ]
  },
  "gastos": [
    {
      "id": 1,
      "descripcion": "Almuerzo restaurante",
      "monto": 25.50,
      "fecha": "2025-07-10T12:30:00",
      "confianza_categoria": 0.9
    }
  ]
}
```

**Campos de la Respuesta:**
- `usuario_id`: ID del usuario analizado
- `categoria`: Categoría analizada
- `periodo_dias`: Período de días analizado
- `total_gastos`: Número total de gastos en la categoría
- `monto_total`: Suma total de todos los gastos
- `monto_promedio`: Promedio de gasto por transacción
- `monto_minimo`: Gasto más bajo en la categoría
- `monto_maximo`: Gasto más alto en la categoría
- `gastos_por_dia`: Promedio de gastos por día
- `gastos_por_fecha`: Gastos agrupados por fecha
- `gastos`: Lista completa de gastos con detalles

**Errores:**
- `404`: Usuario no encontrado
- `422`: Categoría inválida

## Categorías Disponibles

El sistema maneja tres categorías principales de gastos:

1. **COMIDA**: Gastos relacionados con alimentación
   - Restaurantes
   - Supermercados
   - Delivery de comida
   - Cafeterías

2. **TRANSPORTE**: Gastos de movilidad
   - Uber/Taxi
   - Metro/Bus
   - Combustible
   - Estacionamiento

3. **VARIOS**: Otros gastos no categorizados
   - Farmacia
   - Entretenimiento
   - Compras diversas
   - Servicios

## Funcionalidades Adicionales

### Filtros de Fecha
Ambos endpoints soportan filtros de fecha para analizar períodos específicos:
- `fecha_desde`: Incluye gastos desde esta fecha
- `fecha_hasta`: Incluye gastos hasta esta fecha
- `dias`: Para estadísticas, analiza los últimos N días

### Ordenamiento
Los gastos se retornan ordenados por fecha de forma descendente (más recientes primero).

### Límites
Se puede controlar el número máximo de gastos retornados usando el parámetro `limite`.

## Casos de Uso

### Frontend/App Móvil
```javascript
// Obtener gastos de comida del usuario logueado
const gastosComida = await fetch(`/gastos/usuario/${userId}/categoria/COMIDA`);

// Mostrar estadísticas mensuales de transporte
const statsTransporte = await fetch(`/gastos/usuario/${userId}/categoria/TRANSPORTE/estadisticas?dias=30`);
```

### Análisis de Patrones
```javascript
// Comparar gastos de diferentes categorías
const categories = ['COMIDA', 'TRANSPORTE', 'VARIOS'];
const statsPromises = categories.map(cat => 
  fetch(`/gastos/usuario/${userId}/categoria/${cat}/estadisticas`)
);
const allStats = await Promise.all(statsPromises);
```

### Reportes Personalizados
```javascript
// Reporte semanal de gastos de comida
const gastosSemanales = await fetch(
  `/gastos/usuario/${userId}/categoria/COMIDA?fecha_desde=${startOfWeek}&fecha_hasta=${endOfWeek}`
);
```

## Integración con ML

Los endpoints están completamente integrados con el sistema de Machine Learning existente:

- Los gastos retornados incluyen información de confianza de categorización
- Las estadísticas consideran la calidad de la clasificación automática
- Se pueden usar para entrenar y validar modelos de predicción de gastos

## Testing

Se incluye un script de pruebas completo en `test_gastos_categoria.py` que valida:
- Creación de gastos de prueba
- Funcionamiento de ambos endpoints
- Filtros de fecha
- Manejo de errores
- Casos extremos

Para ejecutar las pruebas:
```bash
python test_gastos_categoria.py
```

## Consideraciones de Rendimiento

- Los endpoints incluyen índices en las columnas más consultadas
- Se limita el número de resultados por defecto
- Las consultas están optimizadas para evitar N+1 queries
- Se recomienda usar paginación para grandes volúmenes de datos

## Seguridad

- Validación de tipos en todos los parámetros
- Verificación de existencia de usuario antes de consultar gastos
- Manejo apropiado de errores sin exponer información sensible
- Compatible con el sistema de autenticación existente (tokens JWT)
