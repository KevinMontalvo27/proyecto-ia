from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class PlantAnalysisBase(BaseModel):
    analysis_type: Literal['health', 'pest'] = Field(..., description="Tipo de análisis")
    result: str = Field(..., min_length=1, max_length=100, description="Resultado del análisis")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confianza del modelo (0-1)")


class PlantAnalysisCreate(PlantAnalysisBase):
    """Schema para crear un análisis de planta"""
    plant_id: int = Field(..., gt=0, description="ID de la planta")


class PlantAnalysisResponse(PlantAnalysisBase):
    """Schema para respuesta de análisis"""
    id: int
    plant_id: int
    analyzed_at: datetime

    class Config:
        from_attributes = True