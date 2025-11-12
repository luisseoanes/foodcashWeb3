# domain/services/autenticacion_service.py

from domain.models.usuario import Usuario
from domain.repositories.usuario_repository import UsuarioRepository
from domain.exceptions.exceptions import UsuarioYaExisteError, CredencialesInvalidasError, UsuarioNoEncontradoError
from infrastructure.security.password_hasher import PasswordHasher
from infrastructure.utils.text_normalizer import TextNormalizer
from typing import List


class AutenticacionService:
    """Servicio de dominio para gestionar la autenticación y usuarios"""
    
    def __init__(self, usuario_repository: UsuarioRepository, password_hasher: PasswordHasher):
        self.usuario_repository = usuario_repository
        self.password_hasher = password_hasher
        self.text_normalizer = TextNormalizer()
        
    def registrar_usuario(self, usuario: str, contrasena: str, nombre: str, rol: str) -> Usuario:
        """Registra un nuevo usuario en el sistema"""
        if self.usuario_repository.existe_usuario(usuario):
            raise UsuarioYaExisteError(f"El usuario '{usuario}' ya existe")
            
        # Validación de dominio
        if len(usuario) < 3:
            raise ValueError("El usuario debe tener al menos 3 caracteres")
        if len(contrasena) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        
        # Normalizar el nombre (sin tildes/signos, mayúsculas)
        nombre_normalizado = self.text_normalizer.normalizar_nombre(nombre)
            
        # Crear y guardar el usuario
        contrasena_hash = self.password_hasher.hash_password(contrasena)
        nuevo_usuario = Usuario.crear(usuario, nombre_normalizado, rol, contrasena_hash)
        self.usuario_repository.guardar(nuevo_usuario)
        
        return nuevo_usuario
        
    def autenticar(self, usuario: str, contrasena: str) -> Usuario:
        """Autentica un usuario con sus credenciales"""
        usuario_encontrado = self.usuario_repository.buscar_por_nombre_usuario(usuario)
        
        if not usuario_encontrado:
            raise UsuarioNoEncontradoError(f"Usuario '{usuario}' no encontrado")
            
        if not self.password_hasher.verify_password(contrasena, usuario_encontrado.contrasena_hash):
            raise CredencialesInvalidasError("Credenciales incorrectas")
            
        return usuario_encontrado
    
    def obtener_usuario_por_id(self, usuario_id: str) -> Usuario:
        """Obtiene un usuario por su ID (como string)."""
        usuario = self.usuario_repository.buscar_por_id(usuario_id)
        
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID '{usuario_id}' no encontrado")
            
        return usuario

    def obtener_usuario_por_nombre(self, nombre_usuario: str) -> Usuario:
        """Obtiene un usuario por su nombre de usuario."""
        usuario = self.usuario_repository.buscar_por_nombre_usuario(nombre_usuario)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario '{nombre_usuario}' no encontrado")
        return usuario
    
    def listar_usuarios_por_rol(self, rol: str) -> List[Usuario]:
        """Lista todos los usuarios con un rol específico."""
        return self.usuario_repository.listar_por_rol(rol)

    def actualizar_saldo_usuario(self, nombre_usuario: str, recarga: float) -> Usuario:
        """Recarga el saldo de un usuario."""
        usuario_actual = self.usuario_repository.buscar_por_nombre_usuario(nombre_usuario)
        if not usuario_actual:
            raise UsuarioNoEncontradoError("Usuario no encontrado")

        usuario_actual.agregar_saldo(recarga)
        
        usuario_actualizado = self.usuario_repository.actualizar_saldo(nombre_usuario, usuario_actual.saldo)
        if not usuario_actualizado:
             raise RuntimeError("No se pudo actualizar el saldo.")
             
        return usuario_actualizado
    
    def descargar_saldo_usuario(self, nombre_usuario: str, descarga: float) -> Usuario:
        """Descarga saldo de un usuario."""
        usuario_actual = self.usuario_repository.buscar_por_nombre_usuario(nombre_usuario)
        if not usuario_actual:
            raise UsuarioNoEncontradoError("Usuario no encontrado")

        usuario_actual.descargar_saldo(descarga)

        usuario_actualizado = self.usuario_repository.actualizar_saldo(nombre_usuario, usuario_actual.saldo)
        if not usuario_actualizado:
             raise RuntimeError("No se pudo actualizar el saldo.")

        return usuario_actualizado