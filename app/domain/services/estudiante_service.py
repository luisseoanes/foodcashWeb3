# domain/services/estudiante_service.py

from typing import List
from domain.models.estudiante import Estudiante
from domain.repositories.estudiante_repository import EstudianteRepository
from domain.exceptions.exceptions import UsuarioNoEncontradoError
from infrastructure.utils.text_normalizer import TextNormalizer

class EstudianteService:
    def __init__(self, estudiante_repository: EstudianteRepository):
        self.estudiante_repository = estudiante_repository
        self.text_normalizer = TextNormalizer()
    
    def crear_estudiante(
        self, 
        nombre: str, 
        email: str, 
        fecha_nacimiento: str, 
        responsable_financiero: str, 
        cedula: str
    ) -> Estudiante:
        """Crea un nuevo estudiante"""
        # Normalizar el nombre (sin tildes/signos, mayúsculas)
        nombre_normalizado = self.text_normalizer.normalizar_nombre(nombre)
        
        # Crear estudiante con saldo inicial 0
        nuevo_estudiante = Estudiante(
            id=None,  # Se asignará en la BD
            nombre=nombre_normalizado,
            email=email,
            fecha_nacimiento=fecha_nacimiento,
            responsableFinanciero=responsable_financiero,
            saldo=0.0,
            cedula=cedula
        )
        
        return self.estudiante_repository.crear(nuevo_estudiante)

    def listar_hijos(self, responsable: str) -> List[Estudiante]:
        estudiantes = self.estudiante_repository.listar_por_responsable(responsable)
        if not estudiantes:
            raise UsuarioNoEncontradoError(f"No se encontraron estudiantes asociados a {responsable}")
        return estudiantes

    def actualizar_saldo_estudiante(self, estudiante_id: int, recarga: float) -> Estudiante:
        estudiante = self.estudiante_repository.obtener_por_id(estudiante_id)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante_id} no encontrado")
        estudiante.recargar_saldo(recarga)
        return self.estudiante_repository.guardar(estudiante)

    def descargar_saldo_estudiante(self, estudiante_id: int, descarga: float) -> Estudiante:
        estudiante = self.estudiante_repository.obtener_por_id(estudiante_id)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante_id} no encontrado")
        estudiante.descargar_saldo(descarga)
        return self.estudiante_repository.guardar(estudiante)

    def buscar_por_cedula(self, cedula: str) -> Estudiante:
        estudiante = self.estudiante_repository.buscar_por_cedula(cedula)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con cédula {cedula} no encontrado")
        return estudiante