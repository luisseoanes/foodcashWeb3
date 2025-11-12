# domain/services/recarga_service.py

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import logging

from domain.models.recarga import Recarga, EstadoRecarga
from domain.repositories.recarga_repository import RecargaRepository
from domain.repositories.estudiante_repository import EstudianteRepository
from domain.repositories.usuario_repository import UsuarioRepository
from domain.exceptions.exceptions import UsuarioNoEncontradoError

logger = logging.getLogger(__name__)

class RecargaService:
    """
    Servicio de dominio para manejar la lógica de negocio de recargas
    ✅ CORREGIDO: Manejo de transacciones y estados
    """
    
    def __init__(self, 
                 recarga_repository: RecargaRepository,
                 usuario_repository: UsuarioRepository,
                 estudiante_repository: EstudianteRepository): 
        self.recarga_repository = recarga_repository
        self.usuario_repository = usuario_repository
        self.estudiante_repository = estudiante_repository
    
    def crear_recarga_pendiente(self, usuario_id: str, monto: float) -> Recarga:
        """Crea una recarga en estado pendiente"""
        
        if not usuario_id or not usuario_id.strip():
            raise ValueError("El usuario_id es requerido")
        
        usuario_id = str(usuario_id)
        
        # Validar que el usuario existe
        try:
            usuario = self.usuario_repository.buscar_por_id(usuario_id)
            if not usuario:
                raise UsuarioNoEncontradoError(f"Usuario con ID {usuario_id} no encontrado")
        except Exception as e:
            raise UsuarioNoEncontradoError(f"Error al validar usuario: {str(e)}")
        
        # Validar monto
        try:
            monto = float(monto)
        except (ValueError, TypeError):
            raise ValueError("El monto debe ser un número válido")
        
        MONTO_MINIMO = 10000
        MONTO_MAXIMO = 1000000
        
        if monto < MONTO_MINIMO:
            raise ValueError(f"El monto mínimo de recarga es ${MONTO_MINIMO:,.0f} COP")
        
        if monto > MONTO_MAXIMO:
            raise ValueError(f"El monto máximo de recarga es ${MONTO_MAXIMO:,.0f} COP")
        
        try:
            recarga = Recarga(
                monto=monto,
                usuario_id=usuario_id,
                estado=EstadoRecarga.PENDIENTE
            )
            
            self.recarga_repository.guardar(recarga)
            return recarga
            
        except Exception as e:
            raise ValueError(f"Error al crear la recarga: {str(e)}")
    
    def obtener_configuracion_widget(self, recarga_id: str) -> dict:
        """Obtiene la configuración necesaria para inicializar el widget de WOMPI"""
        recarga = self.recarga_repository.buscar_por_id(recarga_id)
        if not recarga:
            raise ValueError(f"Recarga con ID {recarga_id} no encontrada")
        
        if recarga.estado != EstadoRecarga.PENDIENTE:
            raise ValueError(f"La recarga ya fue procesada. Estado actual: {recarga.estado.value}")
        
        usuario = self.usuario_repository.buscar_por_id(recarga.usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {recarga.usuario_id} no encontrado")
        
        if not recarga.referencia_wompi:
            referencia = self._generar_referencia_unica(recarga.id, recarga.usuario_id)
            recarga.establecer_referencia_wompi(referencia)
            self.recarga_repository.actualizar(recarga)
        else:
            referencia = recarga.referencia_wompi
        
        return {
            "reference": referencia,
            "amount_in_cents": int(float(recarga.monto) * 100),
            "currency": "COP",
            "customer_email": usuario.usuario,
            "customer_data": {
                "email": usuario.usuario,
                "full_name": getattr(usuario, 'nombre', f"Usuario {usuario.usuario}"),
                "phone_number": getattr(usuario, 'telefono', "")
            },
            "redirect_url": None,
            "payment_description": f"Recarga de saldo - ${recarga.monto:,.0f} COP"
        }
    
    def procesar_webhook_pago(self, referencia_wompi: str, estado_pago: str, 
                             transaction_id: str = None, finalized_at: str = None) -> Optional[Recarga]:
        """
        ✅ CORREGIDO: Procesa el webhook con manejo de transacciones
        """
        logger.info(f"🔔 === PROCESANDO WEBHOOK ===")
        logger.info(f"📋 Reference: {referencia_wompi}")
        logger.info(f"📊 Estado WOMPI: {estado_pago}")
        logger.info(f"🆔 Transaction ID: {transaction_id}")
        
        # Buscar la recarga por referencia de WOMPI
        recarga = self.recarga_repository.buscar_por_referencia_wompi(referencia_wompi)
        if not recarga:
            logger.error(f"❌ Recarga con referencia {referencia_wompi} no encontrada")
            raise ValueError(f"Recarga con referencia WOMPI {referencia_wompi} no encontrada")
        
        logger.info(f"✅ Recarga encontrada: ID={recarga.id}")
        logger.info(f"📍 Estado ACTUAL en BD: {recarga.estado.value}")
        
        # Solo procesar si está pendiente
        if not recarga.es_procesable():
            logger.warning(f"⚠️ Recarga ya procesada: {recarga.estado.value}")
            return recarga  # ✅ Retornar sin error si ya fue procesada
        
        # ✅ MAPEO CORRECTO DE ESTADOS DE WOMPI
        estado_anterior = recarga.estado
        
        try:
            if estado_pago in ["APPROVED", "approved"]:
                logger.info("💰 ===== APROBANDO RECARGA =====")
                self._aprobar_recarga(recarga)
                logger.info(f"✅ Recarga aprobada: {recarga.id}")
                
            elif estado_pago in ["DECLINED", "declined"]:
                logger.info("❌ Rechazando recarga...")
                recarga.rechazar()
                
            elif estado_pago in ["VOIDED", "voided"]:
                logger.info("🚫 Cancelando recarga...")
                recarga.cancelar()
                
            else:
                logger.warning(f"⚠️ Estado WOMPI desconocido: {estado_pago}")
                raise ValueError(f"Estado de pago desconocido: {estado_pago}")
            
            # ✅ CRÍTICO: ACTUALIZAR EN BASE DE DATOS
            logger.info(f"💾 Guardando cambios en BD...")
            logger.info(f"   Estado: {estado_anterior.value} → {recarga.estado.value}")
            
            self.recarga_repository.actualizar(recarga)
            
            logger.info(f"✅ Recarga actualizada exitosamente en BD")
            logger.info(f"📊 Estado final: {recarga.estado.value}")
            logger.info(f"🔔 === FIN PROCESAMIENTO WEBHOOK ===")
            
            return recarga
            
        except Exception as e:
            logger.error(f"❌ Error procesando webhook: {str(e)}", exc_info=True)
            raise ValueError(f"Error al procesar webhook: {str(e)}")
    
    def verificar_estado_recarga(self, recarga_id: str) -> Recarga:
        """Verifica el estado actual de una recarga"""
        recarga = self.recarga_repository.buscar_por_id(recarga_id)
        if not recarga:
            raise ValueError(f"Recarga con ID {recarga_id} no encontrada")
        return recarga
    
    def cancelar_recarga_pendiente(self, recarga_id: str) -> Recarga:
        """Cancela una recarga que está pendiente"""
        recarga = self.recarga_repository.buscar_por_id(recarga_id)
        if not recarga:
            raise ValueError(f"Recarga con ID {recarga_id} no encontrada")
        
        if not recarga.es_procesable():
            raise ValueError(f"No se puede cancelar una recarga en estado {recarga.estado.value}")
        
        recarga.cancelar()
        self.recarga_repository.actualizar(recarga)
        return recarga
    
    def obtener_recargas_usuario(self, usuario_id: str, limite: int = 10) -> List[Recarga]:
        """Obtiene las recargas de un usuario específico"""
        usuario = self.usuario_repository.buscar_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {usuario_id} no encontrado")
        
        return self.recarga_repository.buscar_por_usuario(usuario_id, limite)
    
    def obtener_recarga_por_id(self, recarga_id: str) -> Optional[Recarga]:
        """Obtiene una recarga por su ID"""
        return self.recarga_repository.buscar_por_id(recarga_id)
    
    def confirmar_recarga_manual(self, recarga_id: str, nuevo_estado: EstadoRecarga) -> Recarga:
        """Permite confirmar manualmente una recarga (función de administrador)"""
        recarga = self.recarga_repository.buscar_por_id(recarga_id)
        if not recarga:
            raise ValueError(f"Recarga con ID {recarga_id} no encontrada")
        
        if nuevo_estado == EstadoRecarga.APROBADA:
            self._aprobar_recarga(recarga)
        elif nuevo_estado == EstadoRecarga.RECHAZADA:
            recarga.rechazar()
        elif nuevo_estado == EstadoRecarga.CANCELADA:
            recarga.cancelar()
        
        self.recarga_repository.actualizar(recarga)
        return recarga
    
    def _aprobar_recarga(self, recarga: Recarga) -> None:
        """
        ✅ CORREGIDO: Aprueba la recarga con manejo de transacciones
        """
        logger.info(f"💰 === APROBANDO RECARGA {recarga.id} ===")
        
        try:
            # 1️⃣ Cambiar estado de la recarga PRIMERO
            estado_anterior = recarga.estado
            recarga.aprobar()
            logger.info(f"   Estado cambiado: {estado_anterior.value} → {recarga.estado.value}")
            
            # 2️⃣ Actualizar saldo del ESTUDIANTE
            estudiante_id = int(recarga.usuario_id)
            logger.info(f"👤 Buscando estudiante ID: {estudiante_id}")
            
            estudiante = self.estudiante_repository.obtener_por_id(estudiante_id)
            if not estudiante:
                logger.error(f"❌ Estudiante {estudiante_id} no encontrado")
                # Rollback del estado
                recarga.estado = estado_anterior
                raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante_id} no encontrado")
            
            saldo_anterior = estudiante.saldo
            nuevo_saldo = saldo_anterior + Decimal(str(recarga.monto))
            
            logger.info(f"💵 Actualizando saldo:")
            logger.info(f"   Anterior: ${saldo_anterior:,.0f}")
            logger.info(f"   Recarga:  +${recarga.monto:,.0f}")
            logger.info(f"   Nuevo:    ${nuevo_saldo:,.0f}")
            
            # 3️⃣ Actualizar saldo en la base de datos
            estudiante_actualizado = self.estudiante_repository.actualizar_saldo(
                estudiante_id=estudiante_id,
                nuevo_saldo=nuevo_saldo
            )
            
            if not estudiante_actualizado:
                logger.error("❌ Error al actualizar saldo en BD")
                # Rollback del estado
                recarga.estado = estado_anterior
                raise Exception("Error al actualizar saldo del estudiante en la base de datos")
            
            logger.info(f"✅ Saldo actualizado exitosamente")
            logger.info(f"💰 === FIN APROBACIÓN RECARGA ===")
                
        except UsuarioNoEncontradoError:
            raise
        except Exception as e:
            logger.error(f"❌ Error en _aprobar_recarga: {str(e)}", exc_info=True)
            # Asegurar rollback
            recarga.estado = estado_anterior if 'estado_anterior' in locals() else EstadoRecarga.PENDIENTE
            raise Exception(f"Error al aprobar recarga: {str(e)}")
    
    def _generar_referencia_unica(self, recarga_id: str, usuario_id: str) -> str:
        """Genera una referencia única para la transacción"""
        timestamp = int(datetime.now().timestamp())
        # ✅ Formato limpio sin caracteres especiales
        return f"REC{recarga_id.replace('-', '')[:8]}{usuario_id}{timestamp}"