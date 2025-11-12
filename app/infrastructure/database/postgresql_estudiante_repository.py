# infrastructure/database/postgresql_estudiante_repository.py

from typing import List, Optional
from domain.models.estudiante import Estudiante
from domain.repositories.estudiante_repository import EstudianteRepository
from domain.exceptions.exceptions import UsuarioNoEncontradoError
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager
from psycopg2.extras import RealDictCursor

class PostgresqlEstudianteRepository(EstudianteRepository):
    def __init__(self, connection_manager: PostgresqlConnectionManager):
        self.connection_manager = connection_manager

    def obtener_por_id(self, estudiante_id: int) -> Optional[Estudiante]:
        query = """
            SELECT id, nombre, email, fecha_nacimiento, responsablefinanciero, saldo, cedula
            FROM estudiantes
            WHERE id = %s
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (estudiante_id,))
                result = cur.fetchone()
                if result is None:
                    return None
                return Estudiante(
                    id=result.get('id'),
                    nombre=result.get('nombre'),
                    email=result.get('email'),
                    fecha_nacimiento=result.get('fecha_nacimiento'),
                    responsableFinanciero=result.get('responsablefinanciero'),
                    saldo=result.get('saldo'),
                    cedula=result.get('cedula')
                )

    def guardar(self, estudiante: Estudiante) -> Estudiante:
        query = """
            UPDATE estudiantes 
            SET nombre = %s, 
                email = %s,
                fecha_nacimiento = %s,
                responsablefinanciero = %s,
                saldo = %s,
                cedula = %s
            WHERE id = %s 
            RETURNING id, nombre, email, fecha_nacimiento, responsablefinanciero, saldo, cedula
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (
                    estudiante.nombre,
                    estudiante.email,
                    estudiante.fecha_nacimiento,
                    estudiante.responsableFinanciero,
                    float(estudiante.saldo),
                    estudiante.cedula,
                    estudiante.id
                ))
                conn.commit()
                if cur.rowcount == 0:
                    raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante.id} no encontrado")
                result = cur.fetchone()
                return Estudiante(
                    id=result.get('id'),
                    nombre=result.get('nombre'),
                    email=result.get('email'),
                    fecha_nacimiento=result.get('fecha_nacimiento'),
                    responsableFinanciero=result.get('responsablefinanciero'),
                    saldo=result.get('saldo'),
                    cedula=result.get('cedula')
                )
    
    def crear(self, estudiante: Estudiante) -> Estudiante:
        """Crea un nuevo estudiante en la base de datos"""
        query = """
            INSERT INTO estudiantes (nombre, email, fecha_nacimiento, responsablefinanciero, saldo, cedula)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, nombre, email, fecha_nacimiento, responsablefinanciero, saldo, cedula
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (
                    estudiante.nombre,
                    estudiante.email,
                    estudiante.fecha_nacimiento,
                    estudiante.responsableFinanciero,
                    float(estudiante.saldo),
                    estudiante.cedula
                ))
                conn.commit()
                result = cur.fetchone()
                return Estudiante(
                    id=result.get('id'),
                    nombre=result.get('nombre'),
                    email=result.get('email'),
                    fecha_nacimiento=result.get('fecha_nacimiento'),
                    responsableFinanciero=result.get('responsablefinanciero'),
                    saldo=result.get('saldo'),
                    cedula=result.get('cedula')
                )

    def listar_por_responsable(self, responsable: str) -> List[Estudiante]:
        query = """
            SELECT id, nombre, email, fecha_nacimiento, responsablefinanciero, saldo, cedula
            FROM estudiantes
            WHERE responsablefinanciero = %s
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (responsable,))
                results = cur.fetchall()
                return [
                    Estudiante(
                        id=result.get('id'),
                        nombre=result.get('nombre'),
                        email=result.get('email'),
                        fecha_nacimiento=result.get('fecha_nacimiento'),
                        responsableFinanciero=result.get('responsablefinanciero'),
                        saldo=result.get('saldo'),
                        cedula=result.get('cedula')
                    )
                    for result in results
                ]

    def buscar_por_cedula(self, cedula: str) -> Optional[Estudiante]:
        query = """
            SELECT id, nombre, email, fecha_nacimiento, responsablefinanciero, saldo, cedula
            FROM estudiantes
            WHERE cedula = %s
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (cedula,))
                result = cur.fetchone()
                if result is None:
                    return None
                return Estudiante(
                    id=result.get('id'),
                    nombre=result.get('nombre'),
                    email=result.get('email'),
                    fecha_nacimiento=result.get('fecha_nacimiento'),
                    responsableFinanciero=result.get('responsablefinanciero'),
                    saldo=result.get('saldo'),
                    cedula=result.get('cedula')
                )

    def actualizar_saldo(self, estudiante_id: int, nuevo_saldo: float) -> Optional[Estudiante]:
        """
        Actualiza el saldo de un estudiante.
        """
        query = """
            UPDATE estudiantes 
            SET saldo = %s
            WHERE id = %s 
            RETURNING id, nombre, email, fecha_nacimiento, responsablefinanciero, saldo, cedula
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (float(nuevo_saldo), estudiante_id))
                conn.commit()
                
                if cur.rowcount == 0:
                    raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante_id} no encontrado")
                
                result = cur.fetchone()
                return Estudiante(
                    id=result.get('id'),
                    nombre=result.get('nombre'),
                    email=result.get('email'),
                    fecha_nacimiento=result.get('fecha_nacimiento'),
                    responsableFinanciero=result.get('responsablefinanciero'),
                    saldo=result.get('saldo'),
                    cedula=result.get('cedula')
                )