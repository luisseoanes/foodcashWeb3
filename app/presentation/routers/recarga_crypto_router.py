# presentation/routers/recarga_crypto_router.py

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging

from application.dto.recarga_crypto_dto import (
    CrearRecargaCryptoRequest,
    ConfirmarRecargaCryptoRequest,
    RecargaCryptoResponse,
    InstruccionesPagoCryptoResponse,
    EstadoVerificacionResponse,
    ConfiguracionCryptoResponse,
    TipoCrypto,
    EstadoRecargaCrypto
)
from domain.services.recarga_crypto_service import RecargaCryptoService
from infrastructure.service.celo_service import CeloService
from infrastructure.database.postgresql_repository import (
    PostgresqlConnectionManager,
    PostgresqlUsuarioRepository
)
# Necesitarás crear este repositorio
# from infrastructure.database.postgresql_recarga_crypto_repository import PostgresqlRecargaCryptoRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/recargas/crypto",
    tags=["Recargas Crypto"],
    responses={404: {"description": "Not found"}}
)

# Dependencias
def get_celo_service() -> CeloService:
    """Crea instancia del servicio de Celo"""
    # Por defecto usar Mainnet. Cambiar a True para testnet
    use_testnet = False  # Cambiar según configuración
    return CeloService(use_testnet=use_testnet)

def get_recarga_crypto_service(
    celo_service: CeloService = Depends(get_celo_service)
) -> RecargaCryptoService:
    """Crea instancia del servicio de recargas crypto"""
    connection_manager = PostgresqlConnectionManager()
    usuario_repo = PostgresqlUsuarioRepository(connection_manager)
    
    # ✅ REPOSITORIO POSTGRESQL IMPLEMENTADO
    from infrastructure.database.postgresql_recarga_crypto_repository import PostgresqlRecargaCryptoRepository
    recarga_crypto_repo = PostgresqlRecargaCryptoRepository(connection_manager)
    
    return RecargaCryptoService(
        celo_service=celo_service,
        recarga_crypto_repository=recarga_crypto_repo,
        usuario_repository=usuario_repo
    )


@router.post(
    "/iniciar",
    response_model=InstruccionesPagoCryptoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar recarga con criptomonedas",
    description="""
    Crea una nueva recarga con criptomonedas (cCOP) y retorna las instrucciones de pago.
    
    **Flujo:**
    1. El usuario especifica el monto en COP
    2. El sistema calcula el monto equivalente en cCOP (1:1)
    3. Se genera una dirección de destino (FoodCash)
    4. Se retornan instrucciones para que el usuario realice el pago desde su wallet
    """
)
async def iniciar_recarga_crypto(
    request: CrearRecargaCryptoRequest,
    service: RecargaCryptoService = Depends(get_recarga_crypto_service)
) -> InstruccionesPagoCryptoResponse:
    """
    Inicia una recarga con criptomonedas.
    """
    try:
        logger.info(f"Iniciando recarga crypto - Usuario: {request.usuario_id}, Monto: {request.monto_cop} COP")
        
        # Crear recarga pendiente
        recarga = service.crear_recarga_pendiente(
            usuario_id=request.usuario_id,
            monto_cop=request.monto_cop,
            tipo_crypto=request.tipo_crypto
        )
        
        # Obtener instrucciones de pago
        instrucciones = service.obtener_instrucciones_pago(recarga.id)
        
        return InstruccionesPagoCryptoResponse(**instrucciones)
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConnectionError as e:
        logger.error(f"Error de conexión: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de blockchain no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post(
    "/confirmar",
    response_model=EstadoVerificacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmar pago con hash de transacción",
    description="""
    Confirma un pago verificando la transacción en la blockchain de Celo.
    
    **Flujo:**
    1. El usuario realiza el pago desde su wallet
    2. El usuario copia el hash de la transacción
    3. El usuario envía el hash a través de este endpoint
    4. El sistema verifica la transacción en la blockchain
    5. Si es válida, se acredita el saldo al usuario
    """
)
async def confirmar_pago_crypto(
    request: ConfirmarRecargaCryptoRequest,
    service: RecargaCryptoService = Depends(get_recarga_crypto_service)
) -> EstadoVerificacionResponse:
    """
    Confirma un pago crypto verificando la transacción en blockchain.
    """
    try:
        logger.info(f"Confirmando pago - Recarga: {request.recarga_id}, TX: {request.tx_hash}")
        
        # Verificar y confirmar pago
        exito, mensaje, recarga = service.confirmar_pago(
            recarga_id=request.recarga_id,
            tx_hash=request.tx_hash,
            wallet_address=request.wallet_address
        )
        
        if not exito:
            # Si no fue exitoso pero tenemos la recarga, retornar el estado actual
            if recarga:
                return EstadoVerificacionResponse(
                    recarga_id=recarga.id,
                    estado=EstadoRecargaCrypto(recarga.estado.value),
                    verificada=False,
                    mensaje=mensaje,
                    detalles_blockchain=None
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=mensaje
                )
        
        # Éxito - retornar estado verificado
        return EstadoVerificacionResponse(
            recarga_id=recarga.id,
            estado=EstadoRecargaCrypto(recarga.estado.value),
            verificada=True,
            mensaje=mensaje,
            detalles_blockchain=recarga.detalles_blockchain
        )
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirmando pago: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verificando transacción"
        )


