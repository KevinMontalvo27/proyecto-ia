from fastapi import APIRouter, File, UploadFile, HTTPException, status
from PIL import Image
import io
from typing import List, Dict, Any
from clients.plants_health import classify_plant_health

router = APIRouter(prefix="/plant-analysis", tags=["plant-analysis"])


@router.post("/classify", status_code=status.HTTP_200_OK)
async def analyze_plant_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Analiza una imagen de planta para detectar enfermedades o problemas de salud

    Args:
        file: Archivo de imagen (JPG, JPEG, PNG)

    Returns:
        Dict con las predicciones:
        {
            "filename": "nombre_archivo.jpg",
            "predictions": [
                {"label": "tomato_late_blight", "score": 0.95},
                {"label": "tomato_healthy", "score": 0.03},
                ...
            ]
        }

    Raises:
        HTTPException 400: Si el archivo no es una imagen válida
        HTTPException 500: Si hay error en el procesamiento
    """
    # Validar tipo de archivo
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser una imagen (JPG, JPEG, PNG)"
        )

    try:
        # Leer el archivo de imagen
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Convertir a RGB si es necesario (por si es RGBA o escala de grises)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Clasificar la imagen
        predictions = classify_plant_health(image)

        return {
            "filename": file.filename,
            "predictions": predictions
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la imagen: {str(e)}"
        )
    finally:
        await file.close()