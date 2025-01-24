import json
from sqlalchemy.orm import Session
from models.metric import Metric
from models.metric_extra_response import MetricExtraResponse


def save_metrics_response(db: Session, metrics_data):
    print(f"[save_metrics_response] db {db}")
    print(f"[save_metrics_response] metrics_data {json.dumps(metrics_data, indent=4)}")

    # memory_initial = metrics_data["memory_usage"]["initial"]
    # memory_final = metrics_data["memory_usage"]["final"]

    metrics = Metric(
        total_time=metrics_data.get("total_time", 0),
        cpu_initial=metrics_data.get("cpu_usage", {}).get("initial", 0),
        cpu_final=metrics_data.get("cpu_usage", {}).get("final", 0),
        memory_initial=metrics_data.get("memory_usage", {}).get("initial", 0),
        memory_final=metrics_data.get("memory_usage", {}).get("final", 0),
    )

    # Guardar las métricas en la base de datos
    db.add(metrics)
    db.commit()
    db.refresh(metrics)

    # Crear la asociación entre la métrica y el documento
    metric_extra_response = MetricExtraResponse(
        metric_id=metrics.id,
        load_model_duration=metrics_data.get("load_duration", 0),
        number_tokens_prompt=metrics_data.get("prompt_eval_count", 0),
        time_evaluating_prompt=metrics_data.get("prompt_eval_duration", 0),
        number_tokens_response=metrics_data.get("eval_count", 0),
        time_generating_response=metrics_data.get("eval_duration", 0),
    )

    # Guardar la asociación en la base de datos
    db.add(metric_extra_response)
    db.commit()

    # Opcionalmente, actualizar las métricas con las asociaciones
    db.refresh(metrics)
    db.refresh(metric_extra_response)

    print(
        f"Metricas guardadas: {metrics}, metricas extra guardadas: {metric_extra_response}"
    )

    return metrics, metric_extra_response
