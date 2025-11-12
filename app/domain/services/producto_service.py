# app/domain/services/producto_service.py
from abc import ABC, abstractmethod
from typing import Optional

class ProductoRepository(ABC):
    @abstractmethod
    def obtener_producto_por_id(self, producto_id: int):
        pass

class ProductoService:
    def __init__(self, producto_repository: ProductoRepository):
        self.producto_repository = producto_repository

    def obtener_producto_por_id(self, producto_id: int):
        return self.producto_repository.obtener_producto_por_id(producto_id)