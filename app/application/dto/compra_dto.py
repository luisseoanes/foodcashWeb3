from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CompraItemDTO(BaseModel):
    producto_id: int
    cantidad: int
    precio_unitario: float

    # Nuevos campos:
    nombre_alimento: Optional[str] = None
    calorias: Optional[float] = None


class CompraInputDTO(BaseModel):
    usuario_id: int
    items: List[CompraItemDTO]


class CompraOutputDTO(BaseModel):
    id: int
    fecha: datetime
    usuario_id: int
    total: float
    items: List[CompraItemDTO]
