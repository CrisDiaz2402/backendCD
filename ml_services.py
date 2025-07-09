"""
Servicios de Machine Learning para clasificación y análisis de gastos
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from models import Gasto, CategoriaGasto, PatronGasto, TipoPatron, Usuario
from sqlalchemy.orm import Session
import nltk
from textblob import TextBlob

# Descargar recursos de NLTK si es necesario
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ClasificadorGastos:
    """Clasificador de gastos usando Machine Learning"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=['de', 'la', 'el', 'en', 'y', 'a', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son'],
            ngram_range=(1, 2)
        )
        self.clasificador = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced'
        )
        self.scaler = StandardScaler()
        self.modelo_entrenado = False
        
    def preprocesar_texto(self, texto: str) -> str:
        """Preprocesa el texto para mejorar la clasificación"""
        if not texto:
            return ""
        
        # Convertir a minúsculas
        texto = texto.lower()
        
        # Remover caracteres especiales pero mantener espacios
        texto = re.sub(r'[^\w\s]', '', texto)
        
        # Normalizar espacios
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
    
    def extraer_caracteristicas_numericas(self, gastos_df: pd.DataFrame) -> np.ndarray:
        """Extrae características numéricas de los gastos"""
        caracteristicas = []
        
        for _, gasto in gastos_df.iterrows():
            features = [
                gasto.get('monto', 0),
                gasto.get('dia_semana', 0),
                gasto.get('hora_gasto', 12),
                int(gasto.get('es_fin_semana', False)),
                gasto.get('frecuencia_descripcion', 1)
            ]
            caracteristicas.append(features)
        
        return np.array(caracteristicas)
    
    def entrenar(self, db: Session, usuario_id: Optional[int] = None) -> Dict:
        """Entrena el modelo con los gastos existentes"""
        try:
            # Obtener gastos etiquetados
            query = db.query(Gasto).filter(Gasto.categoria.isnot(None))
            if usuario_id:
                query = query.filter(Gasto.usuario_id == usuario_id)
            
            gastos = query.all()
            
            if len(gastos) < 10:
                return {
                    "status": "error",
                    "mensaje": "Se necesitan al menos 10 gastos etiquetados para entrenar"
                }
            
            # Preparar datos
            datos = []
            for gasto in gastos:
                datos.append({
                    'descripcion': gasto.descripcion,
                    'monto': gasto.monto,
                    'categoria': gasto.categoria.value,
                    'dia_semana': gasto.dia_semana or 0,
                    'hora_gasto': gasto.hora_gasto or 12,
                    'es_fin_semana': gasto.es_fin_semana or False,
                    'frecuencia_descripcion': gasto.frecuencia_descripcion or 1
                })
            
            df = pd.DataFrame(datos)
            
            # Preprocesar textos
            textos_procesados = [self.preprocesar_texto(desc) for desc in df['descripcion']]
            
            # Vectorizar textos
            X_texto = self.vectorizer.fit_transform(textos_procesados)
            
            # Características numéricas
            X_numerico = self.extraer_caracteristicas_numericas(df)
            X_numerico_scaled = self.scaler.fit_transform(X_numerico)
            
            # Combinar características
            X = np.hstack([X_texto.toarray(), X_numerico_scaled])
            y = df['categoria'].values
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Entrenar modelo
            self.clasificador.fit(X_train, y_train)
            
            # Evaluar
            y_pred = self.clasificador.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.modelo_entrenado = True
            
            # Guardar modelo
            self.guardar_modelo(usuario_id)
            
            return {
                "status": "success",
                "accuracy": accuracy,
                "gastos_entrenamiento": len(gastos),
                "reporte": classification_report(y_test, y_pred, output_dict=True)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "mensaje": f"Error en entrenamiento: {str(e)}"
            }
    
    def predecir_categoria(self, descripcion: str, monto: float = 0, 
                          dia_semana: int = 0, hora_gasto: int = 12) -> Tuple[str, float]:
        """Predice la categoría de un gasto"""
        if not self.modelo_entrenado:
            return "VARIOS", 0.5
        
        try:
            # Preprocesar texto
            texto_procesado = self.preprocesar_texto(descripcion)
            X_texto = self.vectorizer.transform([texto_procesado])
            
            # Características numéricas
            X_numerico = np.array([[monto, dia_semana, hora_gasto, 
                                   int(dia_semana >= 5), 1]])
            X_numerico_scaled = self.scaler.transform(X_numerico)
            
            # Combinar características
            X = np.hstack([X_texto.toarray(), X_numerico_scaled])
            
            # Predecir
            categoria = self.clasificador.predict(X)[0]
            probabilidades = self.clasificador.predict_proba(X)[0]
            confianza = max(probabilidades)
            
            return categoria, confianza
            
        except Exception as e:
            print(f"Error en predicción: {e}")
            return "VARIOS", 0.5
    
    def guardar_modelo(self, usuario_id: Optional[int] = None):
        """Guarda el modelo entrenado"""
        modelo_data = {
            'vectorizer': self.vectorizer,
            'clasificador': self.clasificador,
            'scaler': self.scaler,
            'modelo_entrenado': self.modelo_entrenado
        }
        
        filename = f"modelo_gastos_{usuario_id or 'global'}.joblib"
        joblib.dump(modelo_data, f"models/{filename}")
    
    def cargar_modelo(self, usuario_id: Optional[int] = None):
        """Carga un modelo previamente entrenado"""
        try:
            filename = f"modelo_gastos_{usuario_id or 'global'}.joblib"
            modelo_data = joblib.load(f"models/{filename}")
            
            self.vectorizer = modelo_data['vectorizer']
            self.clasificador = modelo_data['clasificador']
            self.scaler = modelo_data['scaler']
            self.modelo_entrenado = modelo_data['modelo_entrenado']
            
            return True
        except Exception as e:
            print(f"Error cargando modelo: {e}")
            return False

