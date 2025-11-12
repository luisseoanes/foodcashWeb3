from typing import Optional, List
from domain.models.compra import Compra, CompraItem
from psycopg2.extras import RealDictCursor
from domain.repositories.compra_repository import CompraRepository
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager


class PostgresqlCompraRepository(CompraRepository):
    def __init__(self, connection_manager: PostgresqlConnectionManager):
        self.connection_manager = connection_manager

    def guardar_compra(self, compra: Compra) -> Compra:
        query_insert_compra = """
            INSERT INTO compras (usuario_id, fecha, total)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        query_insert_item = """
            INSERT INTO compra_items (compra_id, producto_id, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s)
        """
        query_update_stock = """
            UPDATE alimentos
            SET cantidad_en_stock = cantidad_en_stock - %s
            WHERE id = %s
        """

        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    query_insert_compra,
                    (compra.usuario_id, compra.fecha, compra.total)
                )
                row = cursor.fetchone()
                compra_id = row["id"]

                for item in compra.items:
                    cursor.execute(
                        query_insert_item,
                        (compra_id, item.producto_id, item.cantidad, item.precio_unitario)
                    )
                    cursor.execute(
                        query_update_stock,
                        (item.cantidad, item.producto_id)
                    )

                conn.commit()

        compra.id = compra_id
        return compra

    def obtener_compra_por_id(self, compra_id: int) -> Optional[dict]:
        """
        Devuelve un diccionario con los datos de la compra, incluyendo:
          - id, usuario_id, fecha (timestamp), total
          - items: lista de { producto_id, cantidad, precio_unitario, nombre_alimento, calorias }
        """
        query_compra = """
            SELECT id, usuario_id, fecha, total
            FROM compras
            WHERE id = %s
        """
        query_items = """
            SELECT 
                ci.producto_id,
                ci.cantidad,
                ci.precio_unitario,
                a.nombre      AS nombre_alimento,
                a.calorias    AS calorias
            FROM compra_items ci
            INNER JOIN alimentos a ON ci.producto_id = a.id
            WHERE ci.compra_id = %s
        """

        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 1) Obtener datos generales de la compra
                cursor.execute(query_compra, (compra_id,))
                compra_row = cursor.fetchone()
                if not compra_row:
                    return None

                # 2) Obtener items asociados a esa compra, junto con nombre y calorías del alimento
                cursor.execute(query_items, (compra_id,))
                items_raw = cursor.fetchall()

                items: List[dict] = []
                for item in items_raw:
                    # Cada item_raw ya es un dict con las columnas: producto_id, cantidad,
                    # precio_unitario, nombre_alimento y calorias.
                    items.append({
                        "producto_id": item["producto_id"],
                        "cantidad": item["cantidad"],
                        "precio_unitario": float(item["precio_unitario"]),
                        "nombre_alimento": item["nombre_alimento"],
                        "calorias": float(item["calorias"]) if item["calorias"] is not None else 0.0
                    })

                return {
                    "id": compra_row["id"],
                    "usuario_id": compra_row["usuario_id"],
                    "fecha": compra_row["fecha"],               # Timestamp
                    "total": float(compra_row["total"]),
                    "items": items
                }

    def obtener_compras_por_usuario_id(self, usuario_id: int) -> List[dict]:
        """
        Trae únicamente el ID de cada compra de un usuario y luego,
        para cada ID, invoca obtener_compra_por_id para traer los datos completos
        (incluyendo nombre_alimento y calorias).
        """
        query = """
            SELECT id
            FROM compras
            WHERE usuario_id = %s
            ORDER BY fecha DESC
        """

        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (usuario_id,))
                compras_rows = cursor.fetchall()

                compras: List[dict] = []
                for row in compras_rows:
                    compra_id = row["id"]
                    compra_completa = self.obtener_compra_por_id(compra_id)
                    if compra_completa:
                        compras.append(compra_completa)

                return compras

    def obtener_ultimas_compras_por_usuario_id(self, usuario_id: int, limit: int = 5) -> List[dict]:
        """
        Mismo procedimiento, pero con LIMIT para traer sólo las últimas N compras.
        """
        query = """
            SELECT id
            FROM compras
            WHERE usuario_id = %s
            ORDER BY fecha DESC
            LIMIT %s
        """

        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (usuario_id, limit))
                compras_rows = cursor.fetchall()

                compras: List[dict] = []
                for row in compras_rows:
                    compra_id = row["id"]
                    compra_completa = self.obtener_compra_por_id(compra_id)
                    if compra_completa:
                        compras.append(compra_completa)

                return compras
    
    def obtener_todas_las_compras(self) -> List[dict]:
        """
        Obtiene todas las compras de la base de datos.
        Primero trae todos los IDs de compra y luego invoca
        obtener_compra_por_id para cada uno para obtener los detalles completos.
        """
        query = """
            SELECT id
            FROM compras
            ORDER BY fecha DESC
        """

        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                compras_rows = cursor.fetchall()

                compras: List[dict] = []
                for row in compras_rows:
                    compra_id = row["id"]
                    compra_completa = self.obtener_compra_por_id(compra_id)
                    if compra_completa:
                        compras.append(compra_completa)

                return compras
