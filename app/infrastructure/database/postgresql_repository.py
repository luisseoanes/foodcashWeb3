# infrastructure/database/postgresql_repository.py

from contextlib import contextmanager
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List

from domain.models.usuario import Usuario, RolUsuario
from domain.repositories.usuario_repository import UsuarioRepository
from domain.exceptions.exceptions import UsuarioNoEncontradoError

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

class PostgresqlConnectionManager:
    """Gestiona conexiones a la base de datos PostgreSQL"""
    
    def __init__(self, 
                 db_name: str = DB_NAME, 
                 db_user: str = DB_USER, 
                 db_password: str = DB_PASSWORD, 
                 db_host: str = DB_HOST, 
                 db_port: str = DB_PORT):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        
    @contextmanager
    def get_connection(self):
        conexion = None
        try:
            conexion = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                cursor_factory=RealDictCursor
            )
            yield conexion
        except psycopg2.OperationalError as e:
            print(f"❌ Error de conexión a PostgreSQL: {e}")
            raise
        finally:
            if conexion is not None:
                conexion.close()

def get_connection_manager():
    """
    Función de dependencia que crea y retorna una instancia del
    gestor de conexiones. Esto evita que FastAPI exponga las
    credenciales en los endpoints.
    """
    return PostgresqlConnectionManager()

class PostgresqlUsuarioRepository(UsuarioRepository):
    """Implementación del repositorio de usuarios con PostgreSQL"""
    
    def __init__(self, connection_manager: PostgresqlConnectionManager):
        self.connection_manager = connection_manager
        
    def guardar(self, usuario: Usuario) -> None:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO usuarios (usuario, contrasena, nombre, rol, saldo) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (usuario.usuario, usuario.contrasena_hash, usuario.nombre, usuario.rol.value, usuario.saldo)
                )
                new_id = cursor.fetchone()["id"]
                usuario.id = str(new_id)
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"❌ Error al guardar usuario: {e}")
                raise
    
    def _map_row_to_usuario(self, row: dict) -> Optional[Usuario]:
        """Mapea una fila de la DB a un objeto Usuario."""
        if not row:
            return None
        
        saldo = 0.0
        if row["saldo"] is not None:
            saldo = float(row["saldo"])
            
        return Usuario(
            id=str(row["id"]),
            usuario=row["usuario"],
            nombre=row["nombre"],
            rol=RolUsuario(row["rol"]),
            saldo=saldo,
            contrasena_hash=row["contrasena"]
        )

    def buscar_por_id(self, id_str: str) -> Optional[Usuario]:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                id_int = int(id_str)
            except ValueError:
                return None

            cursor.execute(
                "SELECT id, usuario, contrasena, nombre, rol, saldo FROM usuarios WHERE id = %s",
                (id_int,)
            )
            usuario_db = cursor.fetchone()
            return self._map_row_to_usuario(usuario_db)
            
    def buscar_por_nombre_usuario(self, nombre_usuario: str) -> Optional[Usuario]:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, usuario, contrasena, nombre, rol, saldo FROM usuarios WHERE usuario = %s",
                (nombre_usuario,)
            )
            usuario_db = cursor.fetchone()
            return self._map_row_to_usuario(usuario_db)
            
    def existe_usuario(self, nombre_usuario: str) -> bool:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT usuario FROM usuarios WHERE usuario = %s",
                (nombre_usuario,)
            )
            return cursor.fetchone() is not None
            
    def actualizar(self, usuario: Usuario) -> None:
        with self.connection_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE usuarios 
                    SET nombre = %s, saldo = %s, contrasena = %s, rol = %s
                    WHERE id = %s
                    """,
                    (usuario.nombre, usuario.saldo, usuario.contrasena_hash, usuario.rol.value, int(usuario.id))
                )
                conn.commit()

    def actualizar_saldo(self, nombre_usuario: str, nuevo_saldo: float) -> Optional[Usuario]:
        with self.connection_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE usuarios 
                    SET saldo = %s 
                    WHERE usuario = %s 
                    RETURNING id, usuario, nombre, rol, saldo, contrasena
                    """,
                    (nuevo_saldo, nombre_usuario)
                )
                conn.commit()
                usuario_actualizado = cursor.fetchone()
                return self._map_row_to_usuario(usuario_actualizado)
    
    def listar_por_rol(self, rol: str) -> List[Usuario]:
        """Lista todos los usuarios con un rol específico"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, usuario, contrasena, nombre, rol, saldo FROM usuarios WHERE rol = %s ORDER BY nombre ASC",
                (rol,)
            )
            usuarios_db = cursor.fetchall()
            return [self._map_row_to_usuario(row) for row in usuarios_db]