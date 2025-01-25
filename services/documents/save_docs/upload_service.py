import os
import pytz
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from models.database import get_db
from models.document import Document
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documents")


def get_files(directory=DOCUMENTS_PATH):
    print(
        f"Accediendo al directorio: {os.path.abspath(directory)}"
    )  # Verifica la ruta absoluta
    if not os.path.exists(directory):
        print(f"El directorio {directory} no existe.")
        return []

    files = os.listdir(directory)
    print(f"Archivos encontrados: {files}")
    return files


def check_document_exists(document_name, collection_name):
    # print(
    #     f"[UPLOAD_SERVICE] Llega con estos valores: dn:{document_name} y cn:{collection_name}"
    # )

    try:
        # Obtener la sesión de la base de datos
        db_session = next(get_db())

        # Realizar una consulta en la base de datos buscando coincidencias
        document = (
            db_session.query(Document)
            .filter(
                Document.name == document_name,
                Document.collection_name == collection_name,
            )
            .first()
        )  # Obtener solo el primer resultado

        # Si se encuentra un documento, significa que ya existe
        if document:
            print(f"[UPLOAD_SERVICE] Documento ya existe en la base de datos.")
            return True
        else:
            print(f"[UPLOAD_SERVICE] Documento no encontrado en la base de datos.")
            return False

    except Exception as e:
        print(f"Error al comprobar la existencia del documento: {e}")
        return False


async def save_document(file, collection_name: str, public_url, physical_path=None):
    """
    Guarda un archivo en Supabase y registra su información en la base de datos.
    Esta versión no guarda el archivo en el sistema de archivos local.

    :param file: Objeto de archivo cargado por el usuario.
    :param collection_name: Nombre de la colección asociada al documento.
    :param storage_path: Ruta donde el archivo está almacenado en Supabase.
    :return: Documento registrado en la base de datos o None si ocurre un error.
    """
    db = next(get_db())

    try:
        # Crear un nuevo documento en la base de datos
        document = Document(
            name=file.filename,
            collection_name=collection_name,
            path=public_url,
            physical_path=physical_path,
            created_at=datetime.now(pytz.timezone(TIME_ZONE)),
            embeddings_uuids=[],
        )

        # Registrar el documento en la base de datos
        db.add(document)
        db.commit()
        db.refresh(document)  # Obtener el documento recién creado para devolverlo

        return document

    except Exception as e:
        print(f"Error al guardar el documento en la base de datos: {e}")
        db.rollback()
        return None
    finally:
        db.close()
