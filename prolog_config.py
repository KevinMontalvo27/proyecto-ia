"""
Script para crear las tablas sensor_data y plant_health,
y poblar plant_health con los datos de diagnósticos de plantas

from database_config import engine, SessionLocal
from models import Base
from models.sensor_data import SensorData
from models.plant_health import PlantHealth


def create_tables():
    Crea las tablas en la base de datos
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente")


def populate_plant_health():
    Pobla la tabla plant_health con los diagnósticos
    db = SessionLocal()

    try:
        # Datos de diagnósticos por planta (adaptados para Prolog)
        plant_diagnostics = [
            # Maíz (Corn/Maize)
            {"plant": "maiz", "diagnostic": "cercospora_gray_leaf_spot"},
            {"plant": "maiz", "diagnostic": "common_rust"},
            {"plant": "maiz", "diagnostic": "northern_leaf_blight"},
            {"plant": "maiz", "diagnostic": "healthy"},

            # Uva (Grape)
            {"plant": "uva", "diagnostic": "black_rot"},
            {"plant": "uva", "diagnostic": "esca_black_measles"},
            {"plant": "uva", "diagnostic": "isariopsis_leaf_spot"},
            {"plant": "uva", "diagnostic": "healthy"},

            # Papa (Potato)
            {"plant": "papa", "diagnostic": "early_blight"},
            {"plant": "papa", "diagnostic": "late_blight"},
            {"plant": "papa", "diagnostic": "healthy"},

            # Tomate (Tomato)
            {"plant": "tomate", "diagnostic": "bacterial_spot"},
            {"plant": "tomate", "diagnostic": "early_blight"},
            {"plant": "tomate", "diagnostic": "late_blight"},
            {"plant": "tomate", "diagnostic": "leaf_mold"},
            {"plant": "tomate", "diagnostic": "septoria_leaf_spot"},
            {"plant": "tomate", "diagnostic": "spider_mites_two_spotted"},
            {"plant": "tomate", "diagnostic": "target_spot"},
            {"plant": "tomate", "diagnostic": "yellow_leaf_curl_virus"},
            {"plant": "tomate", "diagnostic": "mosaic_virus"},
            {"plant": "tomate", "diagnostic": "healthy"},
        ]

        print(f"\nInsertando {len(plant_diagnostics)} diagnósticos...")

        for data in plant_diagnostics:
            plant_health = PlantHealth(
                plant=data["plant"],
                diagnostic=data["diagnostic"]
            )
            db.add(plant_health)

        db.commit()
        print("Datos insertados correctamente")

        # Verificar inserción
        count = db.query(PlantHealth).count()
        print(f"\nTotal de registros en plant_health: {count}")

        # Mostrar algunos ejemplos
        print("\nEjemplos de registros insertados:")
        examples = db.query(PlantHealth).limit(5).all()
        for ex in examples:
            print(f"  ID: {ex.id} | Planta: {ex.plant} | Diagnóstico: {ex.diagnostic}")

    except Exception as e:
        db.rollback()
        print(f"Error al insertar datos: {e}")
    finally:
        db.close()


def main():
    print("=" * 60)
    print("CREACIÓN Y POBLACIÓN DE TABLAS")
    print("=" * 60)

    # Crear tablas
    create_tables()

    # Poblar plant_health
    populate_plant_health()

    print("\n" + "=" * 60)
    print("✅ Proceso completado")
    print("=" * 60)


if __name__ == "__main__":
    main()
"""