# routes/routes_documents.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.database import get_db
from models.document import Document
from models.metric import Metric
from models.metric_extra_document import MetricExtraDocument
from models.requested_document import RequestedDocument
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/documents/top_requests")
async def get_top_documents(limit: int = 5, db: Session = Depends(get_db)):
    # Obtener los documentos más solicitados con límite
    documents = (
        db.query(Document)
        .join(RequestedDocument)
        .group_by(Document.id)
        .order_by(func.sum(RequestedDocument.requested_count).desc())
        .limit(limit)  # Aquí se limita la cantidad de registros
        .all()
    )

    return [
        {
            "name": document.name,  # Cambiado de 'id' a 'name'
            "collection_name": document.collection_name,
            "requests_count": db.query(func.sum(RequestedDocument.requested_count))
            .filter(RequestedDocument.document_id == document.id)
            .scalar()
            or 0,  # Asegurar que no sea None
            "path": document.path,
            "physical_path": document.physical_path,
            "created_at": document.created_at.isoformat(),
        }
        for document in documents
    ]


@router.get("/documents/time_distribution")
async def get_time_distribution(limit: int = 5, db: Session = Depends(get_db)):
    # Consulta los tiempos de guardado y procesamiento de documentos con límite
    time_distribution = (
        db.query(
            Document.name,  # Cambiado de 'id' a 'name'
            MetricExtraDocument.save_time,
            MetricExtraDocument.process_time,
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .limit(limit)  # Aquí se limita la cantidad de registros
        .all()
    )

    return [
        {
            "name": doc.name,  # Cambiado de 'id' a 'name'
            "save_time": doc.save_time,
            "process_time": doc.process_time,
        }
        for doc in time_distribution
    ]


@router.get("/documents/processing_metrics")
async def get_processing_metrics(limit: int = 5, db: Session = Depends(get_db)):
    # Consulta las métricas de procesamiento de documentos con límite
    processing_metrics = (
        db.query(
            Document.name,  # Cambiado de 'id' a 'name'
            MetricExtraDocument.cpu_save,
            MetricExtraDocument.memory_save,
            MetricExtraDocument.cpu_process,
            MetricExtraDocument.memory_process,
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .limit(limit)  # Aquí se limita la cantidad de registros
        .all()
    )

    return [
        {
            "name": doc.name,  # Cambiado de 'id' a 'name'
            "cpu_save": doc.cpu_save,
            "memory_save": doc.memory_save,
            "cpu_process": doc.cpu_process,
            "memory_process": doc.memory_process,
        }
        for doc in processing_metrics
    ]


@router.get("/documents/resources_usage")
async def get_resources_usage(limit: int = 5, db: Session = Depends(get_db)):
    # Consulta los datos de uso de CPU y memoria con límite
    resources_usage = (
        db.query(
            Document.name,  # Ahora traemos el `name` del documento
            Metric.cpu_initial,
            Metric.cpu_final,
            Metric.memory_initial,
            Metric.memory_final,
            Metric.total_time,
        )
        .join(MetricExtraDocument, MetricExtraDocument.metric_id == Metric.id)
        .join(Document, Document.id == MetricExtraDocument.document_id)
        .limit(limit)  # Aquí se limita la cantidad de registros
        .all()
    )

    return [
        {
            "name": row[0],  # Accede al 'name' del documento
            "cpu_initial": row[1],
            "cpu_final": row[2],
            "memory_initial": row[3],
            "memory_final": row[4],
            "total_time": row[5],
        }
        for row in resources_usage
    ]
