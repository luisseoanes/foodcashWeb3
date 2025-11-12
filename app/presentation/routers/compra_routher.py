from fastapi import APIRouter, Depends, HTTPException
from fastapi import FastAPI
from typing import List
from application.dto.compra_dto import CompraInputDTO, CompraOutputDTO
from domain.services.compra_service import CompraService
from domain.exceptions.exceptions import UsuarioNoEncontradoError, ProductoNoEncontradoError, CompraError
from infrastructure.database.postgresql_compra_repository import PostgresqlCompraRepository
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager,PostgresqlUsuarioRepository
from infrastructure.database.postgresql_producto_repository import PostgresqlProductoRepository

app = FastAPI(debug=True)
router = APIRouter(tags=["compras"])

class CompraController:
    def __init__(self, service: CompraService):
        self.service = service

    def guardar_compra(self, datos: CompraInputDTO) -> CompraOutputDTO:
        return self.service.guardar_compra(datos)

    def obtener_compra(self, compra_id: int) -> CompraOutputDTO:
        compra = self.service.obtener_compra_por_id(compra_id)
        if not compra:
            raise HTTPException(status_code=404, detail="Compra no encontrada")
        return compra

    def obtener_compras_usuario(self, usuario_id: int) -> List[CompraOutputDTO]:
        return self.service.obtener_compras_por_usuario_id(usuario_id)
    
    def obtener_ultimas_compras_usuario(self, usuario_id: int, limit: int = 5) -> List[CompraOutputDTO]:
        """Obtiene las últimas N compras de un usuario"""
        return self.service.obtener_ultimas_compras_por_usuario_id(usuario_id, limit)
    
    def obtener_todas_las_compras(self) -> List[CompraOutputDTO]:
        """Llama al servicio para obtener todas las compras."""
        return self.service.obtener_todas_las_compras()

# Dependencias
def get_compra_service() -> CompraService:
    cm = PostgresqlConnectionManager()
    compra_repo = PostgresqlCompraRepository(cm)
    usuario_repo = PostgresqlUsuarioRepository(cm)
    producto_repo = PostgresqlProductoRepository(cm)
    return CompraService(compra_repo, usuario_repo, producto_repo)

def get_compra_controller(
    service: CompraService = Depends(get_compra_service)
) -> CompraController:
    return CompraController(service)

# Endpoints
@router.post("/guardarCompra", response_model=CompraOutputDTO)
async def guardar_compra(
    datos: CompraInputDTO,
    controller: CompraController = Depends(get_compra_controller)
) -> CompraOutputDTO:
    try:
        return controller.guardar_compra(datos)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProductoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CompraError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/compras/{compra_id}", response_model=CompraOutputDTO)
async def obtener_compra(
    compra_id: int,
    controller: CompraController = Depends(get_compra_controller)
) -> CompraOutputDTO:
    try:
        return controller.obtener_compra(compra_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compras/usuario/{usuario_id}", response_model=List[CompraOutputDTO])
async def obtener_compras_usuario(
    usuario_id: int,
    controller: CompraController = Depends(get_compra_controller)
) -> List[CompraOutputDTO]:
    try:
        return controller.obtener_compras_usuario(usuario_id)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compras/usuario/{usuario_id}/ultimas", response_model=List[CompraOutputDTO])
async def obtener_ultimas_compras_usuario(
    usuario_id: int,
    limit: int = 5,
    controller: CompraController = Depends(get_compra_controller)
) -> List[CompraOutputDTO]:
    try:
        return controller.obtener_ultimas_compras_usuario(usuario_id, limit)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/compras", response_model=List[CompraOutputDTO])
async def obtener_todas_las_compras(
    controller: CompraController = Depends(get_compra_controller),
) -> List[CompraOutputDTO]:
    """
    Obtiene un listado de todas las compras realizadas en el sistema.
    Este endpoint es más eficiente para el dashboard de administrador
    que iterar por cada usuario.
    """
    try:
        return controller.obtener_todas_las_compras()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

