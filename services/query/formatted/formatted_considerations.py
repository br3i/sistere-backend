import re


def clean_text(text):
    """Limpia el texto con los patrones definidos."""
    if isinstance(text, list):
        # Si es una lista, conviértela en una cadena
        text = " ".join(
            map(str, text)
        )  # Concatena los elementos de la lista en un solo string

    replace_patterns = [
        (r"[\n\r\f]", " "),  # Reemplaza saltos de línea y de página por un espacio
        (r"\|", ","),  # Reemplaza "|" por una coma
        (r"\s{2,}", " "),  # Reemplaza múltiples espacios por uno solo
    ]
    for pattern, replacement in replace_patterns:
        text = re.sub(pattern, replacement, text)
    return text.strip()


def formatted_considerations(data):
    """Formatea las consideraciones en base a los datos proporcionados."""
    if not isinstance(data, list):
        return "No se encontraron consideraciones para mostrar."

    formatted_list = [
        {
            "Documento": item.get("document_name", "Sin nombre"),
            "Consideraciones": clean_text(
                item.get("considerations", "Sin consideraciones")
            ),
            "A quien se envió copia": item.get("copia", "Sin copia"),
        }
        for item in data
    ]
    return formatted_list
