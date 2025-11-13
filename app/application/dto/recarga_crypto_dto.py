# application/dto/recarga_crypto_dto.py

from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum

class TipoCrypto(str, Enum):
    """Tipos de criptomonedas soportadas"""
    CCOP = "cCOP"  # Colombian Peso stablecoin en Celo
    CUSD = "cUSD"  # Celo Dollar
    CELO = "CELO"  # Token nativo de Celo

class EstadoRecargaCrypto(str, Enum):
    """Estados de una recarga con criptomonedas"""
    PENDIENTE = "pendiente"  # Esperando transacción
    VERIFICANDO = "verificando"  # Verificando en blockchain
    CONFIRMADA = "confirmada"  # Transacción confirmada
    COMPLETADA = "completada"  # Saldo acreditado al usuario
    RECHAZADA = "rechazada"  # Transacción rechazada
    ERROR = "error"  # Error en el proceso

class CrearRecargaCryptoRequest(BaseModel):
    """Request para iniciar una recarga con criptomonedas"""
    usuario_id: int = Field(..., description="ID del usuario que realiza la recarga")
    monto_cop: Decimal = Field(..., gt=0, description="Monto en pesos colombianos")
    tipo_crypto: TipoCrypto = Field(default=TipoCrypto.CCOP, description="Tipo de criptomoneda a usar")
    
    @validator('monto_cop')
    def validar_monto_minimo(cls, v):
        if v < Decimal("1000"):
            raise ValueError("El monto mínimo de recarga es $1,000 COP")
        if v > Decimal("5000000"):
            raise ValueError("El monto máximo de recarga es $5,000,000 COP")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "usuario_id": 1,
                "monto_cop": 50000,
                "tipo_crypto": "cCOP"
            }
        }

class ConfirmarRecargaCryptoRequest(BaseModel):
    """Request para confirmar una recarga con el hash de transacción"""
    recarga_id: str = Field(..., description="ID de la recarga creada")
    tx_hash: str = Field(..., min_length=64, max_length=68, description="Hash de la transacción en Celo")
    wallet_address: str = Field(..., min_length=40, max_length=42, description="Dirección de la wallet que envió el pago")
    
    @validator('tx_hash')
    def validar_tx_hash(cls, v):
        # Remover 0x si existe
        if v.startswith('0x'):
            v = v[2:]
        # Verificar que sea hexadecimal
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("tx_hash debe ser un valor hexadecimal válido")
        return f"0x{v}"
    
    @validator('wallet_address')
    def validar_wallet_address(cls, v):
        # Asegurar formato 0x
        if not v.startswith('0x'):
            v = f"0x{v}"
        if len(v) != 42:
            raise ValueError("wallet_address debe tener 42 caracteres (incluyendo 0x)")
        # Verificar que sea hexadecimal
        try:
            int(v[2:], 16)
        except ValueError:
            raise ValueError("wallet_address debe ser un valor hexadecimal válido")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "recarga_id": "REC_CRYPTO_123456",
                "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                "wallet_address": "0x1234567890123456789012345678901234567890"
            }
        }

class RecargaCryptoResponse(BaseModel):
    """Response con los datos de una recarga cripto"""
    id: str = Field(..., description="ID único de la recarga")
    usuario_id: int
    monto_cop: Decimal
    monto_crypto: Decimal
    tipo_crypto: TipoCrypto
    tasa_conversion: Decimal = Field(..., description="Tasa de conversión COP/Crypto usada")
    estado: EstadoRecargaCrypto
    tx_hash: Optional[str] = Field(None, description="Hash de la transacción en blockchain")
    wallet_address: Optional[str] = Field(None, description="Dirección de origen del pago")
    direccion_destino: str = Field(..., description="Dirección de FoodCash para recibir el pago")
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_confirmacion: Optional[datetime] = None
    mensaje: Optional[str] = Field(None, description="Mensaje adicional sobre el estado")
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "id": "REC_CRYPTO_123456",
                "usuario_id": 1,
                "monto_cop": 50000,
                "monto_crypto": 50000,
                "tipo_crypto": "cCOP",
                "tasa_conversion": 1.0,
                "estado": "pendiente",
                "tx_hash": None,
                "wallet_address": None,
                "direccion_destino": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "fecha_creacion": "2025-01-13T10:30:00",
                "fecha_actualizacion": "2025-01-13T10:30:00",
                "fecha_confirmacion": None,
                "mensaje": "Esperando transacción del usuario"
            }
        }

class InstruccionesPagoCryptoResponse(BaseModel):
    """Instrucciones para realizar el pago con crypto"""
    recarga_id: str
    monto_cop: Decimal
    monto_crypto: Decimal
    tipo_crypto: TipoCrypto
    direccion_destino: str
    tiempo_expiracion_minutos: int = Field(default=30, description="Tiempo en minutos antes de que expire")
    instrucciones: list[str]
    info_adicional: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "recarga_id": "REC_CRYPTO_123456",
                "monto_cop": 50000,
                "monto_crypto": 50000,
                "tipo_crypto": "cCOP",
                "direccion_destino": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "tiempo_expiracion_minutos": 30,
                "instrucciones": [
                    "1. Abre tu wallet de Celo (Valora, MetaMask, etc.)",
                    "2. Asegúrate de estar en la red de Celo",
                    "3. Envía exactamente 50000 cCOP a la dirección indicada",
                    "4. Copia el hash de la transacción",
                    "5. Regresa a FoodCash y confirma el pago pegando el hash"
                ],
                "info_adicional": {
                    "red": "Celo Mainnet",
                    "token_contract": "0x00Be915B9dCf56a3CBE739D9B9c202ca692409EC",
                    "fee_estimado": "< $0.01 USD",
                    "tiempo_confirmacion": "~5 segundos"
                }
            }
        }

class EstadoVerificacionResponse(BaseModel):
    """Response del estado de verificación de una transacción"""
    recarga_id: str
    estado: EstadoRecargaCrypto
    verificada: bool
    mensaje: str
    detalles_blockchain: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "recarga_id": "REC_CRYPTO_123456",
                "estado": "confirmada",
                "verificada": True,
                "mensaje": "Pago verificado exitosamente. Saldo acreditado.",
                "detalles_blockchain": {
                    "tx_hash": "0xabc...123",
                    "block_number": 12345678,
                    "from": "0x123...abc",
                    "to": "0x742...bEb",
                    "amount": 50000,
                    "timestamp": "2025-01-13T10:35:00"
                }
            }
        }

class ConfiguracionCryptoResponse(BaseModel):
    """Configuración y estado del sistema de pagos crypto"""
    criptomonedas_soportadas: list[TipoCrypto]
    red_activa: str
    direccion_recepcion: str
    estado_servicio: str
    info_red: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "criptomonedas_soportadas": ["cCOP", "cUSD", "CELO"],
                "red_activa": "Celo Mainnet",
                "direccion_recepcion": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "estado_servicio": "operativo",
                "info_red": {
                    "connected": True,
                    "latest_block": 12345678,
                    "chain_id": 42220
                }
            }
        }
