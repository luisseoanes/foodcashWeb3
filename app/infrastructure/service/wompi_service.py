# infrastructure/service/wompi_service.py

import os
import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class WompiService:
    """
    Servicio para integrar con WOMPI usando el widget.
    - Prepara configuración para el widget (backend -> frontend)
    - Valida webhooks (checksum)
    - Procesa payloads de webhook
    - Genera firma de integridad (signature) usando la Integrity Secret (SHA-256)
    """

    def __init__(self):
        # Credenciales / secretos desde variables de entorno
        self.public_key = os.getenv("WOMPI_PUBLIC_KEY")
        self.private_key = os.getenv("WOMPI_PRIVATE_KEY")
        self.integrity_secret = os.getenv("WOMPI_INTEGRITY_SECRET")
        self.webhook_secret = os.getenv("WOMPI_WEBHOOK_SECRET")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.environment = os.getenv("WOMPI_ENVIRONMENT", "sandbox")  # sandbox o production

        # Validaciones iniciales mínimas
        if not self.public_key:
            logger.warning("WOMPI_PUBLIC_KEY no configurada (widget no podrá inicializarse).")
        if not self.integrity_secret:
            logger.warning("WOMPI_INTEGRITY_SECRET no configurada (signature/integrity no se generará).")

    def _normalize_reference(self, reference: Optional[str]) -> Optional[str]:
        if reference is None:
            return None
        # elimino espacios en los extremos y garantizo str
        return str(reference).strip()

    def _normalize_amount(self, amount) -> int:
        """
        Asegura que amount (centavos) sea entero.
        El input puede venir como int, str, float; convertir a entero exacto.
        """
        try:
            return int(amount)
        except Exception:
            logger.exception("Amount_in_cents inválido: %r", amount)
            return 0

    def generar_integrity(self, reference: str, amount_in_cents: int, currency: str = "COP") -> Optional[str]:
        reference_n = self._normalize_reference(reference)
        if reference_n is None:
            logger.warning("No se puede generar integrity: reference es None")
            return None

        amount_int = self._normalize_amount(amount_in_cents)
        currency_s = (currency or "COP").upper()

        if not self.integrity_secret:
            logger.warning("WOMPI_INTEGRITY_SECRET no configurada; no se generará integrity.")
            return None

        # Logs de toda la firma
        logger.info(f"🔐 === GENERANDO SIGNATURE ===")
        logger.info(f"🔐 Reference original: '{reference}'")
        logger.info(f"🔐 Reference normalizada: '{reference_n}'")
        logger.info(f"🔐 Reference length: {len(reference_n)}")
        logger.info(f"🔐 Amount: {amount_int}")
        logger.info(f"🔐 Currency: {currency_s}")
        
        # Formato según documentación
        message = f"{reference_n}{amount_int}{currency_s}{self.integrity_secret}"
        
        # Log del mensaje (sin el secret)
        message_preview = f"{reference_n}{amount_int}{currency_s}[SECRET]"
        logger.info(f"🔐 Mensaje para hash: '{message_preview}'")
        
        signature = hashlib.sha256(message.encode("utf-8")).hexdigest()
        
        logger.info(f"🔐 Signature generada: {signature}")
        logger.info(f"🔐 === FIN SIGNATURE ===")
        
        return signature

    def obtener_configuracion_integridad(self, reference: str, amount_in_cents: int) -> Dict[str, Any]:
        """
        Interfaz que devuelve un dict con signature y metadatos.
        """
        signature = self.generar_integrity(reference, amount_in_cents, currency="COP")
        amount_int = self._normalize_amount(amount_in_cents)
        return {
            "signature": signature,
            "integrity": signature,
            "reference": self._normalize_reference(reference),
            "amount_in_cents": amount_int,
            "amountInCents": amount_int,
            "currency": "COP"
        }

    def obtener_configuracion_widget(self, config_recarga: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara objeto para frontend (snake_case).
        Espera config_recarga con keys: reference, amount_in_cents (int) y opcionales customer_data, customer_email, etc.
        
        CAMBIOS CRÍTICOS PARA CORREGIR SIGNATURE:
        1. Validar que public_key tenga el formato correcto (pub_test_ o pub_prod_)
        2. Asegurar que amount_in_cents sea exactamente un entero
        3. Verificar que reference no tenga caracteres extraños
        4. Limpiar customer_data de campos vacíos que puedan causar problemas
        """
        reference = self._normalize_reference(config_recarga.get("reference"))
        amount = config_recarga.get("amount_in_cents") or config_recarga.get("amountInCents") or 0
        amount_int = self._normalize_amount(amount)

        # Logs
        logger.info(f"🔍 MONTO NORMALIZADO: {amount_int} (tipo: {type(amount_int)})")
        logger.info(f"🔍 REFERENCE: {reference}")

        # Validaciones críticas
        if not reference:
            raise ValueError("Reference es requerido para generar la configuración del widget")
        
        if not amount_int or amount_int <= 0:
            raise ValueError("Amount debe ser mayor a 0 para generar la configuración del widget")

        # Validar public key format
        if not self.public_key or not (self.public_key.startswith("pub_test_") or self.public_key.startswith("pub_prod_")):
            raise ValueError("WOMPI_PUBLIC_KEY debe tener formato válido (pub_test_xxx o pub_prod_xxx)")

        customer_email = config_recarga.get("customer_email") or config_recarga.get("customerEmail")
        raw_customer_data = config_recarga.get("customer_data") or config_recarga.get("customerData") or {}
        payment_description = config_recarga.get("payment_description") or config_recarga.get("paymentDescription") or "Recarga de saldo"

        redirect_url = config_recarga.get("redirect_url") or config_recarga.get("redirectUrl") or f"{self.frontend_url}/recargas/resultado"

        # LIMPIAR customer_data - remover campos vacíos que pueden causar problemas
        customer_data = {}
        if isinstance(raw_customer_data, dict):
            for key, value in raw_customer_data.items():
                if value is not None and str(value).strip():  # Solo incluir valores no vacíos
                    customer_data[key] = str(value).strip()

        # Build base widget config
        widget = {
            "public_key": self.public_key,
            "currency": "COP",
            "amount_in_cents": amount_int,
            "reference": reference,
            "redirect_url": redirect_url,
            "payment_description": payment_description,
            "payment_methods": config_recarga.get("payment_methods") or config_recarga.get("paymentMethods") or {},
            "customization": config_recarga.get("customization") or config_recarga.get("customization") or {}
        }

        # Agregar customer_email y customer_data solo si tienen contenido
        if customer_email and str(customer_email).strip():
            widget["customer_email"] = str(customer_email).strip()
        
        if customer_data:
            widget["customer_data"] = customer_data

        # Generar signature (integrity) y anexar
        try:
            signature = self.generar_integrity(reference, amount_int, currency="COP")
            if not signature:
                raise ValueError("No se pudo generar la firma de integridad")
            
            # Verificar que la signature tenga el formato correcto (64 caracteres hexadecimales)
            if len(signature) != 64 or not all(c in '0123456789abcdefABCDEF' for c in signature):
                raise ValueError(f"Signature generada tiene formato inválido: {signature}")
            
            widget["signature"] = signature
            widget["integrity"] = signature
            
            logger.info("Signature generada exitosamente para reference: %s (length: %d)", reference, len(signature))
            
        except Exception as e:
            logger.error("Error crítico generando signature para widget: %s", e, exc_info=True)
            raise ValueError(f"No se pudo generar la firma de integridad: {str(e)}")

        # Validation final: verificar campos críticos del widget
        required_fields = ["public_key", "amount_in_cents", "currency", "reference", "signature"]
        missing_fields = [field for field in required_fields if not widget.get(field)]
        if missing_fields:
            raise ValueError(f"Campos requeridos faltantes en widget config: {missing_fields}")

        # Safety logs (útiles para depuración)
        logger.debug("Widget config generado correctamente:")
        logger.debug("- public_key: %s", widget["public_key"][:20] + "..." if len(widget["public_key"]) > 20 else widget["public_key"])
        logger.debug("- reference: %s", widget["reference"])
        logger.debug("- amount_in_cents: %s", widget["amount_in_cents"])
        logger.debug("- signature: %s", widget["signature"][:16] + "..." if widget["signature"] else "None")

        return widget

    def validar_webhook_signature(self, payload: str, header_checksum: str = None, header_timestamp: str = None) -> bool:
        """
        Valida los webhooks de Wompi (usa properties + timestamp + webhook_secret).
        CORREGIDO: Lee timestamp del nivel raíz del evento
        """
        if not self.webhook_secret:
            logger.error("WOMPI_WEBHOOK_SECRET no configurado")
            return False

        try:
            event = json.loads(payload)
        except Exception as e:
            logger.error(f"Error parseando payload JSON para validar webhook: {e}")
            return False

        # CORRECCIÓN: El timestamp está en el nivel raíz del evento
        timestamp = event.get("timestamp") or header_timestamp
        
        signature_obj = event.get("signature") or {}
        properties = signature_obj.get("properties", [])
        checksum_from_body = signature_obj.get("checksum")
        checksum_header = header_checksum

        expected_checksum_source = (checksum_header or checksum_from_body)
        if not expected_checksum_source:
            logger.warning("No se encontró checksum en header ni en body.signature")
            return False

        # VALIDAR TIMESTAMP
        if timestamp is None:
            logger.warning("Timestamp no encontrado en el evento")
            return False

        logger.info(f"🔐 Validando webhook - timestamp: {timestamp}, checksum: {expected_checksum_source[:16]}...")

        def _get_by_path(root: dict, path: str):
            current = root
            for p in path.split("."):
                if isinstance(current, dict):
                    current = current.get(p)
                else:
                    return None
            return current

        data_root = event.get("data", {}) if isinstance(event.get("data", {}), dict) else {}

        try:
            concatenated = ""
            
            # Concatenar valores de las propiedades especificadas
            if properties and isinstance(properties, list):
                for prop in properties:
                    # Buscar primero en data.transaction, luego en data, finalmente en root
                    value = _get_by_path(data_root, prop)
                    if value is None:
                        value = _get_by_path(event, prop)
                    
                    concatenated += str(value or "")
                    logger.debug(f"   Property '{prop}': {value}")
            
            # Agregar timestamp y secret
            concatenated += str(timestamp)
            concatenated += str(self.webhook_secret)

            # Calcular checksum
            calculated = hashlib.sha256(concatenated.encode()).hexdigest()
            
            logger.info(f"🔐 Checksum calculado: {calculated[:16]}...")
            logger.info(f"🔐 Checksum esperado:  {expected_checksum_source[:16]}...")
            
            is_valid = hmac.compare_digest(calculated, str(expected_checksum_source))
            
            if is_valid:
                logger.info("✅ Signature válida")
            else:
                logger.warning("❌ Signature inválida")
                
            return is_valid

        except Exception as e:
            logger.error(f"Error validando checksum webhook: {e}", exc_info=True)
            return False

    def procesar_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            event_type = event_data.get("event")
            transaction_data = event_data.get("data", {})

            logger.info(f"Procesando evento WOMPI: {event_type}")

            if event_type == "transaction.updated":
                tx = transaction_data.get("transaction") or transaction_data or {}
                return {
                    "event_type": "payment_update",
                    "transaction_id": tx.get("id") or tx.get("transaction_id"),
                    "reference": tx.get("reference"),
                    "status": tx.get("status"),
                    "amount": (tx.get("amount_in_cents", 0) or 0) / 100,
                    "payment_method": self._extract_payment_method(tx),
                    "finalized_at": tx.get("finalized_at"),
                    "customer_email": tx.get("customer_email"),
                    "raw_data": tx
                }

            elif event_type == "payment_link.updated":
                return {
                    "event_type": "payment_link_update",
                    "payment_link_id": transaction_data.get("id"),
                    "status": transaction_data.get("status"),
                    "raw_data": transaction_data
                }
            else:
                logger.warning(f"Evento no reconocido: {event_type}")
                return {
                    "event_type": "unknown",
                    "raw_event_type": event_type,
                    "raw_data": event_data
                }

        except Exception as e:
            logger.error(f"Error procesando evento webhook: {e}")
            return {
                "event_type": "error",
                "error": str(e),
                "raw_data": event_data
            }

    def _extract_payment_method(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        payment_method = transaction_data.get("payment_method", {}) or {}
        extra = payment_method.get("extra", {}) or {}
        return {
            "type": payment_method.get("type", "unknown"),
            "extra": {
                "bin": extra.get("bin"),
                "name": extra.get("name"),
                "brand": extra.get("brand"),
                "exp_year": extra.get("exp_year"),
                "exp_month": extra.get("exp_month"),
                "last_four": extra.get("last_four"),
                "external_identifier": extra.get("external_identifier")
            }
        }

    def obtener_urls_webhook(self) -> Dict[str, Any]:
        base_url = os.getenv("BACKEND_BASE_URL", "https://tu-api.com")
        return {
            "webhook_url": f"{base_url}/api/recargas/webhook/wompi",
            "events": ["transaction.updated"]
        }

    def es_evento_final(self, status: str) -> bool:
        estados_finales = ["APPROVED", "DECLINED", "VOIDED"]
        return status in estados_finales