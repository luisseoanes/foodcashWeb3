# app/infrastructure/repositories/postgresql_producto_repository.py
from domain.services.producto_service import ProductoRepository
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager

class PostgresqlProductoRepository(ProductoRepository):
    def __init__(self, connection_manager: PostgresqlConnectionManager):
        self.connection_manager = connection_manager

    def obtener_producto_por_id(self, producto_id: int):
        with self.connection_manager.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id FROM alimentos WHERE id = %s
                    """,
                    (producto_id,)
                )
                result = cursor.fetchone()
                return result is not None