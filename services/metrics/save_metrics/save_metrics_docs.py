from sqlalchemy.orm import Session
from models.metric import Metric
from models.metric_extra_document import MetricExtraDocument
import time


def save_metrics_docs(
    db: Session,
    document_id: int,
    execution_times: dict,
    cpu_usage: dict,
    memory_usage: dict,
):
    # print("\n\n[save_metrics]")
    # print(f"[save_metrics] execution_times: {execution_times}")
    # print(f"[save_metrics] cpu_usage: {cpu_usage}")
    # print(f"[save_metrics] memory_usage: {memory_usage}")
    metrics = Metric(
        total_time=execution_times.get("total_time", 0),
        cpu_initial=cpu_usage.get("initial", 0),
        cpu_final=cpu_usage.get("final", 0),
        memory_initial=memory_usage.get("initial", 0),
        memory_final=memory_usage.get("final", 0),
    )

    # Guardar las métricas en la base de datos
    db.add(metrics)
    db.commit()
    db.refresh(metrics)

    # Crear la asociación entre la métrica y el documento
    metric_extra_document = MetricExtraDocument(
        metric_id=metrics.id,
        document_id=document_id,
        save_time=execution_times.get("save_time", 0),
        cpu_save=cpu_usage.get("save", 0),
        memory_save=memory_usage.get("save", 0),
        process_time=execution_times.get("process_time", 0),
        cpu_process=cpu_usage.get("process", 0),
        memory_process=memory_usage.get("process", 0),
    )

    # Guardar la asociación en la base de datos
    db.add(metric_extra_document)
    db.commit()

    # Opcionalmente, actualizar las métricas con las asociaciones
    db.refresh(metrics)
    db.refresh(metric_extra_document)

    print(
        f"Metricas guardadas: {metrics}, metricas extra guardadas {metric_extra_document}"
    )

    return metrics, metric_extra_document
