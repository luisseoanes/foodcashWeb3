from passlib.context import CryptContext

class PasswordHasher:
    """Clase para hashear y verificar contraseñas usando passlib."""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Genera el hash de una contraseña."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña plana coincide con su hash."""
        return self.pwd_context.verify(plain_password, hashed_password)