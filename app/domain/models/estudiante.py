# domain/models/estudiante.py

from datetime import date, datetime
from typing import Optional, Union
from decimal import Decimal

class Estudiante:
    def __init__(
        self, 
        id: int, 
        nombre: str, 
        email: str, 
        fecha_nacimiento: Optional[Union[str, date, datetime]], 
        responsableFinanciero: str, 
        saldo, 
        cedula: str  # Nuevo atributo
    ):
        """
        Crea una instancia de Estudiante.
        """
        self.id = id
        self.nombre = nombre
        self.email = email
        self.fecha_nacimiento = fecha_nacimiento
        self.responsableFinanciero = responsableFinanciero
        # Si saldo es None, asigna 0.0; de lo contrario, lo convierte a Decimal
        if saldo is None:
            self.saldo = Decimal("0.0")
        else:
            self.saldo = saldo if isinstance(saldo, Decimal) else Decimal(saldo)
        self.cedula = cedula

    def recargar_saldo(self, monto: float) -> None:
        """
        Incrementa el saldo del estudiante en la cantidad especificada.
        """
        if monto <= 0:
            raise ValueError("El monto de recarga debe ser mayor que cero")
        self.saldo += Decimal(monto)

    def descargar_saldo(self, monto: float) -> None:
        """
        Disminuye el saldo del estudiante en la cantidad especificada.
        """
        if monto <= 0:
            raise ValueError("El monto de descarga debe ser mayor que cero")
        if Decimal(monto) > self.saldo:
            raise ValueError(f"Saldo insuficiente. Saldo actual: {self.saldo}")
        self.saldo -= Decimal(monto)

    def __repr__(self) -> str:
        return (
            f"Estudiante(id={self.id}, nombre={self.nombre}, email={self.email}, "
            f"fecha_nacimiento={self.fecha_nacimiento}, responsableFinanciero={self.responsableFinanciero}, "
            f"saldo={self.saldo}, cedula={self.cedula})"
        )