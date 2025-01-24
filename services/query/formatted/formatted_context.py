import urllib.parse

def formatted_context(context):
    """
    Procesa el contexto eliminando saltos de línea, decodificando caracteres especiales 
    y corrigiendo los problemas de codificación sin eliminar los caracteres especiales.
    
    Args:
        context (str): Texto del contexto que será procesado.
        
    Returns:
        str: Contexto formateado en una línea con los caracteres correctamente decodificados.
    """
    # Reemplazar saltos de línea por espacios
    cleaned_context = context.replace("\n", " ").strip()
    
    # Decodificar caracteres especiales de URLs (por si existen en el contexto)
    cleaned_context = urllib.parse.unquote(cleaned_context)
    
    # Asegurarnos de que los caracteres Unicode mal interpretados sean correctamente procesados
    cleaned_context = cleaned_context.encode('utf-8').decode('utf-8', errors='ignore')

    return cleaned_context