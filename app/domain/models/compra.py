from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class CompraItem:
    producto_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float = field(init=False)

    def __post_init__(self):
        self.subtotal = self.cantidad * self.precio_unitario

@dataclass
class Compra:
    usuario_id: int
    items: List[CompraItem] = field(default_factory=list)
    fecha: datetime = field(default_factory=datetime.now)
    total: float = 0
    id: Optional[int] = None

    def calcular_total(self):
        self.total = sum(item.subtotal for item in self.items)
        return self.total