from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.greenhouse_schema import (
    GreenhouseCreate,
    GreenhouseUpdate,
    GreenhouseResponse,
    GreenhouseDetailResponse
)
from services.greenhouse_service import GreenhouseService
from database_config import SessionLocal


router = APIRouter(prefix="/greenhouses", tags=["greenhouses"])

def get_db():
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=GreenhouseResponse, status_code=status.HTTP_201_CREATED)
def create_greenhouse(
        greenhouse: GreenhouseCreate,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Crear un nuevo invernadero

    Args:
        greenhouse: Datos del invernadero (name y location opcional)
        user_id: ID del usuario propietario (por ahora query param, luego JWT)
        db: Sesión de base de datos

    Returns:
        GreenhouseResponse: Invernadero creado

    Raises:
        HTTPException 400: Si hay error al crear
    """
    # TODO: Verificar que el user_id existe
    # user = UserService.get_user_by_id(db, user_id)
    # if not user:
    #     raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Crear invernadero
    db_greenhouse = GreenhouseService.create_greenhouse(
        db=db,
        name=greenhouse.name,
        user_id=user_id,
        location=greenhouse.location
    )

    if not db_greenhouse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear el invernadero"
        )

    return db_greenhouse


@router.get("/{greenhouse_id}", response_model=GreenhouseDetailResponse)
def get_greenhouse(greenhouse_id: int, db: Session = Depends(get_db)):
    """
    Obtener un invernadero por su ID con plantas y sensores

    Args:
        greenhouse_id: ID del invernadero
        db: Sesión de base de datos

    Returns:
        GreenhouseDetailResponse: Invernadero con plantas y sensores

    Raises:
        HTTPException 404: Si el invernadero no existe
    """
    # Obtener invernadero con relaciones
    greenhouse = GreenhouseService.get_greenhouse_complete(db, greenhouse_id)

    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    return greenhouse


@router.patch("/{greenhouse_id}", response_model=GreenhouseResponse)
def update_greenhouse(
        greenhouse_id: int,
        greenhouse_update: GreenhouseUpdate,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Actualizar un invernadero existente

    Args:
        greenhouse_id: ID del invernadero a actualizar
        greenhouse_update: Datos a actualizar (name y/o location)
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        GreenhouseResponse: Invernadero actualizado

    Raises:
        HTTPException 404: Si el invernadero no existe
        HTTPException 403: Si el usuario no es el propietario
        HTTPException 400: Si no hay datos para actualizar
    """
    # Verificar si el invernadero existe
    existing_greenhouse = GreenhouseService.get_greenhouse_by_id(db, greenhouse_id)
    if not existing_greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    # Verificar que el usuario sea el propietario
    if not GreenhouseService.user_owns_greenhouse(db, greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar este invernadero"
        )

    # Convertir Pydantic a dict, excluyendo valores no establecidos
    update_data = greenhouse_update.model_dump(exclude_unset=True)

    # Si no hay nada que actualizar
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron datos para actualizar"
        )

    # Actualizar invernadero
    updated_greenhouse = GreenhouseService.update_greenhouse(
        db, greenhouse_id, update_data
    )

    if not updated_greenhouse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar el invernadero"
        )

    return updated_greenhouse


@router.delete("/{greenhouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_greenhouse(
        greenhouse_id: int,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Eliminar un invernadero

    ADVERTENCIA: Esto eliminará en cascada todas las plantas y sensores asociados

    Args:
        greenhouse_id: ID del invernadero a eliminar
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: Si el invernadero no existe
        HTTPException 403: Si el usuario no es el propietario
    """
    # Verificar si el invernadero existe
    existing_greenhouse = GreenhouseService.get_greenhouse_by_id(db, greenhouse_id)
    if not existing_greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    # Verificar que el usuario sea el propietario
    if not GreenhouseService.user_owns_greenhouse(db, greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este invernadero"
        )

    # Eliminar invernadero
    deleted = GreenhouseService.delete_greenhouse(db, greenhouse_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al eliminar el invernadero"
        )