# presentation/routers/estudiante_router.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from application.dto.estudiante_dto import EstudianteDTO, CrearEstudianteDTO, RecargaSaldoDTO, DescargaSaldoDTO
from domain.services.estudiante_service import EstudianteService
from domain.exceptions.exceptions import UsuarioNoEncontradoError
from domain.models.usuario import Usuario
from infrastructure.database.postgresql_repository import PostgresqlConnectionManager
from infrastructure.database.postgresql_estudiante_repository import PostgresqlEstudianteRepository
from presentation.routers.auth_router import get_current_user

router = APIRouter(tags=["Estudiantes"])

def get_estudiante_service():
    connection_manager = PostgresqlConnectionManager()
    estudiante_repo = PostgresqlEstudianteRepository(connection_manager)
    return EstudianteService(estudiante_repo)

# --- Endpoint público (SIN AUTENTICACIÓN) ---

@router.post("/estudiantes", response_model=EstudianteDTO, status_code=201)
def crear_estudiante(
    datos: CrearEstudianteDTO,
    service: EstudianteService = Depends(get_estudiante_service)
):
    """
    Endpoint para crear un nuevo estudiante.
    ⚠️ TEMPORAL: Sin autenticación para pruebas
    """
    try:
        estudiante = service.crear_estudiante(
            nombre=datos.nombre,
            email=datos.email,
            fecha_nacimiento=datos.fecha_nacimiento,
            responsable_financiero=datos.responsable_financiero,
            cedula=datos.cedula
        )
        return EstudianteDTO(**estudiante.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")

# --- Endpoints protegidos (CON AUTENTICACIÓN) ---

@router.get("/estudiantes/{responsable}/hijos", response_model=List[EstudianteDTO])
def listar_hijos(
    responsable: str, 
    service: EstudianteService = Depends(get_estudiante_service),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        hijos = service.listar_hijos(responsable)
        return [EstudianteDTO(**h.__dict__) for h in hijos]
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/estudiantes/{estudiante_id}/recargaSaldo", response_model=EstudianteDTO)
def actualizar_saldo(
    estudiante_id: int,
    datos: RecargaSaldoDTO,
    service: EstudianteService = Depends(get_estudiante_service),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        estudiante = service.actualizar_saldo_estudiante(estudiante_id, datos.monto)
        return EstudianteDTO(**estudiante.__dict__)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/estudiantes/{estudiante_id}/descargaSaldo", response_model=EstudianteDTO)
def descargar_saldo(
    estudiante_id: int,
    datos: DescargaSaldoDTO,
    service: EstudianteService = Depends(get_estudiante_service),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        estudiante = service.descargar_saldo_estudiante(estudiante_id, datos.monto)
        return EstudianteDTO(**estudiante.__dict__)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/estudiantes/cedula/{cedula}", response_model=EstudianteDTO)
def buscar_por_cedula(
    cedula: str, 
    service: EstudianteService = Depends(get_estudiante_service),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        estudiante = service.buscar_por_cedula(cedula)
        return EstudianteDTO(**estudiante.__dict__)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))