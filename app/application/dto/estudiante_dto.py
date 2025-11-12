# application/dto/estudiante_dto.py

from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional, Union

class EstudianteDTO(BaseModel):
    id: int
    nombre: str
    email: str
    fecha_nacimiento: Optional[Union[str, date, datetime]] = None
    responsableFinanciero: str
    saldo: float
    cedula: str

    @validator('fecha_nacimiento', pre=True)
    def parse_fecha_nacimiento(cls, value):
        if isinstance(value, (date, datetime)):
            return value.strftime("%Y-%m-%d")
        return value

    @validator('saldo', pre=True, always=True)
    def set_saldo_default(cls, value):
        if value is None:
            return 0.0
        return value

class CrearEstudianteDTO(BaseModel):
    """DTO para crear un nuevo estudiante"""
    nombre: str = Field(..., min_length=1, description="Nombre completo del estudiante")
    email: str = Field(..., description="Email del estudiante")
    fecha_nacimiento: str = Field(..., description="Fecha de nacimiento (YYYY-MM-DD)")
    responsable_financiero: str = Field(..., description="Usuario (correo) del responsable financiero")
    cedula: str = Field(..., min_length=1, description="Cédula del estudiante")

class RecargaSaldoDTO(BaseModel):
    monto: float = Field(gt=0, description="Monto a recargar, debe ser mayor que cero")

class DescargaSaldoDTO(BaseModel):
    monto: float = Field(gt=0, description="Monto a descargar, debe ser mayor que cero")