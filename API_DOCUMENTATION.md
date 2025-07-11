# Money Manager G5 - Documentación de API

## Autenticación

Todos los endpoints protegidos requieren un token JWT en el header:
```
Authorization: Bearer <token_jwt>
```

## Base URL del backend
```
https://backendcd.onrender.com
```

---

## 📝 ENDPOINTS DE AUTENTICACIÓN

### 1. Login
**POST** `/auth/login`

Autentica al usuario y devuelve token JWT junto con información del usuario.

**Request Body:**
```json
{
  "username": "usuario@email.com",
  "password": "mi_contraseña"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nombre": "Juan Pérez",
    "email": "usuario@email.com",
    "telefono": "1234567890",
    "presupuesto": 500.0,
    "periodo_presupuesto": "MENSUAL",
    "is_active": true,
    "last_login": "2025-07-10T17:30:00.000Z",
    "created_at": "2025-07-01T10:00:00.000Z",
    "updated_at": "2025-07-10T17:30:00.000Z"
  }
}
```

**Errors:**
- `401`: Credenciales inválidas
- `400`: Usuario inactivo

---

### 2. Obtener Usuario Actual
**GET** `/auth/me`

Obtiene la información del usuario autenticado.

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Response (200):**
```json
{
  "id": 1,
  "nombre": "Juan Pérez",
  "email": "usuario@email.com",
  "telefono": "1234567890",
  "presupuesto": 500.0,
  "periodo_presupuesto": "MENSUAL",
  "is_active": true,
  "last_login": "2025-07-10T17:30:00.000Z",
  "created_at": "2025-07-01T10:00:00.000Z",
  "updated_at": "2025-07-10T17:30:00.000Z"
}
```

---

## 👤 ENDPOINTS DE PERFIL DE USUARIO

### 3. Actualizar Perfil Completo
**PATCH** `/auth/perfil`

Permite actualizar cualquier campo del perfil del usuario. Solo se envían los campos que se desean modificar.

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Request Body (todos los campos son opcionales):**
```json
{
  "nombre": "Nuevo Nombre",
  "telefono": "9876543210",
  "presupuesto": 1000.0,
  "periodo_presupuesto": "SEMANAL"
}
```

**Validaciones:**
- `nombre`: Mínimo 2 caracteres
- `telefono`: Exactamente 10 dígitos numéricos
- `presupuesto`: Número positivo o cero
- `periodo_presupuesto`: "DIARIO", "SEMANAL", o "MENSUAL"

**Response (200):**
```json
{
  "id": 1,
  "nombre": "Nuevo Nombre",
  "email": "usuario@email.com",
  "telefono": "9876543210",
  "presupuesto": 1000.0,
  "periodo_presupuesto": "SEMANAL",
  "is_active": true,
  "last_login": "2025-07-10T17:30:00.000Z",
  "created_at": "2025-07-01T10:00:00.000Z",
  "updated_at": "2025-07-10T18:00:00.000Z"
}
```

**Errors:**
- `400`: Datos inválidos
- `422`: Error de validación

---

### 4. Actualizar Solo Nombre
**PATCH** `/auth/perfil/nombre`

Endpoint específico para actualizar únicamente el nombre del usuario.

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Request Body:**
```json
{
  "nombre": "Mi Nuevo Nombre"
}
```

**Response (200):**
```json
{
  "message": "Nombre actualizado exitosamente",
  "nombre": "Mi Nuevo Nombre"
}
```

---

### 5. Actualizar Solo Teléfono
**PATCH** `/auth/perfil/telefono`

Endpoint específico para agregar o actualizar el teléfono del usuario.

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Request Body:**
```json
{
  "telefono": "5551234567"
}
```

**Validaciones:**
- Exactamente 10 dígitos
- Solo números (sin espacios, guiones, paréntesis)

**Response (200):**
```json
{
  "message": "Teléfono actualizado exitosamente",
  "telefono": "5551234567"
}
```

**Errors:**
- `400`: "El teléfono debe tener exactamente 10 dígitos numéricos"

---

