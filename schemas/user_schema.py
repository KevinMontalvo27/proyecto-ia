from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario")


class UserCreate(UserBase):
    """Schema para crear un usuario"""
    password: str = Field(..., min_length=8, description="Contraseña (mínimo 8 caracteres)")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not any(char.isupper() for char in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        return v


class UserLogin(BaseModel):
    """Schema para login"""
    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema para actualizar usuario"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """Schema para respuesta de usuario"""
    id: int

    class Config:
        from_attributes = True