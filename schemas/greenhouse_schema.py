from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GreenhouseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del invernadero")
    location: Optional[str] = Field(None, max_length=200, description="Ubicación física")


class GreenhouseCreate(GreenhouseBase):
    """Schema para crear un invernadero"""
    pass


class GreenhouseUpdate(BaseModel):
    """Schema para actualizar invernadero"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)


class GreenhouseResponse(GreenhouseBase):
    """Schema para respuesta de invernadero"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Definimos el detalle usando STRINGS para las clases que aún no conoce
class GreenhouseDetailResponse(GreenhouseResponse):
    plants: List['PlantResponse'] = []  # Referencia diferida
    sensors: List['SensorResponse'] = []  # Referencia diferida

    class Config:
        from_attributes = True


# --- ZONA DE RESOLUCIÓN DE REFERENCIAS ---
# Esto debe ir AL FINAL del archivo para evitar el error de "not fully defined"

try:
    # 1. Importamos los esquemas que referenciamos arriba como strings
    from schemas.plant_schema import PlantResponse
    from schemas.sensor_schema import SensorResponse

    # 2. Le decimos a Pydantic: "Ya importé las clases, reconstruye el modelo ahora"
    GreenhouseDetailResponse.model_rebuild()
except ImportError:
    pass