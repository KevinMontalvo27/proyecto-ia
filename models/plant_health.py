from sqlalchemy import Column, Float, Integer, String
from . import Base


class PlantHealth(Base):
    __tablename__ = 'plant_health'

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant = Column(String(255), nullable=False)
    diagnostic = Column(String, nullable=False)