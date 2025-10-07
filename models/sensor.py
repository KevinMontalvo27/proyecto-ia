from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from . import Base


class Sensor(Base):
    __tablename__ = 'sensors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    greenhouse_id = Column(Integer, ForeignKey('greenhouses.id'), nullable=False)
    name = Column(String, nullable=False)  # Ej. Sensor de temperatura 1
    type = Column(String, nullable=False)  # temperature | humidity | light | soil_moisture
    active = Column(Boolean, default=True)
    installed_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    greenhouse = relationship('Greenhouse', back_populates='sensors')
    readings = relationship('SensorReading', back_populates='sensor', cascade='all, delete-orphan')