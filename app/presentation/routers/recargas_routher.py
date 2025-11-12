# presentation/routers/recargas_routher.py

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
import logging
import traceback

from application.dto.recarga_dto import (
    CrearRecargaRequest,
    RecargaResponse,
    ConfiguracionWidgetResponse,
    EstadoRecargaResponse
)
from domain.services.recarga_service import RecargaService
from domain.models.recarga import EstadoRecarga
from domain.exceptions.exceptions import UsuarioNoEncontradoError
from infrastructure.service.wompi_service import WompiService
from presentation.dependencies.dependencies import get_recarga_service

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/recargas",
    tags=["recargas"],
    responses={404: {"description": "Not found"}}
)


def _snake_to_camel_widget(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea keys de snake_case a camelCase para el frontend (WidgetCheckout).
    Mantiene compatibilidad si ya vienen en camelCase.
    """
    if not cfg:
        return {}
    
    result = {
        "publicKey": cfg.get("public_key") or cfg.get("publicKey"),
        "amountInCents": cfg.get("amount_in_cents") or cfg.get("amountInCents"),
        "currency": cfg.get("currency", "COP"),
        "reference": cfg.get("reference"),
        "signature": cfg.get("signature") or cfg.get("integrity"),
    }
    
    # Campos opcionales - solo agregar si tienen valor
    optional_fields = {
        "redirectUrl": cfg.get("redirect_url") or cfg.get("redirectUrl"),
        "customerEmail": cfg.get("customer_email") or cfg.get("customerEmail"),
        "paymentDescription": cfg.get("payment_description") or cfg.get("paymentDescription"),
    }
    
    for key, value in optional_fields.items():
        if value:
            result[key] = value
    
    # customer_data y otros objetos
    customer_data = cfg.get("customer_data") or cfg.get("customerData")
    if customer_data and isinstance(customer_data, dict):
        result["customerData"] = customer_data
    
    payment_methods = cfg.get("payment_methods") or cfg.get("paymentMethods")
    if payment_methods:
        result["paymentMethods"] = payment_methods
    
    customization = cfg.get("customization")
    if customization:
        result["customization"] = customization
    
    return result


def _normalize_customer_data_for_frontend(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza customer_data de snake_case a camelCase
    y garantiza claves mínimas que el widget espera: fullName, email, phoneNumber.
    SOLO incluye campos con valores válidos.
    """
    if not customer_data or not isinstance(customer_data, dict):
        return {}

    # Mapear keys comunes - solo si tienen valor
    result = {}
    
    full_name = customer_data.get("full_name") or customer_data.get("fullName") or customer_data.get("name") or ""
    if full_name and str(full_name).strip():
        result["fullName"] = str(full_name).strip()

    email = customer_data.get("email") or customer_data.get("customer_email") or ""
    if email and str(email).strip():
        result["email"] = str(email).strip()

    phone = customer_data.get("phone_number") or customer_data.get("phoneNumber") or customer_data.get("phone") or ""
    if phone and str(phone).strip():
        result["phoneNumber"] = str(phone).strip()

    # Otros campos opcionales
    phone_prefix = customer_data.get("phone_number_prefix") or customer_data.get("phoneNumberPrefix") or ""
    if phone_prefix and str(phone_prefix).strip():
        result["phoneNumberPrefix"] = str(phone_prefix).strip()

    legal_id = customer_data.get("legal_id") or customer_data.get("legalId") or ""
    if legal_id and str(legal_id).strip():
        result["legalId"] = str(legal_id).strip()

    legal_id_type = customer_data.get("legal_id_type") or customer_data.get("legalIdType") or ""
    if legal_id_type and str(legal_id_type).strip():
        result["legalIdType"] = str(legal_id_type).strip()

    return result


@router.post("/iniciar", response_model=ConfiguracionWidgetResponse, status_code=status.HTTP_201_CREATED)
async def iniciar_recarga(
    request: CrearRecargaRequest,
    recarga_service: RecargaService = Depends(get_recarga_service),
):
    """
    Crea una recarga pendiente y retorna la configuración para el widget de WOMPI.
    El frontend abrirá el WidgetCheckout usando los datos retornados.
    
    MEJORAS PARA DEBUGGING:
    1. Más logs detallados del proceso
    2. Validaciones adicionales antes de enviar al frontend
    3. Verificación de la signature generada
    """
    try:
        logger.info(f"[INICIAR_RECARGA] Usuario {request.usuario_id}, monto: {request.monto}")

        # 1) Crear recarga pendiente (servicio de dominio)
        recarga = recarga_service.crear_recarga_pendiente(
            usuario_id=request.usuario_id,
            monto=request.monto
        )
        logger.info(f"[RECARGA_CREADA] ID: {recarga.id}")

        # 2) Obtener configuración del domain service (estructura interna)
        config_recarga = recarga_service.obtener_configuracion_widget(recarga.id)
        logger.debug("[CONFIG_DOMAIN] Configuración obtenida: %s", {
            k: (v if k != 'customer_data' else '[CUSTOMER_DATA]') for k, v in config_recarga.items()
        })

        # 3) Instanciar servicio Wompi
        try:
            wompi_service = WompiService()
        except Exception as e:
            logger.error("[WOMPI_INIT_ERROR] %s", e)
            raise HTTPException(status_code=500, detail="Error en configuración de pagos")

        # 4) Obtener configuración preparada para frontend (incluye signature)
        try:
            config_widget = wompi_service.obtener_configuracion_widget(config_recarga)
            
            # VALIDACIÓN CRÍTICA: verificar signature antes de continuar
            if not config_widget.get("signature"):
                raise ValueError("Signature no fue generada correctamente")
                
            signature_len = len(config_widget["signature"])
            if signature_len != 64:
                raise ValueError(f"Signature tiene longitud incorrecta: {signature_len} (esperado: 64)")
            
            logger.info("[SIGNATURE_OK] Signature generada correctamente (length: %d)", signature_len)
            logger.debug("[CONFIG_WIDGET] Configuración preparada: %s", {
                k: (v if k != 'signature' else v[:12] + '...' if v else None) for k, v in config_widget.items()
            })
            
        except Exception as e:
            logger.error("[CONFIG_ERROR] Error generando configuración: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error preparando configuración de pago: {str(e)}")

        # 5) Mapear widget config a camelCase para el frontend
        widget_config_camel = _snake_to_camel_widget(config_widget)

        # 6) Normalizar customerData (a camelCase) si existe
        if widget_config_camel.get("customerData"):
            normalized_customer_data = _normalize_customer_data_for_frontend(widget_config_camel["customerData"])
            if normalized_customer_data:  # Solo asignar si hay datos válidos
                widget_config_camel["customerData"] = normalized_customer_data
            else:
                widget_config_camel.pop("customerData", None)  # Remover si está vacío

        # 7) Preparar objeto integrity para compatibilidad
        signature_value = config_widget.get("signature")
        amount_in_cents = int(config_widget.get("amount_in_cents") or 0)

        integrity_object = {
            "signature": signature_value,
            "integrity": signature_value,
            "reference": config_widget.get("reference"),
            "amountInCents": amount_in_cents
        }

        # 8) VALIDACIONES FINALES antes de enviar al frontend
        required_widget_fields = ["publicKey", "amountInCents", "currency", "reference", "signature"]
        missing_fields = [field for field in required_widget_fields if not widget_config_camel.get(field)]
        if missing_fields:
            logger.error("[VALIDATION_ERROR] Campos faltantes: %s", missing_fields)
            raise HTTPException(status_code=500, detail=f"Configuración incompleta: {missing_fields}")

        # Validar formato de campos críticos
        if not str(widget_config_camel["publicKey"]).startswith(("pub_test_", "pub_prod_")):
            logger.error("[VALIDATION_ERROR] PublicKey inválida: %s", widget_config_camel["publicKey"])
            raise HTTPException(status_code=500, detail="PublicKey tiene formato inválido")

        if widget_config_camel["amountInCents"] <= 0:
            logger.error("[VALIDATION_ERROR] Amount inválido: %s", widget_config_camel["amountInCents"])
            raise HTTPException(status_code=500, detail="Monto debe ser mayor a 0")

        # Log final para debugging
        logger.info("[WIDGET_READY] Configuración lista para frontend:")
        logger.info("  - publicKey: %s", widget_config_camel["publicKey"][:20] + "...")
        logger.info("  - reference: %s", widget_config_camel["reference"])
        logger.info("  - amountInCents: %s", widget_config_camel["amountInCents"])
        logger.info("  - signature: %s", signature_value[:16] + "...")
        
        # 9) Retornar respuesta
        return ConfiguracionWidgetResponse(
            recarga_id=recarga.id,
            widget_config=widget_config_camel,
            integrity=integrity_object,
            estado=recarga.estado
        )

    except ValueError as e:
        logger.error(f"[VALIDATION_ERROR] {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except UsuarioNoEncontradoError as e:
        logger.error(f"[USER_NOT_FOUND] {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"[UNEXPECTED_ERROR] {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/estado/{recarga_id}", response_model=EstadoRecargaResponse)
async def verificar_estado_recarga(
    recarga_id: str,
    recarga_service: RecargaService = Depends(get_recarga_service),
):
    try:
        recarga = recarga_service.verificar_estado_recarga(recarga_id)

        return EstadoRecargaResponse(
            recarga_id=recarga.id,
            estado=recarga.estado,
            monto=recarga.monto,
            usuario_id=recarga.usuario_id,
            referencia_wompi=recarga.referencia_wompi,
            fecha_creacion=recarga.fecha_creacion,
            fecha_actualizacion=recarga.fecha_actualizacion,
            es_exitosa=recarga.es_exitosa()
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error verificar estado: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/cancelar/{recarga_id}", response_model=RecargaResponse)
async def cancelar_recarga(
    recarga_id: str,
    recarga_service: RecargaService = Depends(get_recarga_service),
):
    try:
        recarga = recarga_service.cancelar_recarga_pendiente(recarga_id)

        return RecargaResponse(
            id=recarga.id,
            monto=recarga.monto,
            usuario_id=recarga.usuario_id,
            estado=recarga.estado,
            referencia_wompi=recarga.referencia_wompi,
            url_pago=None,  # No aplica para widget
            fecha_creacion=recarga.fecha_creacion,
            fecha_actualizacion=recarga.fecha_actualizacion
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelar recarga: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/usuario/{usuario_id}", response_model=List[RecargaResponse])
async def obtener_recargas_usuario(
    usuario_id: str,
    limite: int = 10,
    recarga_service: RecargaService = Depends(get_recarga_service),
):
    try:
        recargas = recarga_service.obtener_recargas_usuario(usuario_id, limite)

        return [
            RecargaResponse(
                id=r.id,
                monto=r.monto,
                usuario_id=r.usuario_id,
                estado=r.estado,
                referencia_wompi=r.referencia_wompi,
                url_pago=None,  # No aplica para widget
                fecha_creacion=r.fecha_creacion,
                fecha_actualizacion=r.fecha_actualizacion
            ) for r in recargas
        ]

    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error obtener recargas usuario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{recarga_id}", response_model=RecargaResponse)
async def obtener_recarga_por_id(
    recarga_id: str,
    recarga_service: RecargaService = Depends(get_recarga_service),
):
    try:
        recarga = recarga_service.obtener_recarga_por_id(recarga_id)

        if not recarga:
            raise HTTPException(status_code=404, detail="Recarga no encontrada")

        return RecargaResponse(
            id=recarga.id,
            monto=recarga.monto,
            usuario_id=recarga.usuario_id,
            estado=recarga.estado,
            referencia_wompi=recarga.referencia_wompi,
            url_pago=None,  # No aplica para widget
            fecha_creacion=recarga.fecha_creacion,
            fecha_actualizacion=recarga.fecha_actualizacion
        )

    except Exception as e:
        logger.error(f"Error obtener recarga: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/webhook/wompi")
async def webhook_wompi(
    request: Request,
    recarga_service: RecargaService = Depends(get_recarga_service)
):
    try:
        body = await request.body()
        payload = body.decode('utf-8')

        # Logs para entender mejor que está ocurriendo con el webhook
        logger.info("=" * 80)
        logger.info("🔔 WEBHOOK COMPLETO RECIBIDO:")
        logger.info(f"📦 PAYLOAD: {payload}")
        logger.info(f"📋 HEADERS: {dict(request.headers)}")
        logger.info("=" * 80)

        checksum_header = request.headers.get('X-Event-Checksum') or request.headers.get('X-Event-Signature')
        timestamp_header = request.headers.get('X-Timestamp')

        logger.info(f"Webhook recibido - checksum presente: {bool(checksum_header)}, timestamp: {bool(timestamp_header)}")

        try:
            wompi_service = WompiService()
        except Exception as e:
            logger.error("Error inicializando WompiService en webhook: %s", e)
            return JSONResponse(status_code=200, content={"status": "error", "message": "Error configuración backend"})

        # Validar signature del webhook
        if not wompi_service.validar_webhook_signature(payload, header_checksum=checksum_header, header_timestamp=timestamp_header):
            logger.warning("Webhook WOMPI con signature inválida")
            return JSONResponse(status_code=200, content={"status": "error", "message": "Signature inválida"})

        # Procesar evento
        event_data = json.loads(payload)
        processed_event = wompi_service.procesar_webhook_event(event_data)

        logger.info(f"Evento procesado: {processed_event.get('event_type')}")

        if processed_event.get("event_type") == "payment_update":
            if wompi_service.es_evento_final(processed_event.get("status")):
                try:
                    recarga = recarga_service.procesar_webhook_pago(
                        referencia_wompi=processed_event.get("reference"),
                        estado_pago=processed_event.get("status"),
                        transaction_id=processed_event.get("transaction_id"),
                        finalized_at=processed_event.get("finalized_at")
                    )

                    logger.info(f"Recarga {recarga.id} actualizada a {recarga.estado.value}")

                except Exception as e:
                    logger.error(f"Error procesando pago en webhook: {e}", exc_info=True)
                    return JSONResponse(
                        status_code=200,
                        content={"status": "error", "message": f"Error procesando pago: {str(e)}"}
                    )
            else:
                logger.info(f"Estado no final ignorado: {processed_event.get('status')}")

            return JSONResponse(
                status_code=200,
                content={"status": "success", "message": "Webhook procesado correctamente"}
            )

        elif processed_event.get("event_type") == "error":
            logger.error(f"Error en webhook: {processed_event.get('error', 'Unknown')}")
            return JSONResponse(
                status_code=200,
                content={"status": "error", "message": "Error procesando evento"}
            )

        return JSONResponse(
            status_code=200,
            content={"status": "ignored", "message": "Evento no procesado"}
        )

    except json.JSONDecodeError:
        logger.error("JSON inválido en webhook")
        return JSONResponse(status_code=200, content={"status": "error", "message": "JSON inválido"})
    except Exception as e:
        logger.error(f"Error procesando webhook WOMPI: {e}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": "Error interno procesando webhook"}
        )


@router.post("/admin/confirmar", response_model=RecargaResponse)
async def confirmar_recarga_manual(
    recarga_id: str,
    nuevo_estado: EstadoRecarga,
    recarga_service: RecargaService = Depends(get_recarga_service),
):
    try:
        recarga = recarga_service.confirmar_recarga_manual(
            recarga_id=recarga_id,
            nuevo_estado=nuevo_estado
        )

        return RecargaResponse(
            id=recarga.id,
            monto=recarga.monto,
            usuario_id=recarga.usuario_id,
            estado=recarga.estado,
            referencia_wompi=recarga.referencia_wompi,
            url_pago=None,
            fecha_creacion=recarga.fecha_creacion,
            fecha_actualizacion=recarga.fecha_actualizacion
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error confirmar recarga manual: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/admin/configuracion-webhooks")
async def obtener_configuracion_webhooks():
    try:
        wompi_service = WompiService()
        config = wompi_service.obtener_urls_webhook()

        return {
            "webhook_configuration": config,
            "instrucciones": [
                "1. Accede al dashboard de WOMPI",
                "2. Ve a la sección de Webhooks",
                "3. Configura la URL del webhook",
                "4. Selecciona los eventos: transaction.updated",
                "5. Guarda la configuración"
            ]
        }

    except Exception as e:
        logger.error(f"Error obteniendo configuración webhooks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ENDPOINT DE DEBUG - Solo para desarrollo/testing
@router.post("/debug/test-signature")
async def debug_test_signature(data: dict):
    """
    Endpoint para probar la generación de signature manualmente.
    Uso: POST /api/recargas/debug/test-signature
    Body: {"reference": "TEST_REF", "amount_in_cents": 25000}
    """
    try:
        wompi_service = WompiService()
        
        reference = data.get("reference", "TEST_REF")
        amount_in_cents = int(data.get("amount_in_cents", 25000))
        
        # Generar signature
        signature = wompi_service.generar_integrity(reference, amount_in_cents)
        
        # Obtener configuración completa
        config_test = {
            "reference": reference,
            "amount_in_cents": amount_in_cents,
            "customer_email": "test@example.com"
        }
        
        widget_config = wompi_service.obtener_configuracion_widget(config_test)
        
        return {
            "debug_info": {
                "reference": reference,
                "amount_in_cents": amount_in_cents,
                "signature": signature,
                "signature_length": len(signature) if signature else 0,
                "public_key": wompi_service.public_key,
                "integrity_secret_configured": bool(wompi_service.integrity_secret),
            },
            "widget_config": widget_config
        }
        
    except Exception as e:
        logger.error(f"Error en debug signature: {e}", exc_info=True)
        return {"error": str(e), "type": type(e).__name__}