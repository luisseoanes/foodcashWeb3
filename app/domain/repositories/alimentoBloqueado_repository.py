from abc import ABC, abstractmethod
from typing import List, Optional
from domain.models.alimentoBloqueado import AlimentoBloqueado

class AlimentoBloqueadoRepository(ABC):
    @abstractmethod
    def bloquear_alimento(self, alimento_bloqueado: AlimentoBloqueado) -> AlimentoBloqueado:
        """
        Bloquea un alimento para un estudiante específico.
        """
        pass

    @abstractmethod
    def desbloquear_alimento(self, id_estudiante: int, id_alimento: int) -> bool:
        """
        Desbloquea un alimento para un estudiante específico.
        """
        pass

    @abstractmethod
    def obtener_alimentos_bloqueados_por_estudiante(self, id_estudiante: int) -> List[AlimentoBloqueado]:
        """
        Obtiene todos los alimentos bloqueados para un estudiante.
        """
        pass

    @abstractmethod
    def existe_bloqueo(self, id_estudiante: int, id_alimento: int) -> bool:
        """
        Verifica si ya existe un bloqueo para el estudiante y alimento específico.
        """
        pass
