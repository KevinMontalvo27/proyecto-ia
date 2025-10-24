from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from schemas.chat_schema import (
    ChatCreate,
    ChatResponse,
    ChatDetailResponse,
    ChatUpdate
)
from schemas.message_schema import MessageCreate, MessageResponse
from services.chat_service import ChatService
from database_config import SessionLocal

router = APIRouter(prefix="/chats", tags=["chats"])


# Schema adicional para envío de mensajes
class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    sensor_data: Optional[dict] = Field(None, description="Datos de sensores (opcional)")
    plant_analysis: Optional[dict] = Field(None, description="Análisis de plantas (opcional)")


def get_db():
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
        chat: ChatCreate,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Crear un nuevo chat

    Args:
        chat: Datos del chat (nombre)
        user_id: ID del usuario propietario
        db: Sesión de base de datos

    Returns:
        ChatResponse: Chat creado

    Raises:
        HTTPException 400: Si hay error al crear el chat
    """
    db_chat = ChatService.create_chat(
        db=db,
        user_id=user_id,
        name=chat.name
    )

    if not db_chat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear el chat"
        )

    return db_chat


@router.get("/user/{user_id}", response_model=List[ChatResponse])
def get_user_chats(
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db)
):
    """
    Obtener todos los chats de un usuario

    Args:
        user_id: ID del usuario
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos

    Returns:
        List[ChatResponse]: Lista de chats del usuario ordenados por fecha de actualización
    """
    chats = ChatService.get_user_chats(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit
    )

    return chats


@router.get("/{chat_id}", response_model=ChatDetailResponse)
def get_chat(
        chat_id: int,
        user_id: int,  # TODO: Obtener del JWT
        db: Session = Depends(get_db)
):
    """
    Obtener un chat con todos sus mensajes

    Args:
        chat_id: ID del chat
        user_id: ID del usuario (para verificar permisos)
        db: Sesión de base de datos

    Returns:
        ChatDetailResponse: Chat con historial completo de mensajes

    Raises:
        HTTPException 404: Si el chat no existe
        HTTPException 403: Si el usuario no es propietario del chat
    """
    # Verificar que el chat existe
    chat = ChatService.get_chat_with_messages(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado"
        )

    # Verificar permisos
    if not ChatService.user_owns_chat(db, chat_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este chat"
        )

    return chat


@router.post("/{chat_id}/messages", response_model=MessageResponse)
def send_message(
        chat_id: int,
        request: SendMessageRequest,
        user_id: int,  # TODO: Obtener del JWT
        db: Session = Depends(get_db)
):
    """
    Enviar un mensaje a Gemini en un chat

    Este endpoint:
    1. Guarda el mensaje del usuario en la BD
    2. Obtiene el historial del chat
    3. Envía el mensaje a Gemini con el contexto
    4. Guarda la respuesta de Gemini
    5. Retorna la respuesta al usuario

    Args:
        chat_id: ID del chat
        request: Objeto con el mensaje y datos opcionales
        user_id: ID del usuario
        db: Sesión de base de datos

    Returns:
        MessageResponse: Respuesta de Gemini guardada en la BD

    Raises:
        HTTPException 404: Si el chat no existe
        HTTPException 403: Si el usuario no es propietario
        HTTPException 500: Si hay error al comunicarse con Gemini

    Example:
        ```json
        {
          "message": "¿Qué temperatura necesitan los tomates?",
          "sensor_data": {
            "temperature": 26.5,
            "humidity": 75.0
          },
          "plant_analysis": {
            "label": "Tomato___Late_blight",
            "confidence_percent": 98.23
          }
        }
        ```
    """
    # Verificar que el chat existe
    chat = ChatService.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado"
        )

    # Verificar permisos
    if not ChatService.user_owns_chat(db, chat_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para enviar mensajes en este chat"
        )

    # Enviar mensaje a Gemini
    try:
        response = ChatService.send_message_to_gemini(
            db=db,
            chat_id=chat_id,
            user_message=request.message,
            sensor_data=request.sensor_data,
            plant_analysis=request.plant_analysis
        )

        if not response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar el mensaje"
            )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al comunicarse con Gemini: {str(e)}"
        )


@router.patch("/{chat_id}", response_model=ChatResponse)
def update_chat(
        chat_id: int,
        chat_update: ChatUpdate,
        user_id: int,  # TODO: Obtener del JWT
        db: Session = Depends(get_db)
):
    """
    Actualizar el nombre de un chat

    Args:
        chat_id: ID del chat
        chat_update: Nuevo nombre del chat
        user_id: ID del usuario
        db: Sesión de base de datos

    Returns:
        ChatResponse: Chat actualizado

    Raises:
        HTTPException 404: Si el chat no existe
        HTTPException 403: Si el usuario no es propietario
        HTTPException 400: Si no se proporciona nombre
    """
    # Verificar que el chat existe
    chat = ChatService.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado"
        )

    # Verificar permisos
    if not ChatService.user_owns_chat(db, chat_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar este chat"
        )

    # Actualizar nombre
    if not chat_update.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes proporcionar un nombre"
        )

    updated_chat = ChatService.update_chat_name(
        db=db,
        chat_id=chat_id,
        new_name=chat_update.name
    )

    if not updated_chat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar el chat"
        )

    return updated_chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
        chat_id: int,
        user_id: int,  # TODO: Obtener del JWT
        db: Session = Depends(get_db)
):
    """
    Eliminar un chat y todos sus mensajes

    ADVERTENCIA: Esta acción eliminará permanentemente el chat y todo su historial

    Args:
        chat_id: ID del chat
        user_id: ID del usuario
        db: Sesión de base de datos

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: Si el chat no existe
        HTTPException 403: Si el usuario no es propietario
        HTTPException 400: Si hay error al eliminar
    """
    # Verificar que el chat existe
    chat = ChatService.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat no encontrado"
        )

    # Verificar permisos
    if not ChatService.user_owns_chat(db, chat_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este chat"
        )

    # Eliminar chat
    deleted = ChatService.delete_chat(db, chat_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al eliminar el chat"
        )