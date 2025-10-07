from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from . import Base


class SensorReading(Base):
    __tablename__ = 'sensor_readings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey('sensors.id'), nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relaciones
    sensor = relationship('Sensor', back_populates='readings')