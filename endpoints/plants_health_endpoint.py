from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from PIL import Image
import io
from typing import List, Dict, Any
from clients.plants_health import classify_plant_health
from services.plant_analysis_service import PlantAnalysisService
from services.prolog_service import PrologService
from utils.plant_mapper import PlantMapper
from sqlalchemy.orm import Session
from database_config import SessionLocal
router = APIRouter(prefix="/plant-analysis", tags=["plant-analysis"])

# Inicializar servicio de Prolog
prolog_service = PrologService(prolog_file_path="prolog/plant_diagnostics.pl")

def get_db():
    """
    Generador de sesiones de base de datos para FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/classify", status_code=status.HTTP_200_OK)
async def analyze_plant_image(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analiza una imagen de planta, guarda el resultado en BD y consulta Prolog.

    Args:
        file: Archivo de imagen (JPG, JPEG, PNG)

    Returns:
        Dict con respuesta de Prolog y detalles del análisis:
        {
            "prolog_response": "Alerta activada para tomate: late_blight",
            "analysis_details": {
                "plant": "tomate",
                "plant_id": 1,
                "diagnostic": "late_blight",
                "confidence": 0.95,
                "analysis_id": 123
            }
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
        # 1. Leer y procesar imagen
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        if image.mode != "RGB":
            image = image.convert("RGB")

        # 2. Clasificar con HuggingFace
        prediction = classify_plant_health(image)
        hf_label = prediction['label']
        confidence = prediction['score']

        print(f"🔍 HuggingFace result: {hf_label} ({confidence:.2%})")

        # 3. Parsear la etiqueta de HuggingFace usando el mapper
        try:
            plant_info = PlantMapper.parse_label(hf_label)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        plant = plant_info['plant']
        plant_id = plant_info['plant_id']
        diagnostic = plant_info['diagnostic']

        print(f"📊 Parsed: Plant={plant} (ID={plant_id}), Diagnostic={diagnostic}")

        # 4. Guardar en base de datos usando el servicio
        analysis = PlantAnalysisService.create_analysis(
            db=db,
            plant_id=plant_id,
            diagnosis=diagnostic,
            confidence=confidence,
            analysis_type='health'
        )

        # 5. Consultar Prolog usando el servicio
        prolog_response = prolog_service.check_plant(plant, diagnostic)

        print(f"🤖 Prolog response: {prolog_response}")

        # 6. Retornar respuesta
        return {
            "prolog_response": prolog_response,
            "analysis_details": {
                "plant": plant,
                "plant_id": plant_id,
                "diagnostic": diagnostic,
                "confidence": round(confidence, 4),
                "analysis_id": analysis.id,
                "analyzed_at": analysis.analyzed_at.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la imagen: {str(e)}"
        )
    finally:
        await file.close()


@router.get("/history/{plant_id}", status_code=status.HTTP_200_OK)
async def get_plant_analysis_history(
        plant_id: int,
        limit: int = 10,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene el historial de análisis de una planta.

    Args:
        plant_id: ID de la planta (1=tomate, 2=maiz, 3=uva, 4=papa)
        limit: Número máximo de resultados

    Returns:
        Historial de análisis
    """
    history = PlantAnalysisService.get_plant_history(db, plant_id, limit)

    return {
        "plant_id": plant_id,
        "plant_name": PlantMapper.get_plant_name(plant_id),
        "total_analyses": PlantAnalysisService.count_analyses_by_plant(db, plant_id),
        "history": [
            {
                "id": analysis.id,
                "diagnostic": analysis.result,
                "confidence": analysis.confidence,
                "analyzed_at": analysis.analyzed_at.isoformat()
            }
            for analysis in history
        ]
    }


@router.get("/unhealthy", status_code=status.HTTP_200_OK)
async def get_unhealthy_plants(
        confidence_threshold: float = 0.7,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene todas las plantas con problemas de salud.

    Args:
        confidence_threshold: Umbral mínimo de confianza (0-1)

    Returns:
        Lista de plantas no saludables
    """
    unhealthy = PlantAnalysisService.get_unhealthy_plants(db, confidence_threshold)

    return {
        "count": len(unhealthy),
        "plants": [
            {
                "analysis_id": analysis.id,
                "plant_id": analysis.plant_id,
                "plant_name": PlantMapper.get_plant_name(analysis.plant_id),
                "diagnostic": analysis.result,
                "confidence": analysis.confidence,
                "analyzed_at": analysis.analyzed_at.isoformat()
            }
            for analysis in unhealthy
        ]
    }