from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas.sensor_schema import (
    SensorCreate,
    SensorUpdate,
    SensorResponse,
    SensorDetailResponse
)
from services.sensor_service import SensorService
from services.greenhouse_service import GreenhouseService
from database_config import SessionLocal

router = APIRouter(prefix="/sensors", tags=["sensors"])


def get_db():
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
        sensor: SensorCreate,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Crear un nuevo sensor

    Args:
        sensor: Datos del sensor (name, type, greenhouse_id, active)
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        SensorResponse: Sensor creado

    Raises:
        HTTPException 404: Si el invernadero no existe
        HTTPException 403: Si el usuario no es propietario del invernadero
        HTTPException 400: Si hay error al crear
    """
    # Verificar que el invernadero existe
    greenhouse = GreenhouseService.get_greenhouse_by_id(db, sensor.greenhouse_id)
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    # Verificar que el usuario es propietario del invernadero
    if not GreenhouseService.user_owns_greenhouse(db, sensor.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para agregar sensores a este invernadero"
        )

    # Crear sensor
    db_sensor = SensorService.create_sensor(
        db=db,
        name=sensor.name,
        type=sensor.type,
        greenhouse_id=sensor.greenhouse_id,
        active=sensor.active if sensor.active is not None else True
    )

    if not db_sensor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear el sensor"
        )

    return db_sensor


@router.get("/greenhouse/{greenhouse_id}", response_model=List[SensorResponse])
def get_greenhouse_sensors(
        greenhouse_id: int,
        active_only: bool = Query(False, description="Filtrar solo sensores activos"),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Obtener todos los sensores de un invernadero

    Args:
        greenhouse_id: ID del invernadero
        active_only: Si True, solo retorna sensores activos
        skip: Número de registros a saltar
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos

    Returns:
        List[SensorResponse]: Lista de sensores del invernadero

    Raises:
        HTTPException 404: Si el invernadero no existe

    Example:
        GET /sensors/greenhouse/1?active_only=true&skip=0&limit=10
    """
    # Verificar que el invernadero existe
    greenhouse = GreenhouseService.get_greenhouse_by_id(db, greenhouse_id)
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invernadero no encontrado"
        )

    if active_only:
        sensors = SensorService.get_active_sensors_by_greenhouse(
            db=db,
            greenhouse_id=greenhouse_id,
            skip=skip,
            limit=limit
        )
    else:
        sensors = SensorService.get_sensors_by_greenhouse(
            db=db,
            greenhouse_id=greenhouse_id,
            skip=skip,
            limit=limit
        )

    return sensors

@router.get("/{sensor_id}", response_model=SensorDetailResponse)
def get_sensor(
        sensor_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener un sensor por su ID con sus lecturas

    Args:
        sensor_id: ID del sensor
        db: Sesión de base de datos

    Returns:
        SensorDetailResponse: Sensor con lecturas

    Raises:
        HTTPException 404: Si el sensor no existe
    """
    sensor = SensorService.get_sensor_complete(db, sensor_id)

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    return sensor


@router.patch("/{sensor_id}", response_model=SensorResponse)
def update_sensor(
        sensor_id: int,
        sensor_update: SensorUpdate,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Actualizar un sensor existente

    Args:
        sensor_id: ID del sensor a actualizar
        sensor_update: Datos a actualizar (name, type, active)
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        SensorResponse: Sensor actualizado

    Raises:
        HTTPException 404: Si el sensor no existe
        HTTPException 403: Si el usuario no es propietario del invernadero
        HTTPException 400: Si no hay datos para actualizar
    """
    # Verificar que el sensor existe
    existing_sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not existing_sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    # Verificar que el usuario es propietario del invernadero
    if not GreenhouseService.user_owns_greenhouse(db, existing_sensor.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar este sensor"
        )

    # Convertir Pydantic a dict, excluyendo valores no establecidos
    update_data = sensor_update.model_dump(exclude_unset=True)

    # Si no hay nada que actualizar
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron datos para actualizar"
        )

    # Actualizar sensor
    updated_sensor = SensorService.update_sensor(
        db, sensor_id, update_data
    )

    if not updated_sensor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar el sensor"
        )

    return updated_sensor

@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(
        sensor_id: int,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Eliminar un sensor

    ADVERTENCIA: Esta acción eliminará permanentemente el sensor y todas sus lecturas

    Args:
        sensor_id: ID del sensor a eliminar
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: Si el sensor no existe
        HTTPException 403: Si el usuario no es propietario del invernadero
    """
    # Verificar que el sensor existe
    existing_sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not existing_sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    # Verificar permisos
    if not GreenhouseService.user_owns_greenhouse(db, existing_sensor.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este sensor"
        )

    # Eliminar sensor
    deleted = SensorService.delete_sensor(db, sensor_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al eliminar el sensor"
        )

    @router.get("/", response_model=List[SensorResponse])
    def get_all_sensors(
            skip: int = 0,
            limit: int = 100,
            db: Session = Depends(get_db)
    ):
        """
        Obtener todos los sensores

        Args:
            skip: Número de registros a saltar (paginación)
            limit: Número máximo de registros a retornar (máximo 100)
            db: Sesión de base de datos

        Returns:
            List[SensorResponse]: Lista de sensores

        Example:
            GET /sensors/?skip=0&limit=10
        """
        # Limitar el máximo de sensores por request
        if limit > 100:
            limit = 100

        sensors = SensorService.get_all_sensors(db=db, skip=skip, limit=limit)
        return sensors