class DetectorAnomalias:
    """Detector de gastos anómalos usando clustering"""
    
    def __init__(self):
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        self.scaler = StandardScaler()
        self.modelo_entrenado = False
        self.umbrales_categoria = {}
    
    def entrenar(self, db: Session, usuario_id: int) -> Dict:
        """Entrena el detector de anomalías"""
        try:
            # Obtener gastos del usuario
            gastos = db.query(Gasto).filter(
                Gasto.usuario_id == usuario_id,
                Gasto.categoria.isnot(None)
            ).all()
            
            if len(gastos) < 20:
                return {
                    "status": "error",
                    "mensaje": "Se necesitan al menos 20 gastos para detectar anomalías"
                }
            
            # Preparar datos
            datos = []
            for gasto in gastos:
                datos.append({
                    'monto': gasto.monto,
                    'categoria': gasto.categoria.value,
                    'dia_semana': gasto.dia_semana or 0,
                    'hora_gasto': gasto.hora_gasto or 12,
                    'frecuencia_descripcion': gasto.frecuencia_descripcion or 1
                })
            
            df = pd.DataFrame(datos)
            
            # Calcular umbrales por categoría
            for categoria in df['categoria'].unique():
                cat_data = df[df['categoria'] == categoria]['monto']
                media = cat_data.mean()
                std = cat_data.std()
                self.umbrales_categoria[categoria] = {
                    'media': media,
                    'std': std,
                    'umbral_superior': media + 2 * std,
                    'umbral_inferior': max(0, media - 2 * std)
                }
            
            # Preparar características para clustering
            X = df[['monto', 'dia_semana', 'hora_gasto', 'frecuencia_descripcion']].values
            X_scaled = self.scaler.fit_transform(X)
            
            # Entrenar clustering
            self.kmeans.fit(X_scaled)
            self.modelo_entrenado = True
            
            return {
                "status": "success",
                "umbrales_calculados": len(self.umbrales_categoria),
                "clusters_encontrados": self.kmeans.n_clusters
            }
            
        except Exception as e:
            return {
                "status": "error",
                "mensaje": f"Error en entrenamiento de anomalías: {str(e)}"
            }
    
    def detectar_anomalia(self, gasto: Gasto) -> Tuple[bool, float, str]:
        """Detecta si un gasto es anómalo"""
        if not self.modelo_entrenado:
            return False, 0.0, "Modelo no entrenado"
        
        try:
            categoria = gasto.categoria.value if gasto.categoria else "VARIOS"
            
            # Verificar umbral por categoría
            if categoria in self.umbrales_categoria:
                umbral = self.umbrales_categoria[categoria]
                
                if gasto.monto > umbral['umbral_superior']:
                    nivel = min(1.0, (gasto.monto - umbral['umbral_superior']) / umbral['media'])
                    return True, nivel, f"Monto muy alto para {categoria}"
                
                if gasto.monto < umbral['umbral_inferior']:
                    nivel = min(1.0, (umbral['umbral_inferior'] - gasto.monto) / umbral['media'])
                    return True, nivel, f"Monto muy bajo para {categoria}"
            
            # Verificar con clustering
            X = np.array([[
                gasto.monto,
                gasto.dia_semana or 0,
                gasto.hora_gasto or 12,
                gasto.frecuencia_descripcion or 1
            ]])
            X_scaled = self.scaler.transform(X)
            
            # Calcular distancia al centroide más cercano
            distancias = self.kmeans.transform(X_scaled)[0]
            distancia_min = min(distancias)
            
            # Si está muy lejos de cualquier cluster, es anómalo
            if distancia_min > 2.0:  # Umbral ajustable
                return True, min(1.0, distancia_min / 3.0), "Patrón de gasto inusual"
            
            return False, 0.0, "Gasto normal"
            
        except Exception as e:
            return False, 0.0, f"Error en detección: {str(e)}"

