from typing import List, Optional
from datetime import datetime
import logging

from domain.models.recarga_crypto import RecargaCrypto, TipoCrypto, EstadoRecargaCrypto
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager
from psycopg2.extras import RealDictCursor
import json

logger = logging.getLogger(__name__)

class PostgresqlRecargaCryptoRepository:
    """
    Repositorio PostgreSQL para recargas con criptomonedas (cCOP).
    Sigue el mismo patrón que los otros repositorios del proyecto.
    """
    
    def __init__(self, connection_manager: PostgresqlConnectionManager):
        self.connection_manager = connection_manager
    
    def guardar(self, recarga: RecargaCrypto) -> RecargaCrypto:
        """Guarda una nueva recarga crypto en la base de datos"""
        query = """
            INSERT INTO recargas_crypto (
                id, usuario_id, monto_cop, monto_crypto, tipo_crypto,
                tasa_conversion, estado, direccion_destino, tx_hash,
                wallet_address, block_number, fecha_creacion, 
                fecha_actualizacion, fecha_confirmacion, mensaje, detalles_blockchain
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, usuario_id, monto_cop, monto_crypto, tipo_crypto,
                      tasa_conversion, estado, direccion_destino, tx_hash,
                      wallet_address, block_number, fecha_creacion,
                      fecha_actualizacion, fecha_confirmacion, mensaje, detalles_blockchain
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                try:
                    logger.info(f"💾 Guardando recarga crypto: {recarga.id}")
                    
                    # Convertir detalles_blockchain a JSON
                    detalles_json = json.dumps(recarga.detalles_blockchain) if recarga.detalles_blockchain else None
                    
                    cur.execute(query, (
                        recarga.id,
                        recarga.usuario_id,
                        float(recarga.monto_cop),
                        float(recarga.monto_crypto),
                        recarga.tipo_crypto.value,
                        float(recarga.tasa_conversion),
                        recarga.estado.value,
                        recarga.direccion_destino,
                        recarga.tx_hash,
                        recarga.wallet_address,
                        recarga.block_number,
                        recarga.fecha_creacion,
                        recarga.fecha_actualizacion,
                        recarga.fecha_confirmacion,
                        recarga.mensaje,
                        detalles_json
                    ))
                    conn.commit()
                    
                    result = cur.fetchone()
                    logger.info(f"✅ Recarga crypto guardada exitosamente: {recarga.id}")
                    
                    return self._map_row_to_recarga(result)
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"❌ Error al guardar recarga crypto: {e}", exc_info=True)
                    raise
    
    def actualizar(self, recarga: RecargaCrypto) -> RecargaCrypto:
        """Actualiza una recarga crypto existente"""
        query = """
            UPDATE recargas_crypto 
            SET monto_cop = %s,
                monto_crypto = %s,
                tipo_crypto = %s,
                tasa_conversion = %s,
                estado = %s,
                direccion_destino = %s,
                tx_hash = %s,
                wallet_address = %s,
                block_number = %s,
                fecha_actualizacion = %s,
                fecha_confirmacion = %s,
                mensaje = %s,
                detalles_blockchain = %s
            WHERE id = %s
            RETURNING id, usuario_id, monto_cop, monto_crypto, tipo_crypto,
                      tasa_conversion, estado, direccion_destino, tx_hash,
                      wallet_address, block_number, fecha_creacion,
                      fecha_actualizacion, fecha_confirmacion, mensaje, detalles_blockchain
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                try:
                    logger.info(f"💾 Actualizando recarga crypto: {recarga.id}")
                    logger.info(f"   Estado: {recarga.estado.value}")
                    
                    # Convertir detalles_blockchain a JSON
                    detalles_json = json.dumps(recarga.detalles_blockchain) if recarga.detalles_blockchain else None
                    
                    cur.execute(query, (
                        float(recarga.monto_cop),
                        float(recarga.monto_crypto),
                        recarga.tipo_crypto.value,
                        float(recarga.tasa_conversion),
                        recarga.estado.value,
                        recarga.direccion_destino,
                        recarga.tx_hash,
                        recarga.wallet_address,
                        recarga.block_number,
                        recarga.fecha_actualizacion or datetime.utcnow(),
                        recarga.fecha_confirmacion,
                        recarga.mensaje,
                        detalles_json,
                        recarga.id
                    ))
                    conn.commit()
                    
                    if cur.rowcount == 0:
                        raise ValueError(f"Recarga con ID {recarga.id} no encontrada")
                    
                    result = cur.fetchone()
                    logger.info(f"✅ Recarga crypto actualizada exitosamente: {recarga.id}")
                    
                    return self._map_row_to_recarga(result)
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"❌ Error al actualizar recarga crypto: {e}", exc_info=True)
                    raise
    
    def obtener_por_id(self, recarga_id: str) -> Optional[RecargaCrypto]:
        """Obtiene una recarga crypto por su ID"""
        query = """
            SELECT id, usuario_id, monto_cop, monto_crypto, tipo_crypto,
                   tasa_conversion, estado, direccion_destino, tx_hash,
                   wallet_address, block_number, fecha_creacion,
                   fecha_actualizacion, fecha_confirmacion, mensaje, detalles_blockchain
            FROM recargas_crypto
            WHERE id = %s
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (recarga_id,))
                result = cur.fetchone()
                
                if result is None:
                    logger.info(f"⚠️ No se encontró recarga crypto con ID: {recarga_id}")
                    return None
                
                logger.info(f"✅ Recarga crypto encontrada: {recarga_id}")
                return self._map_row_to_recarga(result)
    
    def obtener_por_tx_hash(self, tx_hash: str) -> Optional[RecargaCrypto]:
        """Obtiene una recarga crypto por su hash de transacción"""
        query = """
            SELECT id, usuario_id, monto_cop, monto_crypto, tipo_crypto,
                   tasa_conversion, estado, direccion_destino, tx_hash,
                   wallet_address, block_number, fecha_creacion,
                   fecha_actualizacion, fecha_confirmacion, mensaje, detalles_blockchain
            FROM recargas_crypto
            WHERE tx_hash = %s
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (tx_hash,))
                result = cur.fetchone()
                
                if result is None:
                    logger.info(f"⚠️ No se encontró recarga crypto con TX: {tx_hash}")
                    return None
                
                return self._map_row_to_recarga(result)
    
    def listar_por_usuario(self, usuario_id: int) -> List[RecargaCrypto]:
        """Lista todas las recargas crypto de un usuario"""
        query = """
            SELECT id, usuario_id, monto_cop, monto_crypto, tipo_crypto,
                   tasa_conversion, estado, direccion_destino, tx_hash,
                   wallet_address, block_number, fecha_creacion,
                   fecha_actualizacion, fecha_confirmacion, mensaje, detalles_blockchain
            FROM recargas_crypto
            WHERE usuario_id = %s
            ORDER BY fecha_creacion DESC
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (usuario_id,))
                results = cur.fetchall()
                
                logger.info(f"📋 Encontradas {len(results)} recargas crypto para usuario {usuario_id}")
                
                return [self._map_row_to_recarga(result) for result in results]
    
    def listar_por_estado(self, estado: EstadoRecargaCrypto, limite: int = 100) -> List[RecargaCrypto]:
        """Lista recargas crypto por estado"""
        query = """
            SELECT id, usuario_id, monto_cop, monto_crypto, tipo_crypto,
                   tasa_conversion, estado, direccion_destino, tx_hash,
                   wallet_address, block_number, fecha_creacion,
                   fecha_actualizacion, fecha_confirmacion, mensaje, detalles_blockchain
            FROM recargas_crypto
            WHERE estado = %s
            ORDER BY fecha_creacion DESC
            LIMIT %s
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (estado.value, limite))
                results = cur.fetchall()
                
                logger.info(f"📋 Encontradas {len(results)} recargas crypto con estado {estado.value}")
                
                return [self._map_row_to_recarga(result) for result in results]
    
    def listar_todas(self, offset: int = 0, limite: int = 50) -> List[RecargaCrypto]:
        """Lista todas las recargas crypto con paginación"""
        query = """
            SELECT id, usuario_id, monto_cop, monto_crypto, tipo_crypto,
                   tasa_conversion, estado, direccion_destino, tx_hash,
                   wallet_address, block_number, fecha_creacion,
                   fecha_actualizacion, fecha_confirmacion, mensaje, detalles_blockchain
            FROM recargas_crypto
            ORDER BY fecha_creacion DESC
            LIMIT %s OFFSET %s
        """
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (limite, offset))
                results = cur.fetchall()
                
                logger.info(f"📋 Listadas {len(results)} recargas crypto (offset: {offset}, limite: {limite})")
                
                return [self._map_row_to_recarga(result) for result in results]
    
    def eliminar(self, recarga_id: str) -> bool:
        """
        Elimina una recarga crypto.
        NOTA: Considera usar eliminación lógica en lugar de física.
        """
        query = "DELETE FROM recargas_crypto WHERE id = %s"
        
        with self.connection_manager.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(query, (recarga_id,))
                    conn.commit()
                    
                    if cur.rowcount > 0:
                        logger.info(f"🗑️ Recarga crypto eliminada: {recarga_id}")
                        return True
                    else:
                        logger.warning(f"⚠️ No se encontró recarga crypto para eliminar: {recarga_id}")
                        return False
                        
                except Exception as e:
                    conn.rollback()
                    logger.error(f"❌ Error al eliminar recarga crypto: {e}", exc_info=True)
                    raise
    
    def _map_row_to_recarga(self, row: dict) -> RecargaCrypto:
        """Mapea una fila de la DB a un objeto RecargaCrypto"""
        if not row:
            return None
        
        try:
            # Parsear detalles_blockchain de JSON
            detalles = {}
            if row.get('detalles_blockchain'):
                if isinstance(row['detalles_blockchain'], str):
                    detalles = json.loads(row['detalles_blockchain'])
                elif isinstance(row['detalles_blockchain'], dict):
                    detalles = row['detalles_blockchain']
            
            return RecargaCrypto(
                id=row['id'],
                usuario_id=row['usuario_id'],
                monto_cop=row['monto_cop'],
                monto_crypto=row['monto_crypto'],
                tipo_crypto=TipoCrypto(row['tipo_crypto']),
                tasa_conversion=row['tasa_conversion'],
                estado=EstadoRecargaCrypto(row['estado']),
                direccion_destino=row['direccion_destino'],
                fecha_creacion=row['fecha_creacion'],
                fecha_actualizacion=row['fecha_actualizacion'],
                tx_hash=row.get('tx_hash'),
                wallet_address=row.get('wallet_address'),
                fecha_confirmacion=row.get('fecha_confirmacion'),
                block_number=row.get('block_number'),
                mensaje=row.get('mensaje'),
                detalles_blockchain=detalles
            )
            
        except Exception as e:
            logger.error(f"❌ Error mapeando fila a RecargaCrypto: {e}, row: {row}", exc_info=True)
            raise