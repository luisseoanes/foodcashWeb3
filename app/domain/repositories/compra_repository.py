from abc import ABC, abstractmethod
from typing import Optional
from domain.models.compra import Compra

class CompraRepository(ABC):
    @abstractmethod
    def guardar_compra(self, compra: Compra) -> Compra:
        pass

    @abstractmethod
    def obtener_compra_por_id(self, compra_id: int) -> Optional[Compra]:
        pass

    @abstractmethod
    def obtener_compras_por_usuario_id(self, usuario_id: int) -> list[Compra]:
        pass