from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any
from models.user_model import User


class UserService:
    @staticmethod
    def create_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Crea un nuevo usuario en la base de datos

        Args:
            db: Sesión de base de datos
            username: Nombre de usuario
            password: Contraseña

        Returns:
            User: Usuario creado o None si ya existe
        """
        try:
            # Crear usuario
            db_user = User(
                username=username,
                password=password
            )

            db.add(db_user)
            db.commit()
            db.refresh(db_user)

            return db_user

        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por su ID

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario

        Returns:
            User: Usuario encontrado o None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user(
            db: Session,
            user_id: int,
            update_data: Dict[str, Any]
    ) -> Optional[User]:
        """
        Actualiza los datos de un usuario

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario a actualizar
            update_data: Diccionario con los campos a actualizar
                        Ejemplo: {"username": "nuevo", "password": "nueva123"}

        Returns:
            User: Usuario actualizado o None si no existe
        """
        db_user = UserService.get_user_by_id(db, user_id)

        if not db_user:
            return None

        # Actualizar campos
        for field, value in update_data.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)

        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            return None

    def authenticate_user(
            db: Session,
            username: str,
            password: str
    ) -> Optional[User]:
        """
        Autentica un usuario verificando username y contraseña

        Args:
            db: Sesión de base de datos
            username: Nombre de usuario
            password: Contraseña

        Returns:
            User: Usuario autenticado o None si las credenciales son inválidas
        """
        user = UserService.get_user_by_username(db, username)

        if not user:
            return None

        if user.password != password:
            return None

        return user

    @staticmethod
    def username_exists(db: Session, username: str) -> bool:
        """
        Verifica si un username ya existe en la base de datos

        Args:
            db: Sesión de base de datos
            username: Nombre de usuario a verificar

        Returns:
            bool: True si existe, False si no
        """
        return db.query(User).filter(User.username == username).first() is not None

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Obtiene un usuario por su username

        Args:
            db: Sesión de base de datos
            username: Nombre de usuario

        Returns:
            User: Usuario encontrado o None
        """
        return db.query(User).filter(User.username == username).first()