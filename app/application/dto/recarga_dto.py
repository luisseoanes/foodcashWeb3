from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EstadoRecarga(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    CANCELADA = "CANCELADA"

class CrearRecargaRequest(BaseModel):
    """DTO para iniciar una nueva recarga con widget"""
    monto: float = Field(..., gt=0, description="Monto a recargar en COP")
    usuario_id: str = Field(..., description="ID del usuario que recarga")
    
    class Config:
        json_schema_extra = {
            "example": {
                "monto": 50000.0,
                "usuario_id": "123"
            }
        }

class ConfiguracionWidgetResponse(BaseModel):
    """DTO con la configuración completa para el widget de WOMPI"""
    recarga_id: str = Field(..., description="ID de la recarga creada")
    widget_config: Dict[str, Any] = Field(..., description="Configuración del widget WOMPI")
    integrity: Dict[str, Any] = Field(..., description="Hash de integridad para validación")
    estado: EstadoRecarga = Field(..., description="Estado actual de la recarga")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recarga_id": "rec_123",
                "widget_config": {
                    "public_key": "pub_test_xxx",
                    "currency": "COP",
                    "amount_in_cents": 5000000,
                    "reference": "REC_rec_123_user_456_1703176800",
                    "customer_email": "usuario@ejemplo.com",
                    "redirect_url": "https://mi-app.com/recargas/resultado",
                    "payment_description": "Recarga de saldo - $50,000 COP"
                },
                "integrity": {
                    "integrity": "hash_integridad_xxx",
                    "reference": "REC_rec_123_user_456_1703176800",
                    "amount_in_cents": "5000000"
                },
                "estado": "PENDIENTE"
            }
        }

class EstadoRecargaResponse(BaseModel):
    """DTO para consultar el estado de una recarga"""
    recarga_id: str
    estado: EstadoRecarga
    monto: float
    usuario_id: str
    referencia_wompi: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    es_exitosa: bool = Field(..., description="Indica si la recarga fue exitosa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recarga_id": "rec_123",
                "estado": "APROBADA",
                "monto": 50000.0,
                "usuario_id": "123",
                "referencia_wompi": "REC_rec_123_user_456_1703176800",
                "fecha_creacion": "2023-12-01T10:30:00Z",
                "fecha_actualizacion": "2023-12-01T10:35:00Z",
                "es_exitosa": True
            }
        }

class RecargaResponse(BaseModel):
    """DTO de respuesta con datos básicos de la recarga"""
    id: str
    monto: float
    usuario_id: str
    estado: EstadoRecarga
    referencia_wompi: Optional[str] = None
    url_pago: Optional[str] = None  # Deprecated para widget, mantenido por compatibilidad
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rec_123",
                "monto": 50000.0,
                "usuario_id": "123",
                "estado": "PENDIENTE",
                "referencia_wompi": "REC_rec_123_user_456_1703176800",
                "url_pago": None,
                "fecha_creacion": "2023-12-01T10:30:00Z",
                "fecha_actualizacion": None
            }
        }

class WebhookWompiRequest(BaseModel):
    """DTO para recibir webhooks de WOMPI"""
    event: str = Field(..., description="Tipo de evento")
    data: Dict[str, Any] = Field(..., description="Datos del evento")
    timestamp: int = Field(..., description="Timestamp del evento")
    signature: str = Field(..., description="Signature para validación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event": "transaction.updated",
                "data": {
                    "id": "wompi_transaction_123",
                    "reference": "REC_rec_123_user_456_1703176800",
                    "status": "APPROVED",
                    "amount_in_cents": 5000000,
                    "currency": "COP",
                    "customer_email": "usuario@ejemplo.com",
                    "finalized_at": "2023-12-01T10:35:00Z"
                },
                "timestamp": 1703176800,
                "signature": "signature_hash_xxx"
            }
        }

class ConfirmarRecargaRequest(BaseModel):
    """DTO para confirmar manualmente una recarga (admin)"""
    recarga_id: str = Field(..., description="ID de la recarga a confirmar")
    estado: EstadoRecarga = Field(..., description="Nuevo estado de la recarga")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recarga_id": "rec_123",
                "estado": "APROBADA"
            }
        }

class ResultadoPagoWidget(BaseModel):
    """DTO para manejar el resultado del pago desde el widget (si es necesario)"""
    recarga_id: str = Field(..., description="ID de la recarga")
    status: str = Field(..., description="Estado devuelto por el widget")
    transaction_id: Optional[str] = Field(None, description="ID de transacción de WOMPI")
    reference: Optional[str] = Field(None, description="Referencia de la transacción")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recarga_id": "rec_123",
                "status": "APPROVED",
                "transaction_id": "wompi_trans_456",
                "reference": "REC_rec_123_user_456_1703176800"
            }
        }