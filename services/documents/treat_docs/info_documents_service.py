import PyPDF2
import re
import unicodedata


def extract_text_from_pages(reader):
    """
    Extrae el texto de todas las páginas de un archivo PDF desde el inicio hasta encontrar el patrón "RESUELVE:".

    Args:
        reader (PdfReader): Objeto PdfReader.

    Returns:
        tuple: Texto combinado de todas las páginas desde el inicio hasta encontrar el patrón "RESUELVE:" y el número de la página en la que se encontró.
    """
    total_text = ""
    final_page = None  # Inicializa el número de página donde se encontró "RESUELVE:"
    third_last_page = None
    fallback_page = 0

    replace_patterns = [(r"[\n\r\f]", " "), (r"\s{2,}", " ")]
    clean_patterns = [
        (
            r"^\s*ESPOCH ESCUELA SUPERIOR POLITÉCNICA DE CHIMBORAZO DIRECCIÓN DE SECRETARÍA GENERAL",
            "",
        )
    ]
    search_patterns = [r"unanimidad,.*?RESUELVE\s*:\s*(Art[íi]culo)"]

    try:
        total_pages = len(reader.pages)

        # Iterar desde la página inicial hasta la última página
        for page_num in range(total_pages):
            page = reader.pages[page_num]
            page_text = page.extract_text().strip()

            # Primer procesamiento: Replace patterns
            for pattern, replacement in replace_patterns:
                page_text = re.sub(pattern, replacement, page_text)

            # Segundo procesamiento: Clean patterns
            for pattern, replacement in clean_patterns:
                page_text = re.sub(pattern, replacement, page_text)
            page_text = page_text.strip()
            total_text += (
                page_text  # Concatenar texto de cada página con un espacio en blanco
            )

            # Actualizar la penúltima página (solo si es válida)
            if page_num == len(reader.pages) - 3:
                third_last_page = page_num

            # Buscar el patrón "unanimidad, - - RESUELVE - - : - - Art[ií]culo"
            for search_pattern in search_patterns:
                if re.search(search_pattern, page_text, flags=re.IGNORECASE):
                    final_page = (
                        page_num  # Guardar la página donde se encontró el patrón
                    )
                    print(
                        f"[[info_docs_service]] Patrón encontrado: {search_pattern} en página {page_num}"
                    )
                    break  # Detener la búsqueda después de encontrar el patrón

        total_text = re.sub(r"\…{2,}", "FIRMA", total_text, flags=re.IGNORECASE)
        total_text = re.sub(r"\s{2,}", " ", total_text, flags=re.IGNORECASE)
        if final_page is not None:
            return total_text, final_page
        # Si no se encontró el patrón, devolver la penúltima página
        elif third_last_page is not None:
            return total_text, third_last_page
        else:
            if total_pages <= 2:
                fallback_page = 0
            else:
                fallback_page = total_pages - 3
            return total_text, fallback_page
    except Exception as e:
        print(f"Error extrayendo texto de varias páginas: {e}")
        return "Error extrayendo texto de varias páginas.", 0


