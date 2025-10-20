import os, certifi
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

import requests
from transformers import pipeline
from PIL import Image

# Testear conexión HTTPS con Hugging Face usando certifi
response = requests.get("https://huggingface.co", verify=certifi.where())
print("Status conexión HuggingFace:", response.status_code)

image_url = "https://content.peat-cloud.com/w400/tomato-late-blight-tomato-1556463954.jpg"

print('Cargando modelo')
plant_classifier = pipeline(
    task="image-classification",
    model="linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification",
    use_fast=True
)
print("Modelo cargado")

try:
    image = Image.open(requests.get(image_url, stream=True).raw)
    print("Imagen cargada")
except Exception as exception:
    print(f"No se pudo cargar la imagen debido a: {exception}")
    exit()

print("Realizando análisis de imagen")
predictions = plant_classifier(image)

print("Resultado de la predicción")
print(predictions)
