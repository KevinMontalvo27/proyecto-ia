from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict, Any
from models.greenhouse_model import Greenhouse


class GreenhouseService:
    @staticmethod
    def create_greenhouse(
            db: Session,
            name: str,
            user_id: int,
            location: Optional[str] = None
    ) -> Optional[Greenhouse]:
        """
        Crea un nuevo invernadero en la base de datos

        Args:
            db: Sesión de base de datos
            name: Nombre del invernadero
            user_id: ID del usuario propietario
            location: Ubicación física (opcional)

        Returns:
            Greenhouse: Invernadero creado o None si hay error
        """
        try:
            db_greenhouse = Greenhouse(
                name=name,
                user_id=user_id,
                location=location
            )

            db.add(db_greenhouse)
            db.commit()
            db.refresh(db_greenhouse)

            return db_greenhouse

        except IntegrityError:
            db.rollback()
            return None

    def get_greenhouse_by_id(db: Session, greenhouse_id: int) -> Optional[Greenhouse]:
        """
        Obtiene un invernadero por su ID

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero

        Returns:
            Greenhouse: Invernadero encontrado o None
        """
        return db.query(Greenhouse).filter(Greenhouse.id == greenhouse_id).first()

    @staticmethod
    def update_greenhouse(
            db: Session,
            greenhouse_id: int,
            update_data: Dict[str, Any]
    ) -> Optional[Greenhouse]:
        """
        Actualiza los datos de un invernadero

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero a actualizar
            update_data: Diccionario con los campos a actualizar
                        Ejemplo: {"name": "Nuevo nombre", "location": "Nueva ubicación"}

        Returns:
            Greenhouse: Invernadero actualizado o None si no existe
        """
        db_greenhouse = GreenhouseService.get_greenhouse_by_id(db, greenhouse_id)

        if not db_greenhouse:
            return None

        # Actualizar campos
        for field, value in update_data.items():
            if hasattr(db_greenhouse, field):
                setattr(db_greenhouse, field, value)

        try:
            db.commit()
            db.refresh(db_greenhouse)
            return db_greenhouse
        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def delete_greenhouse(db: Session, greenhouse_id: int) -> bool:
        """
        Elimina un invernadero de la base de datos

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero a eliminar

        Returns:
            bool: True si se eliminó, False si no existe
        """
        db_greenhouse = GreenhouseService.get_greenhouse_by_id(db, greenhouse_id)

        if not db_greenhouse:
            return False

        db.delete(db_greenhouse)
        db.commit()
        return True
