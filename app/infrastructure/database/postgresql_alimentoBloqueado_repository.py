from typing import List, Optional
from domain.models.alimentoBloqueado import AlimentoBloqueado
from domain.repositories.alimentoBloqueado_repository import AlimentoBloqueadoRepository
from domain.exceptions.exceptions import UsuarioNoEncontradoError
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager
from psycopg2.extras import RealDictCursor
import psycopg2

class PostgresqlAlimentoBloqueadoRepository(AlimentoBloqueadoRepository):
    def __init__(self, connection_manager: PostgresqlConnectionManager):
        self.connection_manager = connection_manager

    def bloquear_alimento(self, alimento_bloqueado: AlimentoBloqueado) -> AlimentoBloqueado:
        query = """
            INSERT INTO alimentos_bloqueados (id_estudiante, id_alimento, fecha_bloqueo)
            VALUES (%s, %s, %s)
            ON CONFLICT (id_estudiante, id_alimento) DO NOTHING
            RETURNING id_estudiante, id_alimento, fecha_bloqueo
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                try:
                    cur.execute(query, (
                        alimento_bloqueado.id_estudiante,
                        alimento_bloqueado.id_alimento,
                        alimento_bloqueado.fecha_bloqueo
                    ))
                    conn.commit()
                    
                    result = cur.fetchone()
                    if result is None:
                        # El bloqueo ya existía, obtenemos la información existente
                        return self._obtener_bloqueo_existente(alimento_bloqueado.id_estudiante, alimento_bloqueado.id_alimento)
                    
                    return AlimentoBloqueado(
                        id_estudiante=result.get('id_estudiante'),
                        id_alimento=result.get('id_alimento'),
                        fecha_bloqueo=result.get('fecha_bloqueo')
                    )
                except psycopg2.IntegrityError as e:
                    if "estudiantes" in str(e):
                        raise UsuarioNoEncontradoError(f"Estudiante con ID {alimento_bloqueado.id_estudiante} no encontrado")
                    elif "alimentos" in str(e):
                        raise ValueError(f"Alimento con ID {alimento_bloqueado.id_alimento} no encontrado")
                    else:
                        raise ValueError(f"Error de integridad: {str(e)}")

    def _obtener_bloqueo_existente(self, id_estudiante: int, id_alimento: int) -> AlimentoBloqueado:
        query = """
            SELECT id_estudiante, id_alimento, fecha_bloqueo
            FROM alimentos_bloqueados
            WHERE id_estudiante = %s AND id_alimento = %s
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (id_estudiante, id_alimento))
                result = cur.fetchone()
                return AlimentoBloqueado(
                    id_estudiante=result.get('id_estudiante'),
                    id_alimento=result.get('id_alimento'),
                    fecha_bloqueo=result.get('fecha_bloqueo')
                )

    def desbloquear_alimento(self, id_estudiante: int, id_alimento: int) -> bool:
        query = """
            DELETE FROM alimentos_bloqueados
            WHERE id_estudiante = %s AND id_alimento = %s
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (id_estudiante, id_alimento))
                conn.commit()
                return cur.rowcount > 0

    def obtener_alimentos_bloqueados_por_estudiante(self, id_estudiante: int) -> List[AlimentoBloqueado]:
        query = """
            SELECT id_estudiante, id_alimento, fecha_bloqueo
            FROM alimentos_bloqueados
            WHERE id_estudiante = %s
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (id_estudiante,))
                results = cur.fetchall()
                return [
                    AlimentoBloqueado(
                        id_estudiante=result.get('id_estudiante'),
                        id_alimento=result.get('id_alimento'),
                        fecha_bloqueo=result.get('fecha_bloqueo')
                    )
                    for result in results
                ]

    def existe_bloqueo(self, id_estudiante: int, id_alimento: int) -> bool:
        query = """
            SELECT 1 FROM alimentos_bloqueados
            WHERE id_estudiante = %s AND id_alimento = %s
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (id_estudiante, id_alimento))
                return cur.fetchone() is not None
