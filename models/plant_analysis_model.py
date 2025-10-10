from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from . import Base


class PlantAnalysis(Base):
    __tablename__ = 'plants_analysis'

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey('plants.id'), nullable=False)
    analysis_type = Column(String, nullable=False)  # health | pest
    result = Column(String, nullable=False)
    confidence = Column(Float)  # 0-1
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    plant = relationship('Plant', back_populates='analyses')