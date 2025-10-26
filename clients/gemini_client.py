import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
load_dotenv()


class GeminiClient:
    """Cliente para interactuar con la API de Gemini"""

    def __init__(self):
        """Inicializa el cliente de Gemini con la API key"""
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en las variables de entorno")

        genai.configure(api_key=self.api_key)

        # Configuración del modelo
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        # Configuración de seguridad
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]

        # Inicializar modelo
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )

        # Cargar prompt del sistema
        self.system_prompt = self._load_system_prompt()

        logger.info("Cliente de Gemini inicializado correctamente")

    def _load_system_prompt(self) -> str:
        """Carga el prompt del sistema desde el archivo"""
        try:
            prompt_path = os.path.join("prompts", "greenhouse_assistant_prompt.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Archivo de prompt no encontrado, usando prompt por defecto")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Prompt por defecto si no se encuentra el archivo"""
        return """Eres un asistente experto en agricultura de invernaderos y sistemas de monitoreo de plantas.

Tu función es ayudar a los usuarios a:
- Interpretar datos de sensores (temperatura, humedad, luz, humedad del suelo)
- Analizar la salud de las plantas
- Proporcionar recomendaciones sobre cuidado de cultivos
- Detectar problemas y sugerir soluciones

Responde de manera clara, concisa y profesional. Si no tienes información suficiente, pide más detalles al usuario."""

    def create_chat_session(self, history: Optional[List[Dict[str, str]]] = None):
        """
        Crea una nueva sesión de chat

        Args:
            history: Historial de mensajes previos (opcional)
                    Formato: [{"role": "user", "parts": ["mensaje"]}, ...]

        Returns:
            Chat session de Gemini
        """
        # Preparar historial con el prompt del sistema
        formatted_history = []

        # Agregar prompt del sistema como primer mensaje
        formatted_history.append({
            "role": "user",
            "parts": [self.system_prompt]
        })
        formatted_history.append({
            "role": "model",
            "parts": [
                "Entendido. Estoy listo para asistirte con todo lo relacionado a tu invernadero. ¿En qué puedo ayudarte?"]
        })

        # Agregar historial previo si existe
        if history:
            formatted_history.extend(history)

        return self.model.start_chat(history=formatted_history)

    def send_message(
            self,
            chat_session,
            message: str,
            sensor_data: Optional[Dict] = None,
            plant_analysis: Optional[Dict] = None
    ) -> str:
        """
        Envía un mensaje al chat

        Args:
            chat_session: Sesión de chat activa
            message: Mensaje del usuario
            sensor_data: Datos de sensores (opcional, para uso futuro)
            plant_analysis: Análisis de plantas (opcional, para uso futuro)

        Returns:
            Respuesta del modelo
        """
        try:
            # Construir contexto adicional si hay datos de sensores o análisis
            context = ""

            if sensor_data:
                context += f"\n\n[DATOS DE SENSORES]\n{self._format_sensor_data(sensor_data)}"

            if plant_analysis:
                context += f"\n\n[ANÁLISIS DE PLANTA]\n{self._format_plant_analysis(plant_analysis)}"

            # Enviar mensaje con contexto
            full_message = message + context
            response = chat_session.send_message(full_message)

            return response.text

        except Exception as e:
            logger.error(f"Error al enviar mensaje a Gemini: {str(e)}")
            raise Exception(f"Error en la comunicación con Gemini: {str(e)}")

    def _format_sensor_data(self, sensor_data: Dict) -> str:
        """Formatea los datos de sensores para el contexto"""
        formatted = []
        for sensor_type, value in sensor_data.items():
            formatted.append(f"- {sensor_type}: {value}")
        return "\n".join(formatted)

    def _format_plant_analysis(self, plant_analysis: Dict) -> str:
        """Formatea el análisis de plantas para el contexto"""
        return f"""Enfermedad detectada: {plant_analysis.get('label', 'N/A')}
Confianza: {plant_analysis.get('confidence_percent', 0):.2f}%"""

    def generate_response(self, prompt: str) -> str:
        """
        Genera una respuesta sin historial (útil para consultas únicas)

        Args:
            prompt: Prompt completo

        Returns:
            Respuesta del modelo
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error al generar respuesta: {str(e)}")
            raise Exception(f"Error en la generación de contenido: {str(e)}")


# Función de prueba
def test_gemini_client():
    """Prueba básica del cliente de Gemini"""
    try:
        print("Inicializando cliente de Gemini...")
        client = GeminiClient()
        print("✓ Cliente inicializado\n")

        print("Creando sesión de chat...")
        chat = client.create_chat_session()
        print("✓ Sesión creada\n")

        # Mensaje de prueba
        test_message = "Hola, ¿qué temperatura es ideal para cultivar tomates en un invernadero?"
        print(f"Usuario: {test_message}\n")

        response = client.send_message(chat, test_message)
        print(f"Asistente: {response}\n")

        # Segundo mensaje para probar continuidad
        test_message2 = "¿Y qué nivel de humedad necesitan?"
        print(f"Usuario: {test_message2}\n")

        response2 = client.send_message(chat, test_message2)
        print(f"Asistente: {response2}\n")

        print("✓ Prueba completada exitosamente")

    except Exception as e:
        print(f"✗ Error en la prueba: {str(e)}")


if __name__ == "__main__":
    test_gemini_client()