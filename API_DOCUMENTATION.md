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

## 📊 ENUMERACIONES

### Categorías de Gastos
```
COMIDA
TRANSPORTE
VARIOS
```

### Períodos de Presupuesto
```
DIARIO
SEMANAL
MENSUAL
```

---

## ❌ CÓDIGOS DE ERROR COMUNES

### 400 - Bad Request
```json
{
  "detail": "El teléfono debe tener exactamente 10 dígitos numéricos"
}
```

### 401 - Unauthorized
```json
{
  "detail": "No se pudieron validar las credenciales"
}
```

### 422 - Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "presupuesto"],
      "msg": "El presupuesto debe ser positivo o cero",
      "type": "value_error"
    }
  ]
}
```

### 404 - Not Found
```json
{
  "detail": "Usuario no encontrado"
}
```

---


## 📋 NOTAS IMPORTANTES

1. **Autenticación**: Todos los endpoints de perfil y gastos requieren autenticación JWT.

2. **Campos Opcionales**: En las actualizaciones PATCH, solo se envían los campos que se desean modificar.

3. **Validaciones**: El backend valida automáticamente los tipos de datos y restricciones.

4. **Fechas**: Todas las fechas se devuelven en formato ISO 8601 UTC.

5. **Seguridad**: Los usuarios solo pueden acceder y modificar su propia información.

6. **Presupuesto**: El presupuesto es opcional al crear el usuario, pero una vez establecido puede modificarse.

7. **Teléfono**: El campo teléfono es opcional y debe tener exactamente 10 dígitos numéricos.
