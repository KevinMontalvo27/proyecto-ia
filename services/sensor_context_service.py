from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from services.sensor_service import SensorService
from services.sensor_reading_service import SensorReadingService


class SensorContextService:
    """Servicio para generar contexto de sensores para Gemini"""

    @staticmethod
    def get_sensor_context_for_gemini(
            db: Session,
            greenhouse_id: int,
            days: int = 7,
            max_readings_per_sensor: int = 10
    ) -> str:
        """
        Genera un resumen OPTIMIZADO en texto de los datos de sensores para Gemini.
        Solo incluye las últimas N lecturas de cada sensor para reducir el uso de tokens.

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero
            days: Días de historial para estadísticas generales (por defecto 7)
            max_readings_per_sensor: Número máximo de lecturas recientes a incluir por sensor (por defecto 10)

        Returns:
            str: Texto formateado con el contexto de sensores (OPTIMIZADO)
        """
        # Obtener todos los sensores del invernadero
        sensors = SensorService.get_sensors_by_greenhouse(
            db=db,
            greenhouse_id=greenhouse_id
        )

        if not sensors:
            return "No hay datos de sensores disponibles para este invernadero."

        context_parts = []
        context_parts.append(
            f"=== DATOS DE SENSORES DEL INVERNADERO (Últimas {max_readings_per_sensor} lecturas) ===\n")

        for sensor in sensors:
            # Obtener estadísticas generales (promedio de los últimos días)
            stats = SensorReadingService.get_statistics(
                db=db,
                sensor_id=sensor.id,
                start_date=datetime.utcnow() - timedelta(days=days)
            )

            if stats['count'] > 0:
                # Formato compacto: solo promedio, mín y máx
                sensor_summary = SensorContextService._format_sensor_summary_compact(
                    sensor=sensor,
                    stats=stats
                )
                context_parts.append(sensor_summary)

                # Agregar solo las últimas N lecturas
                recent_readings = SensorReadingService.get_readings_by_sensor(
                    db=db,
                    sensor_id=sensor.id,
                    limit=max_readings_per_sensor
                )

                if recent_readings:
                    readings_text = SensorContextService._format_recent_readings(
                        sensor=sensor,
                        readings=recent_readings
                    )
                    context_parts.append(readings_text)
            else:
                context_parts.append(f"\n• {sensor.name} ({sensor.type}): Sin datos disponibles")

        return "\n".join(context_parts)

    @staticmethod
    def _format_sensor_summary_compact(sensor, stats: Dict) -> str:
        """
        Formatea las estadísticas de un sensor en formato COMPACTO

        Args:
            sensor: Objeto Sensor de SQLAlchemy
            stats: Diccionario con estadísticas (average, minimum, maximum, count)

        Returns:
            str: Resumen formateado compacto
        """
        sensor_type_names = {
            'temperatura': '°C',
            'humedad': '%',
            'luz': 'lux',
            'humo': 'ppm'
        }

        unit = sensor_type_names.get(sensor.type, '')

        # Formato compacto en una sola línea
        summary = f"\n• {sensor.name} ({sensor.type.upper()}): "
        summary += f"Promedio {stats['average']:.1f}{unit}, "
        summary += f"Rango {stats['minimum']:.1f}-{stats['maximum']:.1f}{unit}"

        return summary

    @staticmethod
    def _format_recent_readings(sensor, readings: List) -> str:
        """
        Formatea las lecturas recientes en formato compacto

        Args:
            sensor: Objeto Sensor
            readings: Lista de lecturas recientes

        Returns:
            str: Lecturas formateadas
        """
        sensor_type_names = {
            'temperatura': '°C',
            'humedad': '%',
            'luz': 'lux',
            'humo': 'ppm'
        }

        unit = sensor_type_names.get(sensor.type, '')

        # Formato: valor (tiempo_relativo)
        readings_list = []
        for reading in readings[:10]:  # Asegurar máximo 10
            time_ago = SensorContextService._format_time_ago(reading.recorded_at)
            readings_list.append(f"{reading.value:.1f}{unit} ({time_ago})")

        return f"  Últimas lecturas: {', '.join(readings_list)}"

    @staticmethod
    def _format_sensor_summary(
            sensor,
            stats: Dict,
            days: int
    ) -> str:
        """
        Formatea las estadísticas de un sensor en texto legible

        Args:
            sensor: Objeto Sensor de SQLAlchemy
            stats: Diccionario con estadísticas (average, minimum, maximum, count)
            days: Número de días del período

        Returns:
            str: Resumen formateado
        """
        sensor_type_names = {
            'temperatura': '°C',
            'humedad': '%',
            'luz': 'lux',
            'humo': 'ppm'
        }

        unit = sensor_type_names.get(sensor.type, '')

        summary = f"\n• {sensor.name} ({sensor.type.upper()}):\n"
        summary += f"  - Promedio: {stats['average']:.2f} {unit}\n"
        summary += f"  - Mínimo: {stats['minimum']:.2f} {unit}\n"
        summary += f"  - Máximo: {stats['maximum']:.2f} {unit}\n"
        summary += f"  - Lecturas: {stats['count']} en {days} días"

        return summary

    @staticmethod
    def _format_time_ago(timestamp: datetime) -> str:
        """
        Convierte un timestamp en texto legible de tiempo transcurrido

        Args:
            timestamp: Fecha y hora de la lectura

        Returns:
            str: Tiempo transcurrido en formato legible
        """
        now = datetime.utcnow()
        delta = now - timestamp

        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())} segundos"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)} minutos"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)} horas"
        else:
            return f"{int(delta.total_seconds() / 86400)} días"

    @staticmethod
    def get_sensor_alerts(
            db: Session,
            greenhouse_id: int,
            days: int = 7
    ) -> str:
        """
        Genera un resumen de posibles alertas basadas en umbrales

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero
            days: Días de historial a analizar

        Returns:
            str: Texto con alertas detectadas
        """
        sensors = SensorService.get_sensors_by_greenhouse(
            db=db,
            greenhouse_id=greenhouse_id
        )

        if not sensors:
            return ""

        alerts = []

        # Umbrales de ejemplo (deberían venir de la BD en un sistema real)
        thresholds = {
            'temperatura': {'min': 18.0, 'max': 32.0},
            'humedad': {'min': 50.0, 'max': 85.0},
            'luz': {'min': 10000.0, 'max': 40000.0},
            'humo': {'min': 0.0, 'max': 50.0}
        }

        for sensor in sensors:
            stats = SensorReadingService.get_statistics(
                db=db,
                sensor_id=sensor.id,
                start_date=datetime.utcnow() - timedelta(days=days)
            )

            if stats['count'] == 0:
                continue

            threshold = thresholds.get(sensor.type)
            if not threshold:
                continue

            # Verificar si el promedio está fuera de rango
            if stats['average'] < threshold['min']:
                alerts.append(
                    f"⚠️ {sensor.name}: Promedio BAJO ({stats['average']:.2f}, "
                    f"mínimo recomendado: {threshold['min']})"
                )
            elif stats['average'] > threshold['max']:
                alerts.append(
                    f"⚠️ {sensor.name}: Promedio ALTO ({stats['average']:.2f}, "
                    f"máximo recomendado: {threshold['max']})"
                )

            # Verificar valores extremos
            if stats['minimum'] < threshold['min']:
                alerts.append(
                    f"⚠️ {sensor.name}: Se detectó valor MUY BAJO ({stats['minimum']:.2f})"
                )

            if stats['maximum'] > threshold['max']:
                alerts.append(
                    f"⚠️ {sensor.name}: Se detectó valor MUY ALTO ({stats['maximum']:.2f})"
                )

        if not alerts:
            return "\n=== CONDICIONES AMBIENTALES ===\nTodas las condiciones están dentro de rangos normales."

        return "\n=== ALERTAS DETECTADAS ===\n" + "\n".join(alerts)

    @staticmethod
    def get_complete_context(
            db: Session,
            greenhouse_id: int,
            days: int = 7,
            max_readings_per_sensor: int = 10
    ) -> str:
        """
        Genera el contexto completo OPTIMIZADO incluyendo datos y alertas

        Args:
            db: Sesión de base de datos
            greenhouse_id: ID del invernadero
            days: Días de historial para estadísticas generales
            max_readings_per_sensor: Número máximo de lecturas a incluir por sensor

        Returns:
            str: Contexto completo formateado (OPTIMIZADO para menos tokens)
        """
        sensor_data = SensorContextService.get_sensor_context_for_gemini(
            db=db,
            greenhouse_id=greenhouse_id,
            days=days,
            max_readings_per_sensor=max_readings_per_sensor
        )

        alerts = SensorContextService.get_sensor_alerts(
            db=db,
            greenhouse_id=greenhouse_id,
            days=days
        )

        return f"{sensor_data}\n\n{alerts}"