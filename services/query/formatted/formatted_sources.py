import urllib.parse


def formatted_sources(sources):
    """
    Decodifica, procesa y formatea las fuentes para mostrarlas en un formato compacto sin saltos de línea.

    Args:
        sources (list): Lista de fuentes, donde cada fuente es un diccionario con los campos
                        'file_path', 'document_name' y 'resolve_page'.

    Returns:
        str: String formateado con las fuentes en un solo texto.
    """
    formatted_sources = []

    # Verifica si 'sources' es una lista
    if isinstance(sources, list):
        print("[formatted_sources] sources es una lista")
        for source in sources:
            # Decodificar cada campo relevante
            file_path = urllib.parse.unquote(source.get("file_path", "Desconocido"))
            document_name = urllib.parse.unquote(
                source.get("document_name", "Desconocido")
            )
            resolve_page = source.get("resolve_page", "Desconocido")

            # Crear el texto formateado para la fuente
            formatted_sources.append(
                f"Documento: {document_name}, Página: {resolve_page}, Ubicación: {file_path}"
            )

        # Combinar todas las fuentes en un solo string, separadas por espacios
        return " ".join(formatted_sources)
    else:
        return "No se encontraron fuentes para mostrar."
