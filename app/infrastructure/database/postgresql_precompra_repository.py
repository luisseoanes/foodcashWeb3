from typing import List, Optional
from datetime import datetime
from psycopg2.extras import RealDictCursor

from domain.models.precompra import Precompra
from domain.models.compra import Compra, CompraItem
from domain.repositories.precompra_repository import PrecompraRepository
from domain.repositories.compra_repository import CompraRepository
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager
import json
import logging

class PostgresqlPrecompraRepository(PrecompraRepository):
    
    def __init__(self, connection_manager: PostgresqlConnectionManager, compra_repository: CompraRepository):
        self.connection_manager = connection_manager
        self.compra_repository = compra_repository
    
    def guardar(self, precompra: Precompra) -> Precompra:
        """
        Guarda una precompra. Si no tiene ID, la inserta; si tiene ID, la actualiza.
        """
        if precompra.id is None:
            return self._insertar(precompra)
        else:
            return precompra

    def crear_precompra_con_compra(self, precompra: Precompra, items_compra: List[CompraItem]) -> Precompra:
        """
        Crea una precompra y delega la creación de la compra asociada.
        """
        compra_obj = Compra(
            usuario_id=precompra.id_estudiante,
            fecha=precompra.fecha_precompra,
            total=precompra.costo_total,
            items=items_compra
        )
        
        compra_guardada = self.compra_repository.guardar_compra(compra_obj)
        
        precompra.id_compra = compra_guardada.id
        return self.guardar(precompra) # Usamos el método guardar para insertar

    def _insertar(self, precompra: Precompra) -> Precompra:
        """Inserta una nueva precompra en la base de datos."""
        query = """
            INSERT INTO precompras (
                id_compra, id_estudiante, fecha_precompra, costo_total, 
                costo_adicional, entregado, fecha_entrega, activo,
                fecha_creacion, fecha_actualizacion
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, fecha_creacion, fecha_actualizacion
        """
        now = datetime.now()
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (
                    precompra.id_compra, precompra.id_estudiante, precompra.fecha_precompra,
                    precompra.costo_total, precompra.costo_adicional, precompra.entregado,
                    precompra.fecha_entrega, precompra.activo, now, now
                ))
                result = cursor.fetchone()
                conn.commit()
                precompra.id = result['id']
                precompra.fecha_creacion = result['fecha_creacion']
                precompra.fecha_actualizacion = result['fecha_actualizacion']
                return precompra
    
    def _actualizar(self, precompra: Precompra) -> Precompra:
        query = """
            UPDATE precompras SET
                id_compra = %s,
                id_estudiante = %s,
                fecha_precompra = %s,
                costo_total = %s,
                costo_adicional = %s,
                entregado = %s,
                fecha_entrega = %s,
                activo = %s,
                fecha_actualizacion = %s
            WHERE id = %s
            RETURNING fecha_actualizacion
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (
                    precompra.id_compra,
                    precompra.id_estudiante,
                    precompra.fecha_precompra,
                    precompra.costo_total,
                    precompra.costo_adicional,
                    precompra.entregado,
                    precompra.fecha_entrega,
                    precompra.activo,
                    datetime.now(),
                    precompra.id
                ))
                
                result = cursor.fetchone()
                conn.commit()
                
                precompra.fecha_actualizacion = result['fecha_actualizacion']
                return precompra
    
    def obtener_por_id(self, precompra_id: int) -> Optional[Precompra]:
        query = """
            SELECT * FROM precompras 
            WHERE id = %s AND activo = TRUE
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (precompra_id,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return self._row_to_precompra(result)
    
    def obtener_por_compra_id(self, compra_id: int) -> Optional[Precompra]:
        query = """
            SELECT * FROM precompras 
            WHERE id_compra = %s AND activo = TRUE
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (compra_id,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return self._row_to_precompra(result)
    
    def obtener_precompra_con_detalles_compra(self, precompra_id: int) -> Optional[dict]:
        """
        Obtiene una precompra junto con los detalles de la compra asociada.
        
        Returns:
            dict: {
                'precompra': Precompra object,
                'compra': dict con detalles de la compra (incluyendo items)
            }
        """
        precompra = self.obtener_por_id(precompra_id)
        if not precompra:
            return None
        
        compra_detalles = self.compra_repository.obtener_compra_por_id(precompra.id_compra)
        
        return {
            'precompra': precompra,
            'compra': compra_detalles
        }
    
    def obtener_por_estudiante_id(self, estudiante_id: int) -> List[Precompra]:
        query = """
            SELECT * FROM precompras 
            WHERE id_estudiante = %s AND activo = TRUE
            ORDER BY fecha_precompra DESC
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (estudiante_id,))
                results = cursor.fetchall()
                
                return [self._row_to_precompra(row) for row in results]
    
    def obtener_pendientes_entrega(self) -> List[Precompra]:
        query = """
            SELECT * FROM precompras 
            WHERE entregado = FALSE AND activo = TRUE
            ORDER BY fecha_precompra ASC
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                return [self._row_to_precompra(row) for row in results]
    
    def obtener_por_estudiante_pendientes(self, estudiante_id: int) -> List[Precompra]:
        query = """
            SELECT * FROM precompras 
            WHERE id_estudiante = %s AND entregado = FALSE AND activo = TRUE
            ORDER BY fecha_precompra ASC
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (estudiante_id,))
                results = cursor.fetchall()
                
                return [self._row_to_precompra(row) for row in results]
    
    def eliminar(self, precompra_id: int) -> bool:
        query = """
            UPDATE precompras SET 
                activo = FALSE, 
                fecha_actualizacion = %s
            WHERE id = %s AND activo = TRUE
            RETURNING id
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (datetime.now(), precompra_id))
                result = cursor.fetchone()
                conn.commit()
                
                return result is not None
    
    def existe_precompra_para_compra(self, compra_id: int) -> bool:
        query = """
            SELECT 1 FROM precompras 
            WHERE id_compra = %s AND activo = TRUE
            LIMIT 1
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (compra_id,))
                result = cursor.fetchone()
                
                return result is not None
    
    def marcar_como_entregado(self, precompra_id: int, fecha_entrega: datetime = None) -> bool:
        """
        Marca una precompra como entregada.
        
        Args:
            precompra_id: ID de la precompra
            fecha_entrega: Fecha de entrega (si es None, usa la fecha actual)
            
        Returns:
            bool: True si se actualizó correctamente
        """
        if fecha_entrega is None:
            fecha_entrega = datetime.now()
            
        query = """
            UPDATE precompras SET 
                entregado = TRUE,
                fecha_entrega = %s,
                fecha_actualizacion = %s
            WHERE id = %s AND activo = TRUE
            RETURNING id
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (fecha_entrega, datetime.now(), precompra_id))
                result = cursor.fetchone()
                conn.commit()
                
                return result is not None
    
    def _row_to_precompra(self, row) -> Precompra:
        """Convierte una fila de la base de datos a un objeto Precompra"""
        return Precompra(
            id=row['id'],
            id_compra=row['id_compra'],
            id_estudiante=row['id_estudiante'],
            fecha_precompra=row['fecha_precompra'],
            costo_total=float(str(row['costo_total'])),
            costo_adicional=float(str(row['costo_adicional'])),
            entregado=row['entregado'],
            fecha_entrega=row['fecha_entrega'],
            activo=row['activo'],
            fecha_creacion=row['fecha_creacion'],
            fecha_actualizacion=row['fecha_actualizacion']
        )
    
    def obtener_todas_con_detalles(self) -> List[dict]:
        """
        Obtiene TODAS las precompras con detalles usando una única consulta
        optimizada y robusta con la sintaxis SQL correcta.
        """
        query = """
            SELECT
                p.id,
                p.id_compra,
                p.fecha_precompra,
                p.costo_total,
                p.entregado,
                p.fecha_entrega,
                e.nombre AS nombre_estudiante,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'nombre', a.nombre,
                            'cantidad', ci.cantidad,
                            'precio_unitario', ci.precio_unitario
                        )
                    ) FILTER (WHERE ci.id IS NOT NULL), -- CORRECCIÓN: FILTER va después de json_agg()
                    '[]'::json
                ) AS items
            FROM
                precompras p
            JOIN
                estudiantes e ON p.id_estudiante = e.id
            LEFT JOIN
                compra_items ci ON p.id_compra = ci.compra_id
            LEFT JOIN
                alimentos a ON ci.producto_id = a.id
            GROUP BY
                p.id, e.nombre
            ORDER BY
                p.fecha_precompra DESC;
        """
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    # Algunos drivers de DB pueden devolver el JSON como un string,
                    # esta lógica asegura que siempre sea un objeto Python.
                    for row in results:
                        if isinstance(row.get('items'), str):
                            row['items'] = json.loads(row['items'])
                    return results
        except Exception as e:
            logging.error(f"Error en la base de datos al ejecutar obtener_todas_con_detalles: {e}", exc_info=True)
            raise

    def obtener_historial_por_estudiante(self, estudiante_id: int) -> List[dict]:
        """
        Obtiene el historial detallado de un estudiante específico, incluyendo
        el nombre del estudiante y los items de cada precompra.
        """
        query = """
            SELECT
                p.id,
                p.id_compra,
                p.fecha_precompra,
                p.costo_total,
                p.entregado,
                p.fecha_entrega,
                e.nombre AS nombre_estudiante, -- <-- CORRECCIÓN: Se añade el nombre del estudiante
                COALESCE(
                    json_agg(
                        json_build_object(
                            'nombre', a.nombre,
                            'cantidad', ci.cantidad,
                            'precio_unitario', ci.precio_unitario
                        )
                    ) FILTER (WHERE ci.id IS NOT NULL),
                    '[]'::json
                ) AS items
            FROM
                precompras p
            -- CORRECCIÓN: Se añade el JOIN a la tabla de estudiantes
            JOIN 
                estudiantes e ON p.id_estudiante = e.id
            LEFT JOIN 
                compra_items ci ON p.id_compra = ci.compra_id
            LEFT JOIN
                alimentos a ON ci.producto_id = a.id
            WHERE 
                p.id_estudiante = %s
            GROUP BY
                p.id, e.nombre -- CORRECCIÓN: Se añade el nombre al GROUP BY
            ORDER BY
                p.fecha_precompra DESC;
        """
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (estudiante_id,))
                results = cursor.fetchall()
                # Procesamos el JSON que puede venir como texto
                for row in results:
                    if isinstance(row.get('items'), str):
                        row['items'] = json.loads(row['items'])
                return results