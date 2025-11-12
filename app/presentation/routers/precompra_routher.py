from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Dict, Any

# DTOs actualizados y necesarios
from application.dto.precompra_dto import (
    PrecompraResponseDTO,
    PrecompraNuevaCreateDTO,         # DTO para crear precompras nuevas
    PrecompraCalculoResponseDTO,     # DTO para la respuesta del cálculo de costo
    PrecompraConDetallesResponseDTO, # DTO para la respuesta con detalles de compra
    PrecompraHistorialDetalladoDTO
)
from domain.services.precompra_service import PrecompraService
from domain.exceptions.exceptions import (
    UsuarioNoEncontradoError, 
    PrecompraError, 
    ProductoNoEncontradoError
)

# Importar TODAS las dependencias de repositorios necesarias
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager
from infrastructure.database.postgresql_precompra_repository import PostgresqlPrecompraRepository
from infrastructure.database.postgresql_estudiante_repository import PostgresqlEstudianteRepository
from infrastructure.database.postgresql_compra_repository import PostgresqlCompraRepository
from infrastructure.database.postgresql_alimento_repository import PostgresqlAlimentoRepository

# --- Router de la API ---
router = APIRouter(prefix="/api/precompras", tags=["Precompras"])


# --- Dependencias actualizadas ---

def get_precompra_service() -> PrecompraService:
    """
    Crea y devuelve una instancia del servicio de precompras con todas
    sus dependencias de repositorios inyectadas.
    """
    cm = PostgresqlConnectionManager()
    # Se necesita el repositorio de compras para el método que crea la compra
    compra_repo = PostgresqlCompraRepository(cm)
    precompra_repo = PostgresqlPrecompraRepository(cm, compra_repo)
    estudiante_repo = PostgresqlEstudianteRepository(cm)
    # El servicio ahora necesita el AlimentoRepository para validar productos y precios
    alimento_repo = PostgresqlAlimentoRepository(cm)
    
    return PrecompraService(precompra_repo, estudiante_repo, compra_repo, alimento_repo)


# --- Endpoints actualizados y completos ---

