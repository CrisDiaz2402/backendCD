# API de Eliminación de Gastos - Money Manager G5

## Endpoints de Eliminación Implementados

Se han implementado varios endpoints para eliminar gastos con diferentes niveles de granularidad y seguridad.

### 1. Eliminar Gasto Individual

**Endpoint:** `DELETE /gastos/{gasto_id}`

**Descripción:** Elimina un gasto específico por su ID.

**Parámetros de Ruta:**
- `gasto_id` (int): ID del gasto a eliminar

**Parámetros de Query (Opcionales):**
- `usuario_id` (int): ID del usuario (para validación adicional de seguridad)

**Ejemplo de Uso:**
```bash
# Eliminar gasto por ID
DELETE /gastos/123

# Eliminar gasto con validación de usuario
DELETE /gastos/123?usuario_id=1
```

**Respuesta Exitosa (200):**
```json
{
  "mensaje": "Gasto eliminado correctamente",
  "gasto_eliminado": {
    "id": 123,
    "descripcion": "Almuerzo restaurante",
    "monto": 25.50,
    "categoria": "COMIDA",
    "fecha": "2025-07-10T12:30:00",
    "usuario_id": 1
  }
}
```

**Errores:**
- `404`: Gasto no encontrado o no pertenece al usuario especificado

### 2. Eliminar Múltiples Gastos

**Endpoint:** `DELETE /gastos/batch`

**Descripción:** Elimina múltiples gastos por sus IDs en una sola operación.

**Parámetros de Query:**
- `gastos_ids` (List[int]): Lista de IDs de gastos a eliminar (máximo 100)
- `usuario_id` (int, opcional): ID del usuario para validación

**Ejemplo de Uso:**
```bash
# Eliminar múltiples gastos
DELETE /gastos/batch?gastos_ids=123&gastos_ids=124&gastos_ids=125

# Con validación de usuario
DELETE /gastos/batch?gastos_ids=123&gastos_ids=124&usuario_id=1
```

**Respuesta Exitosa (200):**
```json
{
  "mensaje": "Eliminados 3 gastos correctamente",
  "gastos_eliminados": 3,
  "monto_total_eliminado": 87.50,
  "gastos_eliminados_detalle": [
    {
      "id": 123,
      "descripcion": "Almuerzo",
      "monto": 25.50,
      "categoria": "COMIDA",
      "fecha": "2025-07-10T12:30:00"
    }
  ],
  "ids_solicitados": 3,
  "ids_no_encontrados": []
}
```

**Errores:**
- `400`: Lista vacía o más de 100 gastos
- `404`: Ningún gasto encontrado con los IDs proporcionados

### 3. Eliminar Gastos por Categoría

**Endpoint:** `DELETE /gastos/usuario/{usuario_id}/categoria/{categoria}`

**Descripción:** Elimina todos los gastos de un usuario en una categoría específica.

**Parámetros de Ruta:**
- `usuario_id` (int): ID del usuario
- `categoria` (string): Categoría (COMIDA, TRANSPORTE, VARIOS)

**Parámetros de Query:**
- `confirmar` (bool): **REQUERIDO** - Debe ser `true` para confirmar la operación
- `fecha_desde` (datetime, opcional): Fecha inicial para filtrar
- `fecha_hasta` (datetime, opcional): Fecha final para filtrar

**Ejemplo de Uso:**
```bash
# Eliminar todos los gastos de comida
DELETE /gastos/usuario/1/categoria/COMIDA?confirmar=true

# Eliminar gastos de transporte en un rango de fechas
DELETE /gastos/usuario/1/categoria/TRANSPORTE?confirmar=true&fecha_desde=2025-07-01T00:00:00&fecha_hasta=2025-07-10T23:59:59
```

**Respuesta Exitosa (200):**
```json
{
  "mensaje": "Eliminados 5 gastos de la categoría COMIDA",
  "usuario_id": 1,
  "categoria": "COMIDA",
  "gastos_eliminados": 5,
  "monto_total_eliminado": 127.50,
  "rango_fechas": {
    "desde": null,
    "hasta": null
  },
  "gastos_eliminados_detalle": [
    {
      "id": 123,
      "descripcion": "Almuerzo",
      "monto": 25.50,
      "fecha": "2025-07-10T12:30:00"
    }
  ]
}
```

**Errores:**
- `400`: Falta confirmación (`confirmar=true`)
- `404`: Usuario no encontrado
- `422`: Categoría inválida

### 4. Eliminar Todos los Gastos de un Usuario

**Endpoint:** `DELETE /gastos/usuario/{usuario_id}/todos`

**Descripción:** Elimina TODOS los gastos de un usuario (operación destructiva).

**Parámetros de Ruta:**
- `usuario_id` (int): ID del usuario

**Parámetros de Query (REQUERIDOS):**
- `confirmar` (bool): Debe ser `true`
- `confirmar_todos` (bool): Debe ser `true` (doble confirmación)

**Ejemplo de Uso:**
```bash
# Eliminar todos los gastos (requiere doble confirmación)
DELETE /gastos/usuario/1/todos?confirmar=true&confirmar_todos=true
```

**Respuesta Exitosa (200):**
```json
{
  "mensaje": "TODOS los gastos del usuario 1 han sido eliminados",
  "usuario_id": 1,
  "total_gastos_eliminados": 25,
  "monto_total_eliminado": 1254.75,
  "estadisticas_por_categoria": {
    "COMIDA": {
      "cantidad": 15,
      "monto_total": 487.50,
      "gastos": [...]
    },
    "TRANSPORTE": {
      "cantidad": 8,
      "monto_total": 156.25,
      "gastos": [...]
    },
    "VARIOS": {
      "cantidad": 2,
      "monto_total": 611.00,
      "gastos": [...]
    }
  },
  "fecha_eliminacion": "2025-07-10T15:30:00",
  "advertencia": "Esta acción no se puede deshacer"
}
```

