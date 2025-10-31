from sqlalchemy import Column, Float, Integer, String
from . import Base


class SensorData(Base):
    __tablename__ = 'sensor_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor = Column(String(255), nullable=False)
    umbral = Column(Float, nullable=False)