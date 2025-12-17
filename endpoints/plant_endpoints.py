from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas.plant_schema import (
    PlantCreate,
    PlantUpdate,
    PlantResponse,
    PlantDetailResponse
)
from services.plant_service import PlantService
from services.greenhouse_service import GreenhouseService
from database_config import SessionLocal

router = APIRouter(prefix="/plants", tags=["plants"])


def get_db():
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=PlantResponse, status_code=status.HTTP_201_CREATED)
def create_plant(
        plant: PlantCreate,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Crear una nueva planta

    Args:
        plant: Datos de la planta (name, type, greenhouse_id)
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        PlantResponse: Planta creada

    Raises:
        HTTPException 404: Si el invernadero no existe
        HTTPException 403: Si el usuario no es propietario del invernadero
        HTTPException 400: Si hay error al crear
    """
    # Verificar que el invernadero existe
    greenhouse = GreenhouseService.get_greenhouse_by_id(db, plant.greenhouse_id)
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    # Verificar que el usuario es propietario del invernadero
    if not GreenhouseService.user_owns_greenhouse(db, plant.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para agregar plantas a este invernadero"
        )

    # Crear planta
    db_plant = PlantService.create_plant(
        db=db,
        name=plant.name,
        type=plant.type,
        greenhouse_id=plant.greenhouse_id
    )

    if not db_plant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear la planta"
        )

    return db_plant


@router.get("/", response_model=List[PlantResponse])
def get_all_plants(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Obtener todas las plantas

    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos

    Returns:
        List[PlantResponse]: Lista de todas las plantas

    Example:
        GET /plants/?skip=0&limit=10
    """
    plants = PlantService.get_all_plants(
        db=db,
        skip=skip,
        limit=limit
    )
    return plants


@router.get("/search", response_model=List[PlantResponse])
def search_plants(
        name: str = Query(..., min_length=1, description="Término de búsqueda"),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Buscar plantas por nombre (búsqueda parcial)

    Args:
        name: Término de búsqueda (case-insensitive)
        skip: Número de registros a saltar
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos

    Returns:
        List[PlantResponse]: Lista de plantas que coinciden con la búsqueda

    Example:
        GET /plants/search?name=tomate&skip=0&limit=10
    """
    plants = PlantService.search_plants_by_name(
        db=db,
        search_term=name,
        skip=skip,
        limit=limit
    )
    return plants


@router.get("/type/{plant_type}", response_model=List[PlantResponse])
def get_plants_by_type(
        plant_type: str,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Obtener todas las plantas de un tipo específico

    Args:
        plant_type: Tipo de planta (ej: "tomate", "lechuga")
        skip: Número de registros a saltar
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos

    Returns:
        List[PlantResponse]: Lista de plantas del tipo especificado

    Example:
        GET /plants/type/tomate?skip=0&limit=10
    """
    plants = PlantService.get_plants_by_type(
        db=db,
        plant_type=plant_type,
        skip=skip,
        limit=limit
    )
    return plants


@router.get("/greenhouse/{greenhouse_id}", response_model=List[PlantResponse])
def get_greenhouse_plants(
        greenhouse_id: int,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Obtener todas las plantas de un invernadero

    Args:
        greenhouse_id: ID del invernadero
        skip: Número de registros a saltar
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos

    Returns:
        List[PlantResponse]: Lista de plantas del invernadero

    Raises:
        HTTPException 404: Si el invernadero no existe

    Example:
        GET /plants/greenhouse/1?skip=0&limit=10
    """
    # Verificar que el invernadero existe
    greenhouse = GreenhouseService.get_greenhouse_by_id(db, greenhouse_id)
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    plants = PlantService.get_plants_by_greenhouse(
        db=db,
        greenhouse_id=greenhouse_id,
        skip=skip,
        limit=limit
    )
    return plants


@router.get("/greenhouse/{greenhouse_id}/count")
def count_greenhouse_plants(
        greenhouse_id: int,
        db: Session = Depends(get_db)
):
    """
    Contar el número de plantas en un invernadero

    Args:
        greenhouse_id: ID del invernadero
        db: Sesión de base de datos

    Returns:
        dict: Objeto con el conteo de plantas

    Raises:
        HTTPException 404: Si el invernadero no existe

    Example:
        GET /plants/greenhouse/1/count
        Response: {"greenhouse_id": 1, "count": 15}
    """
    # Verificar que el invernadero existe
    greenhouse = GreenhouseService.get_greenhouse_by_id(db, greenhouse_id)
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    count = PlantService.count_plants_by_greenhouse(
        db=db,
        greenhouse_id=greenhouse_id
    )

    return {
        "greenhouse_id": greenhouse_id,
        "count": count
    }


@router.get("/{plant_id}", response_model=PlantDetailResponse)
def get_plant(
        plant_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener una planta por su ID con sus análisis

    Args:
        plant_id: ID de la planta
        db: Sesión de base de datos

    Returns:
        PlantDetailResponse: Planta con análisis

    Raises:
        HTTPException 404: Si la planta no existe
    """
    plant = PlantService.get_plant_complete(db, plant_id)

    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planta no encontrada"
        )

    return plant


@router.patch("/{plant_id}", response_model=PlantResponse)
def update_plant(
        plant_id: int,
        plant_update: PlantUpdate,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Actualizar una planta existente

    Args:
        plant_id: ID de la planta a actualizar
        plant_update: Datos a actualizar (name y/o type)
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        PlantResponse: Planta actualizada

    Raises:
        HTTPException 404: Si la planta no existe
        HTTPException 403: Si el usuario no es propietario del invernadero
        HTTPException 400: Si no hay datos para actualizar
    """
    # Verificar que la planta existe
    existing_plant = PlantService.get_plant_by_id(db, plant_id)
    if not existing_plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planta no encontrada"
        )

    # Verificar que el usuario es propietario del invernadero
    if not GreenhouseService.user_owns_greenhouse(db, existing_plant.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta planta"
        )

    # Convertir Pydantic a dict, excluyendo valores no establecidos
    update_data = plant_update.model_dump(exclude_unset=True)

    # Si no hay nada que actualizar
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron datos para actualizar"
        )

    # Actualizar planta
    updated_plant = PlantService.update_plant(
        db, plant_id, update_data
    )

    if not updated_plant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar la planta"
        )

    return updated_plant


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plant(
        plant_id: int,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Eliminar una planta

    ADVERTENCIA: Esta acción eliminará permanentemente la planta y todos sus análisis

    Args:
        plant_id: ID de la planta a eliminar
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: Si la planta no existe
        HTTPException 403: Si el usuario no es propietario del invernadero
    """
    # Verificar que la planta existe
    existing_plant = PlantService.get_plant_by_id(db, plant_id)
    if not existing_plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planta no encontrada"
        )

    # Verificar que el usuario es propietario del invernadero
    if not GreenhouseService.user_owns_greenhouse(db, existing_plant.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta planta"
        )

    # Eliminar planta
    deleted = PlantService.delete_plant(db, plant_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al eliminar la planta"
        )


@router.delete("/greenhouse/{greenhouse_id}/all", status_code=status.HTTP_200_OK)
def delete_all_greenhouse_plants(
        greenhouse_id: int,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Eliminar todas las plantas de un invernadero

    ADVERTENCIA: Esta acción eliminará permanentemente todas las plantas del invernadero

    Args:
        greenhouse_id: ID del invernadero
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        dict: Objeto con el número de plantas eliminadas

    Raises:
        HTTPException 404: Si el invernadero no existe
        HTTPException 403: Si el usuario no es propietario del invernadero

    Example:
        DELETE /plants/greenhouse/1/all
        Response: {"message": "Plantas eliminadas exitosamente", "deleted_count": 15}
    """
    # Verificar que el invernadero existe
    greenhouse = GreenhouseService.get_greenhouse_by_id(db, greenhouse_id)
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    # Verificar que el usuario es propietario del invernadero
    if not GreenhouseService.user_owns_greenhouse(db, greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar plantas de este invernadero"
        )

    # Eliminar todas las plantas
    deleted_count = PlantService.bulk_delete_plants_by_greenhouse(
        db=db,
        greenhouse_id=greenhouse_id
    )

    return {
        "message": "Plantas eliminadas exitosamente",
        "deleted_count": deleted_count
    }