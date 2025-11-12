from datetime import datetime
from typing import Optional

class AlimentoBloqueado:
    def __init__(
        self, 
        id_estudiante: int, 
        id_alimento: int, 
        fecha_bloqueo: Optional[datetime] = None
    ):
        self.id_estudiante = id_estudiante
        self.id_alimento = id_alimento
        self.fecha_bloqueo = fecha_bloqueo or datetime.now()

    def __repr__(self) -> str:
        return (
            f"AlimentoBloqueado(id_estudiante={self.id_estudiante}, "
            f"id_alimento={self.id_alimento}, fecha_bloqueo={self.fecha_bloqueo})"
        )