### 6. Actualizar Presupuesto
**PATCH** `/auth/perfil/presupuesto`

Endpoint específico para establecer o modificar el presupuesto y su período.

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Request Body:**
```json
{
  "presupuesto": 750.50,
  "periodo_presupuesto": "MENSUAL"
}
```

**Períodos válidos:**
- `"DIARIO"`: Presupuesto diario
- `"SEMANAL"`: Presupuesto semanal
- `"MENSUAL"`: Presupuesto mensual

**Response (200):**
```json
{
  "message": "Presupuesto actualizado exitosamente",
  "presupuesto": 750.50,
  "periodo_presupuesto": "MENSUAL"
}
```

**Errors:**
- `400`: "El presupuesto debe ser positivo o cero"
- `422`: Período de presupuesto inválido

---

## 💰 ENDPOINTS DE GASTOS

### 7. Obtener Gastos del Usuario
**GET** `/auth/gastos`

Obtiene todos los gastos del usuario autenticado con filtros opcionales.

**Headers:**
```
Authorization: Bearer <token_jwt>
```

**Query Parameters (opcionales):**
- `categoria`: Filtrar por categoría ("COMIDA", "TRANSPORTE", "VARIOS")
- `fecha_inicio`: Fecha de inicio en formato YYYY-MM-DD
- `fecha_fin`: Fecha de fin en formato YYYY-MM-DD

**Ejemplos de URLs:**
```
GET /auth/gastos
GET /auth/gastos?categoria=COMIDA
GET /auth/gastos?fecha_inicio=2025-07-01&fecha_fin=2025-07-10
GET /auth/gastos?categoria=TRANSPORTE&fecha_inicio=2025-07-01
```

**Response (200):**
```json
[
  {
    "id": 1,
    "descripcion": "Almuerzo en restaurante",
    "monto": 25.50,
    "categoria": "COMIDA",
    "fecha": "2025-07-10T12:30:00.000Z",
    "created_at": "2025-07-10T12:30:00.000Z",
    "updated_at": "2025-07-10T12:30:00.000Z"
  },
  {
    "id": 2,
    "descripcion": "Pasaje de bus",
    "monto": 15.00,
    "categoria": "TRANSPORTE",
    "fecha": "2025-07-10T08:00:00.000Z",
    "created_at": "2025-07-10T08:00:00.000Z",
    "updated_at": "2025-07-10T08:00:00.000Z"
  }
]
```

**Response vacía (200):**
```json
[]
```

---

## 🤖 ENDPOINTS DE MACHINE LEARNING

### 8. Obtener Sugerencia de Categoría
**POST** `/ml/sugerencia`

Obtiene una sugerencia de categoría del modelo de ML sin crear un gasto. Útil para probar qué categoría sugiere el modelo antes de crear realmente el gasto.

**Request Body:**
```json
{
  "descripcion": "Almuerzo en McDonald's",
  "categoria_usuario": "VARIOS"
}
```

**Response (200):**
```json
{
  "exito": true,
  "prediccion_modelo": {
    "Descripción": "Almuerzo en McDonald's",
    "Categoría Usuario": "varios",
    "Categoría Sugerida": "Comida",
    "¿Coincide?": "❌ No"
  },
  "categoria_original": "varios",
  "descripcion": "Almuerzo en McDonald's",
  "recomendacion": {
    "categoria_sugerida": "comida",
    "categoria_original": "varios",
    "coincide": false,
    "mensaje": "💡 Sugerencia: Considera cambiar de 'varios' a 'comida' para una mejor clasificación."
  },
  "confianza": 0.75
}
```

**Errors:**
- `400`: Descripción vacía o muy corta
- `500`: Error en el servicio de ML

---

### 9. Crear Gasto con Sugerencia ML
**POST** `/gastos/con-sugerencia`

Crea un nuevo gasto y obtiene automáticamente una sugerencia del modelo ML sobre si la categoría elegida es la más apropiada.

**Request Body:**
```json
{
  "descripcion": "Taxi al aeropuerto",
  "monto": 45.50,
  "categoria": "TRANSPORTE",
  "usuario_id": 1
}
```

