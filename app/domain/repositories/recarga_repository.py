from abc import ABC, abstractmethod
from typing import List, Optional
from domain.models.recarga import Recarga, EstadoRecarga

class RecargaRepository(ABC):
    """
    Interfaz del repositorio de recargas
    Define el contrato para la persistencia de recargas
    """
    
    @abstractmethod
    def guardar(self, recarga: Recarga) -> None:
        """
        Guarda una nueva recarga en la base de datos
        """
        pass
    
    @abstractmethod
    def buscar_por_id(self, recarga_id: str) -> Optional[Recarga]:
        """
        Busca una recarga por su ID
        """
        pass
    
    @abstractmethod
    def buscar_por_referencia_wompi(self, referencia: str) -> Optional[Recarga]:
        """
        Busca una recarga por su referencia de WOMPI
        """
        pass
    
    @abstractmethod
    def buscar_por_usuario(self, usuario_id: str, limite: int = 10) -> List[Recarga]:
        """
        Busca las recargas de un usuario específico
        """
        pass
    
    @abstractmethod
    def buscar_por_estado(self, estado: EstadoRecarga, limite: int = 100) -> List[Recarga]:
        """
        Busca recargas por estado
        """
        pass
    
    @abstractmethod
    def actualizar(self, recarga: Recarga) -> None:
        """
        Actualiza una recarga existente
        """
        pass
    
    @abstractmethod
    def listar_todas(self, offset: int = 0, limite: int = 50) -> List[Recarga]:
        """
        Lista todas las recargas con paginación
        """
        pass