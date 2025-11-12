# domain/repositories/estudiante_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.models.estudiante import Estudiante

class EstudianteRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, estudiante_id: int) -> Optional[Estudiante]:
        pass

    @abstractmethod
    def guardar(self, estudiante: Estudiante) -> Estudiante:
        pass
    
    @abstractmethod
    def crear(self, estudiante: Estudiante) -> Estudiante:
        """Crea un nuevo estudiante en la base de datos"""
        pass

    @abstractmethod
    def listar_por_responsable(self, responsable: str) -> List[Estudiante]:
        pass

    @abstractmethod
    def buscar_por_cedula(self, cedula: str) -> Optional[Estudiante]:
        """
        Busca y retorna un estudiante por su cédula.
        """
        pass

    @abstractmethod
    def actualizar_saldo(self, estudiante_id: int, nuevo_saldo: float) -> Optional[Estudiante]:
        """
        Actualiza el saldo de un estudiante y retorna el estudiante actualizado.
        """
        pass