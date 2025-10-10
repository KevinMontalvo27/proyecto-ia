from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Importar todos los modelos para que estén disponibles
from .user_model import User
from .greenhouse_model import Greenhouse
from .plant_model import Plant
from .sensor_model import Sensor
from .sensor_reading_model import SensorReading
from .plant_analysis_model import PlantAnalysis
from .chat_model import Chat
from .message_model import Message

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