@router.post("/nueva", response_model=PrecompraResponseDTO, status_code=status.HTTP_201_CREATED)
async def crear_precompra_nueva(
    datos: PrecompraNuevaCreateDTO,
    service: PrecompraService = Depends(get_precompra_service)
) -> PrecompraResponseDTO:
    """
    Crea una nueva precompra a partir de una lista de productos.
    Este es el flujo principal y recomendado.
    """
    try:
        # El servicio espera una lista de diccionarios, no objetos Pydantic
        items_dict = [item.dict() for item in datos.items]
        
        precompra = service.crear_precompra_nueva(
            estudiante_id=datos.estudiante_id,
            items_productos=items_dict,
            costo_adicional=datos.costo_adicional
        )
        return precompra
    except (UsuarioNoEncontradoError, ProductoNoEncontradoError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PrecompraError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno: {str(e)}")

@router.post("/calcular-costo", response_model=PrecompraCalculoResponseDTO)
async def calcular_costo_precompra(
    datos: PrecompraNuevaCreateDTO,
    service: PrecompraService = Depends(get_precompra_service)
):
    """
    Calcula el costo total de una posible precompra sin crearla.
    Útil para mostrar una vista previa al usuario.
    """
    try:
        items_dict = [item.dict() for item in datos.items]
        calculo = service.calcular_costo_precompra(
            items_productos=items_dict,
            costo_adicional=datos.costo_adicional
        )
        return calculo
    except ProductoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno: {str(e)}")

@router.get("/{precompra_id}/detalles", response_model=PrecompraConDetallesResponseDTO)
async def obtener_precompra_con_detalles(
    precompra_id: int,
    service: PrecompraService = Depends(get_precompra_service)
):
    """
    Obtiene una precompra con todos los detalles de la compra y sus productos.
    """
    try:
        detalles = service.obtener_precompra_con_detalles(precompra_id)
        return detalles
    except PrecompraError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno: {str(e)}")

@router.get("/{precompra_id}", response_model=PrecompraResponseDTO)
async def obtener_precompra(
    precompra_id: int,
    service: PrecompraService = Depends(get_precompra_service)
) -> PrecompraResponseDTO:
    """Obtiene los datos básicos de una precompra por su ID."""
    try:
        precompra = service.obtener_precompra_por_id(precompra_id)
        return precompra
    except PrecompraError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.patch("/{precompra_id}/entregar", response_model=PrecompraResponseDTO)
async def marcar_como_entregado(
    precompra_id: int,
    service: PrecompraService = Depends(get_precompra_service)
) -> PrecompraResponseDTO:
    """Marca una precompra como entregada."""
    try:
        precompra = service.marcar_como_entregado(precompra_id)
        return precompra
    except PrecompraError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/{precompra_id}/cancelar-entrega", response_model=PrecompraResponseDTO)
async def cancelar_entrega(
    precompra_id: int,
    service: PrecompraService = Depends(get_precompra_service)
) -> PrecompraResponseDTO:
    """Cancela la entrega de una precompra (la marca como no entregada)."""
    try:
        precompra = service.cancelar_entrega(precompra_id)
        return precompra
    except PrecompraError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{precompra_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_precompra(
    precompra_id: int,
    service: PrecompraService = Depends(get_precompra_service)
):
    """Elimina lógicamente una precompra (la marca como inactiva)."""
    try:
        success = service.eliminar_precompra(precompra_id)
        if not success:
             # Esto puede ocurrir si el ID no existe o ya está inactivo
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Precompra con ID {precompra_id} no encontrada o ya eliminada.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except PrecompraError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Endpoints de Búsqueda ---

@router.get("/estudiante/{estudiante_id}", response_model=List[PrecompraResponseDTO])
async def obtener_precompras_estudiante(
    estudiante_id: int,
    service: PrecompraService = Depends(get_precompra_service)
) -> List[PrecompraResponseDTO]:
    """Obtiene todas las precompras activas de un estudiante."""
    try:
        return service.obtener_precompras_estudiante(estudiante_id)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/estudiante/{estudiante_id}/pendientes", response_model=List[PrecompraResponseDTO])
async def obtener_precompras_pendientes_estudiante(
    estudiante_id: int,
    service: PrecompraService = Depends(get_precompra_service)
) -> List[PrecompraResponseDTO]:
    """Obtiene las precompras pendientes de entrega para un estudiante."""
    try:
        return service.obtener_precompras_pendientes_estudiante(estudiante_id)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/pendientes/todas", response_model=List[PrecompraResponseDTO])
async def obtener_todas_pendientes(
    service: PrecompraService = Depends(get_precompra_service)
) -> List[PrecompraResponseDTO]:
    """Obtiene todas las precompras pendientes de entrega de todos los estudiantes."""
    return service.obtener_precompras_pendientes()


@router.get("/todas/detalladas", response_model=List[PrecompraHistorialDetalladoDTO])
async def obtener_todas_detalladas(
    service: PrecompraService = Depends(get_precompra_service)
):
    """
    Obtiene un historial detallado de TODAS las precompras, incluyendo
    el nombre del estudiante y los items de cada una. Ideal para el panel de admin.
    """
    try:
        return service.obtener_todas_las_precompras_detalladas()
    except Exception as e:
        # Manejo de error genérico para el caso de que la DB falle
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener el historial: {str(e)}"
        )
# En tu router de precompras (precompra_router.py)

@router.get("/estudiante/{estudiante_id}/historial", response_model=List[PrecompraHistorialDetalladoDTO])
async def obtener_historial_estudiante(
    estudiante_id: int,
    service: PrecompraService = Depends(get_precompra_service)
):
    """
    Obtiene el historial detallado de todas las precompras de un estudiante específico.
    """
    # Necesitarás implementar la lógica en tu servicio y repositorio para
    # llamar a la consulta SQL que hicimos para el admin, pero con un WHERE id_estudiante = ...
    return service.obtener_historial_por_estudiante(estudiante_id)