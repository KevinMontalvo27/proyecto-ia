from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from schemas.sensor_reading_schema import (
    SensorReadingCreate,
    SensorReadingResponse,
    SensorReadingBulkCreate, ArduinoResponse
)
from services.sensor_reading_service import SensorReadingService
from services.sensor_service import SensorService
from services.greenhouse_service import GreenhouseService
from database_config import SessionLocal

router = APIRouter(prefix="/sensor-readings", tags=["sensor-readings"])


def get_db():
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ArduinoResponse, status_code=status.HTTP_201_CREATED)
def create_reading(
        reading: SensorReadingCreate,
        db: Session = Depends(get_db)
):
    """
    Crear una nueva lectura de sensor (endpoint para Arduino)

    Este endpoint NO requiere autenticación ya que es usado por dispositivos Arduino.
    Solo valida que el sensor exista en la base de datos.

    Args:
        reading: Datos de la lectura (sensor_id, value)
        db: Sesión de base de datos

    Returns:
        ArduinoResponse: Respuesta con status, mensaje y estado de actuación

    Example Request:
        POST /sensor-readings/
        Body: {
          "sensor_id": 1,
          "value": 25.5
        }

    Example Response:
        {
          "status": "ok",
          "msg": "Datos recibidos correctamente",
          "actuado": true
        }
    """
    try:
        # Verificar que el sensor existe
        sensor = SensorService.get_sensor_by_id(db, reading.sensor_id)
        if not sensor:
            return ArduinoResponse(
                status="error",
                msg="Sensor no encontrado",
                actuado=False
            )

        # Crear lectura
        db_reading = SensorReadingService.create_reading(
            db=db,
            sensor_id=reading.sensor_id,
            value=reading.value
        )

        if not db_reading:
            return ArduinoResponse(
                status="error",
                msg="Error al crear la lectura",
                actuado=False
            )

        actuado = False

        return ArduinoResponse(
            status="ok",
            msg="Datos recibidos correctamente",
            actuado=actuado
        )

    except Exception as e:
        return ArduinoResponse(
            status="error",
            msg=f"Error al procesar la lectura: {str(e)}",
            actuado=False
        )

@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def create_bulk_readings(
        bulk_reading: SensorReadingBulkCreate,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Crear múltiples lecturas de un sensor de una vez

    Args:
        bulk_reading: Objeto con sensor_id y lista de valores
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        dict: Objeto con el número de lecturas creadas

    Raises:
        HTTPException 404: Si el sensor no existe
        HTTPException 403: Si el usuario no es propietario del invernadero
        HTTPException 400: Si hay error al crear

    Example:
        POST /sensor-readings/bulk
        Body: {
          "sensor_id": 1,
          "readings": [25.5, 26.0, 26.5, 27.0]
        }
        Response: {"message": "Lecturas creadas exitosamente", "created_count": 4}
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, bulk_reading.sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    # Verificar permisos
    if not GreenhouseService.user_owns_greenhouse(db, sensor.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para agregar lecturas a este sensor"
        )

    # Crear lecturas
    created_count = SensorReadingService.create_bulk_readings(
        db=db,
        sensor_id=bulk_reading.sensor_id,
        values=bulk_reading.readings
    )

    if created_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear las lecturas"
        )

    return {
        "message": "Lecturas creadas exitosamente",
        "created_count": created_count
    }


