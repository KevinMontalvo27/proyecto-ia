from typing import List

from pydantic import BaseModel, Field
from datetime import datetime


class SensorReadingBase(BaseModel):
    value: float = Field(..., description="Valor medido por el sensor")


class SensorReadingCreate(SensorReadingBase):
    """Schema para crear una lectura de sensor"""
    sensor_id: int = Field(..., gt=0, description="ID del sensor")


class SensorReadingResponse(SensorReadingBase):
    """Schema para respuesta de lectura"""
    id: int
    sensor_id: int
    recorded_at: datetime

    class Config:
        from_attributes = True


class SensorReadingBulkCreate(BaseModel):
    """Schema para crear múltiples lecturas a la vez"""
    sensor_id: int = Field(..., gt=0)
    readings: List[float] = Field(..., min_length=1, max_length=1000)
