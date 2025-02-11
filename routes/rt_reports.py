# routes/routes_documents.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, Float, cast
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
    # Consulta con join adicional a Metric y ordenamiento por total_time descendente
    time_distribution = (
        db.query(
            Document.name,  # Nombre del documento
            MetricExtraDocument.save_time,  # Tiempo de guardado
            MetricExtraDocument.cpu_save,  # Uso de CPU durante el guardado
            MetricExtraDocument.memory_save,  # Uso de memoria durante el guardado
            MetricExtraDocument.process_time,  # Tiempo de procesamiento
            MetricExtraDocument.cpu_process,  # Uso de CPU durante el procesamiento
            MetricExtraDocument.memory_process,  # Uso de memoria durante el procesamiento
            Metric.total_time,  # Tiempo total (guardado + procesamiento)
            Metric.memory_initial,  # Memoria RAM inicial
            Metric.memory_final,  # Memoria RAM final
            Metric.cpu_initial,  # Uso de CPU inicial
            Metric.cpu_final,  # Uso de CPU final
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .join(Metric, MetricExtraDocument.metric_id == Metric.id)  # Join con Metric
        .order_by(desc(Metric.total_time))  # Ordenar por tiempo total descendente
        .limit(limit)  # Limitar resultados
        .all()
    )

    # Formatear la respuesta
    return [
        {
            "name": doc.name,
            "save_time": doc.save_time,
            "cpu_save": doc.cpu_save,
            "memory_save": doc.memory_save,
            "process_time": doc.process_time,
            "cpu_process": doc.cpu_process,
            "memory_process": doc.memory_process,
            "total_time": doc.total_time,
            "memory_initial": doc.memory_initial,
            "memory_final": doc.memory_final,
            "cpu_initial": doc.cpu_initial,
            "cpu_final": doc.cpu_final,
        }
        for doc in time_distribution
    ]


@router.get("/documents/time_distribution/save")
async def get_time_distribution_save(limit: int = 5, db: Session = Depends(get_db)):
    db.expire_all()

    # Consulta con join adicional a Metric y ordenamiento por total_time descendente
    time_distribution = (
        db.query(
            Document.name,  # Nombre del documento
            MetricExtraDocument.save_time,  # Tiempo de guardado
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .order_by(
            desc(cast(MetricExtraDocument.save_time, Float))
        )  # Convertir a número explícitamente
        .limit(limit)  # Limitar resultados
        .all()
    )

    # Formatear la respuesta
    return [
        {
            "name": doc.name,
            "save_time": doc.save_time,
        }
        for doc in time_distribution
    ]


@router.get("/documents/time_distribution/process")
async def get_time_distribution_process(limit: int = 5, db: Session = Depends(get_db)):
    # Consulta con join adicional a Metric y ordenamiento por total_time descendente
    time_distribution = (
        db.query(
            Document.name,  # Nombre del documento
            MetricExtraDocument.process_time,  # Tiempo de procesamiento
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .order_by(
            desc(MetricExtraDocument.process_time)
        )  # Ordenar por tiempo total descendente
        .limit(limit)  # Limitar resultados
        .all()
    )

    # Formatear la respuesta
    return [
        {
            "name": doc.name,
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


@router.get("/documents/processing_metrics/cpu_save")
async def get_processing_metrics_cpu_save(
    limit: int = 5, db: Session = Depends(get_db)
):
    # Consulta las métricas de procesamiento de documentos con límite
    processing_metrics = (
        db.query(
            Document.name,  # Cambiado de 'id' a 'name'
            MetricExtraDocument.cpu_save,
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .order_by(desc(MetricExtraDocument.cpu_save))
        .limit(limit)  # Aquí se limita la cantidad de registros
        .all()
    )

    return [
        {
            "name": doc.name,  # Cambiado de 'id' a 'name'
            "cpu_save": doc.cpu_save,
        }
        for doc in processing_metrics
    ]


@router.get("/documents/processing_metrics/memory_save")
async def get_processing_metrics_memomy_save(
    limit: int = 5, db: Session = Depends(get_db)
):
    # Consulta las métricas de procesamiento de documentos con límite
    processing_metrics = (
        db.query(
            Document.name,  # Cambiado de 'id' a 'name'
            MetricExtraDocument.memory_save,
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .order_by(desc(MetricExtraDocument.memory_save))
        .limit(limit)  # Aquí se limita la cantidad de registros
        .all()
    )

    return [
        {
            "name": doc.name,  # Cambiado de 'id' a 'name'
            "memory_save": doc.memory_save,
        }
        for doc in processing_metrics
    ]


@router.get("/documents/processing_metrics/cpu_process")
async def get_processing_metrics_cpu_process(
    limit: int = 5, db: Session = Depends(get_db)
):
    # Consulta las métricas de procesamiento de documentos con límite
    processing_metrics = (
        db.query(
            Document.name,  # Cambiado de 'id' a 'name'
            MetricExtraDocument.cpu_process,
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .order_by(desc(MetricExtraDocument.cpu_process))
        .limit(limit)  # Aquí se limita la cantidad de registros
        .all()
    )

    return [
        {
            "name": doc.name,  # Cambiado de 'id' a 'name'
            "cpu_process": doc.cpu_process,
        }
        for doc in processing_metrics
    ]


@router.get("/documents/processing_metrics/memory_process")
async def get_processing_metrics_memory_process(
    limit: int = 5, db: Session = Depends(get_db)
):
    # Consulta las métricas de procesamiento de documentos con límite
    processing_metrics = (
        db.query(
            Document.name,  # Cambiado de 'id' a 'name'
            MetricExtraDocument.memory_process,
        )
        .join(MetricExtraDocument, Document.id == MetricExtraDocument.document_id)
        .order_by(desc(MetricExtraDocument.memory_process))
        .limit(limit)  # Aquí se limita la cantidad de registros
        .all()
    )

    return [
        {
            "name": doc.name,  # Cambiado de 'id' a 'name'
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
