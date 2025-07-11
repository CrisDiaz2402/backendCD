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
            if categoria_usuario.lower() not in categorias_validas:
                categoria_usuario = 'varios'  # Categoría por defecto
            
            # Llamar al modelo
            result = self.client.predict(
                descripcion=descripcion,
                categoria_usuario=categoria_usuario.lower(),
                api_name="/predict"
            )
            
            logger.info(f"Predicción exitosa para descripción: '{descripcion[:50]}...'")
            
            return {
                "exito": True,
                "prediccion_modelo": result,
                "categoria_original": categoria_usuario,
                "descripcion": descripcion,
                "recomendacion": self._interpretar_resultado(result, categoria_usuario),
                "confianza": self._calcular_confianza(result, categoria_usuario)
            }
            
        except Exception as e:
            logger.error(f"Error en predicción ML: {str(e)}")
            return self._respuesta_fallback(descripcion, categoria_usuario, error=str(e))
    
    def _interpretar_resultado(self, resultado: Any, categoria_original: str) -> Dict[str, Any]:
        """
        Interpretar el resultado del modelo y generar una recomendación clara
        """
        try:
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
                    'varios': 'varios',
                    'other': 'varios',
                    'others': 'varios',
                    'miscellaneous': 'varios'
                }
                
                categoria_final = mapeo_categorias.get(categoria_sugerida, categoria_original)
                
                return {
                    "categoria_sugerida": categoria_final,
                    "categoria_original": categoria_original,
                    "coincide": categoria_final == categoria_original.lower(),
                    "mensaje": self._generar_mensaje_recomendacion(categoria_final, categoria_original)
                }
            
            # Si es un diccionario o estructura más compleja
            elif isinstance(resultado, (dict, list)):
                return {
                    "categoria_sugerida": categoria_original,
                    "categoria_original": categoria_original,
                    "coincide": True,
                    "mensaje": "El modelo proporcionó una respuesta compleja. Se mantiene la categoría original.",
                    "resultado_raw": resultado
                }
            
            else:
                return {
                    "categoria_sugerida": categoria_original,
                    "categoria_original": categoria_original,
                    "coincide": True,
                    "mensaje": "Se mantiene la categoría original."
                }
                
        except Exception as e:
            logger.error(f"Error interpretando resultado: {str(e)}")
            return {
                "categoria_sugerida": categoria_original,
                "categoria_original": categoria_original,
                "coincide": True,
                "mensaje": "Error en interpretación. Se mantiene la categoría original."
            }
    
    def _generar_mensaje_recomendacion(self, categoria_sugerida: str, categoria_original: str) -> str:
        """Generar mensaje de recomendación basado en la comparación"""
        if categoria_sugerida == categoria_original.lower():
            return f"✅ Excelente elección! La categoría '{categoria_original}' es la más apropiada para este gasto."
        else:
            return f"💡 Sugerencia: Considera cambiar de '{categoria_original}' a '{categoria_sugerida}' para una mejor clasificación."
    
    def _calcular_confianza(self, resultado: Any, categoria_original: str) -> float:
        """Calcular un nivel de confianza básico"""
        try:
            if isinstance(resultado, str):
                # Si coincide con la categoría original, alta confianza
                if resultado.lower().strip() == categoria_original.lower():
                    return 0.9
                # Si es una categoría válida diferente, confianza media
                elif resultado.lower().strip() in ['comida', 'transporte', 'varios']:
                    return 0.75
                else:
                    return 0.5
            else:
                return 0.6  # Confianza por defecto para resultados no string
        except:
            return 0.5
    
    def _respuesta_fallback(self, descripcion: str, categoria_usuario: str, error: str = None) -> Dict[str, Any]:
        """Respuesta de respaldo cuando el modelo no está disponible"""
        return {
            "exito": False,
            "error": error or "Servicio de ML no disponible",
            "categoria_original": categoria_usuario,
            "descripcion": descripcion,
            "recomendacion": {
                "categoria_sugerida": categoria_usuario,
                "categoria_original": categoria_usuario,
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
