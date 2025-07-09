"""
Utilidades para Machine Learning y procesamiento de datos
"""
import re
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from models import Gasto, CategoriaGasto
from sqlalchemy.orm import Session

def normalizar_texto(texto: str) -> str:
    """Normaliza texto para mejorar el procesamiento ML"""
    if not texto:
        return ""
    
    # Convertir a minúsculas
    texto = texto.lower()
    
    # Normalizar términos comunes
    normalizaciones = {
        r'\bbus\b': 'transporte_publico',
        r'\btaxi\b': 'taxi',
        r'\buber\b': 'taxi',
        r'\bcabify\b': 'taxi',
        r'\bmetro\b': 'transporte_publico',
        r'\bcomida\b': 'alimentacion',
        r'\bdesayuno\b': 'alimentacion',
        r'\balmuerzo\b': 'alimentacion',
        r'\bcena\b': 'alimentacion',
        r'\brestaurant\b': 'alimentacion',
        r'\bcine\b': 'entretenimiento',
        r'\bregalo\b': 'regalo',
        r'\bgasolina\b': 'combustible',
        r'\bparkings?\b': 'estacionamiento'
    }
    
    for patron, reemplazo in normalizaciones.items():
        texto = re.sub(patron, reemplazo, texto)
    
    # Remover caracteres especiales pero mantener espacios y guiones bajos
    texto = re.sub(r'[^\w\s_]', '', texto)
    
    # Normalizar espacios
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

def extraer_caracteristicas_temporales(fecha: datetime) -> Dict:
    """Extrae características temporales de una fecha"""
    return {
        'dia_semana': fecha.weekday(),  # 0=Lunes, 6=Domingo
        'hora_gasto': fecha.hour,
        'es_fin_semana': fecha.weekday() >= 5,
        'es_inicio_mes': fecha.day <= 5,
        'es_fin_mes': fecha.day >= 25,
        'mes': fecha.month,
        'patron_temporal': clasificar_patron_temporal(fecha.hour)
    }

def clasificar_patron_temporal(hora: int) -> str:
    """Clasifica la hora en patrones temporales"""
    if 6 <= hora < 12:
        return "mañana"
    elif 12 <= hora < 18:
        return "tarde"
    elif 18 <= hora < 22:
        return "noche"
    else:
        return "madrugada"

def calcular_frecuencia_descripcion(db: Session, descripcion: str, usuario_id: int) -> int:
    """Calcula cuántas veces se ha usado una descripción similar"""
    texto_normalizado = normalizar_texto(descripcion)
    
    # Buscar descripciones similares
    gastos_similares = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.texto_normalizado.contains(texto_normalizado)
    ).count()
    
    return max(1, gastos_similares)

def detectar_categoria_por_palabras_clave(descripcion: str) -> Tuple[Optional[CategoriaGasto], float]:
    """Detecta categoría basada en palabras clave con confianza"""
    texto = normalizar_texto(descripcion)
    
    patrones_categoria = {
        CategoriaGasto.TRANSPORTE: {
            'palabras': ['bus', 'taxi', 'uber', 'cabify', 'metro', 'transporte', 'gasolina', 'combustible', 'parking', 'estacionamiento'],
            'peso': 1.0
        },
        CategoriaGasto.COMIDA: {
            'palabras': ['comida', 'restaurante', 'desayuno', 'almuerzo', 'cena', 'pizza', 'hamburguesa', 'pollo', 'sushi', 'alimentacion'],
            'peso': 1.0
        },
        CategoriaGasto.VARIOS: {
            'palabras': ['cine', 'regalo', 'entretenimiento', 'compra', 'varios', 'farmacia', 'medicina'],
            'peso': 0.8
        }
    }
    
    scores = {}
    for categoria, config in patrones_categoria.items():
        score = 0
        for palabra in config['palabras']:
            if palabra in texto:
                score += config['peso']
        
        if score > 0:
            scores[categoria] = score / len(config['palabras'])
    
    if scores:
        mejor_categoria = max(scores.keys(), key=lambda k: scores[k])
        confianza = min(1.0, scores[mejor_categoria] * 2)  # Escalar confianza
        return mejor_categoria, confianza
    
    return None, 0.0

def crear_features_para_ml(gasto_data: Dict) -> np.ndarray:
    """Crea vector de características para ML"""
    features = [
        gasto_data.get('monto', 0),
        gasto_data.get('dia_semana', 0),
        gasto_data.get('hora_gasto', 12),
        int(gasto_data.get('es_fin_semana', False)),
        gasto_data.get('frecuencia_descripcion', 1),
        int(gasto_data.get('es_inicio_mes', False)),
        int(gasto_data.get('es_fin_mes', False)),
        gasto_data.get('mes', 1)
    ]
    return np.array(features).reshape(1, -1)

