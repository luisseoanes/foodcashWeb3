# domain/models/recarga.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class EstadoRecarga(Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    CANCELADA = "CANCELADA"

@dataclass
class Recarga:
    """
    Entidad de dominio que representa una recarga de saldo
    Contiene las reglas de negocio relacionadas con recargas
    """
    monto: float
    usuario_id: str
    estado: EstadoRecarga = EstadoRecarga.PENDIENTE
    id: Optional[str] = None
    referencia_wompi: Optional[str] = None
    url_pago: Optional[str] = None
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones después de la inicialización"""
        if self.monto <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        if not self.usuario_id or not self.usuario_id.strip():
            raise ValueError("El usuario_id es requerido")
    
    def aprobar(self) -> None:
        """
        Aprueba la recarga
        Regla de negocio: Solo se puede aprobar si está pendiente
        """
        if self.estado != EstadoRecarga.PENDIENTE:
            raise ValueError(f"No se puede aprobar una recarga en estado {self.estado.value}")
        
        self.estado = EstadoRecarga.APROBADA
        self.fecha_actualizacion = datetime.now()
    
    def rechazar(self) -> None:
        """
        Rechaza la recarga
        Regla de negocio: Solo se puede rechazar si está pendiente
        """
        if self.estado != EstadoRecarga.PENDIENTE:
            raise ValueError(f"No se puede rechazar una recarga en estado {self.estado.value}")
        
        self.estado = EstadoRecarga.RECHAZADA
        self.fecha_actualizacion = datetime.now()
    
    def cancelar(self) -> None:
        """
        Cancela la recarga
        Regla de negocio: Solo se puede cancelar si está pendiente
        """
        if self.estado != EstadoRecarga.PENDIENTE:
            raise ValueError(f"No se puede cancelar una recarga en estado {self.estado.value}")
        
        self.estado = EstadoRecarga.CANCELADA
        self.fecha_actualizacion = datetime.now()
    
    def establecer_referencia_wompi(self, referencia: str, url_pago: str = None) -> None:
        """
        Establece la referencia de WOMPI y opcionalmente la URL de pago
        """
        if not referencia or not referencia.strip():
            raise ValueError("La referencia de WOMPI no puede estar vacía")
        
        self.referencia_wompi = referencia
        if url_pago:
            self.url_pago = url_pago
        self.fecha_actualizacion = datetime.now()
    
    def es_procesable(self) -> bool:
        """
        Determina si la recarga puede ser procesada (aprobada/rechazada)
        """
        return self.estado == EstadoRecarga.PENDIENTE
    
    def es_exitosa(self) -> bool:
        """
        Determina si la recarga fue exitosa
        """
        return self.estado == EstadoRecarga.APROBADA