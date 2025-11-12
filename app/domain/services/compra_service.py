from datetime import datetime
from typing import List, Optional,Union
from domain.models.compra import Compra, CompraItem
from application.dto.compra_dto import CompraInputDTO, CompraOutputDTO, CompraItemDTO
from domain.repositories.compra_repository import CompraRepository
from domain.exceptions.exceptions import UsuarioNoEncontradoError, ProductoNoEncontradoError

class CompraService:
    def __init__(
        self,
        compra_repository: CompraRepository,
        usuario_repository,
        producto_repository
    ):
        self.compra_repository = compra_repository
        self.usuario_repository = usuario_repository
        self.producto_repository = producto_repository

    def guardar_compra(self, datos: CompraInputDTO) -> CompraOutputDTO:
        if not self.usuario_repository.buscar_por_id(datos.usuario_id):
            raise UsuarioNoEncontradoError(f"Usuario {datos.usuario_id} no existe.")

        items_compra: List[CompraItem] = []
        for item_dto in datos.items:
            if not self.producto_repository.obtener_producto_por_id(item_dto.producto_id):
                raise ProductoNoEncontradoError(f"Producto {item_dto.producto_id} no existe.")
            items_compra.append(
                CompraItem(
                    producto_id=item_dto.producto_id,
                    cantidad=item_dto.cantidad,
                    precio_unitario=item_dto.precio_unitario,
                )
            )

        compra = Compra(
            usuario_id=datos.usuario_id,
            items=items_compra,
            fecha=datetime.now(),
        )
        compra.calcular_total()
        compra_guardada = self.compra_repository.guardar_compra(compra)
        return self._to_dto(compra_guardada)

    def obtener_compra_por_id(self, compra_id: int) -> Optional[CompraOutputDTO]:
        compra_data = self.compra_repository.obtener_compra_por_id(compra_id)
        if not compra_data:
            return None
        return self._to_dto(compra_data)

    def obtener_compras_por_usuario_id(self, usuario_id: int) -> List[CompraOutputDTO]:
        if not self.usuario_repository.buscar_por_id(usuario_id):
            raise UsuarioNoEncontradoError(f"Usuario {usuario_id} no existe.")
        lista_compras = self.compra_repository.obtener_compras_por_usuario_id(usuario_id)
        return [self._to_dto(c) for c in lista_compras]

    def obtener_ultimas_compras_por_usuario_id(self, usuario_id: int, limit: int = 5) -> List[CompraOutputDTO]:
        if not self.usuario_repository.buscar_por_id(usuario_id):
            raise UsuarioNoEncontradoError(f"Usuario {usuario_id} no existe.")
        lista_compras = self.compra_repository.obtener_ultimas_compras_por_usuario_id(usuario_id, limit)
        return [self._to_dto(c) for c in lista_compras]

    def _to_dto(self, compra: Union[Compra, dict]) -> CompraOutputDTO:
        """
        Convierte un objeto Compra (modelo) o dict (desde repositorio) a CompraOutputDTO,
        asegurándose de incluir todos los campos, incluso nombre_alimento y calorías.
        """
        # Si es instancia de Compra (modelo), creamos DTO básico sin nombre/calorías
        if isinstance(compra, Compra):
            items_dto = [
                CompraItemDTO(
                    producto_id=item.producto_id,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario
                )
                for item in compra.items
            ]
            return CompraOutputDTO(
                id=compra.id,
                fecha=compra.fecha,
                usuario_id=compra.usuario_id,
                total=compra.total,
                items=items_dto
            )

        # Si es dict (de PostgresqlCompraRepository.obtener_compra_por_id)
        compra_dict = compra  # type: ignore
        items_dto = []
        for item_dict in compra_dict["items"]:
            items_dto.append(
                CompraItemDTO(
                    producto_id=item_dict["producto_id"],
                    cantidad=item_dict["cantidad"],
                    precio_unitario=item_dict["precio_unitario"],
                    nombre_alimento=item_dict.get("nombre_alimento"),
                    calorias=item_dict.get("calorias")
                )
            )
        return CompraOutputDTO(
            id=compra_dict["id"],
            fecha=compra_dict["fecha"],
            usuario_id=compra_dict["usuario_id"],
            total=compra_dict["total"],
            items=items_dto
        )
    
    def obtener_todas_las_compras(self) -> List[CompraOutputDTO]:
        """Obtiene todas las compras registradas en el sistema."""
        lista_compras = self.compra_repository.obtener_todas_las_compras()
        return [self._to_dto(c) for c in lista_compras]