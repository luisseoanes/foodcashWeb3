# domain/models/usuario.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from infrastructure.security.password_hasher import PasswordHasher 
# Por simplicidad, no lo inyectamos aquí, se usará en el servicio.

class RolUsuario(str, Enum):
    PADRE = "padre"
    PROFESOR = "profesor"
    ADMIN = "admin"
    VENDEDOR = "vendedor"
    ESTUDIANTE = "estudiante"
    Usuario = "usuario"

@dataclass
class Usuario:
    """Entidad de dominio para Usuario"""
    id: Optional[str]  # Usamos str para consistencia, aunque en DB sea int
    usuario: str
    nombre: str
    rol: RolUsuario
    saldo: float
    contrasena_hash: str
    
    @staticmethod
    def crear(usuario: str, nombre: str, rol: str, contrasena_hash: str):
        """Factory method para crear nuevos usuarios"""
        return Usuario(
            id=None,
            usuario=usuario,
            nombre=nombre,
            rol=RolUsuario(rol),
            saldo=0.0,
            contrasena_hash=contrasena_hash
        )

    # La verificación ahora se hace en el servicio usando el hasher
    def verificar_credenciales(self, contrasena_hash: str) -> bool:
         """Comprueba si la contraseña proporcionada coincide"""
         return self.contrasena_hash == contrasena_hash

    def agregar_saldo(self, cantidad: float) -> None:
        """Agrega saldo a la cuenta del usuario"""
        if cantidad < 0:
            raise ValueError("La cantidad a agregar debe ser positiva")
        self.saldo += cantidad

    def descargar_saldo(self, cantidad: float) -> None:
        """Descarga saldo de la cuenta del usuario"""
        if cantidad < 0:
            raise ValueError("La cantidad a descargar debe ser positiva")
        if self.saldo < cantidad:
            raise ValueError("Saldo insuficiente")
        self.saldo -= cantidad