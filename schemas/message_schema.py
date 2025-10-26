from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class MessageBase(BaseModel):
    author: Literal['user', 'gemini'] = Field(..., description="Autor del mensaje")
    message: str = Field(..., min_length=1, description="Contenido del mensaje")


class MessageCreate(MessageBase):
    """Schema para crear un mensaje"""
    chat_id: int = Field(..., gt=0, description="ID del chat")


class MessageResponse(MessageBase):
    """Schema para respuesta de mensaje"""
    id: int
    chat_id: int
    sent_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }