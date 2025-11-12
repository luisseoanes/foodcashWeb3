from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

# --- DTO para el endpoint Legacy ---
class PrecompraCreateLegacyDTO(BaseModel):
    compra_id: int = Field(..., description="ID de la compra asociada")
    estudiante_id: int = Field(..., description="ID del estudiante")
    costo_adicional: Optional[float] = Field(float('100.00'), description="Costo adicional por ítem")

# --- DTOs para la Creación de Nuevas Precompras ---
class PrecompraItemCreateDTO(BaseModel):
    producto_id: int
    cantidad: int = 1

class PrecompraNuevaCreateDTO(BaseModel):
    estudiante_id: int
    items: List[PrecompraItemCreateDTO]
    costo_adicional: float = Field(default=float('100.00'))

# --- DTOs de Respuesta ---
class PrecompraResponseDTO(BaseModel):
    id: int
    id_compra: int
    id_estudiante: int
    fecha_precompra: datetime
    costo_total: float
    costo_adicional: float
    entregado: bool
    fecha_entrega: Optional[datetime] = None
    activo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    class Config:
        from_attributes = True

# --- DTOs para Detalles y Cálculos ---

class CompraDetalleDTO(BaseModel):
    id: int
    usuario_id: int
    fecha: datetime
    total: float
    items: List[Dict[str, Any]]

    class Config:
        from_attributes = True

class PrecompraConDetallesResponseDTO(BaseModel):
    precompra: PrecompraResponseDTO
    compra: CompraDetalleDTO

class PrecompraCalculoResponseDTO(BaseModel):
    costo_productos: float
    cantidad_items: int
    costo_adicional_por_item: float
    costo_adicional_total: float
    costo_total: float
    detalle_productos: List[Dict[str, Any]]

class PrecompraItemDetalleDTO(BaseModel):
    """Define la estructura de un item individual en el historial."""
    nombre: str
    cantidad: int
    precio_unitario: float

class PrecompraHistorialDetalladoDTO(BaseModel):
    """Este es el modelo de respuesta principal para cada fila de la tabla del admin."""
    id: int
    id_compra: int
    nombre_estudiante: str
    fecha_precompra: datetime
    costo_total: float
    entregado: bool
    fecha_entrega: Optional[datetime] = None
    items: List[PrecompraItemDetalleDTO] = [] # La lista de productos

    class Config:
        from_attributes = True