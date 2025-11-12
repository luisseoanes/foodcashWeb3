# main.py

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.routers.auth_router import router as auth_router
from infrastructure.database.postgresql_repository import PostgresqlUsuarioRepository, PostgresqlConnectionManager
from infrastructure.security.password_hasher import PasswordHasher
from domain.services.autenticacion_service import AutenticacionService
from presentation.routers.alimento_routher import router as alimento_router
from presentation.routers.estudiante_router import router as estudiante_router
from presentation.routers.compra_routher import router as compra_router
from presentation.routers.alimentoBloqueado_routher import router as alimentoBloqueado_routher
from presentation.routers.precompra_routher import router as precompra_routher
from presentation.routers.recargas_routher import router as recargas_router

# Importar dependencias para alimentos
from dependencies import get_alimento_service

# Cargar variables de entorno
load_dotenv()

# Configurar dependencias
connection_manager = PostgresqlConnectionManager(
    db_name=os.getenv("DB_NAME", "foodcash_db"),
    db_user=os.getenv("DB_USER", "postgres"),
    db_password=os.getenv("DB_PASSWORD", "postgres"),
    db_host=os.getenv("DB_HOST", "localhost"),
    db_port=os.getenv("DB_PORT", "5432")
)
usuario_repository = PostgresqlUsuarioRepository(connection_manager)
password_hasher = PasswordHasher()
autenticacion_service = AutenticacionService(usuario_repository, password_hasher)

# Crear aplicación FastAPI
app = FastAPI(
    title="FoodCash API",
    description="API para gestión de cafeterías escolares",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://food-cash-f7ey.vercel.app",
        "https://www.foodcash.online",
        "https://foodcash.online",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar rutas
app.include_router(auth_router, prefix="", tags=["Autenticación"])
app.include_router(alimento_router, prefix="", tags=["Alimentos"])
app.include_router(estudiante_router, prefix="", tags=["Estudiantes"])
app.include_router(compra_router, prefix="", tags=["Compras"])
app.include_router(alimentoBloqueado_routher, prefix="", tags=["Alimentos Bloqueados"])
app.include_router(precompra_routher, prefix="", tags=["Precompras"])
app.include_router(recargas_router, prefix="", tags=["Recargas"])

@app.get("/", tags=["Root"])
def read_root():
    return {
        "mensaje": "API de FoodCash funcionando correctamente",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online"
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint para verificar el estado de la API"""
    return {
        "status": "healthy",
        "service": "FoodCash API"
    }