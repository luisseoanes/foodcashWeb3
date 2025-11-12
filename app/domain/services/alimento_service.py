from typing import List, Optional, Dict, Any
from domain.models.alimento import Alimento
from domain.repositories.alimento_repository import AlimentoRepository
from domain.exceptions.alimento_exceptions import AlimentoNoEncontradoError, AlimentoYaExisteError

class AlimentoService:
    """Servicio de dominio para la lógica de negocio relacionada con Alimentos."""
    
    def __init__(self, alimento_repository: AlimentoRepository):
        self.alimento_repository = alimento_repository
    
    def listar_alimentos(self, filtros: Optional[Dict[str, Any]] = None) -> List[Alimento]:
        return self.alimento_repository.listar_alimentos(filtros)
    
    def obtener_alimento_por_id(self, alimento_id: int) -> Alimento:
        alimento = self.alimento_repository.buscar_por_id(alimento_id)
        if not alimento:
            raise AlimentoNoEncontradoError(f"No existe un alimento con el ID {alimento_id}")
        return alimento
    
    def crear_alimento(self, nombre: str, precio: float, cantidad_en_stock: int,
                        calorias: int, imagen: str, categoria: str) -> Alimento:
        alimento_existente = self.alimento_repository.buscar_por_nombre(nombre)
        if alimento_existente:
            raise AlimentoYaExisteError(f"Ya existe un alimento con el nombre {nombre}")
        
        nuevo_alimento = Alimento.crear(
            nombre=nombre,
            precio=precio,
            cantidad_en_stock=cantidad_en_stock,
            calorias=calorias,
            imagen=imagen,
            categoria=categoria
        )
        return self.alimento_repository.guardar(nuevo_alimento)
    
    def actualizar_alimento(self, alimento_id: int, nombre: Optional[str] = None, 
                            precio: Optional[float] = None, cantidad_en_stock: Optional[int] = None,
                            calorias: Optional[int] = None, imagen: Optional[str] = None, 
                            categoria: Optional[str] = None) -> Alimento:
        alimento = self.obtener_alimento_por_id(alimento_id)

        if nombre and nombre != alimento.nombre:
            alimento_existente = self.alimento_repository.buscar_por_nombre(nombre)
            # 🔑 Si existe pero NO es el mismo alimento -> error
            if alimento_existente and alimento_existente.id != alimento_id:
                raise AlimentoYaExisteError(f"Ya existe un alimento con el nombre {nombre}")

        alimento.actualizar(
            nombre=nombre,
            precio=precio,
            cantidad_en_stock=cantidad_en_stock,
            calorias=calorias,
            imagen=imagen,
            categoria=categoria
        )
        return self.alimento_repository.guardar(alimento)

    
    def eliminar_alimento(self, alimento_id: int) -> bool:
        alimento = self.obtener_alimento_por_id(alimento_id)
        resultado = self.alimento_repository.eliminar(alimento_id)
        if not resultado:
            raise AlimentoNoEncontradoError(f"No se pudo eliminar el alimento con ID {alimento_id}")
        return True


    def disminuir_inventario(self, alimento_id: int, cantidad: int):
        """
        Disminuye el inventario de un alimento específico.
        
        Args:
            alimento_id: ID del alimento a actualizar
            cantidad: Cantidad a disminuir del inventario
            
        Returns:
            Alimento actualizado
            
        Raises:
            AlimentoNoEncontradoError: Si el alimento no existe
            ValueError: Si la cantidad es inválida o el stock es insuficiente
        """
        # Obtener alimento usando el método existente para mantener consistencia
        alimento = self.obtener_alimento_por_id(alimento_id)
        
        if cantidad <= 0:
            raise ValueError("La cantidad a disminuir debe ser mayor que 0")
        
        if alimento.cantidad_en_stock < cantidad:
            raise ValueError(f"Stock insuficiente. Stock actual: {alimento.cantidad_en_stock}, cantidad solicitada: {cantidad}")
        
        # Actualizar la cantidad en stock
        alimento.cantidad_en_stock -= cantidad
        
        # Guardar el alimento actualizado
        return self.alimento_repository.guardar(alimento)