**Errores:**
- `400`: Falta doble confirmación
- `404`: Usuario no encontrado

## Características de Seguridad

### 1. Validaciones
- **Existencia de Gastos:** Verificación antes de eliminar
- **Pertenencia:** Opcional validar que el gasto pertenece al usuario
- **Límites:** Máximo 100 gastos en eliminación múltiple

### 2. Confirmaciones
- **Operaciones Destructivas:** Requieren `confirmar=true`
- **Eliminación Total:** Requiere doble confirmación
- **Feedback Claro:** Mensajes específicos sobre lo que se eliminará

### 3. Información Detallada
- **Resumen Completo:** Detalles de gastos eliminados
- **Estadísticas:** Montos totales y conteos
- **Auditoría:** Fechas y detalles para logs

## Casos de Uso

### Frontend/App Móvil

#### Eliminar Gasto Individual
```javascript
// Eliminar un gasto específico
const eliminarGasto = async (gastoId, usuarioId) => {
  const response = await fetch(
    `/gastos/${gastoId}?usuario_id=${usuarioId}`,
    { method: 'DELETE' }
  );
  return response.json();
};
```

#### Eliminar Selección Múltiple
```javascript
// Eliminar gastos seleccionados
const eliminarGastosSeleccionados = async (gastosIds, usuarioId) => {
  const params = new URLSearchParams();
  gastosIds.forEach(id => params.append('gastos_ids', id));
  params.append('usuario_id', usuarioId);
  
  const response = await fetch(
    `/gastos/batch?${params}`,
    { method: 'DELETE' }
  );
  return response.json();
};
```

#### Limpiar Categoría
```javascript
// Eliminar todos los gastos de una categoría
const limpiarCategoria = async (usuarioId, categoria) => {
  const response = await fetch(
    `/gastos/usuario/${usuarioId}/categoria/${categoria}?confirmar=true`,
    { method: 'DELETE' }
  );
  return response.json();
};
```

### Administración

#### Limpieza de Datos
```javascript
// Eliminar gastos por rango de fechas
const limpiarGastosPorFecha = async (usuarioId, categoria, fechaDesde, fechaHasta) => {
  const params = new URLSearchParams({
    confirmar: 'true',
    fecha_desde: fechaDesde,
    fecha_hasta: fechaHasta
  });
  
  const response = await fetch(
    `/gastos/usuario/${usuarioId}/categoria/${categoria}?${params}`,
    { method: 'DELETE' }
  );
  return response.json();
};
```

#### Reset Completo (Solo Admin)
```javascript
// Eliminar todos los gastos de un usuario (operación destructiva)
const resetUsuario = async (usuarioId) => {
  const response = await fetch(
    `/gastos/usuario/${usuarioId}/todos?confirmar=true&confirmar_todos=true`,
    { method: 'DELETE' }
  );
  return response.json();
};
```

## Mejores Prácticas

### 1. Confirmación de Usuario
```javascript
// Siempre confirmar antes de operaciones destructivas
const confirmarEliminacion = (tipo, cantidad) => {
  const mensaje = `¿Está seguro de eliminar ${cantidad} gasto(s) de ${tipo}?`;
  return confirm(mensaje);
};
```

### 2. Feedback Visual
```javascript
// Mostrar resultado de eliminación
const mostrarResultadoEliminacion = (resultado) => {
  const { gastos_eliminados, monto_total_eliminado } = resultado;
  alert(`Eliminados ${gastos_eliminados} gastos por $${monto_total_eliminado}`);
};
```

### 3. Manejo de Errores
```javascript
// Manejo robusto de errores
const manejarErrorEliminacion = (error) => {
  if (error.status === 404) {
    alert('Gasto no encontrado');
  } else if (error.status === 400) {
    alert('Debe confirmar la eliminación');
  } else {
    alert('Error inesperado al eliminar');
  }
};
```

## Consideraciones de Rendimiento

### 1. Eliminación en Lotes
- Máximo 100 gastos por operación
- Operaciones atómicas (transacciones)
- Información detallada sin queries adicionales

### 2. Optimizaciones de Base de Datos
- Índices en columnas frecuentemente consultadas
- Eliminación en cascada para relaciones
- Transacciones para mantener consistencia

### 3. Memoria
- Recopilación de información antes de eliminar
- Liberación inmediata de recursos
- Garbage collection automático

## Testing

### Script de Pruebas Incluido
El archivo `test_eliminacion_gastos.py` incluye:
- Pruebas de todos los endpoints
- Casos de error y validaciones
- Verificación de seguridad
- Casos extremos

### Ejecutar Pruebas
```bash
python test_eliminacion_gastos.py
```

## Logging y Auditoría

### Información Registrada
- ID del usuario que elimina
- Detalles de gastos eliminados
- Timestamp de la operación
- Tipo de eliminación realizada

### Recomendaciones
- Implementar logs de auditoría
- Backup antes de eliminaciones masivas
- Historial de acciones para compliance

## Integración con ML

### Impacto en Modelos
- Eliminación afecta datasets de entrenamiento
- Reentrenamiento recomendado después de eliminaciones masivas
- Preservación de patrones históricos importantes

### Recomendaciones ML
- Backup de gastos antes de eliminar
- Análisis de impacto en precisión de modelos
- Reentrenamiento automático cuando sea necesario
