import unicodedata
import re


def clean_filename(filename: str) -> str:
    # Paso 1: Convertir a minúsculas
    filename = filename.lower()

    # Paso 2: Normalizar y eliminar acentos de las vocales con tildes
    filename = "".join(
        c
        for c in unicodedata.normalize("NFD", filename)
        if unicodedata.category(c) != "Mn"
    )

    # Paso 3: Eliminar caracteres especiales, dejando solo letras y números
    filename = re.sub(r"[^a-z0-9áéíóúü]", "", filename)

    return filename
