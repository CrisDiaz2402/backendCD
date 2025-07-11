# 🔄 Flujo de Creación de Gastos - Idea Original Implementada

## 📋 **Resumen del Flujo**

Tu idea original ahora está implementada con **2 endpoints separados**:

### **🎯 Endpoints Principales:**

1. **`POST /ml/verificar-categoria`** - Verificar categoría con ML
2. **`POST /gastos/crear-con-decision`** - Crear gasto con decisión del usuario  
3. **`POST /gastos/crear-directo`** - Crear directo (opcional, sin ML)

---

## 🚀 **Flujo Detallado:**

### **PASO 1: Usuario hace clic en "Guardar"**

**Endpoint:** `POST /ml/verificar-categoria`

```json
{
  "descripcion": "Almuerzo en McDonald's",
  "categoria_usuario": "VARIOS"
}
```

**Respuesta si ML sugiere diferente:**
```json
{
  "exito": true,
  "categoria_original": "varios",
  "descripcion": "Almuerzo en McDonald's",
  "recomendacion": {
    "categoria_sugerida": "comida",
    "coincide": false,
    "mensaje": "💡 Sugerencia: Considera cambiar de 'varios' a 'comida'"
  },
  "confianza": 0.92
}
```

**Respuesta si ML coincide:**
```json
{
  "exito": true,
  "categoria_original": "comida",
  "recomendacion": {
    "categoria_sugerida": "comida",
    "coincide": true,
    "mensaje": "✅ Categoría apropiada"
  },
  "confianza": 0.95
}
```

### **PASO 2A: Si ML sugiere diferente → Mostrar Modal**

Frontend muestra modal:
```
🤖 El ML sugiere cambiar la categoría:
VARIOS → COMIDA

¿Qué prefieres?
[Aceptar Sugerencia] [Ignorar y Mantener VARIOS]
```

### **PASO 2B: Usuario decide → Crear gasto**

**Endpoint:** `POST /gastos/crear-con-decision`

**Si acepta sugerencia:**
```json
{
  "descripcion": "Almuerzo en McDonald's",
  "monto": 25.50,
  "categoria_original": "VARIOS",
  "categoria_sugerida": "COMIDA",
  "acepta_sugerencia": true,
  "usuario_id": 1
}
```

**Si ignora sugerencia:**
```json
{
  "descripcion": "Almuerzo en McDonald's", 
  "monto": 25.50,
  "categoria_original": "VARIOS",
  "categoria_sugerida": "COMIDA",
  "acepta_sugerencia": false,
  "usuario_id": 1
}
```

**Respuesta final:**
```json
{
  "id": 123,
  "descripcion": "Almuerzo en McDonald's",
  "monto": 25.50,
  "categoria": "COMIDA",  // o "VARIOS" si ignoró
  "usuario_id": 1,
  "fecha": "2025-07-10T14:30:00"
}
```

### **PASO 2C: Si ML coincide → Crear directo**

**Endpoint:** `POST /gastos/crear-directo`

```json
{
  "descripcion": "Almuerzo en McDonald's",
  "monto": 25.50,
  "categoria": "COMIDA",
  "usar_ml": false
}
```

---

## 💻 **Implementación Frontend Recomendada:**

```javascript
async function manejarCreacionGasto(datosFormulario) {
  try {
    // PASO 1: Verificar categoría con ML
    const respuestaML = await fetch('/ml/verificar-categoria', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        descripcion: datosFormulario.descripcion,
        categoria_usuario: datosFormulario.categoria
      })
    });
    
    const sugerencia = await respuestaML.json();
    
    // PASO 2: Evaluar respuesta del ML
    if (sugerencia.recomendacion.coincide) {
      // ML coincide → Crear directo
      return await crearGastoDirecto(datosFormulario);
    } else {
      // ML sugiere diferente → Mostrar modal de decisión
      const decision = await mostrarModalDecision(sugerencia);
      return await crearGastoConDecision(datosFormulario, decision);
    }
    
  } catch (error) {
    console.error('Error:', error);
    // Fallback: crear sin ML
    return await crearGastoDirecto(datosFormulario);
  }
}

async function mostrarModalDecision(sugerencia) {
  return new Promise((resolve) => {
    const modal = document.getElementById('modal-decision');
    modal.innerHTML = `
      <div class="modal-content">
        <h3>🤖 Sugerencia del ML</h3>
        <p>${sugerencia.recomendacion.mensaje}</p>
        <p>Cambiar de <strong>${sugerencia.categoria_original}</strong> 
           a <strong>${sugerencia.recomendacion.categoria_sugerida}</strong></p>
        
        <button onclick="resolve(true)">Aceptar Sugerencia</button>
        <button onclick="resolve(false)">Mantener Original</button>
      </div>
    `;
    modal.style.display = 'block';
  });
}

async function crearGastoConDecision(datos, acepta) {
  return await fetch('/gastos/crear-con-decision', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      descripcion: datos.descripcion,
      monto: datos.monto,
      categoria_original: datos.categoria,
      categoria_sugerida: datos.categoriaSugerida,
      acepta_sugerencia: acepta
    })
  });
}

async function crearGastoDirecto(datos) {
  return await fetch('/gastos/crear-directo', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      descripcion: datos.descripcion,
      monto: datos.monto,
      categoria: datos.categoria,
      usar_ml: false
    })
  });
}
```

---

## 🎯 **Casos de Uso:**

### **Caso 1: ML Coincide**
```
Usuario: "Pizza Domino's" + "COMIDA"
ML: Sugiere "COMIDA" ✅
Resultado: Crear directo con "COMIDA"
```

### **Caso 2: ML Sugiere Diferente - Usuario Acepta**
```
Usuario: "Almuerzo" + "VARIOS"  
ML: Sugiere "COMIDA" ⚠️
Usuario: [Acepta]
Resultado: Crear con "COMIDA"
```

### **Caso 3: ML Sugiere Diferente - Usuario Ignora**
```
Usuario: "Almuerzo" + "VARIOS"
ML: Sugiere "COMIDA" ⚠️  
Usuario: [Ignora]
Resultado: Crear con "VARIOS"
```

### **Caso 4: Error en ML**
```
Usuario: "Gasolina" + "TRANSPORTE"
ML: Error/No disponible ❌
Resultado: Crear directo con "TRANSPORTE"
```

---

## ✅ **Ventajas de esta Implementación:**

1. **✅ Separación clara** - 2 endpoints con responsabilidades específicas
2. **✅ Autenticación automática** - JWT en todos los endpoints  
3. **✅ Fallback robusto** - Si ML falla, funciona sin él
4. **✅ Decisión del usuario** - Control total sobre la categoría final
5. **✅ Experiencia fluida** - Modal solo cuando hay diferencias

---

## 🔧 **Endpoints Disponibles:**

| Endpoint | Propósito | Cuándo usar |
|----------|-----------|-------------|
| `POST /ml/verificar-categoria` | Verificar con ML | Clic en "Guardar" |
| `POST /gastos/crear-con-decision` | Crear con decisión | Clic en "Aceptar/Ignorar" |
| `POST /gastos/crear-directo` | Crear sin ML | ML coincide o error |
| `POST /gastos/` | Unificado (legacy) | Compatibilidad |

**Tu idea original está completamente implementada! 🎉**
