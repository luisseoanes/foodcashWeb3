from abc import ABC, abstractmethod
from typing import List, Optional
from domain.models.precompra import Precompra

class PrecompraRepository(ABC):
    
    @abstractmethod
    def guardar(self, precompra: Precompra) -> Precompra:
        """Guarda una precompra en la base de datos"""
        pass
    
    @abstractmethod
    def obtener_por_id(self, precompra_id: int) -> Optional[Precompra]:
        """Obtiene una precompra por su ID"""
        pass
    
    @abstractmethod
    def obtener_por_compra_id(self, compra_id: int) -> Optional[Precompra]:
        """Obtiene una precompra por el ID de la compra asociada"""
        pass
    
    @abstractmethod
    def obtener_por_estudiante_id(self, estudiante_id: int) -> List[Precompra]:
        """Obtiene todas las precompras de un estudiante"""
        pass
    
    @abstractmethod
    def obtener_pendientes_entrega(self) -> List[Precompra]:
        """Obtiene todas las precompras pendientes de entrega"""
        pass
    
    @abstractmethod
    def obtener_por_estudiante_pendientes(self, estudiante_id: int) -> List[Precompra]:
        """Obtiene precompras pendientes de un estudiante específico"""
        pass
    
    @abstractmethod
    def eliminar(self, precompra_id: int) -> bool:
        """Elimina lógicamente una precompra"""
        pass
    
    @abstractmethod
    def existe_precompra_para_compra(self, compra_id: int) -> bool:
        """Verifica si ya existe una precompra para una compra específica"""
        pass