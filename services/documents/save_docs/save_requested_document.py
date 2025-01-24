import os
import pytz
import time
import json
from models.database import get_db
from models.document import Document
from models.requested_document import RequestedDocument
from datetime import datetime
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")


def save_requested_document(sources_global):
    print(
        f"[save_requested_document] valor de sources_global : {json.dumps(sources_global, indent=4, default=str)}"
    )
    db = next(get_db())

    # Crear un conjunto para mantener los nombres de documentos únicos
    processed_documents = set()

    for doc in sources_global:
        # print("[save_requested_document] documento a guardar: ", doc)
        document_name = doc["document_name"]
        if not document_name.endswith(".pdf"):
            document_name += ".pdf"
        print("[save_requested_document] doc[document_name]: ", doc["document_name"])

        # Verifica si ya procesaste este documento
        if document_name in processed_documents:
            print(f"[save_requested_document] Documento ya procesado: {document_name}")
            continue

        # Añadir el documento al conjunto de procesados
        processed_documents.add(document_name)

        print("[save_requested_document] Documento a procesar: ", doc["document_name"])

        # Busca el documento en la base de datos por nombre
        document = db.query(Document).filter_by(name=document_name).first()
        # print(f"[save_requested_document] document : {document}")

        if document:
            # Verifica si ya existe un registro de solicitud para el documento
            requested_doc = (
                db.query(RequestedDocument).filter_by(document_id=document.id).first()
            )

            if requested_doc:
                # Si ya existe, actualiza el contador y la fecha
                requested_doc.requested_count += 1  # type: ignore
                requested_doc.last_requested_at = datetime.now(pytz.timezone(TIME_ZONE))  # type: ignore
                print(f"Actualizado: {requested_doc}")
            else:
                # Si no existe, crea un nuevo registro
                requested_doc = RequestedDocument(
                    document_id=document.id,
                    last_requested_at=datetime.now(pytz.timezone(TIME_ZONE)),
                    requested_count=1,
                )
                db.add(requested_doc)
                print(f"Nuevo registro creado: {requested_doc}")
        else:
            print(f"Documento no encontrado: {doc['document_name']}")

    # Realiza el commit de los cambios
    try:
        db.commit()
        print("Cambios guardados exitosamente.")
    except Exception as e:
        db.rollback()
        print(f"Error al guardar los cambios: {e}")
