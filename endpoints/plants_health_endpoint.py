from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends, Query
from PIL import Image
import io
from typing import Dict, Any, Optional
from clients.plants_health import classify_plant_health
from clients.gemini_client import GeminiClient
from services.plant_analysis_service import PlantAnalysisService
from services.prolog_service import PrologService
from services.chat_service import ChatService
from services.sensor_context_service import SensorContextService
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
        user_id: int = Query(..., description="ID del usuario que hace el análisis"),
        greenhouse_id: Optional[int] = Query(None,
                                             description="ID del invernadero (opcional, para contexto de sensores)"),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analiza una imagen de planta, guarda el resultado en BD, consulta Prolog,
    y SI PROLOG DETECTA ALERTA → crea chat automático con Gemini para recomendaciones.

    Args:
        file: Archivo de imagen (JPG, JPEG, PNG)
        user_id: ID del usuario (requerido para crear el chat si Prolog activa alerta)
        greenhouse_id: ID del invernadero (opcional, mejora las recomendaciones con datos de sensores)
        db: Sesión de base de datos

    Returns:
        Dict con respuesta de Prolog y detalles del análisis:
        {
            "prolog_response": "Alerta activada para tomate: late_blight",
            "analysis_details": {
                "plant": "tomate",
                "plant_id": 1,
                "diagnostic": "late_blight",
                "confidence": 0.95,
                "analysis_id": 123,
                "analyzed_at": "2024-01-15T10:30:00"
            },
            "alert_activated": true,  // NUEVO
            "chat_id": 456,           // NUEVO - Solo si alerta activada
            "chat_name": "Diagnóstico: Tomate - Late Blight",  // NUEVO
            "recommendations_preview": "..."  // NUEVO
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
        prolog_response_raw = prolog_service.check_plant(plant, diagnostic)

        # Decodificar respuesta de Prolog (viene en bytes)
        if isinstance(prolog_response_raw, bytes):
            prolog_response = prolog_response_raw.decode('utf-8')
        else:
            prolog_response = str(prolog_response_raw)

        print(f"🤖 Prolog response: {prolog_response}")

        # 6. Preparar respuesta base (MANTENER ESTRUCTURA ORIGINAL)
        response = {
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

        # ========================================
        # 7. NUEVO: VERIFICAR SI PROLOG ACTIVÓ ALERTA
        # ========================================
        # La respuesta de Prolog contiene "Alerta" cuando detecta enfermedad
        # Actualizado para detectar tanto "Alerta activada" como "Alerta:"
        alert_activated = "Alerta" in prolog_response and "Se recomienda" in prolog_response
        response["alert_activated"] = alert_activated

        print(f"{'🚨' if alert_activated else '✅'} Alert activated: {alert_activated}")

        # ========================================
        # 8. NUEVO: SI HAY ALERTA → CREAR CHAT CON GEMINI
        # ========================================
        if alert_activated:
            try:
                print(f"\n🤖 ALERTA DETECTADA - Iniciando proceso con Gemini...")

                # 8.1: Crear el chat
                chat_name = f"Diagnóstico: {plant.title()} - {diagnostic.replace('_', ' ').title()}"
                chat = ChatService.create_chat(
                    db=db,
                    user_id=user_id,
                    name=chat_name
                )

                if not chat:
                    raise Exception("Error al crear el chat")

                print(f"✓ Chat creado (ID: {chat.id}): {chat_name}")

                # 8.2: Obtener contexto de sensores (si hay greenhouse_id)
                sensor_context = None
                if greenhouse_id:
                    print(f"📡 Obteniendo datos de sensores del invernadero {greenhouse_id}...")
                    try:
                        # Optimizado: solo últimas 10 lecturas por sensor
                        sensor_context = SensorContextService.get_complete_context(
                            db=db,
                            greenhouse_id=greenhouse_id,
                            days=7,
                            max_readings_per_sensor=10  # Solo últimas 10 lecturas
                        )
                        print(f"✓ Contexto de sensores obtenido")
                    except Exception as sensor_error:
                        print(f"⚠️ No se pudo obtener contexto de sensores: {sensor_error}")
                        sensor_context = None
                else:
                    print("ℹ️ No se proporcionó greenhouse_id, continuando sin contexto de sensores")

                # 8.3: Generar recomendaciones con Gemini
                print(f"🧠 Generando recomendaciones con Gemini...")
                gemini_client = GeminiClient()

                recommendations = gemini_client.generate_plant_diagnosis_recommendations(
                    plant_name=plant.title(),
                    disease_name=diagnostic,
                    confidence=confidence * 100,  # Convertir a porcentaje
                    sensor_context=sensor_context
                )

                print(f"✓ Recomendaciones generadas ({len(recommendations)} caracteres)")

                # 8.4: Guardar el mensaje de Gemini en el chat
                gemini_message = ChatService.create_message(
                    db=db,
                    chat_id=chat.id,
                    author="gemini",
                    message=recommendations
                )

                if not gemini_message:
                    raise Exception("Error al guardar el mensaje de Gemini")

                print(f"✓ Mensaje guardado en el chat")

                # 8.5: Agregar información del chat a la respuesta
                response.update({
                    "chat_id": chat.id,
                    "chat_name": chat.name,
                    "recommendations_preview": recommendations[:200] + "..." if len(
                        recommendations) > 200 else recommendations
                })

                print(f"✅ Chat con Gemini creado exitosamente\n")

            except Exception as chat_error:
                # Si falla la creación del chat, aún retornamos el análisis y Prolog
                print(f"❌ Error al crear chat con Gemini: {str(chat_error)}")
                response["chat_error"] = f"No se pudieron generar recomendaciones: {str(chat_error)}"

        else:
            print(f"ℹ️ No se requiere chat con Gemini (sin alerta de Prolog)\n")

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la imagen: {str(e)}"
        )
    finally:
        await file.close()


@router.get("/health")
def health_check():
    """
    Endpoint simple para verificar que el servicio está funcionando

    Returns:
        dict: Estado del servicio
    """
    return {
        "status": "ok",
        "service": "plant-analysis",
        "prolog_enabled": True,
        "gemini_enabled": True,
        "message": "Servicio de análisis de plantas con Prolog y Gemini activo"
    }