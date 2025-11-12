from contextlib import contextmanager
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Optional, Dict, Any

from domain.models.alimento import Alimento
from domain.repositories.alimento_repository import AlimentoRepository

# Cargar variables del archivo .env
load_dotenv()

DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")

class PostgresqlConnectionManager:
    """Gestiona conexiones a la base de datos PostgreSQL para Alimentos."""
    
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

class PostgresqlAlimentoRepository(AlimentoRepository):
    """Implementación del repositorio de Alimento con PostgreSQL."""
    
    def __init__(self, connection_manager: PostgresqlConnectionManager):
        self.connection_manager = connection_manager

    def listar_alimentos(self, filtros: Optional[Dict[str, Any]] = None) -> List[Alimento]:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT id, nombre, precio, cantidad_en_stock, calorias, imagen, categoria,
                       fecha_creacion, fecha_actualizacion, activo
                FROM alimentos
                WHERE activo = TRUE
            """
            params = []
            if filtros:
                if 'categoria' in filtros and filtros['categoria']:
                    query += " AND categoria = %s"
                    params.append(filtros['categoria'])
                if 'nombre' in filtros and filtros['nombre']:
                    query += " AND nombre ILIKE %s"
                    params.append(f"%{filtros['nombre']}%")
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            alimentos = []
            for row in rows:
                alimentos.append(
                    Alimento(
                        id=row["id"],
                        nombre=row["nombre"],
                        precio=float(row["precio"]),
                        cantidad_en_stock=row["cantidad_en_stock"],
                        calorias=row["calorias"],
                        imagen=row["imagen"],
                        categoria=row["categoria"],
                        fecha_creacion=row["fecha_creacion"],
                        fecha_actualizacion=row["fecha_actualizacion"],
                        activo=row["activo"]
                    )
                )
            return alimentos

    def buscar_por_id(self, alimento_id: int) -> Optional[Alimento]:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, nombre, precio, cantidad_en_stock, calorias, imagen, categoria,
                       fecha_creacion, fecha_actualizacion, activo
                FROM alimentos
                WHERE id = %s AND activo = TRUE
            """, (alimento_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Alimento(
                id=row["id"],
                nombre=row["nombre"],
                precio=float(row["precio"]),
                cantidad_en_stock=row["cantidad_en_stock"],
                calorias=row["calorias"],
                imagen=row["imagen"],
                categoria=row["categoria"],
                fecha_creacion=row["fecha_creacion"],
                fecha_actualizacion=row["fecha_actualizacion"],
                activo=row["activo"]
            )
    
    def buscar_por_nombre(self, nombre: str) -> Optional[Alimento]:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, nombre, precio, cantidad_en_stock, calorias, imagen, categoria,
                       fecha_creacion, fecha_actualizacion, activo
                FROM alimentos
                WHERE LOWER(nombre) = LOWER(%s) AND activo = TRUE
            """, (nombre,))
            row = cursor.fetchone()
            if not row:
                return None
            return Alimento(
                id=row["id"],
                nombre=row["nombre"],
                precio=float(row["precio"]),
                cantidad_en_stock=row["cantidad_en_stock"],
                calorias=row["calorias"],
                imagen=row["imagen"],
                categoria=row["categoria"],
                fecha_creacion=row["fecha_creacion"],
                fecha_actualizacion=row["fecha_actualizacion"],
                activo=row["activo"]
            )
    
    def guardar(self, alimento: Alimento) -> Alimento:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if alimento.id is not None:
                # Actualización
                cursor.execute("""
                    UPDATE alimentos
                    SET nombre = %s, precio = %s, cantidad_en_stock = %s, calorias = %s,
                        imagen = %s, categoria = %s, fecha_actualizacion = %s, activo = %s
                    WHERE id = %s
                    RETURNING id
                """, (
                    alimento.nombre,
                    alimento.precio,
                    alimento.cantidad_en_stock,
                    alimento.calorias,
                    alimento.imagen,
                    alimento.categoria,
                    datetime.now(),
                    alimento.activo,
                    alimento.id
                ))
            else:
                # Inserción
                cursor.execute("""
                    INSERT INTO alimentos (nombre, precio, cantidad_en_stock, calorias,
                                           imagen, categoria, fecha_creacion, fecha_actualizacion, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    alimento.nombre,
                    alimento.precio,
                    alimento.cantidad_en_stock,
                    alimento.calorias,
                    alimento.imagen,
                    alimento.categoria,
                    alimento.fecha_creacion,
                    alimento.fecha_actualizacion,
                    alimento.activo
                ))
                returned_id = cursor.fetchone()['id']
                alimento.id = returned_id
            
            conn.commit()
            return alimento
    
    def eliminar(self, alimento_id: int) -> bool:
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alimentos
                SET activo = FALSE, fecha_actualizacion = %s
                WHERE id = %s AND activo = TRUE
                RETURNING id
            """, (datetime.now(), alimento_id))
            result = cursor.fetchone()
            conn.commit()
            return result is not None

    def disminuir_inventario(self, alimento_id: int, cantidad: int):
        connection = self.connection_manager.get_connection()
        cursor = connection.cursor()
        try:
            # Actualizar el stock solo si hay suficientes unidades
            cursor.execute(
                """
                UPDATE alimentos
                SET cantidad_en_stock = cantidad_en_stock - %s
                WHERE id = %s AND cantidad_en_stock >= %s
                RETURNING id, nombre, precio, cantidad_en_stock, calorias, imagen, categoria
                """,
                (cantidad, alimento_id, cantidad)
            )
            result = cursor.fetchone()
            if not result:
                raise Exception("No hay stock suficiente o el alimento no existe")
            connection.commit()
            # Suponiendo que transformas el resultado en un objeto de dominio
            return self._map_row_to_alimento(result)
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()
