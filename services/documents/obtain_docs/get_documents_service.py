import os
from sqlalchemy.orm import Session
from models.database import get_db
from models.document import Document
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH")


def get_documents(directory=DOCUMENTS_PATH):
    if directory is None:
        print("El directorio no está especificado.")
        return []
    print(
        f"Accediendo al directorio: {os.path.abspath(directory)}"
    )  # Verifica la ruta absoluta
    if not os.path.exists(directory):
        print(f"El directorio {directory} no existe.")
        return []

    documents = os.listdir(directory)
    print(f"Archivos encontrados: {documents}")
    return documents
