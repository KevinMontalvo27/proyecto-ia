from sqlalchemy import Column, Float, Integer, String
from . import Base


class SensorData(Base):
    __tablename__ = 'sensor_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor = Column(String(255), nullable=False)      # temperature, humidity, light, smoke
    umbral_min = Column(Float, nullable=False)         # umbral minimo
    umbral_max = Column(Float, nullable=False)         # umbral maximo
    plant_type = Column(String(255), nullable=False)