**Response (200):**
```json
{
  "gasto": {
    "id": 15,
    "descripcion": "Taxi al aeropuerto",
    "monto": 45.50,
    "categoria": "TRANSPORTE",
    "usuario_id": 1,
    "fecha": "2025-07-10T15:30:00.000Z",
    "created_at": "2025-07-10T15:30:00.000Z",
    "updated_at": "2025-07-10T15:30:00.000Z"
  },
  "sugerencia_ml": {
    "exito": true,
    "prediccion_modelo": {
      "Descripción": "Taxi al aeropuerto",
      "Categoría Usuario": "transporte",
      "Categoría Sugerida": "Transporte",
      "¿Coincide?": "✅ Sí"
    },
    "categoria_original": "transporte",
    "descripcion": "Taxi al aeropuerto",
    "recomendacion": {
      "categoria_sugerida": "transporte",
      "categoria_original": "transporte",
      "coincide": true,
      "mensaje": "✅ Excelente elección! La categoría 'transporte' es la más apropiada para este gasto."
    },
    "confianza": 0.9
  }
}
```

---

### 10. Verificar Estado del ML
**GET** `/ml/estado`

Verifica si el servicio de Machine Learning está disponible y funcionando correctamente.

**Response (200) - Servicio Activo:**
```json
{
  "servicio_ml": "activo",
  "modelo": "cristiandiaz2403/MiSpace",
  "detalles": {
    "disponible": true,
    "modelo": "cristiandiaz2403/MiSpace",
    "respuesta_test": {
      "exito": true,
      "prediccion_modelo": {
        "Descripción": "test comida hamburguesa",
        "Categoría Usuario": "comida",
        "Categoría Sugerida": "Comida",
        "¿Coincide?": "✅ Sí"
      },
      "categoria_original": "comida",
      "descripcion": "test comida hamburguesa",
      "recomendacion": {
        "categoria_sugerida": "comida",
        "categoria_original": "comida",
        "coincide": true,
        "mensaje": "✅ Excelente elección! La categoría 'comida' es la más apropiada para este gasto."
      },
      "confianza": 0.9
    }
  }
}
```

**Response (200) - Servicio Inactivo:**
```json
{
  "servicio_ml": "inactivo",
  "modelo": "cristiandiaz2403/MiSpace",
  "detalles": {
    "disponible": false,
    "modelo": "cristiandiaz2403/MiSpace",
    "error": "Error de conexión con el modelo"
  }
}
```

---

### 11. Crear Múltiples Gastos con Sugerencias
**POST** `/gastos/batch-con-sugerencias`

Crea múltiples gastos a la vez, cada uno con su respectiva sugerencia de ML. Útil para importación de datos con validación de categorías.

**Request Body:**
```json
[
  {
    "descripcion": "Desayuno en cafetería",
    "monto": 12.50,
    "categoria": "COMIDA",
    "usuario_id": 1
  },
  {
    "descripcion": "Gasolina del carro",
    "monto": 80.00,
    "categoria": "TRANSPORTE",
    "usuario_id": 1
  }
]
```

**Response (200):**
```json
[
  {
    "gasto": {
      "id": 16,
      "descripcion": "Desayuno en cafetería",
      "monto": 12.50,
      "categoria": "COMIDA",
      "usuario_id": 1,
      "fecha": "2025-07-10T15:35:00.000Z",
      "created_at": "2025-07-10T15:35:00.000Z",
      "updated_at": "2025-07-10T15:35:00.000Z"
    },
    "sugerencia_ml": {
      "exito": true,
      "categoria_original": "comida",
      "recomendacion": {
        "categoria_sugerida": "comida",
        "categoria_original": "comida",
        "coincide": true,
        "mensaje": "✅ Excelente elección! La categoría 'comida' es la más apropiada para este gasto."
      },
      "confianza": 0.9
    }
  },
  {
    "gasto": {
      "id": 17,
      "descripcion": "Gasolina del carro",
      "monto": 80.00,
      "categoria": "TRANSPORTE",
      "usuario_id": 1,
      "fecha": "2025-07-10T15:35:01.000Z",
      "created_at": "2025-07-10T15:35:01.000Z",
      "updated_at": "2025-07-10T15:35:01.000Z"
    },
    "sugerencia_ml": {
      "exito": true,
      "categoria_original": "transporte",
      "recomendacion": {
        "categoria_sugerida": "transporte",
        "categoria_original": "transporte",
        "coincide": true,
        "mensaje": "✅ Excelente elección! La categoría 'transporte' es la más apropiada para este gasto."
      },
      "confianza": 0.85
    }
  }
]
```

