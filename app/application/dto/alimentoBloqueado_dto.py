from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BloquearAlimentoDTO(BaseModel):
    id_alimento: int = Field(gt=0, description="ID del alimento a bloquear, debe ser mayor que cero")

class AlimentoBloqueadoDTO(BaseModel):
    id_estudiante: int
    id_alimento: int
    fecha_bloqueo: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
