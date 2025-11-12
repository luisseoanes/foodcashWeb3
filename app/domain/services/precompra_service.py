from typing import List, Dict, Any
from datetime import datetime

# Importamos los modelos que ahora usarán float
from domain.models.precompra import Precompra 
from domain.models.compra import Compra, CompraItem 

from domain.repositories.precompra_repository import PrecompraRepository
from domain.repositories.estudiante_repository import EstudianteRepository
from domain.repositories.compra_repository import CompraRepository
from domain.repositories.alimento_repository import AlimentoRepository
from domain.exceptions.exceptions import (
    UsuarioNoEncontradoError, PrecompraError, ProductoNoEncontradoError
)

class PrecompraService:
    def __init__(
        self, precompra_repo: PrecompraRepository, estudiante_repo: EstudianteRepository,
        compra_repo: CompraRepository, alimento_repo: AlimentoRepository
    ):
        self.precompra_repo = precompra_repo
        self.estudiante_repo = estudiante_repo
        self.compra_repo = compra_repo
        self.alimento_repo = alimento_repo
    
    def crear_precompra_nueva(
        self, estudiante_id: int, items_productos: List[Dict[str, Any]],
        costo_adicional: float = 100.0 
    ) -> Precompra:
        estudiante = self.estudiante_repo.obtener_por_id(estudiante_id)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante_id} no encontrado")
        
        items_compra = []
        costo_total_productos = 0.0
        
        for item_data in items_productos:
            producto_id = item_data.get('producto_id')
            cantidad = item_data.get('cantidad', 1)
            
            alimento = self.alimento_repo.buscar_por_id(producto_id)
            if not alimento:
                raise ProductoNoEncontradoError(f"Producto con ID {producto_id} no encontrado")
            
            if alimento.cantidad_en_stock < cantidad:
                raise PrecompraError(f"Stock insuficiente para {alimento.nombre}")
            
            # El precio del alimento viene como Decimal, lo convertimos a float para los cálculos
            precio_unitario = float(alimento.precio) 
            costo_total_productos += precio_unitario * cantidad
            
            items_compra.append(CompraItem(
                producto_id=producto_id, cantidad=cantidad, precio_unitario=precio_unitario
            ))
        
        costo_total_final = costo_total_productos + (costo_adicional * sum(i.cantidad for i in items_compra))
        
        precompra = Precompra(
            id_estudiante=estudiante_id, fecha_precompra=datetime.now(),
            costo_total=costo_total_final, costo_adicional=costo_adicional,
            entregado=False, activo=True, fecha_creacion=datetime.now()
        )
        
        return self.precompra_repo.crear_precompra_con_compra(precompra, items_compra)
    
    def crear_precompra_desde_compra_existente(
        self, 
        compra_id: int, 
        estudiante_id: int, 
        costo_adicional: float = float('100.00')
    ) -> Precompra:
        """
        Crea una nueva precompra basada en una compra existente.
        MÉTODO LEGACY - Mantiene compatibilidad con el código anterior
        """
        
        # Validar que el estudiante existe
        estudiante = self.estudiante_repo.obtener_por_id(estudiante_id)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante_id} no encontrado")
        
        # Validar que la compra existe
        compra = self.compra_repo.obtener_compra_por_id(compra_id)
        if not compra:
            pass

        # Verificar que no existe ya una precompra para esta compra
        if self.precompra_repo.existe_precompra_para_compra(compra_id):
            raise PrecompraError(f"Ya existe una precompra para la compra {compra_id}")
        
        # Calcular costo total con recargo
        cantidad_items = sum(item['cantidad'] for item in compra['items'])
        costo_original = float(str(compra['total']))
        recargo_total = costo_adicional * cantidad_items
        costo_total_final = costo_original + recargo_total
        
        # Crear la precompra
        precompra = Precompra(
            id_compra=compra_id,
            id_estudiante=estudiante_id,
            fecha_precompra=datetime.now(),
            costo_total=costo_total_final,
            costo_adicional=costo_adicional,
            entregado=False,
            activo=True,
            fecha_creacion=datetime.now()
        )
        
        return self.precompra_repo.guardar(precompra)
    
    def marcar_como_entregado(self, precompra_id: int) -> Precompra:
        """Marca una precompra como entregada"""
        precompra = self.precompra_repo.obtener_por_id(precompra_id)
        if not precompra:
            raise PrecompraError(f"Precompra con ID {precompra_id} no encontrada")
        
        # Usar el método del repositorio que es más eficiente
        success = self.precompra_repo.marcar_como_entregado(precompra_id)
        if not success:
            raise PrecompraError(f"No se pudo marcar como entregada la precompra {precompra_id}")
        
        # Retornar la precompra actualizada
        return self.precompra_repo.obtener_por_id(precompra_id)
    
    def cancelar_entrega(self, precompra_id: int) -> Precompra:
        """Cancela la entrega de una precompra"""
        precompra = self.precompra_repo.obtener_por_id(precompra_id)
        if not precompra:
            raise PrecompraError(f"Precompra con ID {precompra_id} no encontrada")
        
        if not precompra.entregado:
            raise PrecompraError("La precompra no está marcada como entregada")
        
        precompra.cancelar_entrega()
        return self.precompra_repo.guardar(precompra)
    
    def obtener_precompras_estudiante(self, estudiante_id: int) -> List[Precompra]:
        """Obtiene todas las precompras de un estudiante"""
        estudiante = self.estudiante_repo.obtener_por_id(estudiante_id)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante_id} no encontrado")
        
        return self.precompra_repo.obtener_por_estudiante_id(estudiante_id)
    
    def obtener_precompras_pendientes(self) -> List[Precompra]:
        """Obtiene todas las precompras pendientes de entrega"""
        return self.precompra_repo.obtener_pendientes_entrega()
    
    def obtener_precompras_pendientes_estudiante(self, estudiante_id: int) -> List[Precompra]:
        """Obtiene precompras pendientes de un estudiante específico"""
        estudiante = self.estudiante_repo.obtener_por_id(estudiante_id)
        if not estudiante:
            raise UsuarioNoEncontradoError(f"Estudiante con ID {estudiante_id} no encontrado")
        
        return self.precompra_repo.obtener_por_estudiante_pendientes(estudiante_id)
    
    def obtener_precompra_por_id(self, precompra_id: int) -> Precompra:
        """Obtiene una precompra por su ID"""
        precompra = self.precompra_repo.obtener_por_id(precompra_id)
        if not precompra:
            raise PrecompraError(f"Precompra con ID {precompra_id} no encontrada")
        return precompra
    
    def obtener_precompra_con_detalles(self, precompra_id: int) -> Dict[str, Any]:
        """
        Obtiene una precompra junto con los detalles de la compra asociada
        
        Returns:
            Dict con estructura: {
                'precompra': Precompra object,
                'compra': dict con detalles de la compra
            }
        """
        resultado = self.precompra_repo.obtener_precompra_con_detalles_compra(precompra_id)
        if not resultado:
            raise PrecompraError(f"Precompra con ID {precompra_id} no encontrada")
        return resultado
    
    def eliminar_precompra(self, precompra_id: int) -> bool:
        """Elimina una precompra"""
        precompra = self.precompra_repo.obtener_por_id(precompra_id)
        if not precompra:
            raise PrecompraError(f"Precompra con ID {precompra_id} no encontrada")
        
        if precompra.entregado:
            raise PrecompraError("No se puede eliminar una precompra que ya ha sido entregada")
        
        return self.precompra_repo.eliminar(precompra_id)
    
    def calcular_costo_precompra(
        self,
        items_productos: List[Dict[str, Any]],
        costo_adicional: float = float('100.00')
    ) -> Dict[str, Any]:
        """
        Calcula el costo total de una precompra sin crearla.
        Útil para mostrar preview de costos al usuario.
        
        Returns:
            Dict con desglose de costos: {
                'costo_productos': float,
                'cantidad_items': int,
                'costo_adicional_por_item': float,
                'costo_adicional_total': float,
                'costo_total': float,
                'detalle_productos': List[Dict]
            }
        """
        costo_productos = float('0.00')
        cantidad_total = 0
        detalle_productos = []
        
        for item_data in items_productos:
            producto_id = item_data.get('producto_id')
            cantidad = item_data.get('cantidad', 1)
            
            alimento = self.alimento_repo.buscar_por_id(producto_id)
            if not alimento:
                raise ProductoNoEncontradoError(f"Producto con ID {producto_id} no encontrado")
            
            subtotal = alimento.precio * cantidad
            costo_productos += subtotal
            cantidad_total += cantidad
            
            detalle_productos.append({
                'producto_id': producto_id,
                'nombre': alimento.nombre,
                'precio_unitario': alimento.precio,
                'cantidad': cantidad,
                'subtotal': subtotal
            })
        
        costo_adicional_total = costo_adicional * cantidad_total
        costo_total = costo_productos + costo_adicional_total
        
        return {
            'costo_productos': costo_productos,
            'cantidad_items': cantidad_total,
            'costo_adicional_por_item': costo_adicional,
            'costo_adicional_total': costo_adicional_total,
            'costo_total': costo_total,
            'detalle_productos': detalle_productos
        }
    
    def obtener_todas_las_precompras_detalladas(self) -> List[dict]:
        return self.precompra_repo.obtener_todas_con_detalles()
    
    def obtener_historial_por_estudiante(self, estudiante_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene el historial detallado de precompras para un estudiante específico.
        """
        # Este método llama al repositorio para hacer el trabajo pesado.
        return self.precompra_repo.obtener_historial_por_estudiante(estudiante_id)