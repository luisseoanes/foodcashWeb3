# domain/services/recarga_crypto_service.py

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
import secrets

from domain.models.recarga_crypto import RecargaCrypto, TipoCrypto, EstadoRecargaCrypto
from infrastructure.service.celo_service import CeloService

logger = logging.getLogger(__name__)

class RecargaCryptoService:
    """
    Servicio de dominio para gestionar recargas con criptomonedas.
    Maneja la lógica de negocio relacionada con pagos en Celo (cCOP).
    """
    
    def __init__(self, celo_service: CeloService, recarga_crypto_repository, usuario_repository):
        """
        Inicializa el servicio.
        
        Args:
            celo_service: Servicio para interactuar con Celo blockchain
            recarga_crypto_repository: Repositorio para persistir recargas crypto
            usuario_repository: Repositorio de usuarios
        """
        self.celo_service = celo_service
        self.recarga_crypto_repository = recarga_crypto_repository
        self.usuario_repository = usuario_repository
        
        # Configuración
        self.tiempo_expiracion_minutos = 30
        self.monto_minimo_cop = Decimal("1000")
        self.monto_maximo_cop = Decimal("5000000")
    
    def _generar_id_recarga(self) -> str:
        """Genera un ID único para la recarga"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4).upper()
        return f"REC_CRYPTO_{timestamp}_{random_part}"
    
    def _validar_monto(self, monto: Decimal) -> None:
        """Valida que el monto esté dentro de los límites permitidos"""
        if monto < self.monto_minimo_cop:
            raise ValueError(f"El monto mínimo es {self.monto_minimo_cop} COP")
        if monto > self.monto_maximo_cop:
            raise ValueError(f"El monto máximo es {self.monto_maximo_cop} COP")
    
    def _validar_usuario_existe(self, usuario_id: int) -> None:
        """Valida que el usuario exista"""
        usuario = self.usuario_repository.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")
    
    def crear_recarga_pendiente(
        self, 
        usuario_id: int, 
        monto_cop: Decimal,
        tipo_crypto: TipoCrypto = TipoCrypto.CCOP
    ) -> RecargaCrypto:
        """
        Crea una nueva recarga pendiente con criptomonedas.
        
        Args:
            usuario_id: ID del usuario que hace la recarga
            monto_cop: Monto en pesos colombianos
            tipo_crypto: Tipo de criptomoneda (por defecto cCOP)
            
        Returns:
            RecargaCrypto creada
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        logger.info(f"Creando recarga crypto - Usuario: {usuario_id}, Monto: {monto_cop} COP")
        
        # Validaciones
        self._validar_monto(monto_cop)
        self._validar_usuario_existe(usuario_id)
        
        # Verificar que el servicio de Celo esté disponible
        if not self.celo_service.verificar_conexion():
            raise ConnectionError("Servicio de Celo no disponible")
        
        # Obtener dirección de destino (FoodCash)
        direccion_destino = self.celo_service.foodcash_address
        if not direccion_destino:
            raise ValueError("Dirección de recepción de FoodCash no configurada")
        
        # Convertir COP a crypto (para cCOP es 1:1)
        if tipo_crypto == TipoCrypto.CCOP:
            monto_crypto = self.celo_service.convertir_cop_a_ccop(monto_cop)
            tasa_conversion = Decimal("1.0")
        else:
            # Para otros tipos de crypto, implementar conversión aquí
            raise NotImplementedError(f"Conversión para {tipo_crypto.value} no implementada")
        
        # Crear entidad de recarga
        recarga = RecargaCrypto(
            id=self._generar_id_recarga(),
            usuario_id=usuario_id,
            monto_cop=monto_cop,
            monto_crypto=monto_crypto,
            tipo_crypto=tipo_crypto,
            tasa_conversion=tasa_conversion,
            estado=EstadoRecargaCrypto.PENDIENTE,
            direccion_destino=direccion_destino,
            fecha_creacion=datetime.utcnow(),
            fecha_actualizacion=datetime.utcnow(),
            mensaje="Esperando transacción del usuario"
        )
        
        # Guardar en repositorio
        self.recarga_crypto_repository.guardar(recarga)
        
        logger.info(f"Recarga crypto creada: {recarga.id}")
        return recarga
    
    def obtener_instrucciones_pago(self, recarga_id: str) -> dict:
        """
        Obtiene las instrucciones de pago para una recarga.
        
        Args:
            recarga_id: ID de la recarga
            
        Returns:
            Diccionario con instrucciones y detalles
        """
        recarga = self.recarga_crypto_repository.obtener_por_id(recarga_id)
        if not recarga:
            raise ValueError(f"Recarga {recarga_id} no encontrada")
        
        if not recarga.esta_pendiente:
            raise ValueError(f"La recarga {recarga_id} no está pendiente")
        
        # Calcular tiempo de expiración
        tiempo_restante = self._calcular_tiempo_expiracion(recarga)
        
        instrucciones = [
            f"1. Abre tu wallet de Celo (Valora, MetaMask u otra compatible)",
            f"2. Asegúrate de estar en la red de Celo Mainnet",
            f"3. Envía exactamente {recarga.monto_crypto} {recarga.tipo_crypto.value} a la siguiente dirección:",
            f"   {recarga.direccion_destino}",
            f"4. Una vez realizada la transacción, copia el hash (código de la transacción)",
            f"5. Regresa a FoodCash y confirma tu pago pegando el hash de transacción"
        ]
        
        info_adicional = {
            "red": "Celo Mainnet",
            "tiempo_restante_minutos": tiempo_restante,
            "fee_estimado": "< $0.01 USD",
            "tiempo_confirmacion": "~5 segundos",
            "token_contract": self.celo_service.CCOP_CONTRACT_ADDRESS if recarga.tipo_crypto == TipoCrypto.CCOP else None
        }
        
        return {
            "recarga_id": recarga.id,
            "monto_cop": recarga.monto_cop,
            "monto_crypto": recarga.monto_crypto,
            "tipo_crypto": recarga.tipo_crypto.value,
            "direccion_destino": recarga.direccion_destino,
            "tiempo_expiracion_minutos": tiempo_restante,
            "instrucciones": instrucciones,
            "info_adicional": info_adicional
        }
    
    def _calcular_tiempo_expiracion(self, recarga: RecargaCrypto) -> int:
        """Calcula el tiempo restante antes de que expire la recarga"""
        tiempo_transcurrido = datetime.utcnow() - recarga.fecha_creacion
        minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60
        tiempo_restante = max(0, self.tiempo_expiracion_minutos - int(minutos_transcurridos))
        return tiempo_restante
    
    def confirmar_pago(
        self, 
        recarga_id: str, 
        tx_hash: str, 
        wallet_address: str
    ) -> Tuple[bool, str, Optional[RecargaCrypto]]:
        """
        Confirma un pago verificando la transacción en la blockchain.
        
        Args:
            recarga_id: ID de la recarga
            tx_hash: Hash de la transacción
            wallet_address: Dirección de la wallet que envió el pago
            
        Returns:
            Tuple (éxito, mensaje, recarga_actualizada)
        """
        logger.info(f"Confirmando pago - Recarga: {recarga_id}, TX: {tx_hash}")
        
        # Obtener recarga
        recarga = self.recarga_crypto_repository.obtener_por_id(recarga_id)
        if not recarga:
            return False, f"Recarga {recarga_id} no encontrada", None
        
        # Verificar que pueda ser verificada
        if not recarga.puede_ser_verificada:
            return False, f"La recarga ya fue procesada (estado: {recarga.estado.value})", recarga
        
        # Verificar que no haya expirado
        if self._calcular_tiempo_expiracion(recarga) <= 0:
            recarga.marcar_como_rechazada("Tiempo de pago expirado")
            self.recarga_crypto_repository.actualizar(recarga)
            return False, "Tiempo de pago expirado. Por favor, crea una nueva recarga.", recarga
        
        # Marcar como verificando
        recarga.marcar_como_verificando(tx_hash, wallet_address)
        self.recarga_crypto_repository.actualizar(recarga)
        
        # Verificar pago en blockchain
        try:
            es_valido, mensaje_error, detalles = self.celo_service.verificar_pago_recibido(
                tx_hash=tx_hash,
                monto_esperado=recarga.monto_crypto
            )
            
            if not es_valido:
                recarga.marcar_como_rechazada(mensaje_error or "Pago no válido")
                self.recarga_crypto_repository.actualizar(recarga)
                return False, mensaje_error or "Pago no válido", recarga
            
            # Pago válido - marcar como confirmada
            recarga.marcar_como_confirmada(detalles)
            self.recarga_crypto_repository.actualizar(recarga)
            
            # Acreditar saldo al usuario
            try:
                usuario = self.usuario_repository.obtener_por_id(recarga.usuario_id)
                if not usuario:
                    raise ValueError("Usuario no encontrado")
                
                # Acreditar saldo
                usuario.saldo += recarga.monto_cop
                self.usuario_repository.actualizar(usuario)
                
                # Marcar como completada
                recarga.marcar_como_completada()
                self.recarga_crypto_repository.actualizar(recarga)
                
                logger.info(f"Recarga {recarga.id} completada exitosamente")
                return True, "Pago verificado y saldo acreditado exitosamente", recarga
                
            except Exception as e:
                logger.error(f"Error acreditando saldo: {e}", exc_info=True)
                recarga.marcar_como_error(f"Error acreditando saldo: {str(e)}")
                self.recarga_crypto_repository.actualizar(recarga)
                return False, "Pago verificado pero error acreditando saldo. Contacta soporte.", recarga
        
        except Exception as e:
            logger.error(f"Error verificando pago: {e}", exc_info=True)
            recarga.marcar_como_error(f"Error de verificación: {str(e)}")
            self.recarga_crypto_repository.actualizar(recarga)
            return False, "Error verificando transacción. Intenta nuevamente.", recarga
    
    def obtener_recarga_por_id(self, recarga_id: str) -> Optional[RecargaCrypto]:
        """Obtiene una recarga por su ID"""
        return self.recarga_crypto_repository.obtener_por_id(recarga_id)
    
    def listar_recargas_usuario(self, usuario_id: int) -> List[RecargaCrypto]:
        """Lista todas las recargas crypto de un usuario"""
        return self.recarga_crypto_repository.listar_por_usuario(usuario_id)
    
    def obtener_estado_verificacion(self, recarga_id: str) -> dict:
        """
        Obtiene el estado actual de verificación de una recarga.
        
        Args:
            recarga_id: ID de la recarga
            
        Returns:
            Diccionario con el estado y detalles
        """
        recarga = self.recarga_crypto_repository.obtener_por_id(recarga_id)
        if not recarga:
            return {
                "recarga_id": recarga_id,
                "estado": "no_encontrada",
                "verificada": False,
                "mensaje": "Recarga no encontrada"
            }
        
        return {
            "recarga_id": recarga.id,
            "estado": recarga.estado.value,
            "verificada": recarga.esta_completada,
            "mensaje": recarga.mensaje or "Sin mensaje",
            "detalles_blockchain": recarga.detalles_blockchain if recarga.esta_completada else None
        }
    
    def obtener_configuracion_sistema(self) -> dict:
        """Obtiene la configuración del sistema de pagos crypto"""
        info_red = self.celo_service.obtener_info_red()
        
        return {
            "criptomonedas_soportadas": [TipoCrypto.CCOP.value],  # Por ahora solo cCOP
            "red_activa": "Celo Testnet" if self.celo_service.use_testnet else "Celo Mainnet",
            "direccion_recepcion": self.celo_service.foodcash_address,
            "estado_servicio": "operativo" if info_red.get('connected') else "no_disponible",
            "info_red": info_red,
            "configuracion": {
                "monto_minimo_cop": float(self.monto_minimo_cop),
                "monto_maximo_cop": float(self.monto_maximo_cop),
                "tiempo_expiracion_minutos": self.tiempo_expiracion_minutos
            }
        }