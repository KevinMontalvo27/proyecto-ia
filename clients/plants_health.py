import os
import certifi

os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from transformers import pipeline
from PIL import Image
from typing import List, Dict, Any

# Cargar el modelo una sola vez al importar el módulo
print('Cargando modelo de clasificación de plantas...')
plant_classifier = pipeline(
    task="image-classification",
    model="linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification",
    use_fast=True
)
print("Modelo cargado exitosamente")


def classify_plant_health(image: Image.Image) -> List[Dict[str, any]]:
    """
    Clasifica la salud de una planta a partir de una imagen PIL

    Args:
        image: Objeto PIL.Image de la planta a analizar

    Returns:
        List[Dict]: Lista de predicciones con formato:
            [
                {"label": "nombre_enfermedad", "score": 0.95},
                {"label": "otra_enfermedad", "score": 0.03},
                ...
            ]

    Raises:
        Exception: Si hay error en la clasificación
    """
    try:
        print("Realizando análisis de imagen...")
        predictions = plant_classifier(image)
        print(f"Análisis completado. {len(predictions)} predicciones obtenidas")
        return predictions

    except Exception as e:
        print(f"Error al clasificar la imagen: {e}")
        raise Exception(f"Error en la clasificación: {str(e)}")