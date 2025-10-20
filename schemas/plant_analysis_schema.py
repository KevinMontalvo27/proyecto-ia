from pydantic import BaseModel, Field
from typing import List, Literal


class PlantHealthPrediction(BaseModel):
    """Schema para una predicción individual"""
    label: str = Field(..., description="Etiqueta de la enfermedad o condición")
    score: float = Field(..., ge=0.0, le=1.0, description="Puntuación de confianza (0-1)")
    confidence_percent: float = Field(..., ge=0.0, le=100.0, description="Porcentaje de confianza")


class PlantHealthAnalysisResponse(BaseModel):
    """Schema para respuesta del análisis de salud"""
    predictions: List[PlantHealthPrediction] = Field(..., description="Lista de predicciones ordenadas por confianza")
    top_prediction: PlantHealthPrediction = Field(..., description="Predicción con mayor confianza")
    plant_id: int = Field(..., description="ID de la planta analizada")


class DiseaseInfo(BaseModel):
    """Schema para información detallada de una enfermedad"""
    name: str = Field(..., description="Nombre de la enfermedad")
    severity: Literal['none', 'low', 'medium', 'high', 'unknown'] = Field(..., description="Severidad de la enfermedad")
    description: str = Field(..., description="Descripción de la enfermedad")


class DiseaseInfoResponse(BaseModel):
    """Schema para respuesta de información de enfermedad"""
    label: str
    info: DiseaseInfo