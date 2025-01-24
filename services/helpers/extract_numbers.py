import re

patterns = [r"\b\d{3}\b", r"\d+"]

def extract_numbers(query) -> list:
    numbers_extracted = []

    for pattern in patterns:
        matches = re.findall(pattern, query)
        if matches:
            numbers_extracted.extend(matches)

    # Eliminar duplicados y devolver la lista
    return list(set(numbers_extracted))
