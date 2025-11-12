# application/dto/usuario_dto.py

from pydantic import BaseModel, validator, Field
from typing import Optional

class RegistroUsuarioDTO(BaseModel):
    """DTO para los datos de registro de usuario"""
    usuario: str
    contraseña: str
    nombre: str
    rol: str
    
    @validator('usuario')
    def usuario_valido(cls, v):
        if len(v) < 3:
            raise ValueError('El usuario debe tener al menos 3 caracteres')
        return v

    @validator('contraseña')
    def contraseña_valida(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v

class LoginDTO(BaseModel):
    """DTO para los datos de inicio de sesión"""
    usuario: str
    contraseña: str
    
class TokenDTO(BaseModel):
    """DTO para la respuesta del token JWT"""
    access_token: str
    token_type: str = "bearer"

class SaldoUpdateDTO(BaseModel):
    """DTO para actualizar el saldo"""
    monto: float

class UsuarioRespuestaDTO(BaseModel):
    """DTO para la respuesta con datos de usuario"""
    id: str
    usuario: str
    nombre: str
    rol: str
    saldo: float

class UsuarioListaDTO(BaseModel):
    """DTO simplificado para listar usuarios (para selectores)"""
    id: str
    usuario: str
    nombre: str