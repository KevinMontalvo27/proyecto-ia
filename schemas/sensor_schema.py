from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class SensorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del sensor")
    type: Literal['temperature', 'humidity', 'light', 'soil_moisture'] = Field(
        ..., description="Tipo de sensor"
    )


class SensorCreate(SensorBase):
    """Schema para crear un sensor"""
    greenhouse_id: int = Field(..., gt=0, description="ID del invernadero")
    active: Optional[bool] = Field(True, description="Estado del sensor")


class SensorUpdate(BaseModel):
    """Schema para actualizar sensor"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[Literal['temperature', 'humidity', 'light', 'soil_moisture']] = None
    active: Optional[bool] = None


class SensorResponse(SensorBase):
    """Schema para respuesta de sensor"""
    id: int
    greenhouse_id: int
    active: bool
    installed_at: datetime

    class Config:
        from_attributes = True


class SensorDetailResponse(SensorResponse):
    """Schema con lecturas del sensor"""
    readings: List['SensorReadingResponse'] = []