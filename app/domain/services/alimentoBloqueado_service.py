from typing import List
from domain.models.alimentoBloqueado import AlimentoBloqueado
from domain.repositories.alimentoBloqueado_repository import AlimentoBloqueadoRepository
from domain.repositories.estudiante_repository import EstudianteRepository
from domain.exceptions.exceptions import UsuarioNoEncontradoError

class AlimentoBloqueadoService:
    def __init__(
        self, 
        alimento_bloqueado_repository: AlimentoBloqueadoRepository,
        estudiante_repository: EstudianteRepository
    ):
        self.alimento_bloqueado_repository = alimento_bloqueado_repository
        self.estudiante_repository = estudiante_repository

    def bloquear_alimento(self, id_estudiante: int, id_alimento: int) -> AlimentoBloqueado:
        # Verificar que el estudiante existe
        estudiante = self.estudiante_repository.obtener_por_id(id_estudiante)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {id_estudiante} no encontrado")
        
        # Crear el bloqueo
        alimento_bloqueado = AlimentoBloqueado(
            id_estudiante=id_estudiante,
            id_alimento=id_alimento
        )
        
        return self.alimento_bloqueado_repository.bloquear_alimento(alimento_bloqueado)

    def desbloquear_alimento(self, id_estudiante: int, id_alimento: int) -> bool:
        # Verificar que el estudiante existe
        estudiante = self.estudiante_repository.obtener_por_id(id_estudiante)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {id_estudiante} no encontrado")
        
        return self.alimento_bloqueado_repository.desbloquear_alimento(id_estudiante, id_alimento)

    def obtener_alimentos_bloqueados_por_estudiante(self, id_estudiante: int) -> List[AlimentoBloqueado]:
        # Verificar que el estudiante existe
        estudiante = self.estudiante_repository.obtener_por_id(id_estudiante)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {id_estudiante} no encontrado")
        
        return self.alimento_bloqueado_repository.obtener_alimentos_bloqueados_por_estudiante(id_estudiante)