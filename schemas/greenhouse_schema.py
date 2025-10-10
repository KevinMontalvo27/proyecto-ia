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


class GreenhouseDetailResponse(GreenhouseResponse):
    """Schema con detalles completos incluyendo plantas y sensores"""
    plants: List['PlantResponse'] = []
    sensors: List['SensorResponse'] = []