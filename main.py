from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints.user_endpoints import router as user_router
from endpoints.chat_endpoints import router as chat_router
from endpoints.greenhouse_endpoints import router as greenhouse_router
from endpoints.plants_health_endpoint import router as plant_health_router
from endpoints.plant_endpoints import router as plant_router
from endpoints.sensor_endpoint import router as sensor_router
from endpoints.sensor_reading_endpoints import router as reading_router
app = FastAPI(
    title="Greenhouse API",
    description="API para gestión de invernaderos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(user_router)
app.include_router(greenhouse_router)
app.include_router(chat_router)
app.include_router(plant_health_router)
app.include_router(plant_router)
app.include_router(sensor_router)
app.include_router(reading_router)



@app.get("/")
def root():
    return {
        "message": "Greenhouse API v1.0",
        "docs": "/docs",
        "status": "running"
    }