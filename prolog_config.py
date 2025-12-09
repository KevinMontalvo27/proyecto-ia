from database_config import engine, SessionLocal
from models import Base
from models.sensor_data import SensorData 
from models.plant_health import PlantHealth 

def create_tables():
    # Crea las tablas en la base de datos
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas correctamente")

def populate_plant_health(db):
    print("\n--- Poblando diagnósticos (PlantHealth) ---")
    # Verificar si ya existen datos para no duplicar
    if db.query(PlantHealth).first():
        print("⚠️ La tabla plant_health ya tiene datos. Saltando inserción.")
        return

    try:
        plant_diagnostics = [
            # Maíz
            {"plant": "maiz", "diagnostic": "cercospora_gray_leaf_spot"},
            {"plant": "maiz", "diagnostic": "common_rust"},
            {"plant": "maiz", "diagnostic": "northern_leaf_blight"},
            {"plant": "maiz", "diagnostic": "healthy"},
            # Uva
            {"plant": "uva", "diagnostic": "black_rot"},
            {"plant": "uva", "diagnostic": "esca_black_measles"},
            {"plant": "uva", "diagnostic": "isariopsis_leaf_spot"},
            {"plant": "uva", "diagnostic": "healthy"},
            # Papa
            {"plant": "papa", "diagnostic": "early_blight"},
            {"plant": "papa", "diagnostic": "late_blight"},
            {"plant": "papa", "diagnostic": "healthy"},
            # Tomate
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

        for data in plant_diagnostics:
            plant_health = PlantHealth(
                plant=data["plant"],
                diagnostic=data["diagnostic"]
            )
            db.add(plant_health)

        db.commit()
        print(f"✅ {len(plant_diagnostics)} diagnósticos insertados.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar diagnósticos: {e}")

def populate_sensor_data(db):
    print("\n--- Poblando umbrales (SensorData) ---")
    # Verificar si ya existen datos
    if db.query(SensorData).first():
        print("⚠️ La tabla sensor_data ya tiene datos. Saltando inserción.")
        return

    try:
        # Estos son los Hechos de Umbrales que definimos
        sensor_thresholds = [
            # TOMATE
            {"plant_type": "tomate", "sensor": "temperatura", "min": 18.0, "max": 30.0},
            {"plant_type": "tomate", "sensor": "humedad", "min": 60.0, "max": 80.0},
            {"plant_type": "tomate", "sensor": "luz", "min": 10000.0, "max": 35000.0},
            # MAIZ
            {"plant_type": "maiz", "sensor": "temperatura", "min": 25.0, "max": 32.0},
            {"plant_type": "maiz", "sensor": "humedad", "min": 50.0, "max": 70.0},
            {"plant_type": "maiz", "sensor": "luz", "min": 15000.0, "max": 40000.0},
            # PAPA
            {"plant_type": "papa", "sensor": "temperatura", "min": 18.0, "max": 25.0},
            {"plant_type": "papa", "sensor": "humedad", "min": 65.0, "max": 85.0},
            {"plant_type": "papa", "sensor": "luz", "min": 10000.0, "max": 30000.0},
            # UVA
            {"plant_type": "uva", "sensor": "temperatura", "min": 25.0, "max": 32.0},
            {"plant_type": "uva", "sensor": "humedad", "min": 50.0, "max": 60.0},
            {"plant_type": "uva", "sensor": "luz", "min": 10000.0, "max": 35000.0},
            # GENERAL (Seguridad) Ibañez me dijo que lo quitara. LA LUZ QUE SEGUN SI
            {"plant_type": "general", "sensor": "humo", "min": 0.0, "max": 1000.0},
        ]

        for data in sensor_thresholds:
            sensor_fact = SensorData(
                plant_type=data["plant_type"],
                sensor=data["sensor"],
                umbral_min=data["min"],
                umbral_max=data["max"]
            )
            db.add(sensor_fact)

        db.commit()
        print(f"✅ {len(sensor_thresholds)} umbrales insertados.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar umbrales: {e}")

def main():
    print("=" * 60)
    print("INICIALIZACIÓN DE BASE DE DATOS (TABLAS DE HECHOS)")
    print("=" * 60)

    create_tables()

    db = SessionLocal()
    try:
        populate_plant_health(db)
        populate_sensor_data(db)
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("✅ Proceso completado")
    print("=" * 60)

if __name__ == "__main__":
    main()