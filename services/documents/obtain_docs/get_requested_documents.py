from models.database import get_db
from models.requested_document import RequestedDocument

def get_requested_documents():
    db = next(get_db())

    # Contar solo los documentos que han sido solicitados al menos una vez (requested_count > 0)
    requested_documents_count = db.query(RequestedDocument).filter(RequestedDocument.requested_count > 0).count()

    print(f"[get_requested_documents] Total de documentos solicitados (con count > 0): {requested_documents_count}")

    return requested_documents_count
