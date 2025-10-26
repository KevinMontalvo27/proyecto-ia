from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.user_schema import UserCreate, UserUpdate, UserLogin, UserResponse
from services.user_service import UserService
from database_config import SessionLocal
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo usuario

    Args:
        user: Datos del usuario (username y password)
        db: Sesión de base de datos

    Returns:
        UserResponse: Usuario creado

    Raises:
        HTTPException 400: Si el username ya existe
    """
    # Verificar si el username ya existe
    if UserService.username_exists(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El username ya está en uso"
        )

    # Crear usuario
    db_user = UserService.create_user(
        db=db,
        username=user.username,
        password=user.password
    )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear el usuario"
        )

    return db_user

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
        user_id: int,
        user_update: UserUpdate,
        db: Session = Depends(get_db)
):
    """
    Actualizar un usuario existente

    Args:
        user_id: ID del usuario a actualizar
        user_update: Datos a actualizar (username y/o password)
        db: Sesión de base de datos

    Returns:
        UserResponse: Usuario actualizado

    Raises:
        HTTPException 404: Si el usuario no existe
        HTTPException 400: Si el nuevo username ya está en uso
    """
    # Verificar si el usuario existe
    existing_user = UserService.get_user_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Convertir Pydantic a dict, excluyendo valores no establecidos
    update_data = user_update.model_dump(exclude_unset=True)

    # Si no hay nada que actualizar
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron datos para actualizar"
        )

    # Si se está actualizando el username, verificar que no exista
    if "username" in update_data:
        if UserService.username_exists(db, update_data["username"]):
            # Verificar que no sea el mismo usuario
            user_with_username = UserService.get_user_by_username(db, update_data["username"])
            if user_with_username and user_with_username.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El username ya está en uso"
                )

    # Actualizar usuario
    updated_user = UserService.update_user(db, user_id, update_data)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar el usuario"
        )

    return updated_user

@router.post("/login")
def authenticate_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Autenticar un usuario (login)

    Args:
        credentials: Username y password
        db: Sesión de base de datos

    Returns:
        dict: Mensaje de éxito con información del usuario

    Raises:
        HTTPException 401: Si las credenciales son inválidas
    """
    # Autenticar usuario
    user = UserService.authenticate_user(
        db=db,
        username=credentials.username,
        password=credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "message": "Login exitoso",
        "user_id": user.id,
        "username": user.username
    }


@router.get("/", response_model=List[UserResponse])
def get_all_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Obtener todos los usuarios

    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar (máximo 100)
        db: Sesión de base de datos

    Returns:
        List[UserResponse]: Lista de usuarios

    Example:
        GET /users/?skip=0&limit=10
    """
    # Limitar el máximo de usuarios por request
    if limit > 100:
        limit = 100

    users = UserService.get_all_users(db=db, skip=skip, limit=limit)
    return users