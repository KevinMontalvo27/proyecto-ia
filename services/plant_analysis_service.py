from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict, Any
from models.plant_model import Plant


class PlantService:
    @staticmethod
    def create_plant(
            db: Session,
            name: str,
            type: str,
            greenhouse_id: int
    ) -> Optional[Plant]:
        """
        Crea una nueva planta en la base de datos

        Args:
            db: Sesión de base de datos
            name: Nombre de la planta
            type: Tipo de planta
            greenhouse_id: ID del invernadero

        Returns:
            Plant: Planta creada o None si hay error
        """
        try:
            db_plant = Plant(
                name=name,
                type=type,
                greenhouse_id=greenhouse_id
            )

            db.add(db_plant)
            db.commit()
            db.refresh(db_plant)

            return db_plant

        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def get_plant_by_id(db: Session, plant_id: int) -> Optional[Plant]:
        """
        Obtiene una planta por su ID

        Args:
            db: Sesión de base de datos
            plant_id: ID de la planta

        Returns:
            Plant: Planta encontrada o None
        """
        return db.query(Plant).filter(Plant.id == plant_id).first()

    @staticmethod
    def get_plant_complete(db: Session, plant_id: int) -> Optional[Plant]:
        """
        Obtiene una planta con sus análisis cargados

        Args:
            db: Sesión de base de datos
            plant_id: ID de la planta

        Returns:
            Plant: Planta con análisis o None
        """
        return db.query(Plant).options(
            joinedload(Plant.analyses)
        ).filter(Plant.id == plant_id).first()

    @staticmethod
    def get_plants_by_greenhouse(
            db: Session,
            greenhouse_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Plant]:
        """
        Obtiene todas las plantas de un invernadero

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar

        Returns:
            List[Plant]: Lista de plantas
        """
        return db.query(Plant).filter(
            Plant.greenhouse_id == greenhouse_id
        ).offset(skip).limit(limit).all()

    @staticmethod
    def update_plant(
            db: Session,
            plant_id: int,
            update_data: Dict[str, Any]
    ) -> Optional[Plant]:
        """
        Actualiza los datos de una planta

        Args:
            db: Sesión de base de datos
            plant_id: ID de la planta a actualizar
            update_data: Diccionario con los campos a actualizar

        Returns:
            Plant: Planta actualizada o None si no existe
        """
        db_plant = PlantService.get_plant_by_id(db, plant_id)

        if not db_plant:
            return None

        for field, value in update_data.items():
            if hasattr(db_plant, field):
                setattr(db_plant, field, value)

        try:
            db.commit()
            db.refresh(db_plant)
            return db_plant
        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def delete_plant(db: Session, plant_id: int) -> bool:
        """
        Elimina una planta de la base de datos

        Args:
            db: Sesión de base de datos
            plant_id: ID de la planta a eliminar

        Returns:
            bool: True si se eliminó, False si no existe
        """
        db_plant = PlantService.get_plant_by_id(db, plant_id)

        if not db_plant:
            return False

        db.delete(db_plant)
        db.commit()
        return True

    @staticmethod
    def plant_belongs_to_greenhouse(
            db: Session,
            plant_id: int,
            greenhouse_id: int
    ) -> bool:
        """
        Verifica si una planta pertenece a un invernadero específico

        Args:
            db: Sesión de base de datos
            plant_id: ID de la planta
            greenhouse_id: ID del invernadero

        Returns:
            bool: True si pertenece, False si no
        """
        plant = PlantService.get_plant_by_id(db, plant_id)
        if not plant:
            return False
        return plant.greenhouse_id == greenhouse_id