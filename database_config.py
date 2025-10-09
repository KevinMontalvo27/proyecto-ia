from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_database():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos inicializada correctamente")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
    except Exception as e:
        print(f"❌ Error al crear la base de datos: {e}")


create_database()