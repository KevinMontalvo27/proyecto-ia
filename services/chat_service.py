from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime
from models.chat_model import Chat
from models.message_model import Message
from clients.gemini_client import GeminiClient


class ChatService:
    """Servicio para gestionar chats y mensajes con Gemini"""

    # Cliente de Gemini compartido (Singleton)
    _gemini_client = None

    @classmethod
    def get_gemini_client(cls) -> GeminiClient:
        """Obtiene o crea una instancia del cliente de Gemini"""
        if cls._gemini_client is None:
            cls._gemini_client = GeminiClient()
        return cls._gemini_client

    @staticmethod
    def create_chat(
            db: Session,
            user_id: int,
            name: str
    ) -> Optional[Chat]:
        """
        Crea un nuevo chat

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            name: Nombre del chat

        Returns:
            Chat: Chat creado o None si hay error
        """
        try:
            db_chat = Chat(
                user_id=user_id,
                name=name
            )

            db.add(db_chat)
            db.commit()
            db.refresh(db_chat)

            return db_chat

        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def get_chat_by_id(db: Session, chat_id: int) -> Optional[Chat]:
        """Obtiene un chat por su ID"""
        return db.query(Chat).filter(Chat.id == chat_id).first()

    @staticmethod
    def get_chat_with_messages(db: Session, chat_id: int) -> Optional[Chat]:
        """Obtiene un chat con todos sus mensajes"""
        return db.query(Chat).options(
            joinedload(Chat.messages)
        ).filter(Chat.id == chat_id).first()

    @staticmethod
    def get_user_chats(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 50
    ) -> List[Chat]:
        """Obtiene todos los chats de un usuario"""
        return db.query(Chat).filter(
            Chat.user_id == user_id
        ).order_by(
            Chat.updated_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def create_message(
            db: Session,
            chat_id: int,
            author: str,
            message: str
    ) -> Optional[Message]:
        """
        Crea un nuevo mensaje en un chat

        Args:
            db: Sesión de base de datos
            chat_id: ID del chat
            author: Autor del mensaje ('user' o 'gemini')
            message: Contenido del mensaje

        Returns:
            Message: Mensaje creado o None si hay error
        """
        try:
            db_message = Message(
                chat_id=chat_id,
                author=author,
                message=message
            )

            db.add(db_message)

            # Actualizar timestamp del chat
            chat = ChatService.get_chat_by_id(db, chat_id)
            if chat:
                chat.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(db_message)

            return db_message

        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def send_message_to_gemini(
            db: Session,
            chat_id: int,
            user_message: str,
            sensor_data: Optional[dict] = None,
            plant_analysis: Optional[dict] = None
    ) -> Optional[Message]:
        """
        Envía un mensaje a Gemini y guarda la respuesta

        Args:
            db: Sesión de base de datos
            chat_id: ID del chat
            user_message: Mensaje del usuario
            sensor_data: Datos de sensores (opcional)
            plant_analysis: Análisis de plantas (opcional)

        Returns:
            Message: Respuesta de Gemini o None si hay error
        """
        try:
            # Guardar mensaje del usuario
            user_msg = ChatService.create_message(
                db=db,
                chat_id=chat_id,
                author="user",
                message=user_message
            )

            if not user_msg:
                return None

            # Obtener historial del chat
            chat = ChatService.get_chat_with_messages(db, chat_id)
            if not chat:
                return None

            # Convertir historial a formato de Gemini
            history = ChatService._convert_history_to_gemini_format(chat.messages[:-1])

            # Crear sesión de chat con historial
            gemini_client = ChatService.get_gemini_client()
            chat_session = gemini_client.create_chat_session(history=history)

            # Enviar mensaje a Gemini
            response_text = gemini_client.send_message(
                chat_session=chat_session,
                message=user_message,
                sensor_data=sensor_data,
                plant_analysis=plant_analysis
            )

            # Guardar respuesta de Gemini
            gemini_msg = ChatService.create_message(
                db=db,
                chat_id=chat_id,
                author="gemini",
                message=response_text
            )

            return gemini_msg

        except Exception as e:
            db.rollback()
            raise Exception(f"Error al comunicarse con Gemini: {str(e)}")

    @staticmethod
    def _convert_history_to_gemini_format(messages: List[Message]) -> List[dict]:
        """
        Convierte el historial de mensajes al formato de Gemini

        Args:
            messages: Lista de mensajes de la BD

        Returns:
            Lista de mensajes en formato Gemini
        """
        history = []
        for msg in messages:
            role = "user" if msg.author == "user" else "model"
            history.append({
                "role": role,
                "parts": [msg.message]
            })
        return history

    @staticmethod
    def update_chat_name(
            db: Session,
            chat_id: int,
            new_name: str
    ) -> Optional[Chat]:
        """Actualiza el nombre de un chat"""
        chat = ChatService.get_chat_by_id(db, chat_id)

        if not chat:
            return None

        chat.name = new_name
        chat.updated_at = datetime.utcnow()

        try:
            db.commit()
            db.refresh(chat)
            return chat
        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def delete_chat(db: Session, chat_id: int) -> bool:
        """Elimina un chat y todos sus mensajes (cascade)"""
        chat = ChatService.get_chat_by_id(db, chat_id)

        if not chat:
            return False

        db.delete(chat)
        db.commit()
        return True

    @staticmethod
    def user_owns_chat(db: Session, chat_id: int, user_id: int) -> bool:
        """Verifica si un usuario es propietario de un chat"""
        chat = ChatService.get_chat_by_id(db, chat_id)
        if not chat:
            return False
        return chat.user_id == user_id