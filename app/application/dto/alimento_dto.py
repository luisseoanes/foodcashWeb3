from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class AlimentoBaseDTO(BaseModel):
    nombre: str = Field(..., min_length=2, description="Nombre del alimento")
    precio: float = Field(..., gt=0, description="Precio del alimento")
    cantidad_en_stock: int = Field(..., ge=0, description="Cantidad disponible")
    calorias: int = Field(..., ge=0, description="Calorías del alimento")
    imagen: str = Field(..., description="URL o ruta a la imagen del alimento")
    categoria: str = Field(..., min_length=2, description="Categoría del alimento")
    
    @validator('precio')
    def precio_valido(cls, v):
        if v <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        return round(v, 2)

class AlimentoCreateDTO(AlimentoBaseDTO):
    pass

class AlimentoUpdateDTO(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, description="Nombre del alimento")
    precio: Optional[float] = Field(None, gt=0, description="Precio del alimento")
    cantidad_en_stock: Optional[int] = Field(None, ge=0, description="Cantidad disponible")
    calorias: Optional[int] = Field(None, ge=0, description="Calorías del alimento")
    imagen: Optional[str] = Field(None, description="URL o ruta a la imagen del alimento")
    categoria: Optional[str] = Field(None, min_length=2, description="Categoría del alimento")
    
    @validator('precio')
    def precio_valido(cls, v):
        if v is not None and v <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        if v is not None:
            return round(v, 2)
        return v

class AlimentoResponseDTO(AlimentoBaseDTO):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AlimentoFiltroDTO(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None



class DisminuirInventarioDTO(BaseModel):
    cantidad: int = Field(..., gt=0, description="Cantidad a disminuir del inventario (debe ser mayor que 0)")
