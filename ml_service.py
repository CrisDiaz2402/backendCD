from gradio_client import Client
from typing import Dict, Any, Optional
import logging
from models import CategoriaGasto

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLService:
    """Servicio para interactuar con el modelo de Machine Learning en Hugging Face"""
    
    def __init__(self):
        self.client = None
        self.model_space = "cristiandiaz2403/MiSpace"
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializar el cliente de Gradio"""
        try:
            self.client = Client(self.model_space)
            logger.info(f"Cliente ML inicializado correctamente para {self.model_space}")
        except Exception as e:
            logger.error(f"Error al inicializar cliente ML: {str(e)}")
            self.client = None
    
    def obtener_sugerencia_categoria(self, descripcion: str, categoria_usuario: str) -> Dict[str, Any]:
        """
        Obtener sugerencia de categoría del modelo ML
        
        Args:
            descripcion: Descripción del gasto
            categoria_usuario: Categoría elegida por el usuario
            
        Returns:
            Diccionario con la respuesta del modelo y metadatos
        """
        if not self.client:
            logger.warning("Cliente ML no disponible, reintentar inicialización")
            self._initialize_client()
            
        if not self.client:
            return self._respuesta_fallback(descripcion, categoria_usuario)
        
        try:
            # Validar que la categoría del usuario sea válida
            categorias_validas = ['comida', 'transporte', 'varios']
            categoria_usuario_normalizada = categoria_usuario.lower().strip()
            if categoria_usuario_normalizada not in categorias_validas:
                categoria_usuario_normalizada = 'varios'  # Categoría por defecto
            
            # Llamar al modelo
            result = self.client.predict(
                descripcion=descripcion,
                categoria_usuario=categoria_usuario_normalizada,
                api_name="/predict"
            )
            
            logger.info(f"Predicción exitosa para descripción: '{descripcion[:50]}...'")
            
            return {
                "exito": True,
                "prediccion_modelo": result,
                "categoria_original": categoria_usuario_normalizada,
                "descripcion": descripcion,
                "recomendacion": self._interpretar_resultado(result, categoria_usuario_normalizada),
                "confianza": self._calcular_confianza(result, categoria_usuario_normalizada)
            }
            
        except Exception as e:
            logger.error(f"Error en predicción ML: {str(e)}")
            return self._respuesta_fallback(descripcion, categoria_usuario, error=str(e))
    
    def _interpretar_resultado(self, resultado: Any, categoria_original: str) -> Dict[str, Any]:
        """
        Interpretar el resultado del modelo y generar una recomendación clara
        """
        try:
            # Normalizar categoría original a minúsculas
            categoria_original_normalizada = categoria_original.lower().strip()
            
            # Si el resultado es un string, intentar parsearlo como categoría
            if isinstance(resultado, str):
                categoria_sugerida = resultado.lower().strip()
                
                # Mapear posibles respuestas del modelo a nuestras categorías
                mapeo_categorias = {
                    'comida': 'comida',
                    'food': 'comida',
                    'alimentacion': 'comida',
                    'restaurante': 'comida',
                    'transporte': 'transporte',
                    'transport': 'transporte',
                    'viaje': 'transporte',
                    'taxi': 'transporte',
                    'bus': 'transporte',
                    'gasolina': 'transporte',
                    'combustible': 'transporte',
                    'varios': 'varios',
                    'other': 'varios',
                    'others': 'varios',
                    'miscellaneous': 'varios'
                }
                
                categoria_final = mapeo_categorias.get(categoria_sugerida, categoria_original_normalizada)
                
                return {
                    "categoria_sugerida": categoria_final,
                    "categoria_original": categoria_original_normalizada,
                    "coincide": categoria_final == categoria_original_normalizada,
                    "mensaje": self._generar_mensaje_recomendacion(categoria_final, categoria_original_normalizada)
                }
            
            # Si es un diccionario, extraer la categoría sugerida del resultado
            elif isinstance(resultado, dict):
                # Buscar campos que puedan contener la categoría sugerida
                categoria_sugerida = None
                
                # Posibles claves que pueden contener la categoría
                claves_categoria = [
                    'Categoría Sugerida', 'categoria_sugerida', 'suggested_category',
                    'prediction', 'category', 'categoria', 'Categoria Sugerida'
                ]
                
                for clave in claves_categoria:
                    if clave in resultado and resultado[clave]:
                        categoria_sugerida = str(resultado[clave]).lower().strip()
                        break
                
                if categoria_sugerida:
                    # Mapear la categoría encontrada
                    mapeo_categorias = {
                        'comida': 'comida',
                        'food': 'comida',
                        'alimentacion': 'comida',
                        'restaurante': 'comida',
                        'transporte': 'transporte',
                        'transport': 'transporte',
                        'viaje': 'transporte',
                        'taxi': 'transporte',
                        'bus': 'transporte',
                        'gasolina': 'transporte',
                        'combustible': 'transporte',
                        'varios': 'varios',
                        'other': 'varios',
                        'others': 'varios',
                        'miscellaneous': 'varios'
                    }
                    
                    categoria_final = mapeo_categorias.get(categoria_sugerida, categoria_original_normalizada)
                    
                    return {
                        "categoria_sugerida": categoria_final,
                        "categoria_original": categoria_original_normalizada,
                        "coincide": categoria_final == categoria_original_normalizada,
                        "mensaje": self._generar_mensaje_recomendacion(categoria_final, categoria_original_normalizada)
                    }
                else:
                    # Si no encontramos categoría en el diccionario, mantener original
                    logger.warning(f"No se pudo extraer categoría del resultado: {resultado}")
                    return {
                        "categoria_sugerida": categoria_original_normalizada,
                        "categoria_original": categoria_original_normalizada,
                        "coincide": True,
                        "mensaje": "El modelo proporcionó una respuesta compleja. Se mantiene la categoría original.",
                        "resultado_raw": resultado
                    }
            
            # Si es una lista, intentar extraer el primer elemento
            elif isinstance(resultado, list) and len(resultado) > 0:
                # Recursivamente interpretar el primer elemento
                return self._interpretar_resultado(resultado[0], categoria_original)
            
            else:
                return {
                    "categoria_sugerida": categoria_original_normalizada,
                    "categoria_original": categoria_original_normalizada,
                    "coincide": True,
                    "mensaje": "Se mantiene la categoría original."
                }
                
        except Exception as e:
            logger.error(f"Error interpretando resultado: {str(e)}")
            categoria_original_normalizada = categoria_original.lower().strip()
            return {
                "categoria_sugerida": categoria_original_normalizada,
                "categoria_original": categoria_original_normalizada,
                "coincide": True,
                "mensaje": "Error en interpretación. Se mantiene la categoría original."
            }
    
    def _generar_mensaje_recomendacion(self, categoria_sugerida: str, categoria_original: str) -> str:
        """Generar mensaje de recomendación basado en la comparación"""
        # Asegurar que ambas categorías estén normalizadas
        categoria_sugerida = categoria_sugerida.lower().strip()
        categoria_original = categoria_original.lower().strip()
        
        if categoria_sugerida == categoria_original:
            return f"✅ Excelente elección! La categoría '{categoria_original}' es la más apropiada para este gasto."
        else:
            return f"💡 Sugerencia: Considera cambiar de '{categoria_original}' a '{categoria_sugerida}' para una mejor clasificación."
    
    def _calcular_confianza(self, resultado: Any, categoria_original: str) -> float:
        """Calcular un nivel de confianza básico"""
        try:
            categoria_original_normalizada = categoria_original.lower().strip()
            
            if isinstance(resultado, str):
                resultado_normalizado = resultado.lower().strip()
                # Si coincide con la categoría original, alta confianza
                if resultado_normalizado == categoria_original_normalizada:
                    return 0.9
                # Si es una categoría válida diferente, confianza media
                elif resultado_normalizado in ['comida', 'transporte', 'varios']:
                    return 0.75
                else:
                    return 0.5
            elif isinstance(resultado, dict):
                # Si es un diccionario, intentar extraer la categoría
                claves_categoria = [
                    'Categoría Sugerida', 'categoria_sugerida', 'suggested_category',
                    'prediction', 'category', 'categoria', 'Categoria Sugerida'
                ]
                
                for clave in claves_categoria:
                    if clave in resultado and resultado[clave]:
                        resultado_normalizado = str(resultado[clave]).lower().strip()
                        if resultado_normalizado == categoria_original_normalizada:
                            return 0.9
                        elif resultado_normalizado in ['comida', 'transporte', 'varios']:
                            return 0.75
                        break
                
                return 0.6  # Confianza por defecto para diccionarios
            else:
                return 0.6  # Confianza por defecto para resultados no string
        except:
            return 0.5
    
    def _respuesta_fallback(self, descripcion: str, categoria_usuario: str, error: str = None) -> Dict[str, Any]:
        """Respuesta de respaldo cuando el modelo no está disponible"""
        categoria_normalizada = categoria_usuario.lower().strip()
        
        return {
            "exito": False,
            "error": error or "Servicio de ML no disponible",
            "categoria_original": categoria_normalizada,
            "descripcion": descripcion,
            "recomendacion": {
                "categoria_sugerida": categoria_normalizada,
                "categoria_original": categoria_normalizada,
                "coincide": True,
                "mensaje": "🔧 Servicio de ML temporalmente no disponible. Se mantiene tu categoría elegida."
            },
            "confianza": 1.0  # Alta confianza en la elección del usuario cuando ML no está disponible
        }
    
    def probar_conexion(self) -> Dict[str, Any]:
        """Probar la conexión con el modelo"""
        try:
            resultado = self.obtener_sugerencia_categoria("test comida hamburguesa", "comida")
            return {
                "disponible": resultado["exito"],
                "modelo": self.model_space,
                "respuesta_test": resultado
            }
        except Exception as e:
            return {
                "disponible": False,
                "modelo": self.model_space,
                "error": str(e)
            }

# Instancia global del servicio
ml_service = MLService()

# =============================
# Servicio para modelo Capibara
# =============================

class CapibaraService:
    """Servicio para interactuar con el modelo CapibaraModel en Hugging Face"""
    def __init__(self):
        self.client = None
        self.model_space = "cristiandiaz2403/CapibaraModel"
        self._initialize_client()

    def _initialize_client(self):
        try:
            self.client = Client(self.model_space)
            logger.info(f"Cliente Capibara inicializado correctamente para {self.model_space}")
        except Exception as e:
            logger.error(f"Error al inicializar cliente Capibara: {str(e)}")
            self.client = None

    def predecir_dificultad(self, bombs_hit: float, projectiles_hit: float, session_time: float) -> dict:
        """
        Realiza una predicción de dificultad usando el modelo CapibaraModel.
        Args:
            bombs_hit: Bombas acertadas
            projectiles_hit: Proyectiles acertados
            session_time: Tiempo de sesión (segundos)
        Returns:
            Diccionario con la predicción del modelo o error
        """
        if not self.client:
            logger.warning("Cliente Capibara no disponible, reintentar inicialización")
            self._initialize_client()
        if not self.client:
            return self._respuesta_fallback(bombs_hit, projectiles_hit, session_time)
        try:
            result = self.client.predict(
                bombs_hit=bombs_hit,
                projectiles_hit=projectiles_hit,
                session_time=session_time,
                api_name="/predict"
            )
            logger.info(f"Predicción Capibara exitosa: {result}")
            return {
                "exito": True,
                "entrada": {
                    "bombs_hit": bombs_hit,
                    "projectiles_hit": projectiles_hit,
                    "session_time": session_time
                },
                "resultado": result
            }
        except Exception as e:
            logger.error(f"Error en predicción Capibara: {str(e)}")
            return self._respuesta_fallback(bombs_hit, projectiles_hit, session_time, error=str(e))

    def _respuesta_fallback(self, bombs_hit, projectiles_hit, session_time, error=None):
        return {
            "exito": False,
            "error": error or "Servicio Capibara no disponible",
            "entrada": {
                "bombs_hit": bombs_hit,
                "projectiles_hit": projectiles_hit,
                "session_time": session_time
            },
            "resultado": None
        }

# Instancia global del servicio Capibara
capibara_service = CapibaraService()
