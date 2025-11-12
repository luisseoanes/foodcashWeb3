import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

class JWTHandler:
    """Clase para manejar la creación y validación de JWT."""

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un nuevo token de acceso JWT."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        if not SECRET_KEY or not ALGORITHM:
            raise ValueError("JWT_SECRET_KEY y JWT_ALGORITHM deben estar configurados.")
            
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_access_token(self, token: str) -> Optional[dict]:
        """
        Verifica un token de acceso JWT.
        Retorna el payload si el token es válido, None en caso contrario.
        """
        try:
            if not SECRET_KEY or not ALGORITHM:
                raise ValueError("JWT_SECRET_KEY y JWT_ALGORITHM deben estar configurados.")

            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None