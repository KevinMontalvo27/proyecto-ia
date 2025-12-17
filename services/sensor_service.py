from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict, Any
from models.sensor_model import Sensor


class SensorService:
    @staticmethod
    def create_sensor(
            db: Session,
            name: str,
            type: str,
            greenhouse_id: int,
            active: bool = True
    ) -> Optional[Sensor]:
        """
        Crea un nuevo sensor en la base de datos

        Args:
            db: Sesión de base de datos
            name: Nombre del sensor
            type: Tipo de sensor (temperature, humidity, light, soil_moisture)
            greenhouse_id: ID del invernadero
            active: Estado del sensor (por defecto True)

        Returns:
            Sensor: Sensor creado o None si hay error
        """
        try:
            db_sensor = Sensor(
                name=name,
                type=type,
                greenhouse_id=greenhouse_id,
                active=active
            )

            db.add(db_sensor)
            db.commit()
            db.refresh(db_sensor)

            return db_sensor

        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def get_sensor_by_id(db: Session, sensor_id: int) -> Optional[Sensor]:
        """
        Obtiene un sensor por su ID

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor

        Returns:
            Sensor: Sensor encontrado o None
        """
        return db.query(Sensor).filter(Sensor.id == sensor_id).first()

    @staticmethod
    def get_sensor_complete(db: Session, sensor_id: int) -> Optional[Sensor]:
        """
        Obtiene un sensor con sus lecturas cargadas

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor

        Returns:
            Sensor: Sensor con lecturas o None
        """
        return db.query(Sensor).options(
            joinedload(Sensor.readings)
        ).filter(Sensor.id == sensor_id).first()

    @staticmethod
    def get_sensors_by_greenhouse(
            db: Session,
            greenhouse_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Sensor]:
        """
        Obtiene todos los sensores de un invernadero

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar

        Returns:
            List[Sensor]: Lista de sensores ordenados por fecha de instalación
        """
        return db.query(Sensor).filter(
            Sensor.greenhouse_id == greenhouse_id
        ).order_by(
            Sensor.installed_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_active_sensors_by_greenhouse(
            db: Session,
            greenhouse_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Sensor]:
        """
        Obtiene todos los sensores activos de un invernadero

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar

        Returns:
            List[Sensor]: Lista de sensores activos
        """
        return db.query(Sensor).filter(
            Sensor.greenhouse_id == greenhouse_id,
            Sensor.active == True
        ).order_by(
            Sensor.installed_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def update_sensor(
            db: Session,
            sensor_id: int,
            update_data: Dict[str, Any]
    ) -> Optional[Sensor]:
        """
        Actualiza los datos de un sensor

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor a actualizar
            update_data: Diccionario con los campos a actualizar
                        Ejemplo: {"name": "Nuevo nombre", "active": False}

        Returns:
            Sensor: Sensor actualizado o None si no existe
        """
        db_sensor = SensorService.get_sensor_by_id(db, sensor_id)

        if not db_sensor:
            return None

        for field, value in update_data.items():
            if hasattr(db_sensor, field):
                setattr(db_sensor, field, value)

        try:
            db.commit()
            db.refresh(db_sensor)
            return db_sensor
        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def delete_sensor(db: Session, sensor_id: int) -> bool:
        """
        Elimina un sensor de la base de datos

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor a eliminar

        Returns:
            bool: True si se eliminó, False si no existe
        """
        db_sensor = SensorService.get_sensor_by_id(db, sensor_id)

        if not db_sensor:
            return False

        db.delete(db_sensor)
        db.commit()
        return True

    @staticmethod
    def sensor_belongs_to_greenhouse(
            db: Session,
            sensor_id: int,
            greenhouse_id: int
    ) -> bool:
        """
        Verifica si un sensor pertenece a un invernadero específico

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            greenhouse_id: ID del invernadero

        Returns:
            bool: True si pertenece, False si no
        """
        sensor = SensorService.get_sensor_by_id(db, sensor_id)
        if not sensor:
            return False
        return sensor.greenhouse_id == greenhouse_id

    @staticmethod
    def get_all_sensors(db: Session, skip: int = 0, limit: int = 100) -> List[Sensor]:
        """
        Obtener todos los sensores con paginación

        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar

        Returns:
            List[Sensor]: Lista de sensores
        """
        return db.query(Sensor).offset(skip).limit(limit).all()