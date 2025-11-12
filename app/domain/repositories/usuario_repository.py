# domain/repositories/usuario_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List

from domain.models.usuario import Usuario

class UsuarioRepository(ABC):
    """Interfaz para el repositorio de usuarios"""
    
    @abstractmethod
    def guardar(self, usuario: Usuario) -> None:
        """Guarda un usuario en el repositorio"""
        pass
        
    @abstractmethod
    def buscar_por_id(self, id: str) -> Optional[Usuario]:
        """Busca un usuario por su ID"""
        pass
        
    @abstractmethod
    def buscar_por_nombre_usuario(self, nombre_usuario: str) -> Optional[Usuario]:
        """Busca un usuario por su nombre de usuario"""
        pass
        
    @abstractmethod
    def existe_usuario(self, nombre_usuario: str) -> bool:
        """Comprueba si existe un usuario con el nombre de usuario dado"""
        pass

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> None:
        """Actualiza el registro de un usuario en el repositorio"""
        pass

    @abstractmethod
    def actualizar_saldo(self, nombre_usuario: str, nuevo_saldo: float) -> Optional[Usuario]:
        """Actualiza el saldo de un usuario"""
        pass
    
    @abstractmethod
    def listar_por_rol(self, rol: str) -> List[Usuario]:
        """Lista todos los usuarios con un rol específico"""
        pass