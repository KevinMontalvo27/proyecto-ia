from pydantic import BaseModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .message_schema import MessageResponse


class ChatBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del chat")


class ChatCreate(ChatBase):
    """Schema para crear un chat"""
    pass


class ChatUpdate(BaseModel):
    """Schema para actualizar chat"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class ChatResponse(ChatBase):
    """Schema para respuesta de chat"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatDetailResponse(ChatResponse):
    """Schema con mensajes del chat"""
    messages: List['MessageResponse'] = []

    class Config:
        from_attributes = True


# Resolver referencias circulares
from .message_schema import MessageResponse
ChatDetailResponse.model_rebuild()