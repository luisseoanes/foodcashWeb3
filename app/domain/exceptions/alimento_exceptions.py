class AlimentoNoEncontradoError(Exception):
    """Excepción lanzada cuando un alimento no es encontrado."""
    pass

class AlimentoYaExisteError(Exception):
    """Excepción lanzada cuando se intenta crear un alimento con un nombre que ya existe."""
    pass

class StockInsuficienteError(Exception):
    """Excepción lanzada cuando no hay suficiente stock de un alimento."""
    pass