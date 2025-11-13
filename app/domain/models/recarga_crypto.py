# domain/models/recarga_crypto.py

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from enum import Enum

class TipoCrypto(Enum):
    """Tipos de criptomonedas soportadas"""
    CCOP = "cCOP"
    CUSD = "cUSD"
    CELO = "CELO"

class EstadoRecargaCrypto(Enum):
    """Estados posibles de una recarga con criptomonedas"""
    PENDIENTE = "pendiente"
    VERIFICANDO = "verificando"
    CONFIRMADA = "confirmada"
    COMPLETADA = "completada"
    RECHAZADA = "rechazada"
    ERROR = "error"

@dataclass
class RecargaCrypto:
    """
    Entidad de dominio que representa una recarga con criptomonedas.
    """
    id: str
    usuario_id: int
    monto_cop: Decimal
    monto_crypto: Decimal
    tipo_crypto: TipoCrypto
    tasa_conversion: Decimal
    estado: EstadoRecargaCrypto
    direccion_destino: str  # Dirección de FoodCash
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    tx_hash: Optional[str] = None
    wallet_address: Optional[str] = None  # Dirección del usuario que paga
    fecha_confirmacion: Optional[datetime] = None
    block_number: Optional[int] = None
    mensaje: Optional[str] = None
    detalles_blockchain: Optional[dict] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validaciones después de inicialización"""
        if self.monto_cop <= 0:
            raise ValueError("El monto en COP debe ser mayor a 0")
        if self.monto_crypto <= 0:
            raise ValueError("El monto en crypto debe ser mayor a 0")
        if self.tasa_conversion <= 0:
            raise ValueError("La tasa de conversión debe ser mayor a 0")
    
    def marcar_como_verificando(self, tx_hash: str, wallet_address: str):
        """Marca la recarga como en proceso de verificación"""
        self.estado = EstadoRecargaCrypto.VERIFICANDO
        self.tx_hash = tx_hash
        self.wallet_address = wallet_address
        self.fecha_actualizacion = datetime.utcnow()
        self.mensaje = "Verificando transacción en blockchain"
    
    def marcar_como_confirmada(self, detalles: dict):
        """Marca la recarga como confirmada en blockchain"""
        self.estado = EstadoRecargaCrypto.CONFIRMADA
        self.fecha_confirmacion = datetime.utcnow()
        self.fecha_actualizacion = datetime.utcnow()
        self.detalles_blockchain = detalles
        self.block_number = detalles.get('blockNumber')
        self.mensaje = "Transacción confirmada en blockchain"
    
    def marcar_como_completada(self):
        """Marca la recarga como completada (saldo acreditado)"""
        self.estado = EstadoRecargaCrypto.COMPLETADA
        self.fecha_actualizacion = datetime.utcnow()
        self.mensaje = "Recarga completada. Saldo acreditado exitosamente."
    
    def marcar_como_rechazada(self, razon: str):
        """Marca la recarga como rechazada"""
        self.estado = EstadoRecargaCrypto.RECHAZADA
        self.fecha_actualizacion = datetime.utcnow()
        self.mensaje = f"Recarga rechazada: {razon}"
    
    def marcar_como_error(self, error: str):
        """Marca la recarga con error"""
        self.estado = EstadoRecargaCrypto.ERROR
        self.fecha_actualizacion = datetime.utcnow()
        self.mensaje = f"Error: {error}"
    
    @property
    def esta_pendiente(self) -> bool:
        """Verifica si la recarga está pendiente"""
        return self.estado == EstadoRecargaCrypto.PENDIENTE
    
    @property
    def esta_completada(self) -> bool:
        """Verifica si la recarga está completada"""
        return self.estado == EstadoRecargaCrypto.COMPLETADA
    
    @property
    def puede_ser_verificada(self) -> bool:
        """Verifica si la recarga puede ser verificada"""
        return self.estado in [EstadoRecargaCrypto.PENDIENTE, EstadoRecargaCrypto.VERIFICANDO]
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'monto_cop': float(self.monto_cop),
            'monto_crypto': float(self.monto_crypto),
            'tipo_crypto': self.tipo_crypto.value,
            'tasa_conversion': float(self.tasa_conversion),
            'estado': self.estado.value,
            'direccion_destino': self.direccion_destino,
            'tx_hash': self.tx_hash,
            'wallet_address': self.wallet_address,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'fecha_confirmacion': self.fecha_confirmacion.isoformat() if self.fecha_confirmacion else None,
            'block_number': self.block_number,
            'mensaje': self.mensaje,
            'detalles_blockchain': self.detalles_blockchain
        }
