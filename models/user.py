from datetime import datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from . import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    # Relaciones
    greenhouses = relationship('Greenhouse', back_populates='user', cascade='all, delete-orphan')
    chats = relationship('Chat', back_populates='user', cascade='all, delete-orphan')