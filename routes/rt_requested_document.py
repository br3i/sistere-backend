from models.requested_document import RequestedDocument
from models.database import SessionLocal
from pydantic import BaseModel
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


class RequestedDocumentsResponse(BaseModel):
    id: int
    last_requested_at: datetime
    requested_count: int
    document_id: int

    class Config:
        from_attributes = True


@router.get("/requested_documents", response_model=list[RequestedDocumentsResponse])
async def get_all_requested_documents():
    db: Session = SessionLocal()
    try:
        requested_documents = (
            db.query(RequestedDocument).order_by(RequestedDocument.id).all()
        )
        return [
            RequestedDocumentsResponse(
                id=requested_document.id,  # type: ignore
                last_requested_at=requested_document.last_requested_at,  # type: ignore
                requested_count=requested_document.requested_count,  # type: ignore
                document_id=requested_document.document_id,  # type: ignore
            )
            for requested_document in requested_documents
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error al obtener documentos solicitados"
        )
    finally:
        db.close()