@router.get("/sensor/{sensor_id}", response_model=List[SensorReadingResponse])
def get_sensor_readings(
        sensor_id: int,
        skip: int = 0,
        limit: int = 1000,
        db: Session = Depends(get_db)
):
    """
    Obtener todas las lecturas de un sensor

    Args:
        sensor_id: ID del sensor
        skip: Número de registros a saltar
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos

    Returns:
        List[SensorReadingResponse]: Lista de lecturas ordenadas por fecha (más recientes primero)

    Raises:
        HTTPException 404: Si el sensor no existe

    Example:
        GET /sensor-readings/sensor/1?skip=0&limit=100
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    readings = SensorReadingService.get_readings_by_sensor(
        db=db,
        sensor_id=sensor_id,
        skip=skip,
        limit=limit
    )

    return readings


@router.get("/sensor/{sensor_id}/latest", response_model=SensorReadingResponse)
def get_latest_reading(
        sensor_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener la lectura más reciente de un sensor

    Args:
        sensor_id: ID del sensor
        db: Sesión de base de datos

    Returns:
        SensorReadingResponse: Lectura más reciente

    Raises:
        HTTPException 404: Si el sensor no existe o no tiene lecturas

    Example:
        GET /sensor-readings/sensor/1/latest
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    reading = SensorReadingService.get_latest_reading(db, sensor_id)

    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay lecturas disponibles para este sensor"
        )

    return reading


@router.get("/sensor/{sensor_id}/range", response_model=List[SensorReadingResponse])
def get_readings_in_range(
        sensor_id: int,
        start_date: datetime = Query(..., description="Fecha de inicio (ISO 8601)"),
        end_date: datetime = Query(..., description="Fecha de fin (ISO 8601)"),
        skip: int = 0,
        limit: int = 10000,
        db: Session = Depends(get_db)
):
    """
    Obtener lecturas de un sensor en un rango de fechas

    Args:
        sensor_id: ID del sensor
        start_date: Fecha de inicio (formato ISO 8601)
        end_date: Fecha de fin (formato ISO 8601)
        skip: Número de registros a saltar
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos

    Returns:
        List[SensorReadingResponse]: Lista de lecturas en el rango

    Raises:
        HTTPException 404: Si el sensor no existe

    Example:
        GET /sensor-readings/sensor/1/range?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    readings = SensorReadingService.get_readings_in_range(
        db=db,
        sensor_id=sensor_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

    return readings


@router.get("/sensor/{sensor_id}/last-hours", response_model=List[SensorReadingResponse])
def get_readings_last_hours(
        sensor_id: int,
        hours: int = Query(24, ge=1, le=168, description="Número de horas (1-168)"),
        db: Session = Depends(get_db)
):
    """
    Obtener lecturas de las últimas N horas

    Args:
        sensor_id: ID del sensor
        hours: Número de horas hacia atrás (1-168, por defecto 24)
        db: Sesión de base de datos

    Returns:
        List[SensorReadingResponse]: Lista de lecturas

    Raises:
        HTTPException 404: Si el sensor no existe

    Example:
        GET /sensor-readings/sensor/1/last-hours?hours=12
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    readings = SensorReadingService.get_readings_last_hours(
        db=db,
        sensor_id=sensor_id,
        hours=hours
    )

    return readings


@router.get("/sensor/{sensor_id}/last-days", response_model=List[SensorReadingResponse])
def get_readings_last_days(
        sensor_id: int,
        days: int = Query(7, ge=1, le=365, description="Número de días (1-365)"),
        db: Session = Depends(get_db)
):
    """
    Obtener lecturas de los últimos N días

    Args:
        sensor_id: ID del sensor
        days: Número de días hacia atrás (1-365, por defecto 7)
        db: Sesión de base de datos

    Returns:
        List[SensorReadingResponse]: Lista de lecturas

    Raises:
        HTTPException 404: Si el sensor no existe

    Example:
        GET /sensor-readings/sensor/1/last-days?days=30
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    readings = SensorReadingService.get_readings_last_days(
        db=db,
        sensor_id=sensor_id,
        days=days
    )

    return readings


@router.get("/sensor/{sensor_id}/statistics")
def get_sensor_statistics(
        sensor_id: int,
        start_date: Optional[datetime] = Query(None, description="Fecha de inicio (opcional)"),
        end_date: Optional[datetime] = Query(None, description="Fecha de fin (opcional)"),
        db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de las lecturas de un sensor

    Args:
        sensor_id: ID del sensor
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
        db: Sesión de base de datos

    Returns:
        dict: Estadísticas (average, minimum, maximum, count)

    Raises:
        HTTPException 404: Si el sensor no existe

    Example:
        GET /sensor-readings/sensor/1/statistics
        Response: {
          "sensor_id": 1,
          "average": 25.5,
          "minimum": 20.0,
          "maximum": 30.0,
          "count": 1000
        }
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    statistics = SensorReadingService.get_statistics(
        db=db,
        sensor_id=sensor_id,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "sensor_id": sensor_id,
        **statistics
    }


@router.get("/sensor/{sensor_id}/count")
def count_sensor_readings(
        sensor_id: int,
        start_date: Optional[datetime] = Query(None, description="Fecha de inicio (opcional)"),
        end_date: Optional[datetime] = Query(None, description="Fecha de fin (opcional)"),
        db: Session = Depends(get_db)
):
    """
    Contar el número de lecturas de un sensor

    Args:
        sensor_id: ID del sensor
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
        db: Sesión de base de datos

    Returns:
        dict: Objeto con el conteo de lecturas

    Raises:
        HTTPException 404: Si el sensor no existe

    Example:
        GET /sensor-readings/sensor/1/count
        Response: {"sensor_id": 1, "count": 5000}
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    count = SensorReadingService.count_readings(
        db=db,
        sensor_id=sensor_id,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "sensor_id": sensor_id,
        "count": count
    }


@router.get("/sensor/{sensor_id}/hourly-averages")
def get_hourly_averages(
        sensor_id: int,
        days: int = Query(7, ge=1, le=30, description="Número de días (1-30)"),
        db: Session = Depends(get_db)
):
    """
    Obtener promedios por hora de los últimos N días

    Args:
        sensor_id: ID del sensor
        days: Número de días hacia atrás (1-30, por defecto 7)
        db: Sesión de base de datos

    Returns:
        dict: Lista de promedios por hora

    Raises:
        HTTPException 404: Si el sensor no existe

    Example:
        GET /sensor-readings/sensor/1/hourly-averages?days=7
        Response: {
          "sensor_id": 1,
          "days": 7,
          "data": [
            {"timestamp": "2024-01-01T00:00:00", "average": 25.5},
            {"timestamp": "2024-01-01T01:00:00", "average": 25.3}
          ]
        }
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    averages = SensorReadingService.get_hourly_averages(
        db=db,
        sensor_id=sensor_id,
        days=days
    )

    return {
        "sensor_id": sensor_id,
        "days": days,
        "data": averages
    }


@router.get("/sensor/{sensor_id}/daily-averages")
def get_daily_averages(
        sensor_id: int,
        days: int = Query(30, ge=1, le=365, description="Número de días (1-365)"),
        db: Session = Depends(get_db)
):
    """
    Obtener promedios diarios de los últimos N días

    Args:
        sensor_id: ID del sensor
        days: Número de días hacia atrás (1-365, por defecto 30)
        db: Sesión de base de datos

    Returns:
        dict: Lista de promedios, mínimos y máximos diarios

    Raises:
        HTTPException 404: Si el sensor no existe

    Example:
        GET /sensor-readings/sensor/1/daily-averages?days=30
        Response: {
          "sensor_id": 1,
          "days": 30,
          "data": [
            {
              "date": "2024-01-01",
              "average": 25.5,
              "minimum": 20.0,
              "maximum": 30.0
            }
          ]
        }
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    averages = SensorReadingService.get_daily_averages(
        db=db,
        sensor_id=sensor_id,
        days=days
    )

    return {
        "sensor_id": sensor_id,
        "days": days,
        "data": averages
    }


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reading(
        reading_id: int,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Eliminar una lectura específica

    Args:
        reading_id: ID de la lectura a eliminar
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: Si la lectura no existe
        HTTPException 403: Si el usuario no es propietario del invernadero
    """
    # Verificar que la lectura existe
    reading = SensorReadingService.get_reading_by_id(db, reading_id)
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lectura no encontrada"
        )

    # Obtener el sensor para verificar permisos
    sensor = SensorService.get_sensor_by_id(db, reading.sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    # Verificar permisos
    if not GreenhouseService.user_owns_greenhouse(db, sensor.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta lectura"
        )

    # Eliminar lectura
    deleted = SensorReadingService.delete_reading(db, reading_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al eliminar la lectura"
        )


@router.delete("/sensor/{sensor_id}/all", status_code=status.HTTP_200_OK)
def delete_all_sensor_readings(
        sensor_id: int,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Eliminar todas las lecturas de un sensor

    ADVERTENCIA: Esta acción eliminará permanentemente todas las lecturas del sensor

    Args:
        sensor_id: ID del sensor
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        dict: Objeto con el número de lecturas eliminadas

    Raises:
        HTTPException 404: Si el sensor no existe
        HTTPException 403: Si el usuario no es propietario del invernadero

    Example:
        DELETE /sensor-readings/sensor/1/all
        Response: {"message": "Lecturas eliminadas exitosamente", "deleted_count": 1000}
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    # Verificar permisos
    if not GreenhouseService.user_owns_greenhouse(db, sensor.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar lecturas de este sensor"
        )

    # Eliminar todas las lecturas
    deleted_count = SensorReadingService.delete_readings_by_sensor(
        db=db,
        sensor_id=sensor_id
    )

    return {
        "message": "Lecturas eliminadas exitosamente",
        "deleted_count": deleted_count
    }


@router.delete("/sensor/{sensor_id}/older-than/{days}", status_code=status.HTTP_200_OK)
def delete_old_readings(
        sensor_id: int,
        days: int,
        user_id: int,  # TODO: En producción esto vendrá del token JWT
        db: Session = Depends(get_db)
):
    """
    Eliminar lecturas más antiguas que N días

    Args:
        sensor_id: ID del sensor
        days: Número de días (se eliminan lecturas más antiguas)
        user_id: ID del usuario que hace la petición
        db: Sesión de base de datos

    Returns:
        dict: Objeto con el número de lecturas eliminadas

    Raises:
        HTTPException 404: Si el sensor no existe
        HTTPException 403: Si el usuario no es propietario del invernadero

    Example:
        DELETE /sensor-readings/sensor/1/older-than/90
        Response: {"message": "Lecturas antiguas eliminadas", "deleted_count": 500, "days": 90}
    """
    # Verificar que el sensor existe
    sensor = SensorService.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor no encontrado"
        )

    # Verificar permisos
    if not GreenhouseService.user_owns_greenhouse(db, sensor.greenhouse_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar lecturas de este sensor"
        )

    # Eliminar lecturas antiguas
    deleted_count = SensorReadingService.delete_readings_older_than(
        db=db,
        sensor_id=sensor_id,
        days=days
    )

    return {
        "message": "Lecturas antiguas eliminadas",
        "deleted_count": deleted_count,
        "days": days
    }