def extract_text_resolve(reader, start_page):
    """
    Extrae el texto desde una página específica hasta el final del documento, comenzando en la página especificada.
    Procesa el texto para buscar y remover un patrón específico, almacenando las partes separadamente.

    Args:
        reader (PdfReader): Objeto PdfReader.
        start_page (int): Número de página desde la cual comenzar a extraer (1-indexed).

    Returns:
        str, str:
            - full_text: Texto procesado, manteniendo "SECRETARIO GENERAL".
            - copia: Texto desde "Copia:" dentro de la sección "SECRETARIO GENERAL".
    """
    full_text = ""
    copia = ""

    # Lista de patrones para reemplazar en el texto de cada página
    replace_patterns = [
        (
            r"[\n\r\f]",
            " ",
        ),  # Reemplazar saltos de línea y otros caracteres de nueva línea por un espacio
        (r"\s{2,}", " "),  # Reemplazar múltiples espacios por un solo espacio
        (r"\…{2,}", "FIRMA"),  # Reemplazar secuencias de puntos suspensivos por "FIRMA"
        (
            r"^ESPOCH ESCUELA SUPERIOR POLITÉCNICA DE CHIMBORAZO DIRECCIÓN DE SECRETARÍA GENERAL",
            "",
        ),
        (
            r"^\s*ESPOCH ESCUELA SUPERIOR POLITÉCNICA DE CHIMBORAZO DIRECCIÓN DE SECRETARÍA GENERAL",
            "",
        ),
    ]

    # Patrón para buscar "SECRETARIO GENERAL" y su contenido hasta "Copia:"
    section_pattern = r"(SECRETARIO GENERAL.*?Copia:.*)"

    # Subpatrón para extraer desde "Copia:" dentro de la sección encontrada
    copia_pattern = r"(Copia:.*)"

    try:
        # Iterar desde la página especificada hasta la última página
        for page_num in range(start_page, len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text().strip()

            # Aplicar los patrones de reemplazo
            for pattern, replacement in replace_patterns:
                page_text = re.sub(pattern, replacement, page_text, flags=re.IGNORECASE)

            # Concatenar el texto procesado de cada página
            full_text += page_text

        # Buscar la sección completa desde "SECRETARIO GENERAL"
        section_match = re.search(section_pattern, full_text, flags=re.IGNORECASE)
        if section_match:
            section_text = section_match.group(1)  # Extraer desde "SECRETARIO GENERAL"

            # Dentro de la sección, buscar específicamente "Copia:"
            copia_match = re.search(copia_pattern, section_text, flags=re.IGNORECASE)
            if copia_match:
                copia = copia_match.group(1)  # Extraer desde "Copia:"
                # Mantener el texto antes de "Copia:" en el full_text
                full_text = full_text.replace(copia, "").strip()

        return full_text, copia

    except Exception as e:
        print(f"Error extrayendo resuelve: {e}")
        return "Error extrayendo resuelve.", "Error extrayendo copia"


def extract_text_from_first_page(reader):
    """
    Extrae el texto de la primera página de un archivo PDF usando un PdfReader.

    Args:
        reader (PdfReader): Objeto PdfReader.

    Returns:
        str: Texto extraído de la primera página.
    """
    try:
        first_page = reader.pages[0]
        return first_page.extract_text()
    except Exception as e:
        print(f"Error extrayendo texto de la primera página: {e}")
        return "Error extrayendo texto de la primera página."


def separate_text_into_paragraphs(text):
    # Lista de patrones para dividir el texto
    split_patterns = [
        r"(?=Que,)"  # Captura todo después de "Que," y lo incluye como inicio de cada párrafo
    ]

    # Aplicar cada patrón de separación de manera secuencial
    for pattern in split_patterns:
        text = re.sub(
            pattern, "\n", text
        )  # Sustituimos el patrón por un salto de línea
    # Limpiar el texto resultante, eliminando saltos de línea innecesarios y espacios
    paragraphs = text.split("\n")  # Dividir el texto en párrafos usando saltos de línea
    # Limpiar y asegurar que los párrafos no estén vacíos
    paragraphs = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]

    # Devolver los párrafos
    return paragraphs


def process_paragraphs(paragraphs):
    # Lista de patrones para buscar las coincidencias
    search_patterns = [r"Que,(.*?)(;|:|,)"]

    # Lista para almacenar las coincidencias
    article_entity = []

    # print("Procesando párrafos...")
    for paragraph in paragraphs:
        for pattern in search_patterns:
            matches = re.findall(pattern, paragraph, flags=re.IGNORECASE)
            if matches:
                # Si hay coincidencias, añadirlas a la lista
                for match in matches:
                    article_entity.append(match[0])

    print(
        f"\n[info_docs_service] Total de consideraciones encontradas: {len(article_entity)}"
    )
    return article_entity


def get_resolution(text):
    # Limpieza de espacios y formato antes de realizar la búsqueda
    clean_patterns = [
        (r"\s+", ""),  # Eliminar todos los espacios dentro de la resolución
        (
            r"\s*\.?\s*CP\s*\.\s*",
            ".CP.",
        ),  # Asegurar que no haya espacios alrededor de ".CP."
        (
            r"(RESOLUCI[ÓO]N)(\d+)",
            r"\1 \2",
        ),  # Volver a poner un solo espacio entre "RESOLUCIÓN" y el número
    ]

    # Limpiar el texto utilizando los patrones de limpieza
    for pattern, replacement in clean_patterns:
        text = re.sub(pattern, replacement, text)

    # Patrones de búsqueda de la resolución
    search_patterns = [
        r"RESOLUCI[ÓO]N \d{3,4}\.CP\.\d{4,5}",
        r"RESOLUCI[ÓO]N \d{3,4}\.CP\.\d{4,5}",
        r"RESOLUCI[ÓO]N \d{3,4}\.CP\.\d{4,5}",
        r"(?i)R\s*E\s*S\s*O\s*L\s*U\s*C\s*I\s*Ó\s*N\s*((?:\d\s*){3})[\s\.]*C\s*P\s*[\s\.]*((?:\d\s*){4})",
    ]

    # Buscar la primera coincidencia utilizando los patrones de búsqueda
    resolution = None
    for pattern in search_patterns:
        match = re.search(
            pattern, text
        )  # Usar re.search para encontrar solo la primera coincidencia
        if match:
            resolution = match.group(0)  # Obtener la coincidencia encontrada
            break  # Detener la búsqueda después de encontrar la primera coincidencia

    if not resolution:
        return None, None  # Si no se encuentra ninguna resolución

    # Extraer el número de resolución
    match_number = re.search(r"RESOLUCI[ÓO]N (\d{3,4})", resolution)
    number_resolution = None
    if match_number:
        number_resolution = int(
            match_number.group(1)
        )  # Extraemos el número de resolución

    return resolution, number_resolution


