from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre de la planta")
    type: str = Field(..., min_length=1, max_length=50, description="Tipo de planta")


class PlantCreate(PlantBase):
    """Schema para crear una planta"""
    greenhouse_id: int = Field(..., gt=0, description="ID del invernadero")


class PlantUpdate(BaseModel):
    """Schema para actualizar planta"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)


class PlantResponse(PlantBase):
    """Schema para respuesta de planta"""
    id: int
    greenhouse_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PlantDetailResponse(PlantResponse):
    """Schema con análisis de la planta"""
    analyses: List['PlantAnalysisResponse'] = []


# Detalle con referencias diferidas
class PlantDetailResponse(PlantResponse):
    analyses: List['PlantAnalysisResponse'] = []  # Referencia diferida

    class Config:
        from_attributes = True


# --- ZONA DE RESOLUCIÓN DE REFERENCIAS ---
try:
    # Importar el esquema de análisis (ajusta el nombre del archivo si es distinto)
    # Si no tienes este archivo aún, comenta estas líneas temporalmente
    from schemas.plant_analysis_schema import PlantAnalysisResponse

    PlantDetailResponse.model_rebuild()
except ImportError:
    # Si no existe el módulo aún, evitamos que crashée, pero el campo quedará vacío
    pass