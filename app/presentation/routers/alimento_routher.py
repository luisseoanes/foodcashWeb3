from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from domain.services.alimento_service import AlimentoService
from application.dto.alimento_dto import (
    AlimentoResponseDTO, 
    AlimentoCreateDTO, 
    AlimentoUpdateDTO,
    DisminuirInventarioDTO
)

# Importa la función desde el módulo de dependencias para evitar el ciclo
from dependencies import get_alimento_service

router = APIRouter(prefix="/api/alimentos", tags=["Alimentos"])

@router.get("/", response_model=List[AlimentoResponseDTO], status_code=status.HTTP_200_OK)
async def listar_alimentos(
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    service: AlimentoService = Depends(get_alimento_service)
):
    try:
        filtros = {}
        if nombre:
            filtros["nombre"] = nombre
        if categoria:
            filtros["categoria"] = categoria
        alimentos = service.listar_alimentos(filtros)
        return [AlimentoResponseDTO.from_orm(a) for a in alimentos]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar alimentos"
        )

@router.get("/{alimento_id}", response_model=AlimentoResponseDTO, status_code=status.HTTP_200_OK)
async def obtener_alimento(
    alimento_id: int,
    service: AlimentoService = Depends(get_alimento_service)
):
    try:
        alimento = service.obtener_alimento_por_id(alimento_id)
        return AlimentoResponseDTO.from_orm(alimento)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/", response_model=AlimentoResponseDTO, status_code=status.HTTP_201_CREATED)
async def crear_alimento(
    alimento_data: AlimentoCreateDTO,
    service: AlimentoService = Depends(get_alimento_service)
):
    try:
        alimento = service.crear_alimento(
            nombre=alimento_data.nombre,
            precio=alimento_data.precio,
            cantidad_en_stock=alimento_data.cantidad_en_stock,
            calorias=alimento_data.calorias,
            imagen=alimento_data.imagen,
            categoria=alimento_data.categoria
        )
        return AlimentoResponseDTO.from_orm(alimento)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{alimento_id}", response_model=AlimentoResponseDTO, status_code=status.HTTP_200_OK)
async def actualizar_alimento(
    alimento_id: int,
    alimento_data: AlimentoUpdateDTO,
    service: AlimentoService = Depends(get_alimento_service)
):
    try:
        alimento = service.actualizar_alimento(
            alimento_id=alimento_id,
            nombre=alimento_data.nombre,
            precio=alimento_data.precio,
            cantidad_en_stock=alimento_data.cantidad_en_stock,
            calorias=alimento_data.calorias,
            imagen=alimento_data.imagen,
            categoria=alimento_data.categoria
        )
        return AlimentoResponseDTO.from_orm(alimento)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{alimento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_alimento(
    alimento_id: int,
    service: AlimentoService = Depends(get_alimento_service)
):
    try:
        service.eliminar_alimento(alimento_id)
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{alimento_id}/disminuir_inventario", response_model=AlimentoResponseDTO, status_code=status.HTTP_200_OK)
async def disminuir_inventario(
    alimento_id: int,
    datos: DisminuirInventarioDTO,
    service: AlimentoService = Depends(get_alimento_service)
):
    """
    Endpoint para disminuir el inventario de un alimento.
    Recibe la cantidad a restar en el body y actualiza el stock del alimento identificado por alimento_id.
    """
    try:
        alimento_actualizado = service.disminuir_inventario(alimento_id, datos.cantidad)
        return AlimentoResponseDTO.from_orm(alimento_actualizado)
    except ValueError as e:
        # Para errores de validación (cantidad negativa, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except KeyError as e:
        # Para cuando el alimento no existe
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alimento con id {alimento_id} no encontrado"
        )
    except Exception as e:
        # Para otros errores inesperados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )