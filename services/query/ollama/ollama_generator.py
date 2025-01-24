import os
import time
import json
import asyncio
from typing import AsyncGenerator, List
from dotenv import load_dotenv
from ollama import AsyncClient
from services.helpers.system_usage import get_system_usage
from services.metrics.save_metrics.save_metrics_response import save_metrics_response

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.env")
load_dotenv(dotenv_path)

NOMBRE_ASISTENTE = os.getenv("NOMBRE_ASISTENTE", "Sistete")
AREA_ASISTENCIA = os.getenv("AREA_ASISTENCIA", "No defined")


async def ollama_generator(
    db,
    query: str,
    model_name: str,
    historial_interactions: List[dict],
    context: str,
    sources: str,
    considerations: List[dict],
    use_considerations: bool,
    initial_cpu,
    initial_memory,
    cancel_event: asyncio.Event,
) -> AsyncGenerator:

    print(f"\n[rt_query-ollama_generator] Valor de model_name: {model_name}")
    print("[ollama_generator] use_considerations es: ", use_considerations)
    if not use_considerations:
        considerations = "No hay consideraciones disponibles"  # type: ignore

    # Mensaje inicial para configurar al asistente
    system_message = {
        "role": "system",
        "content": (
            f"""Tu nombre es {NOMBRE_ASISTENTE}, eres asistente de {AREA_ASISTENCIA}. Responde únicamente en español, con tono profesional y preciso. Responde la pregunta del usuario. Si la información necesaria no está disponible en el contexto, fuentes o consideraciones, indica que no puedes responder con precisión y menciona las fuentes, pero siempre establece la relación entre los datos disponibles y la pregunta del usuario. Pregunta del usuario {query}, Lista de Fuentes: {sources}, Lista de Contexto: {context}, Lista de consideraciones: {considerations}"""
        ),
    }

    messages = [system_message] + historial_interactions
    print(
        "[rt_query-ollama-messages] Messages enviados al modelo: ",
        json.dumps(messages, indent=4),
    )

    # Crear una instancia del cliente asincrónico
    async_client = AsyncClient()

    # Llamar al modelo con los mensajes combinados
    async for chunk in await async_client.chat(
        model=model_name,
        messages=messages,
        stream=True,
        options={
            "temperature": 0.8,  # Controla la aleatoriedad de las respuestas. 0 - 1
            "num_thread": 2,  # Establece la cantidad de hilos utilizados por el modelo. depende cpu
            "top_k": 85,  # Restringe la selección de palabras a las más probables. 40 - 100
        },
    ):
        if cancel_event.is_set():
            print("[ollama_generator] Cancelado por desconexión.")
            break

        # Procesar el chunk recibido
        if chunk.get("done"):
            # Obtener las métricas finales de CPU y memoria
            final_cpu, final_memory = get_system_usage()

            metrics_data = {
                "created_at": chunk.get("created_at"),
                "total_duration": chunk.get("total_duration"),
                "load_duration": chunk.get("load_duration"),
                "prompt_eval_count": chunk.get("prompt_eval_count"),
                "prompt_eval_duration": chunk.get("prompt_eval_duration"),
                "eval_count": chunk.get("eval_count"),
                "eval_duration": chunk.get("eval_duration"),
                "cpu_usage": {"initial": initial_cpu, "final": final_cpu},
                "memory_usage": {"initial": initial_memory, "final": final_memory},
            }

            save_metrics_response(db, metrics_data)

            yield {"key": "MESSAGE_DONE", **metrics_data}
        else:
            yield chunk["message"]["content"]
