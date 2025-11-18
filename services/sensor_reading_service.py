from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from models.sensor_reading_model import SensorReading


class SensorReadingService:
    @staticmethod
    def create_reading(
            db: Session,
            sensor_id: int,
            value: float
    ) -> Optional[SensorReading]:
        """
        Crea una nueva lectura de sensor

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            value: Valor de la lectura

        Returns:
            SensorReading: Lectura creada o None si hay error
        """
        try:
            db_reading = SensorReading(
                sensor_id=sensor_id,
                value=value
            )

            db.add(db_reading)
            db.commit()
            db.refresh(db_reading)

            return db_reading

        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def create_bulk_readings(
            db: Session,
            sensor_id: int,
            values: List[float]
    ) -> int:
        """
        Crea múltiples lecturas de un sensor de una vez

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            values: Lista de valores a insertar

        Returns:
            int: Número de lecturas creadas
        """
        try:
            readings = [
                SensorReading(sensor_id=sensor_id, value=value)
                for value in values
            ]

            db.bulk_save_objects(readings)
            db.commit()

            return len(readings)

        except IntegrityError:
            db.rollback()
            return 0

    @staticmethod
    def get_reading_by_id(db: Session, reading_id: int) -> Optional[SensorReading]:
        """
        Obtiene una lectura por su ID

        Args:
            db: Sesión de base de datos
            reading_id: ID de la lectura

        Returns:
            SensorReading: Lectura encontrada o None
        """
        return db.query(SensorReading).filter(SensorReading.id == reading_id).first()

    @staticmethod
    def get_readings_by_sensor(
            db: Session,
            sensor_id: int,
            skip: int = 0,
            limit: int = 1000
    ) -> List[SensorReading]:
        """
        Obtiene todas las lecturas de un sensor

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar

        Returns:
            List[SensorReading]: Lista de lecturas ordenadas por fecha (más recientes primero)
        """
        return db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id
        ).order_by(
            SensorReading.recorded_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_latest_reading(db: Session, sensor_id: int) -> Optional[SensorReading]:
        """
        Obtiene la lectura más reciente de un sensor

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor

        Returns:
            SensorReading: Lectura más reciente o None
        """
        return db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id
        ).order_by(
            SensorReading.recorded_at.desc()
        ).first()

    @staticmethod
    def get_readings_in_range(
            db: Session,
            sensor_id: int,
            start_date: datetime,
            end_date: datetime,
            skip: int = 0,
            limit: int = 10000
    ) -> List[SensorReading]:
        """
        Obtiene lecturas de un sensor en un rango de fechas

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            start_date: Fecha de inicio
            end_date: Fecha de fin
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar

        Returns:
            List[SensorReading]: Lista de lecturas en el rango especificado
        """
        return db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.recorded_at >= start_date,
            SensorReading.recorded_at <= end_date
        ).order_by(
            SensorReading.recorded_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_readings_last_hours(
            db: Session,
            sensor_id: int,
            hours: int = 24
    ) -> List[SensorReading]:
        """
        Obtiene las lecturas de las últimas N horas

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            hours: Número de horas hacia atrás (por defecto 24)

        Returns:
            List[SensorReading]: Lista de lecturas
        """
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        return db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.recorded_at >= time_threshold
        ).order_by(
            SensorReading.recorded_at.desc()
        ).all()

    @staticmethod
    def get_readings_last_days(
            db: Session,
            sensor_id: int,
            days: int = 7
    ) -> List[SensorReading]:
        """
        Obtiene las lecturas de los últimos N días

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            days: Número de días hacia atrás (por defecto 7)

        Returns:
            List[SensorReading]: Lista de lecturas
        """
        time_threshold = datetime.utcnow() - timedelta(days=days)

        return db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.recorded_at >= time_threshold
        ).order_by(
            SensorReading.recorded_at.desc()
        ).all()

    @staticmethod
    def get_average_value(
            db: Session,
            sensor_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Calcula el promedio de las lecturas de un sensor

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)

        Returns:
            float: Promedio de lecturas o None si no hay datos
        """
        query = db.query(func.avg(SensorReading.value)).filter(
            SensorReading.sensor_id == sensor_id
        )

        if start_date:
            query = query.filter(SensorReading.recorded_at >= start_date)
        if end_date:
            query = query.filter(SensorReading.recorded_at <= end_date)

        result = query.scalar()
        return float(result) if result is not None else None

    @staticmethod
    def get_min_value(
            db: Session,
            sensor_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Obtiene el valor mínimo de las lecturas

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)

        Returns:
            float: Valor mínimo o None si no hay datos
        """
        query = db.query(func.min(SensorReading.value)).filter(
            SensorReading.sensor_id == sensor_id
        )

        if start_date:
            query = query.filter(SensorReading.recorded_at >= start_date)
        if end_date:
            query = query.filter(SensorReading.recorded_at <= end_date)

        result = query.scalar()
        return float(result) if result is not None else None

    @staticmethod
    def get_max_value(
            db: Session,
            sensor_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Obtiene el valor máximo de las lecturas

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)

        Returns:
            float: Valor máximo o None si no hay datos
        """
        query = db.query(func.max(SensorReading.value)).filter(
            SensorReading.sensor_id == sensor_id
        )

        if start_date:
            query = query.filter(SensorReading.recorded_at >= start_date)
        if end_date:
            query = query.filter(SensorReading.recorded_at <= end_date)

        result = query.scalar()
        return float(result) if result is not None else None

    @staticmethod
    def get_statistics(
            db: Session,
            sensor_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas de las lecturas de un sensor

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)

        Returns:
            Dict: Diccionario con estadísticas (avg, min, max, count)
        """
        query = db.query(
            func.avg(SensorReading.value).label('average'),
            func.min(SensorReading.value).label('minimum'),
            func.max(SensorReading.value).label('maximum'),
            func.count(SensorReading.id).label('count')
        ).filter(
            SensorReading.sensor_id == sensor_id
        )

        if start_date:
            query = query.filter(SensorReading.recorded_at >= start_date)
        if end_date:
            query = query.filter(SensorReading.recorded_at <= end_date)

        result = query.first()

        return {
            'average': float(result.average) if result.average is not None else None,
            'minimum': float(result.minimum) if result.minimum is not None else None,
            'maximum': float(result.maximum) if result.maximum is not None else None,
            'count': result.count
        }

    @staticmethod
    def count_readings(
            db: Session,
            sensor_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> int:
        """
        Cuenta el número de lecturas de un sensor

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)

        Returns:
            int: Número de lecturas
        """
        query = db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id
        )

        if start_date:
            query = query.filter(SensorReading.recorded_at >= start_date)
        if end_date:
            query = query.filter(SensorReading.recorded_at <= end_date)

        return query.count()

    @staticmethod
    def delete_reading(db: Session, reading_id: int) -> bool:
        """
        Elimina una lectura específica

        Args:
            db: Sesión de base de datos
            reading_id: ID de la lectura a eliminar

        Returns:
            bool: True si se eliminó, False si no existe
        """
        reading = SensorReadingService.get_reading_by_id(db, reading_id)

        if not reading:
            return False

        db.delete(reading)
        db.commit()
        return True

    @staticmethod
    def delete_readings_by_sensor(
            db: Session,
            sensor_id: int
    ) -> int:
        """
        Elimina todas las lecturas de un sensor

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor

        Returns:
            int: Número de lecturas eliminadas
        """
        try:
            count = db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor_id
            ).delete()
            db.commit()
            return count
        except Exception:
            db.rollback()
            return 0

    @staticmethod
    def delete_readings_older_than(
            db: Session,
            sensor_id: int,
            days: int
    ) -> int:
        """
        Elimina lecturas más antiguas que N días

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            days: Número de días (se eliminan lecturas más antiguas)

        Returns:
            int: Número de lecturas eliminadas
        """
        try:
            threshold_date = datetime.utcnow() - timedelta(days=days)

            count = db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.recorded_at < threshold_date
            ).delete()

            db.commit()
            return count
        except Exception:
            db.rollback()
            return 0

    @staticmethod
    def delete_readings_in_range(
            db: Session,
            sensor_id: int,
            start_date: datetime,
            end_date: datetime
    ) -> int:
        """
        Elimina lecturas en un rango de fechas específico

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            start_date: Fecha de inicio
            end_date: Fecha de fin

        Returns:
            int: Número de lecturas eliminadas
        """
        try:
            count = db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.recorded_at >= start_date,
                SensorReading.recorded_at <= end_date
            ).delete()

            db.commit()
            return count
        except Exception:
            db.rollback()
            return 0

    @staticmethod
    def get_hourly_averages(
            db: Session,
            sensor_id: int,
            days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Obtiene promedios por hora de los últimos N días

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            days: Número de días hacia atrás

        Returns:
            List[Dict]: Lista de promedios por hora
        """
        time_threshold = datetime.utcnow() - timedelta(days=days)

        # Agrupar por hora
        results = db.query(
            func.date_trunc('hour', SensorReading.recorded_at).label('hour'),
            func.avg(SensorReading.value).label('average')
        ).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.recorded_at >= time_threshold
        ).group_by(
            'hour'
        ).order_by(
            'hour'
        ).all()

        return [
            {
                'timestamp': result.hour.isoformat(),
                'average': float(result.average)
            }
            for result in results
        ]

    @staticmethod
    def get_daily_averages(
            db: Session,
            sensor_id: int,
            days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Obtiene promedios diarios de los últimos N días

        Args:
            db: Sesión de base de datos
            sensor_id: ID del sensor
            days: Número de días hacia atrás

        Returns:
            List[Dict]: Lista de promedios diarios
        """
        time_threshold = datetime.utcnow() - timedelta(days=days)

        # Agrupar por día
        results = db.query(
            func.date_trunc('day', SensorReading.recorded_at).label('day'),
            func.avg(SensorReading.value).label('average'),
            func.min(SensorReading.value).label('minimum'),
            func.max(SensorReading.value).label('maximum')
        ).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.recorded_at >= time_threshold
        ).group_by(
            'day'
        ).order_by(
            'day'
        ).all()

        return [
            {
                'date': result.day.date().isoformat(),
                'average': float(result.average),
                'minimum': float(result.minimum),
                'maximum': float(result.maximum)
            }
            for result in results
        ]