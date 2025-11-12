# dependencies.py
import os
from dotenv import load_dotenv
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager, PostgresqlUsuarioRepository
from infrastructure.database.postgresql_alimento_repository import PostgresqlAlimentoRepository
from infrastructure.security.password_hasher import PasswordHasher
from domain.services.autenticacion_service import AutenticacionService
from domain.services.alimento_service import AlimentoService

load_dotenv()

# Configurar el connection manager usando variables de entorno
connection_manager = PostgresqlConnectionManager(
    db_name=os.getenv("DB_NAME", "foodcash_db"),
    db_user=os.getenv("DB_USER", "postgres"),
    db_password=os.getenv("DB_PASSWORD", "postgres"),
    db_host=os.getenv("DB_HOST", "localhost"),
    db_port=os.getenv("DB_PORT", "5432")
)

# Configurar repositorios y servicios para usuarios (si se necesitan)
usuario_repository = PostgresqlUsuarioRepository(connection_manager)
password_hasher = PasswordHasher()
autenticacion_service = AutenticacionService(usuario_repository, password_hasher)

# Configurar repositorio y servicio de alimentos
alimento_repository = PostgresqlAlimentoRepository(connection_manager)
alimento_service = AlimentoService(alimento_repository)


def get_alimento_service():
    return alimento_service
