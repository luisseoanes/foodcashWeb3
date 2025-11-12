from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Alimento:
    """Entidad de dominio para Alimento."""
    id: Optional[int]  # id autoincrementable
    nombre: str
    precio: float
    cantidad_en_stock: int
    calorias: int
    imagen: str
    categoria: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    activo: bool = True

    @classmethod
    def crear(cls, nombre: str, precio: float, cantidad_en_stock: int, 
              calorias: int, imagen: str, categoria: str) -> "Alimento":
        """Método de fábrica para crear un nuevo alimento."""
        if precio <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        if cantidad_en_stock < 0:
            raise ValueError("La cantidad en stock no puede ser negativa")
        if calorias < 0:
            raise ValueError("Las calorías no pueden ser negativas")
        if not nombre or not categoria:
            raise ValueError("El nombre y la categoría son obligatorios")
            
        return cls(
            id=None,  # Se asignará al guardar en la BD
            nombre=nombre,
            precio=precio,
            cantidad_en_stock=cantidad_en_stock,
            calorias=calorias,
            imagen=imagen,
            categoria=categoria,
            fecha_creacion=datetime.now()
        )
    
    def actualizar(self, nombre: Optional[str] = None, precio: Optional[float] = None,
                   cantidad_en_stock: Optional[int] = None, calorias: Optional[int] = None,
                   imagen: Optional[str] = None, categoria: Optional[str] = None) -> None:
        """Actualiza los atributos del alimento."""
        if nombre is not None:
            if not nombre:
                raise ValueError("El nombre no puede estar vacío")
            self.nombre = nombre
        if precio is not None:
            if precio <= 0:
                raise ValueError("El precio debe ser mayor que cero")
            self.precio = precio
        if cantidad_en_stock is not None:
            if cantidad_en_stock < 0:
                raise ValueError("La cantidad en stock no puede ser negativa")
            self.cantidad_en_stock = cantidad_en_stock
        if calorias is not None:
            if calorias < 0:
                raise ValueError("Las calorías no pueden ser negativas")
            self.calorias = calorias
        if imagen is not None:
            self.imagen = imagen
        if categoria is not None:
            if not categoria:
                raise ValueError("La categoría no puede estar vacía")
            self.categoria = categoria
            
        self.fecha_actualizacion = datetime.now()
        
    def eliminar(self) -> None:
        """Marca el alimento como inactivo (eliminación lógica)."""
        self.activo = False
        self.fecha_actualizacion = datetime.now()
