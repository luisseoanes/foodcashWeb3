from fastapi import APIRouter, Depends, HTTPException
from typing import List
from application.dto.alimentoBloqueado_dto import BloquearAlimentoDTO, AlimentoBloqueadoDTO
from domain.services.alimentoBloqueado_service import AlimentoBloqueadoService
from domain.exceptions.exceptions import UsuarioNoEncontradoError
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager
from infrastructure.database.postgresql_estudiante_repository import PostgresqlEstudianteRepository
from infrastructure.database.postgresql_alimentoBloqueado_repository import PostgresqlAlimentoBloqueadoRepository

router = APIRouter(tags=["Alimentos Bloqueados"])

class AlimentoBloqueadoController:
    def __init__(self, service: AlimentoBloqueadoService):
        self.service = service

    def bloquear_alimento(self, estudiante_id: int, datos: BloquearAlimentoDTO) -> AlimentoBloqueadoDTO:
        alimento_bloqueado = self.service.bloquear_alimento(estudiante_id, datos.id_alimento)
        return AlimentoBloqueadoDTO(
            id_estudiante=alimento_bloqueado.id_estudiante,
            id_alimento=alimento_bloqueado.id_alimento,
            fecha_bloqueo=alimento_bloqueado.fecha_bloqueo
        )

    def desbloquear_alimento(self, estudiante_id: int, id_alimento: int) -> bool:
        return self.service.desbloquear_alimento(estudiante_id, id_alimento)

    def obtener_alimentos_bloqueados_por_estudiante(self, estudiante_id: int) -> List[AlimentoBloqueadoDTO]:
        alimentos_bloqueados = self.service.obtener_alimentos_bloqueados_por_estudiante(estudiante_id)
        return [
            AlimentoBloqueadoDTO(
                id_estudiante=ab.id_estudiante,
                id_alimento=ab.id_alimento,
                fecha_bloqueo=ab.fecha_bloqueo
            )
            for ab in alimentos_bloqueados
        ]

# Dependencias
def get_alimento_bloqueado_service() -> AlimentoBloqueadoService:
    connection_manager = PostgresqlConnectionManager()
    alimento_bloqueado_repo = PostgresqlAlimentoBloqueadoRepository(connection_manager)
    estudiante_repo = PostgresqlEstudianteRepository(connection_manager)
    return AlimentoBloqueadoService(alimento_bloqueado_repo, estudiante_repo)

def get_alimento_bloqueado_controller(
    service: AlimentoBloqueadoService = Depends(get_alimento_bloqueado_service)
) -> AlimentoBloqueadoController:
    return AlimentoBloqueadoController(service)

# Endpoints
@router.post("/estudiantes/{estudiante_id}/bloquearAlimento", response_model=AlimentoBloqueadoDTO)
async def bloquear_alimento(
    estudiante_id: int,
    datos: BloquearAlimentoDTO,
    controller: AlimentoBloqueadoController = Depends(get_alimento_bloqueado_controller)
) -> AlimentoBloqueadoDTO:
    """
    Bloquea un alimento específico para un estudiante.
    """
    try:
        return controller.bloquear_alimento(estudiante_id, datos)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/estudiantes/{estudiante_id}/desbloquearAlimento/{id_alimento}")
async def desbloquear_alimento(
    estudiante_id: int,
    id_alimento: int,
    controller: AlimentoBloqueadoController = Depends(get_alimento_bloqueado_controller)
):
    """
    Desbloquea un alimento específico para un estudiante.
    """
    try:
        eliminado = controller.desbloquear_alimento(estudiante_id, id_alimento)
        if not eliminado:
            raise HTTPException(status_code=404, detail="Bloqueo no encontrado para el estudiante y alimento especificados")
        return {"message": "Alimento desbloqueado exitosamente"}
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions para mantener el status code original
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/estudiantes/{estudiante_id}/alimentosBloqueados", response_model=List[AlimentoBloqueadoDTO])
async def obtener_alimentos_bloqueados_por_estudiante(
    estudiante_id: int,
    controller: AlimentoBloqueadoController = Depends(get_alimento_bloqueado_controller)
) -> List[AlimentoBloqueadoDTO]:
    """
    Lista todos los alimentos bloqueados para un estudiante específico.
    """
    try:
        return controller.obtener_alimentos_bloqueados_por_estudiante(estudiante_id)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
