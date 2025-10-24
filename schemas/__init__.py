from .user_schema import UserCreate, UserLogin, UserResponse, UserUpdate
from .greenhouse_schema import GreenhouseCreate, GreenhouseResponse, GreenhouseUpdate
from .plant_schema import PlantCreate, PlantResponse, PlantUpdate
from .sensor_schema import SensorCreate, SensorResponse, SensorUpdate
from .sensor_reading_schema import SensorReadingCreate, SensorReadingResponse
from .message_schema import MessageCreate, MessageResponse
from .chat_schema import ChatCreate, ChatResponse, ChatUpdate, ChatDetailResponse


__all__ = [
    # User
    'UserCreate', 'UserLogin', 'UserResponse', 'UserUpdate',
    # Greenhouse
    'GreenhouseCreate', 'GreenhouseResponse', 'GreenhouseUpdate',
    # Plant
    'PlantCreate', 'PlantResponse', 'PlantUpdate',
    # Sensor
    'SensorCreate', 'SensorResponse', 'SensorUpdate',
    # SensorReading
    'SensorReadingCreate', 'SensorReadingResponse',
    # PlantAnalysis
    # Message (debe ir antes de Chat)
    'MessageCreate', 'MessageResponse',
    # Chat
    'ChatCreate', 'ChatResponse', 'ChatUpdate', 'ChatDetailResponse',
]