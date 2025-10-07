from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Importar todos los modelos para que estén disponibles
from .user import User
from .greenhouse import Greenhouse
from .plant import Plant
from .sensor import Sensor
from .sensor_reading import SensorReading
from .plant_analysis import PlantAnalysis
from .chat import Chat
from .message import Message

__all__ = [
    'Base',
    'User',
    'Greenhouse',
    'Plant',
    'Sensor',
    'SensorReading',
    'PlantAnalysis',
    'Chat',
    'Message'
]