**Limitaciones:**
- Máximo 50 gastos por solicitud
- Si el ML falla para un gasto, se crea el gasto pero con sugerencia de error

---

## 🎯 CÓMO FUNCIONA EL MACHINE LEARNING

### Flujo de Trabajo con ML

1. **Endpoint de Solo Sugerencia** (`/ml/sugerencia`):
   - Envías descripción + categoría elegida
   - Obtienes sugerencia del modelo SIN crear el gasto
   - Útil para "preview" antes de guardar

2. **Endpoint de Creación con ML** (`/gastos/con-sugerencia`):
   - Creas el gasto normalmente
   - Automáticamente obtienes feedback del ML
   - El gasto se guarda siempre, independiente del ML

3. **Interpretación de Resultados**:
   - `coincide: true` = El modelo está de acuerdo con tu elección ✅
   - `coincide: false` = El modelo sugiere una categoría diferente 💡
   - `confianza: 0.0-1.0` = Nivel de confianza del modelo

### Ejemplo de Uso en Frontend

```javascript
// 1. Obtener sugerencia antes de crear
const sugerencia = await fetch('/ml/sugerencia', {
  method: 'POST',
  body: JSON.stringify({
    descripcion: "Pizza a domicilio",
    categoria_usuario: "VARIOS"
  })
});

// 2. Mostrar sugerencia al usuario
if (!sugerencia.recomendacion.coincide) {
  alert(sugerencia.recomendacion.mensaje);
  // "💡 Sugerencia: Considera cambiar de 'varios' a 'comida'"
}

// 3. Crear gasto con feedback automático
const resultado = await fetch('/gastos/con-sugerencia', {
  method: 'POST',
  body: JSON.stringify({
    descripcion: "Pizza a domicilio",
    monto: 25.50,
    categoria: "COMIDA", // Usuario decidió cambiar
    usuario_id: 1
  })
});
```

### Categorías que Reconoce el Modelo

- **COMIDA**: restaurantes, comida rápida, supermercado, bebidas, etc.
- **TRANSPORTE**: taxi, bus, gasolina, Uber, pasajes, etc.  
- **VARIOS**: todo lo demás (entretenimiento, ropa, servicios, etc.)

---

## 📋 NOTAS IMPORTANTES

1. **Autenticación**: Todos los endpoints de perfil y gastos requieren autenticación JWT.

2. **Campos Opcionales**: En las actualizaciones PATCH, solo se envían los campos que se desean modificar.

3. **Validaciones**: El backend valida automáticamente los tipos de datos y restricciones.

4. **Fechas**: Todas las fechas se devuelven en formato ISO 8601 UTC.

5. **Seguridad**: Los usuarios solo pueden acceder y modificar su propia información.

6. **Presupuesto**: El presupuesto es opcional al crear el usuario, pero una vez establecido puede modificarse.

7. **Teléfono**: El campo teléfono es opcional y debe tener exactamente 10 dígitos numéricos.

8. **Machine Learning**: Los endpoints de ML son opcionales - si fallan, la funcionalidad básica sigue funcionando.

9. **Categorías ML**: El modelo reconoce patrones en las descripciones para sugerir la categoría más apropiada.

10. **Confianza**: Un valor alto (>0.8) indica que el modelo está muy seguro de su sugerencia.

11. **Fallback**: Si el ML no está disponible, se mantiene la categoría elegida por el usuario.

12. **Performance**: Las sugerencias son en tiempo real pero pueden tardar 1-3 segundos.
