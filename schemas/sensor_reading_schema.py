from typing import List, Optional, Literal

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

class ArduinoResponse(BaseModel):
    """
    Schema para respuesta a Arduino
    """
    status: Literal["ok", "error"] = Field(..., description="Estado de la operación")
    msg: str = Field(..., description="Mensaje descriptivo")
    actuado: Optional[bool] = Field(None, description="Estado de actuación (opcional)")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "msg": "Datos recibidos correctamente",
                "actuado": True
            }
        }



class SensorReadingBulkCreate(BaseModel):
    """Schema para crear múltiples lecturas a la vez"""
    sensor_id: int = Field(..., gt=0)
    readings: List[float] = Field(..., min_length=1, max_length=1000)
