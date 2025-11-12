# infrastructure/database/postgresql_recarga_repository.py

from typing import List, Optional
from datetime import datetime
import uuid
import logging

from domain.models.recarga import Recarga, EstadoRecarga
from domain.repositories.recarga_repository import RecargaRepository
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager

logger = logging.getLogger(__name__)

class PostgresqlRecargaRepository(RecargaRepository):
    """
    ✅ CORREGIDO: Implementación con manejo correcto de estados
    """
    
    def __init__(self, connection_manager: PostgresqlConnectionManager):
        self.connection_manager = connection_manager
    
    def guardar(self, recarga: Recarga) -> None:
        """Guarda una nueva recarga en la base de datos"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Generar UUID para la recarga si no tiene ID
                if not recarga.id:
                    recarga.id = str(uuid.uuid4())
                
                estado_db = self._map_estado_to_db(recarga.estado)
                
                logger.info(f"💾 Guardando recarga: {recarga.id}")
                logger.info(f"   Estado: {recarga.estado.value} → DB: {estado_db}")
                
                cursor.execute(
                    """
                    INSERT INTO recharges 
                    (id, user_id, amount, status, wompi_reference, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        recarga.id,
                        int(recarga.usuario_id),
                        recarga.monto,
                        estado_db,  # ✅ Usar mapeo correcto
                        recarga.referencia_wompi,
                        recarga.fecha_creacion,
                        recarga.fecha_actualizacion or datetime.now()
                    )
                )
                conn.commit()
                logger.info(f"✅ Recarga guardada exitosamente: {recarga.id}")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Error al guardar recarga: {e}", exc_info=True)
                raise
    
    def buscar_por_id(self, recarga_id: str) -> Optional[Recarga]:
        """Busca una recarga por su ID"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT id, user_id, amount, status, wompi_reference, wompi_transaction_id,
                       created_at, updated_at 
                FROM recharges 
                WHERE id = %s
                """,
                (recarga_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_recarga(row)
    
    def buscar_por_referencia_wompi(self, referencia: str) -> Optional[Recarga]:
        """Busca una recarga por su referencia de WOMPI"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            logger.info(f"🔍 Buscando recarga por referencia WOMPI: {referencia}")
            
            cursor.execute(
                """
                SELECT id, user_id, amount, status, wompi_reference, wompi_transaction_id,
                       created_at, updated_at 
                FROM recharges 
                WHERE wompi_reference = %s
                """,
                (referencia,)
            )
            row = cursor.fetchone()
            
            if row:
                logger.info(f"✅ Recarga encontrada: ID={row['id']}, Estado={row['status']}")
            else:
                logger.warning(f"⚠️ No se encontró recarga con referencia: {referencia}")
            
            return self._map_row_to_recarga(row)
    
    def buscar_por_usuario(self, usuario_id: str, limite: int = 10) -> List[Recarga]:
        """Busca las recargas de un usuario específico"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                usuario_id_int = int(usuario_id)
            except ValueError:
                logger.error(f"Usuario ID inválido: {usuario_id}")
                return []
                
            cursor.execute(
                """
                SELECT id, user_id, amount, status, wompi_reference, wompi_transaction_id,
                       created_at, updated_at 
                FROM recharges 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """,
                (usuario_id_int, limite)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_recarga(row) for row in rows if row]
    
    def buscar_por_estado(self, estado: EstadoRecarga, limite: int = 100) -> List[Recarga]:
        """Busca recargas por estado"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, amount, status, wompi_reference, wompi_transaction_id,
                       created_at, updated_at 
                FROM recharges 
                WHERE status = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """,
                (self._map_estado_to_db(estado), limite)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_recarga(row) for row in rows if row]
    
    def actualizar(self, recarga: Recarga) -> None:
        """✅ CORREGIDO: Actualiza una recarga con logs detallados"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                estado_db = self._map_estado_to_db(recarga.estado)
                
                logger.info(f"💾 === ACTUALIZANDO RECARGA EN BD ===")
                logger.info(f"   ID: {recarga.id}")
                logger.info(f"   Estado dominio: {recarga.estado.value}")
                logger.info(f"   Estado BD: {estado_db}")
                logger.info(f"   Monto: ${recarga.monto:,.0f}")
                
                cursor.execute(
                    """
                    UPDATE recharges 
                    SET amount = %s, 
                        status = %s, 
                        wompi_reference = %s, 
                        wompi_transaction_id = %s, 
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (
                        recarga.monto,
                        estado_db,  # ✅ Estado mapeado correctamente
                        recarga.referencia_wompi,
                        None,
                        datetime.now(),
                        recarga.id
                    )
                )
                
                rows_affected = cursor.rowcount
                
                if rows_affected == 0:
                    logger.error(f"❌ No se encontró recarga con ID: {recarga.id}")
                    raise ValueError(f"No se encontró recarga con ID: {recarga.id}")
                
                conn.commit()
                
                logger.info(f"✅ Recarga actualizada exitosamente")
                logger.info(f"   Filas afectadas: {rows_affected}")
                logger.info(f"💾 === FIN ACTUALIZACIÓN ===")
                
                # ✅ VERIFICACIÓN POST-ACTUALIZACIÓN
                cursor.execute("SELECT status FROM recharges WHERE id = %s", (recarga.id,))
                verificacion = cursor.fetchone()
                if verificacion:
                    logger.info(f"🔍 Verificación: Estado en BD = {verificacion['status']}")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Error al actualizar recarga {recarga.id}: {e}", exc_info=True)
                raise
    
    def listar_todas(self, offset: int = 0, limite: int = 50) -> List[Recarga]:
        """Lista todas las recargas con paginación"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, amount, status, wompi_reference, wompi_transaction_id,
                       created_at, updated_at 
                FROM recharges 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
                """,
                (limite, offset)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_recarga(row) for row in rows if row]
    
    def _map_row_to_recarga(self, row: dict) -> Optional[Recarga]:
        """Mapea una fila de la DB a un objeto Recarga"""
        if not row:
            return None
        
        try:
            estado = self._map_db_to_estado(row["status"])
            
            return Recarga(
                id=str(row["id"]),
                monto=float(row["amount"]),
                usuario_id=str(row["user_id"]),
                estado=estado,
                referencia_wompi=row["wompi_reference"],
                url_pago=None,
                fecha_creacion=row["created_at"],
                fecha_actualizacion=row["updated_at"]
            )
        except Exception as e:
            logger.error(f"❌ Error mapeando fila a Recarga: {e}, row: {row}", exc_info=True)
            return None
    
    def _map_estado_to_db(self, estado: EstadoRecarga) -> str:
        """
        ✅ CORREGIDO: Mapea estados del dominio a valores de BD
        IMPORTANTE: Verifica que estos valores coincidan con tu tabla
        """
        # Si tu tabla tiene ENUM o constraint, ajusta estos valores
        mapping = {
            EstadoRecarga.PENDIENTE: "PENDING",
            EstadoRecarga.APROBADA: "APPROVED",  # ⚠️ O "COMPLETED" si tu BD usa ese valor
            EstadoRecarga.RECHAZADA: "REJECTED",
            EstadoRecarga.CANCELADA: "CANCELLED"
        }
        
        resultado = mapping.get(estado, estado.value)
        logger.debug(f"Mapeo estado: {estado.value} → {resultado}")
        return resultado
    
    def _map_db_to_estado(self, db_status: str) -> EstadoRecarga:
        """
        ✅ CORREGIDO: Mapea valores de BD a estados del dominio
        """
        # Normalizar a mayúsculas para comparación
        db_status_upper = db_status.upper() if db_status else ""
        
        mapping = {
            "PENDING": EstadoRecarga.PENDIENTE,
            "APPROVED": EstadoRecarga.APROBADA,
            "COMPLETED": EstadoRecarga.APROBADA,  # ⚠️ Por si tu BD usa COMPLETED
            "REJECTED": EstadoRecarga.RECHAZADA,
            "CANCELLED": EstadoRecarga.CANCELADA,
            # Compatibilidad con español
            "PENDIENTE": EstadoRecarga.PENDIENTE,
            "APROBADA": EstadoRecarga.APROBADA,
            "RECHAZADA": EstadoRecarga.RECHAZADA,
            "CANCELADA": EstadoRecarga.CANCELADA
        }
        
        resultado = mapping.get(db_status_upper, EstadoRecarga.PENDIENTE)
        logger.debug(f"Mapeo DB: {db_status} → {resultado.value}")
        return resultado