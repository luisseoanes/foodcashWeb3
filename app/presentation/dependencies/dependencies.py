# presentation/dependencies/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from domain.services.recarga_service import RecargaService
from infrastructure.database.postgresql_recarga_repository import PostgresqlRecargaRepository
from infrastructure.database.postgresql_estudiante_repository import PostgresqlEstudianteRepository  # ← NUEVO
from infrastructure.database.postgresql_repository import get_connection_manager
from infrastructure.database.postgresql_repository import PostgresqlUsuarioRepository
from infrastructure.security.jwt_handler import JWTHandler

security = HTTPBearer()

def get_recarga_repository():
    """
    Función de dependencia que crea el repositorio de recargas
    """
    connection_manager = get_connection_manager()
    return PostgresqlRecargaRepository(connection_manager)

def get_recarga_service():
    """
    Función de dependencia que crea el servicio de recargas
    Inyecta los repositorios de recargas, usuarios y estudiantes
    """
    connection_manager = get_connection_manager()
    
    # Crear repositorios
    recarga_repository = PostgresqlRecargaRepository(connection_manager)
    usuario_repository = PostgresqlUsuarioRepository(connection_manager)
    estudiante_repository = PostgresqlEstudianteRepository(connection_manager)  # ← NUEVO
    
    # Crear y retornar el servicio
    return RecargaService(
        recarga_repository=recarga_repository,
        usuario_repository=usuario_repository,
        estudiante_repository=estudiante_repository  # ← NUEVO
    )

def get_current_user_id(token: str = Depends(security)) -> str:
    """
    Extrae el user_id del JWT token
    """
    try:
        jwt_handler = JWTHandler()
        payload = jwt_handler.decode_token(token.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )