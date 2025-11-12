from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Precompra:
    # ===============================================================
    # PASO 1: Todos los campos OBLIGATORIOS se declaran primero.
    # ===============================================================
    id_estudiante: int
    costo_total: float
    costo_adicional: float
    
    # ===============================================================
    # PASO 2: Todos los campos OPCIONALES (con valor por defecto) van después.
    # ===============================================================
    fecha_precompra: datetime = field(default_factory=datetime.now)
    entregado: bool = False
    activo: bool = True
    id: Optional[int] = None
    id_compra: Optional[int] = None
    fecha_entrega: Optional[datetime] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    def marcar_como_entregado(self):
        """Marca la precompra como entregada y establece la fecha de entrega"""
        if self.entregado:
            raise ValueError("La precompra ya ha sido entregada")
        self.entregado = True
        self.fecha_entrega = datetime.now()
    
    def cancelar_entrega(self):
        """Cancela la entrega de una precompra"""
        if not self.entregado:
            raise ValueError("La precompra no está marcada como entregada")
        self.entregado = False
        self.fecha_entrega = None
    
    def calcular_costo_con_recargo(self, cantidad_items: int) -> float:
        """Calcula el costo total incluyendo el recargo por precompra"""
        recargo_total = self.costo_adicional * cantidad_items
        return self.costo_total + recargo_total
    
    def __post_init__(self):
        if self.fecha_creacion is None:
            self.fecha_creacion = datetime.now()
        if self.fecha_actualizacion is None:
            self.fecha_actualizacion = datetime.now()