class AnalizadorPatrones:
    """Analiza patrones de gasto y genera recomendaciones"""
    
    def __init__(self):
        self.patrones_detectados = []
    
    def analizar_patrones_temporales(self, db: Session, usuario_id: int) -> List[Dict]:
        """Analiza patrones temporales en los gastos"""
        try:
            # Obtener gastos de los últimos 90 días
            fecha_limite = datetime.now() - timedelta(days=90)
            gastos = db.query(Gasto).filter(
                Gasto.usuario_id == usuario_id,
                Gasto.fecha >= fecha_limite
            ).all()
            
            if len(gastos) < 10:
                return []
            
            # Convertir a DataFrame
            datos = []
            for gasto in gastos:
                datos.append({
                    'descripcion': gasto.descripcion,
                    'monto': gasto.monto,
                    'categoria': gasto.categoria.value if gasto.categoria else 'VARIOS',
                    'dia_semana': gasto.dia_semana or 0,
                    'hora_gasto': gasto.hora_gasto or 12,
                    'fecha': gasto.fecha
                })
            
            df = pd.DataFrame(datos)
            patrones = []
            
            # Patrón 1: Gastos recurrentes por descripción
            desc_counts = df['descripcion'].value_counts()
            for desc, count in desc_counts.items():
                if count >= 3:  # Al menos 3 veces
                    desc_data = df[df['descripcion'] == desc]
                    patron = {
                        'tipo': 'RECURRENTE',
                        'descripcion': f"Gasto recurrente: {desc}",
                        'categoria': desc_data['categoria'].mode()[0],
                        'frecuencia': count / 90,  # gastos por día
                        'monto_promedio': desc_data['monto'].mean(),
                        'confianza': min(1.0, count / 10),
                        'datos': {
                            'descripcion_base': desc,
                            'veces_detectado': count,
                            'monto_min': desc_data['monto'].min(),
                            'monto_max': desc_data['monto'].max()
                        }
                    }
                    patrones.append(patron)
            
            # Patrón 2: Gastos por día de la semana
            for categoria in df['categoria'].unique():
                cat_data = df[df['categoria'] == categoria]
                if len(cat_data) >= 5:
                    dow_pattern = cat_data.groupby('dia_semana').size()
                    if dow_pattern.std() > 1:  # Variación significativa
                        dia_preferido = dow_pattern.idxmax()
                        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                        
                        patron = {
                            'tipo': 'ESTACIONAL',
                            'descripcion': f"Tendencia a gastar en {categoria} los {dias[dia_preferido]}",
                            'categoria': categoria,
                            'frecuencia': dow_pattern.max() / len(cat_data),
                            'monto_promedio': cat_data['monto'].mean(),
                            'confianza': min(1.0, dow_pattern.std() / 2),
                            'datos': {
                                'dia_preferido': dia_preferido,
                                'patron_semanal': dow_pattern.to_dict()
                            }
                        }
                        patrones.append(patron)
            
            return patrones
            
        except Exception as e:
            print(f"Error analizando patrones: {e}")
            return []
    
    def generar_recomendaciones(self, db: Session, usuario_id: int) -> List[Dict]:
        """Genera recomendaciones basadas en patrones"""
        try:
            patrones = self.analizar_patrones_temporales(db, usuario_id)
            recomendaciones = []
            
            for patron in patrones:
                if patron['tipo'] == 'RECURRENTE' and patron['confianza'] > 0.7:
                    recomendacion = {
                        'tipo': 'gasto_esperado',
                        'descripcion': patron['datos']['descripcion_base'],
                        'categoria': patron['categoria'],
                        'monto_estimado': patron['monto_promedio'],
                        'confianza': patron['confianza'],
                        'razon': f"Basado en {patron['datos']['veces_detectado']} gastos similares"
                    }
                    recomendaciones.append(recomendacion)
                
                elif patron['tipo'] == 'ESTACIONAL' and patron['confianza'] > 0.6:
                    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                    dia_actual = datetime.now().weekday()
                    
                    if dia_actual == patron['datos']['dia_preferido']:
                        recomendacion = {
                            'tipo': 'tendencia_diaria',
                            'descripcion': f"Es probable que gastes en {patron['categoria']} hoy",
                            'categoria': patron['categoria'],
                            'monto_estimado': patron['monto_promedio'],
                            'confianza': patron['confianza'],
                            'razon': f"Sueles gastar en {patron['categoria']} los {dias[dia_actual]}"
                        }
                        recomendaciones.append(recomendacion)
            
            return recomendaciones
            
        except Exception as e:
            print(f"Error generando recomendaciones: {e}")
            return []

# Instancias globales de los servicios ML
clasificador_gastos = ClasificadorGastos()
detector_anomalias = DetectorAnomalias()
analizador_patrones = AnalizadorPatrones()
