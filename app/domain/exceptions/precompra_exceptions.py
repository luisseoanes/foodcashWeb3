# domain/exceptions/exceptions.py

class DomainException(Exception):
    """Excepción base para errores de dominio"""
    pass

class UsuarioNoEncontradoError(DomainException):
    """Excepción lanzada cuando no se encuentra un usuario/estudiante"""
    pass

class CompraNoEncontradaError(DomainException):
    """Excepción lanzada cuando no se encuentra una compra"""
    pass

class PrecompraError(DomainException):
    """Excepción lanzada para errores relacionados con precompras"""
    pass

class PrecompraNoEncontradaError(PrecompraError):
    """Excepción lanzada cuando no se encuentra una precompra específica"""
    pass

class PrecompraYaExisteError(PrecompraError):
    """Excepción lanzada cuando ya existe una precompra para una compra"""
    pass

class PrecompraYaEntregadaError(PrecompraError):
    """Excepción lanzada cuando se intenta marcar como entregada una precompra ya entregada"""
    pass

class PrecompraNoEntregadaError(PrecompraError):
    """Excepción lanzada cuando se intenta cancelar entrega de una precompra no entregada"""
    pass

class PrecompraNoEliminableError(PrecompraError):
    """Excepción lanzada cuando se intenta eliminar una precompra que no se puede eliminar"""
    pass

class ValidationError(DomainException):
    """Excepción para errores de validación de datos"""
    pass

class RepositoryError(DomainException):
    """Excepción para errores en la capa de repositorio"""
    pass

class ServiceError(DomainException):
    """Excepción para errores en servicios de dominio"""
    pass