@router.get(
    "/{recarga_id}",
    response_model=RecargaCryptoResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalles de una recarga",
    description="Obtiene los detalles completos de una recarga crypto por su ID"
)
async def obtener_recarga(
    recarga_id: str,
    service: RecargaCryptoService = Depends(get_recarga_crypto_service)
) -> RecargaCryptoResponse:
    """
    Obtiene los detalles de una recarga por su ID.
    """
    try:
        recarga = service.obtener_recarga_por_id(recarga_id)
        
        if not recarga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recarga {recarga_id} no encontrada"
            )
        
        return RecargaCryptoResponse(
            id=recarga.id,
            usuario_id=recarga.usuario_id,
            monto_cop=recarga.monto_cop,
            monto_crypto=recarga.monto_crypto,
            tipo_crypto=TipoCrypto(recarga.tipo_crypto.value),
            tasa_conversion=recarga.tasa_conversion,
            estado=EstadoRecargaCrypto(recarga.estado.value),
            tx_hash=recarga.tx_hash,
            wallet_address=recarga.wallet_address,
            direccion_destino=recarga.direccion_destino,
            fecha_creacion=recarga.fecha_creacion,
            fecha_actualizacion=recarga.fecha_actualizacion,
            fecha_confirmacion=recarga.fecha_confirmacion,
            mensaje=recarga.mensaje
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo recarga: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/{recarga_id}/estado",
    response_model=EstadoVerificacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado de verificación",
    description="""
    Consulta el estado actual de verificación de una recarga.
    Útil para polling desde el frontend.
    """
)
async def consultar_estado(
    recarga_id: str,
    service: RecargaCryptoService = Depends(get_recarga_crypto_service)
) -> EstadoVerificacionResponse:
    """
    Consulta el estado de verificación de una recarga.
    """
    try:
        estado = service.obtener_estado_verificacion(recarga_id)
        return EstadoVerificacionResponse(**estado)
        
    except Exception as e:
        logger.error(f"Error consultando estado: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error consultando estado"
        )


@router.get(
    "/usuario/{usuario_id}/historial",
    response_model=List[RecargaCryptoResponse],
    status_code=status.HTTP_200_OK,
    summary="Historial de recargas crypto de un usuario",
    description="Obtiene todas las recargas con criptomonedas realizadas por un usuario"
)
async def obtener_historial_usuario(
    usuario_id: int,
    service: RecargaCryptoService = Depends(get_recarga_crypto_service)
) -> List[RecargaCryptoResponse]:
    """
    Obtiene el historial de recargas crypto de un usuario.
    """
    try:
        recargas = service.listar_recargas_usuario(usuario_id)
        
        return [
            RecargaCryptoResponse(
                id=r.id,
                usuario_id=r.usuario_id,
                monto_cop=r.monto_cop,
                monto_crypto=r.monto_crypto,
                tipo_crypto=TipoCrypto(r.tipo_crypto.value),
                tasa_conversion=r.tasa_conversion,
                estado=EstadoRecargaCrypto(r.estado.value),
                tx_hash=r.tx_hash,
                wallet_address=r.wallet_address,
                direccion_destino=r.direccion_destino,
                fecha_creacion=r.fecha_creacion,
                fecha_actualizacion=r.fecha_actualizacion,
                fecha_confirmacion=r.fecha_confirmacion,
                mensaje=r.mensaje
            )
            for r in recargas
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo historial"
        )


@router.get(
    "/",
    response_model=ConfiguracionCryptoResponse,
    status_code=status.HTTP_200_OK,
    summary="Configuración del sistema de pagos crypto",
    description="""
    Obtiene la configuración actual del sistema de pagos con criptomonedas.
    Incluye información sobre la red, criptomonedas soportadas y estado del servicio.
    """
)
async def obtener_configuracion(
    service: RecargaCryptoService = Depends(get_recarga_crypto_service)
) -> ConfiguracionCryptoResponse:
    """
    Obtiene la configuración del sistema de pagos crypto.
    """
    try:
        config = service.obtener_configuracion_sistema()
        return ConfiguracionCryptoResponse(**config)
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo configuración"
        )


# Endpoints de utilidad/debug

@router.get(
    "/debug/verificar-tx/{tx_hash}",
    tags=["Debug"],
    summary="Verificar transacción (DEBUG)",
    description="Endpoint de debug para verificar manualmente una transacción en Celo"
)
async def debug_verificar_transaccion(
    tx_hash: str,
    celo_service: CeloService = Depends(get_celo_service)
):
    """
    DEBUG: Verifica una transacción directamente en la blockchain.
    """
    try:
        # Obtener transacción
        tx = celo_service.obtener_transaccion(tx_hash)
        if not tx:
            return {"found": False, "message": "Transacción no encontrada"}
        
        # Obtener recibo
        receipt = celo_service.obtener_recibo_transaccion(tx_hash)
        
        return {
            "found": True,
            "transaction": tx,
            "receipt": receipt
        }
        
    except Exception as e:
        logger.error(f"Error en debug: {e}", exc_info=True)
        return {"error": str(e)}


@router.get(
    "/debug/balance/{address}",
    tags=["Debug"],
    summary="Consultar balance cCOP (DEBUG)",
    description="Endpoint de debug para consultar el balance de cCOP de una dirección"
)
async def debug_consultar_balance(
    address: str,
    celo_service: CeloService = Depends(get_celo_service)
):
    """
    DEBUG: Consulta el balance de cCOP de una dirección.
    """
    try:
        balance = celo_service.obtener_balance_ccop(address)
        return {
            "address": address,
            "balance_ccop": float(balance),
            "network": "Testnet" if celo_service.use_testnet else "Mainnet"
        }
        
    except Exception as e:
        logger.error(f"Error consultando balance: {e}", exc_info=True)
        return {"error": str(e)}