def get_resolve(text):
    """
    Procesa el texto dado buscando el patrón "RESUELVE:", descartando todo lo anterior
    y reemplazando las ocurrencias de ciertas cadenas por un espacio vacío.

    Args:
        text (str): El texto en el cual realizar las modificaciones.

    Returns:
        str: El texto procesado con las modificaciones solicitadas.
    """
    # Buscar "RESUELVE:" y descartar todo el texto antes de él
    # resolve_index = re.search(r"unanimidad.*?RESUELVE:\s*(Art[íi]culo)", text, re.IGNORECASE)

    patterns = [
        r"unanimidad,\s*RESUELVE\s*:\s*(Art[íi]culo)",
        r"unanimidad,.*?RESUELVE\s*:\s*(Art[íi]culo)",
        r"unanimidad,.*?RESUELVE:\s*(Art[íi]culo)",
        r"RESUELVE:\s*(Art[íi]culo)",
        r"RESUELVE:",
    ]

    resolve_index = None
    for pattern in patterns:
        # print("[info_docs_service] get_resolve")
        resolve_index = re.search(pattern, text, flags=re.IGNORECASE)
        if resolve_index:
            break

    # Si se encuentra un patrón "RESUELVE:", procesar el texto
    if resolve_index:
        # Extraer el texto desde "RESUELVE:" hasta el final
        text = text[resolve_index.start() :]

    # Reemplazar las ocurrencias de las cadenas especificadas por un espacio vacío
    text = re.sub(r"\s{2,}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[\n\r\f]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\…{2,}", "FIRMA", text, flags=re.IGNORECASE)

    return text


def get_resolve_to_embed(text):
    """
    Procesa el texto recibido convirtiéndolo en minúsculas, eliminando tildes y
    caracteres especiales, excepto puntos y comas.

    Args:
        text (str): El texto procesado previamente con get_resolve.

    Returns:
        str: El texto limpio, listo para generar embeddings.
    """
    # Convertir todo a minúsculas
    text = text.lower()

    # Convertir la ñ para no perderla después de la normalización
    text = text.replace("ñ", "\001")

    # Eliminar tildes y acentos
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )

    # Restaurar la "ñ" (reemplazar el carácter no imprimible por "ñ")
    text = text.replace("\001", "ñ")

    # Lista de patrones y sus reemplazos
    replacements = [
        (r"[^a-z0-9áéíóúüñ%.,:=()/\- ]", ""),  # Eliminar caracteres no permitidos
        (r"\.\s*-\s*", "."),  # Reemplazar .- o . - por .
        (r"-{2,}", "-"),  # Reducir guiones consecutivos a uno solo
        (r"\.{2,}", "."),  # Reducir puntos consecutivos a uno solo
        (r"\(\.\)", ""),  # Eliminar el punto y los paréntesis (.)
        (r"/{2,}", "/"),  # Reducir barras consecutivas a una sola
        (r"\s{2,}", " "),  # Reducir espacios múltiples a uno solo
        (r";", ","),  # Reemplazar ; por ,
    ]

    # Aplicar cada reemplazo al texto
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return text


def get_info_document(document):
    if document:
        # print(f"\n[info_docs_service] Procesando archivo: {document}")

        with document.file as file:
            reader = PyPDF2.PdfReader(file)

            # Extraer texto de la primera página
            text_name_resolution = extract_text_from_first_page(reader)
            # print("\n\n\Text_name_resolution:\n\n", text_name_resolution)

            resolution, number_resolution = get_resolution(text_name_resolution)

            # Extraer texto de varias páginas
            total_text, final_page = extract_text_from_pages(reader)
            # Extraer texto desde "RESUELVE:" y "Copia:"
            text_resolve, copia = extract_text_resolve(reader, final_page)

            resolve = get_resolve(text_resolve)

            if resolution:
                resolve = resolution + " resuelve: por " + resolve
            # print("\n\n\n[info_docs_service] RESOLVE:\n", resolve)

            resolve_to_embed = get_resolve_to_embed(resolve)
            # print(f"[info_documents_service] resolve_to_embed: {resolve_to_embed[-1000:]}")
            print(
                f"[info_documents_service] len resolve_to_embed: {len(resolve_to_embed)}"
            )
            # time.sleep(4000)

            paragraphs = separate_text_into_paragraphs(total_text)
            # print("\n\n\t [info_docs_service] Paragraphs:", paragraphs)

            # Procesar los párrafos y extraer los artículos y sus entidades
            # print("[info_documents_service] resolution: ", resolution)
            articles_entities = process_paragraphs(paragraphs)
            # time.sleep(200)

            # Imprimir artículos y entidades
            # if articles_entities:
            #     # print("\nArtículos y Entidades encontradas:")
            #     for i, (article_entity, delimiter) in enumerate(articles_entities):
            #         print(f"{i + 1}: {article_entity.strip()}")

        return (
            resolution,
            number_resolution,
            articles_entities,
            copia,
            resolve,
            resolve_to_embed,
            final_page + 1,
        )
    else:
        print("[info_documents_service] No existe el documento.")
        return None, None, None, None, None, None, None
