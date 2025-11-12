# infrastructure/utils/text_normalizer.py

import unicodedata
import re

class TextNormalizer:
    """Utilidad para normalizar texto (eliminar tildes, signos y convertir a mayúsculas)"""
    
    @staticmethod
    def normalizar_nombre(texto: str) -> str:
        """
        Normaliza un nombre eliminando tildes y signos especiales,
        y convirtiéndolo a mayúsculas.
        
        Ejemplo: "Julíán Amárílés" -> "JULIAN AMARILES"
        """
        # Eliminar tildes y diacríticos
        texto_sin_tildes = ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Convertir a mayúsculas
        texto_mayusculas = texto_sin_tildes.upper()
        
        # Eliminar caracteres especiales, dejando solo letras, números y espacios
        texto_limpio = re.sub(r'[^A-Z0-9\s]', '', texto_mayusculas)
        
        # Eliminar espacios extras
        texto_final = ' '.join(texto_limpio.split())
        
        return texto_final