def calcular_estadisticas_usuario(db: Session, usuario_id: int, dias: int = 30) -> Dict:
    """Calcula estadísticas del usuario para ML"""
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.fecha >= fecha_limite
    ).all()
    
    if not gastos:
        return {
            'total_gastos': 0,
            'promedio_diario': 0,
            'gastos_por_categoria': {},
            'patrones_temporales': {},
            'gastos_recurrentes': 0
        }
    
    # Convertir a DataFrame para análisis
    datos = []
    for gasto in gastos:
        datos.append({
            'monto': gasto.monto,
            'categoria': gasto.categoria.value if gasto.categoria else 'VARIOS',
            'dia_semana': gasto.dia_semana or 0,
            'hora_gasto': gasto.hora_gasto or 12,
            'descripcion': gasto.descripcion,
            'fecha': gasto.fecha
        })
    
    df = pd.DataFrame(datos)
    
    # Calcular estadísticas
    total_gastos = df['monto'].sum()
    promedio_diario = total_gastos / dias
    
    # Gastos por categoría
    gastos_por_categoria = df.groupby('categoria')['monto'].sum().to_dict()
    
    # Patrones temporales
    patrones_temporales = {
        'por_dia_semana': df.groupby('dia_semana')['monto'].sum().to_dict(),
        'por_hora': df.groupby('hora_gasto')['monto'].sum().to_dict()
    }
    
    # Gastos recurrentes (aparecen más de una vez)
    gastos_recurrentes = df['descripcion'].value_counts()
    gastos_recurrentes = len(gastos_recurrentes[gastos_recurrentes > 1])
    
    return {
        'total_gastos': total_gastos,
        'promedio_diario': promedio_diario,
        'gastos_por_categoria': gastos_por_categoria,
        'patrones_temporales': patrones_temporales,
        'gastos_recurrentes': gastos_recurrentes,
        'numero_gastos': len(gastos)
    }

def validar_gasto_anomalo(gasto: Gasto, estadisticas: Dict) -> Tuple[bool, str]:
    """Valida si un gasto es potencialmente anómalo usando reglas simples"""
    categoria = gasto.categoria.value if gasto.categoria else 'VARIOS'
    
    # Regla 1: Monto muy alto comparado con el promedio diario
    promedio_diario = estadisticas.get('promedio_diario', 0)
    if promedio_diario > 0 and gasto.monto > promedio_diario * 2:
        return True, f"Monto {gasto.monto} es muy alto comparado con promedio diario {promedio_diario:.2f}"
    
    # Regla 2: Monto muy alto para la categoría
    gastos_categoria = estadisticas.get('gastos_por_categoria', {})
    if categoria in gastos_categoria:
        promedio_categoria = gastos_categoria[categoria] / 30  # Promedio diario de la categoría
        if gasto.monto > promedio_categoria * 3:
            return True, f"Monto muy alto para categoría {categoria}"
    
    # Regla 3: Hora inusual (madrugada)
    if gasto.hora_gasto and (gasto.hora_gasto < 6 or gasto.hora_gasto > 23):
        return True, f"Hora inusual: {gasto.hora_gasto}:00"
    
    return False, "Gasto normal"

def procesar_gasto_para_ml(gasto_data: Dict, db: Session, usuario_id: int) -> Dict:
    """Procesa un gasto para añadir características ML"""
    fecha = gasto_data.get('fecha', datetime.now())
    if isinstance(fecha, str):
        fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
    
    # Extraer características temporales
    caracteristicas_temporales = extraer_caracteristicas_temporales(fecha)
    
    # Normalizar texto
    texto_normalizado = normalizar_texto(gasto_data.get('descripcion', ''))
    
    # Calcular frecuencia
    frecuencia = calcular_frecuencia_descripcion(
        db, gasto_data.get('descripcion', ''), usuario_id
    )
    
    # Detectar categoría automáticamente si no se proporciona
    categoria_detectada, confianza = detectar_categoria_por_palabras_clave(
        gasto_data.get('descripcion', '')
    )
    
    # Combinar datos
    gasto_procesado = {
        **gasto_data,
        **caracteristicas_temporales,
        'texto_normalizado': texto_normalizado,
        'frecuencia_descripcion': frecuencia,
        'categoria_sugerida': categoria_detectada.value if categoria_detectada else None,
        'confianza_categoria': confianza
    }
    
    return gasto_procesado

def exportar_datos_para_entrenamiento(db: Session, usuario_id: Optional[int] = None) -> pd.DataFrame:
    """Exporta datos en formato adecuado para entrenamiento ML"""
    query = db.query(Gasto)
    if usuario_id:
        query = query.filter(Gasto.usuario_id == usuario_id)
    
    gastos = query.all()
    
    datos = []
    for gasto in gastos:
        datos.append({
            'id': gasto.id,
            'descripcion': gasto.descripcion,
            'descripcion_normalizada': gasto.texto_normalizado or normalizar_texto(gasto.descripcion),
            'monto': gasto.monto,
            'categoria': gasto.categoria.value if gasto.categoria else None,
            'dia_semana': gasto.dia_semana,
            'hora_gasto': gasto.hora_gasto,
            'es_fin_semana': gasto.es_fin_semana,
            'frecuencia_descripcion': gasto.frecuencia_descripcion,
            'es_recurrente': gasto.es_recurrente,
            'fecha': gasto.fecha,
            'usuario_id': gasto.usuario_id
        })
    
    return pd.DataFrame(datos)

def crear_directorio_modelos():
    """Crea el directorio para guardar modelos ML si no existe"""
    import os
    os.makedirs('models', exist_ok=True)

# Diccionarios de mapeo para categorización
PALABRAS_TRANSPORTE = [
    'bus', 'taxi', 'uber', 'cabify', 'metro', 'transporte', 'gasolina', 
    'combustible', 'parking', 'estacionamiento', 'pasaje', 'billete',
    'autobus', 'colectivo', 'micro'
]

PALABRAS_COMIDA = [
    'comida', 'restaurante', 'desayuno', 'almuerzo', 'cena', 'pizza',
    'hamburguesa', 'pollo', 'sushi', 'alimentacion', 'supermercado',
    'mercado', 'tienda', 'cafe', 'panaderia'
]

PALABRAS_VARIOS = [
    'cine', 'regalo', 'entretenimiento', 'compra', 'varios', 'farmacia',
    'medicina', 'ropa', 'electronico', 'libro', 'juego', 'diversión'
]
