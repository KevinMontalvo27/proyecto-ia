from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from . import Base


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    author = Column(String, nullable=False)  # user | gemini
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    chat = relationship('Chat', back_populates='messages')