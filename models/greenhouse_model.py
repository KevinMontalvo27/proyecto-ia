from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from . import Base


class Greenhouse(Base):
    __tablename__ = 'greenhouses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    location = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship('User', back_populates='greenhouses')
    plants = relationship('Plant', back_populates='greenhouse', cascade='all, delete-orphan')
    sensors = relationship('Sensor', back_populates='greenhouse', cascade='all, delete-orphan')
