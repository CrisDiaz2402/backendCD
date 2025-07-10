# 🚀 Guía para Conectar Frontend al Backend

## Endpoint para Registrar Gastos

**URL:** `POST /gastos/simple`

## 📤 Datos que Espera la API

### Parámetros Requeridos:
- `descripcion` (string): Descripción del gasto
- `monto` (float): Cantidad gastada (debe ser positivo)
- `categoria` (string): Una de: "comida", "transporte", "varios"
- `usuario_id` (int): ID del usuario que registra el gasto

## 📥 Respuesta de la API

```json
{
  "id": 123,
  "usuario_id": 1,
  "descripcion": "Almuerzo en restaurante",
  "monto": 15.50,
  "categoria": "comida",
  "fecha": "2025-07-09T14:30:00",
  "confianza_categoria": 0.9,
  "patron_temporal": "tarde",
  "dia_semana": 1,
  "hora_gasto": 14,
  "es_fin_semana": false,
  "es_recurrente": false,
  "frecuencia_descripcion": 1,
  "created_at": "2025-07-09T14:30:00",
  "updated_at": "2025-07-09T14:30:00"
}
```

## 🌐 Ejemplos de Uso desde Frontend

### JavaScript/TypeScript (Fetch API)

```javascript
// Función para registrar un gasto
async function registrarGasto(descripcion, monto, categoria, usuarioId) {
  try {
    const response = await fetch('/gastos/simple', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        descripcion: descripcion,
        monto: monto.toString(),
        categoria: categoria,
        usuario_id: usuarioId.toString()
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al registrar gasto');
    }

    const nuevoGasto = await response.json();
    return nuevoGasto;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Ejemplo de uso
registrarGasto("Almuerzo en restaurante", 15.50, "comida", 1)
  .then(gasto => {
    console.log('Gasto registrado:', gasto);
    // Actualizar UI
  })
  .catch(error => {
    console.error('Error al registrar:', error.message);
  });
```

### React Hook Personalizado

```jsx
import { useState } from 'react';

export function useGastos() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const registrarGasto = async (gastoData) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/gastos/simple', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          descripcion: gastoData.descripcion,
          monto: gastoData.monto.toString(),
          categoria: gastoData.categoria,
          usuario_id: gastoData.usuario_id.toString()
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail);
      }

      const nuevoGasto = await response.json();
      return nuevoGasto;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { registrarGasto, loading, error };
}
```

### Componente React de Ejemplo

```jsx
import React, { useState } from 'react';
import { useGastos } from './hooks/useGastos';

function FormularioGasto({ usuarioId }) {
  const [descripcion, setDescripcion] = useState('');
  const [monto, setMonto] = useState('');
  const [categoria, setCategoria] = useState('varios');
  
  const { registrarGasto, loading, error } = useGastos();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const gasto = await registrarGasto({
        descripcion,
        monto: parseFloat(monto),
        categoria,
        usuario_id: usuarioId
      });
      
      // Limpiar formulario
      setDescripcion('');
      setMonto('');
      setCategoria('varios');
      
      alert('Gasto registrado exitosamente!');
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Descripción:</label>
        <input
          type="text"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          required
        />
      </div>
      
      <div>
        <label>Monto:</label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={monto}
          onChange={(e) => setMonto(e.target.value)}
          required
        />
      </div>
      
      <div>
        <label>Categoría:</label>
        <select 
          value={categoria} 
          onChange={(e) => setCategoria(e.target.value)}
        >
          <option value="comida">Comida</option>
          <option value="transporte">Transporte</option>
          <option value="varios">Varios</option>
        </select>
      </div>
      
      <button type="submit" disabled={loading}>
        {loading ? 'Registrando...' : 'Registrar Gasto'}
      </button>
      
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
    </form>
  );
}
```

## 🔧 Validaciones del Backend

El endpoint valida automáticamente:
- ✅ Monto debe ser positivo
- ✅ Descripción no puede estar vacía
- ✅ Usuario debe existir
- ✅ Categoría debe ser válida ("comida", "transporte", "varios")

## 🤖 Machine Learning Automático

Al registrar un gasto, el sistema automáticamente:
- 🧠 Calcula confianza de la categoría
- ⏰ Detecta patrón temporal (mañana/tarde/noche)
- 📅 Identifica día de la semana y si es fin de semana
- 🔍 Normaliza el texto para NLP
- 📊 Programa análisis de anomalías en segundo plano

## 🚀 ¡Listo para usar!

Ya puedes empezar a registrar gastos y el sistema comenzará a aprender tus patrones automáticamente.
