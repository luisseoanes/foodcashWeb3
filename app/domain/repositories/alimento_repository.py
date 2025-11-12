from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.models.alimento import Alimento

class AlimentoRepository(ABC):
    """Interfaz de repositorio para gestionar Alimentos."""
    
    @abstractmethod
    def listar_alimentos(self, filtros: Optional[Dict[str, Any]] = None) -> List[Alimento]:
        pass

    @abstractmethod
    def buscar_por_id(self, alimento_id: int) -> Optional[Alimento]:
        pass
    
    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> Optional[Alimento]:
        pass
    
    @abstractmethod
    def guardar(self, alimento: Alimento) -> Alimento:
        pass
    
    @abstractmethod
    def eliminar(self, alimento_id: int) -> bool:
        pass
