from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, Optional
from models.plant_analysis_model import PlantAnalysis


class PlantAnalysisService:
    """
    Servicio para manejar operaciones de análisis de plantas en la base de datos.
    """

    @staticmethod
    def create_analysis(
            db: Session,
            plant_id: int,
            diagnosis: str,
            confidence: float,
            analysis_type: str = 'health'
    ) -> PlantAnalysis:
        """
        Crea un nuevo registro de análisis en la base de datos.

        Args:
            db: Sesión de SQLAlchemy
            plant_id: ID de la planta (1=tomate, 2=maiz, 3=uva, 4=papa)
            diagnosis: Diagnóstico obtenido (ej: "late_blight", "healthy")
            confidence: Nivel de confianza del modelo (0-1)
            analysis_type: Tipo de análisis ('health' o 'pest')

        Returns:
            PlantAnalysis: Objeto del análisis creado

        Raises:
            Exception: Si hay error al guardar en la BD
        """
        try:
            new_analysis = PlantAnalysis(
                plant_id=plant_id,
                analysis_type=analysis_type,
                result=diagnosis,
                confidence=confidence,
                analyzed_at=datetime.utcnow()
            )

            db.add(new_analysis)
            db.commit()
            db.refresh(new_analysis)

            print(f"Análisis guardado: Plant ID {plant_id} - {diagnosis} ({confidence:.2%})")
            return new_analysis

        except Exception as e:
            db.rollback()
            print(f"✗ Error al guardar análisis: {str(e)}")
            raise Exception(f"Error al guardar en BD: {str(e)}")

    @staticmethod
    def get_latest_analysis(
            db: Session,
            plant_id: int,
            analysis_type: str = 'health'
    ) -> Optional[PlantAnalysis]:
        """
        Obtiene el análisis más reciente de una planta.

        Args:
            db: Sesión de SQLAlchemy
            plant_id: ID de la planta
            analysis_type: Tipo de análisis a buscar

        Returns:
            PlantAnalysis o None si no hay análisis
        """
        return db.query(PlantAnalysis).filter(
            PlantAnalysis.plant_id == plant_id,
            PlantAnalysis.analysis_type == analysis_type
        ).order_by(PlantAnalysis.analyzed_at.desc()).first()

    @staticmethod
    def get_plant_history(
            db: Session,
            plant_id: int,
            limit: int = 10
    ) -> list[PlantAnalysis]:
        """
        Obtiene el historial de análisis de una planta.

        Args:
            db: Sesión de SQLAlchemy
            plant_id: ID de la planta
            limit: Número máximo de resultados

        Returns:
            Lista de análisis ordenados por fecha (más reciente primero)
        """
        return db.query(PlantAnalysis).filter(
            PlantAnalysis.plant_id == plant_id
        ).order_by(PlantAnalysis.analyzed_at.desc()).limit(limit).all()

    @staticmethod
    def get_unhealthy_plants(
            db: Session,
            confidence_threshold: float = 0.7
    ) -> list[PlantAnalysis]:
        """
        Obtiene todas las plantas con problemas de salud con alta confianza.

        Args:
            db: Sesión de SQLAlchemy
            confidence_threshold: Umbral mínimo de confianza

        Returns:
            Lista de análisis de plantas no saludables
        """
        from sqlalchemy import and_

        return db.query(PlantAnalysis).filter(
            and_(
                PlantAnalysis.analysis_type == 'health',
                PlantAnalysis.result != 'healthy',
                PlantAnalysis.confidence >= confidence_threshold
            )
        ).order_by(PlantAnalysis.analyzed_at.desc()).all()

    @staticmethod
    def get_analysis_by_id(
            db: Session,
            analysis_id: int
    ) -> Optional[PlantAnalysis]:
        """
        Obtiene un análisis específico por su ID.

        Args:
            db: Sesión de SQLAlchemy
            analysis_id: ID del análisis

        Returns:
            PlantAnalysis o None si no existe
        """
        return db.query(PlantAnalysis).filter(
            PlantAnalysis.id == analysis_id
        ).first()

    @staticmethod
    def count_analyses_by_plant(
            db: Session,
            plant_id: int
    ) -> int:
        """
        Cuenta el número total de análisis de una planta.

        Args:
            db: Sesión de SQLAlchemy
            plant_id: ID de la planta

        Returns:
            Número de análisis realizados
        """
        return db.query(PlantAnalysis).filter(
            PlantAnalysis.plant_id == plant_id
        ).count()

    @staticmethod
    def delete_analysis(
            db: Session,
            analysis_id: int
    ) -> bool:
        """
        Elimina un análisis de la base de datos.

        Args:
            db: Sesión de SQLAlchemy
            analysis_id: ID del análisis a eliminar

        Returns:
            True si se eliminó correctamente, False si no existe
        """
        try:
            analysis = PlantAnalysisService.get_analysis_by_id(db, analysis_id)
            if analysis:
                db.delete(analysis)
                db.commit()
                print(f"Análisis {analysis_id} eliminado")
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"✗ Error al eliminar análisis: {str(e)}")
            raise Exception(f"Error al eliminar análisis: {str(e)}")