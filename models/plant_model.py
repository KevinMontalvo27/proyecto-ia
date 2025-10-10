from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from . import Base


class Plant(Base):
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    greenhouse_id = Column(Integer, ForeignKey('greenhouses.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    greenhouse = relationship('Greenhouse', back_populates='plants')
    analyses = relationship('PlantAnalysis', back_populates='plant', cascade='all, delete-orphan')