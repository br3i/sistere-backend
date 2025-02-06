# routes/routes_query.py
import os
import time
import traceback
import json
import uuid
import pytz
import asyncio
from sqlalchemy.orm import Session
from models.database import SessionLocal
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from services.helpers.system_usage import get_system_usage
from services.documents.obtain_docs.context_sources_service import get_context_sources
from services.query.ollama.ollama_generator import ollama_generator
from services.query.formatted.formatted_history import formatted_history
from services.query.formatted.formatted_sources import formatted_sources
from services.query.formatted.formatted_context import formatted_context
from services.query.formatted.formatted_considerations import formatted_considerations
from services.query.feedback.save_feedback import save_feedback
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

TIME_ZONE = os.getenv("TIME_ZONE", "America/Mexico_City")
SESSION_LIMIT = int(os.getenv("SESSION_LIMIT", "15"))
INTERACTION_LIMIT = int(os.getenv("INTERACTION_LIMIT", "5"))
INACTIVITY_LIMIT = timedelta(minutes=int(os.getenv("INACTIVITY_LIMIT", "2")))

session_data = {}

router = APIRouter()


def clean_inactive_sessions(user_session_uuid):
    now = datetime.now(pytz.timezone(TIME_ZONE))
    sessions_to_remove = []

    # Recorre todas las sesiones
    for (
        user_session_uuid_key,
        session_info,
    ) in session_data.items():  # Cambié el nombre aquí
        last_interaction_time = session_info.get("last_interaction_time")
        if last_interaction_time:
            inactivity_duration = now - last_interaction_time
            if inactivity_duration > INACTIVITY_LIMIT:
                sessions_to_remove.append(user_session_uuid_key)

    # Elimina las sesiones inactivas
    for user_session_uuid_key in sessions_to_remove:
        print(
            f"[clean_inactive_sessions] Eliminando sesión inactiva: {user_session_uuid_key}"
        )
        session_data.pop(user_session_uuid_key)


# Función para eliminar sesiones antiguas si el límite de sesiones es excedido
def clean_old_sessions():
    if len(session_data) > SESSION_LIMIT:
        # Ordenar sesiones por la fecha de la última interacción
        sorted_sessions = sorted(
            session_data.items(),
            key=lambda x: x[1].get(
                "last_interaction_time", datetime.now(pytz.timezone(TIME_ZONE))
            ),
        )
        oldest_session_uuid = sorted_sessions[0][0]
        print(
            f"[clean_old_sessions] Eliminando la sesión más antigua: {oldest_session_uuid}"
        )
        session_data.pop(oldest_session_uuid)


# Función para limpiar interacciones antiguas si se excede el límite de interacciones
def clean_old_interactions(user_session_uuid):
    interactions = session_data[user_session_uuid]["interactions"]
    if len(interactions) > INTERACTION_LIMIT:
        # Eliminar la interacción más antigua
        oldest_interaction = interactions.pop(0)
        print(
            f"[clean_old_interactions] Eliminando la interacción más antigua: {oldest_interaction['interaction_uuid']}"
        )


class QueryModel(BaseModel):
    user_session_uuid: str
    query: str
    use_considerations: bool
    n_documents: int
    word_list: List[str]


class FeedbackQueryModel(BaseModel):
    user_session_uuid: str
    interaction_uuid: str
    model_name: str
    use_considerations: bool
    n_documents: int
    word_list: List[str]
    feedback_type: str
    score: str
    text: Optional[str] = None


class AddResponseQueryModel(BaseModel):
    user_session_uuid: str
    interaction_uuid: str
    full_response: str


@router.post("/process_feedback")
async def process_feedback(feedback_query_model: FeedbackQueryModel):
    # print("[rt_query] user_session_uuid: ", feedback_query_model.user_session_uuid)
    # print("[rt_query] interaction_uuid: ", feedback_query_model.interaction_uuid)
    # print("[rt_query] model_name: ", feedback_query_model.model_name)
    # print("[rt_query] feedback_type: ", feedback_query_model.feedback_type)
    # print("[rt_query] score: ", feedback_query_model.score)
    # print("[rt_query] text: ", feedback_query_model.text)

    user_session_uuid = feedback_query_model.user_session_uuid
    interaction_uuid = feedback_query_model.interaction_uuid
    model_name = feedback_query_model.model_name
    use_considerations = feedback_query_model.use_considerations
    n_documents = (feedback_query_model.n_documents,)
    word_list = (feedback_query_model.word_list,)
    feedback_type = feedback_query_model.feedback_type
    score = feedback_query_model.score
    text = feedback_query_model.text

    user_data = session_data.get(user_session_uuid)

    if user_data:
        # Acceder a la lista de interacciones
        interactions = user_data.get("interactions", [])

        # Buscar la interacción correspondiente
        for interaction in interactions:
            if interaction["interaction_uuid"] == interaction_uuid:
                query = interaction.get("query", "")
                context = interaction.get("context", "")
                full_response = interaction.get("full_response", "")
                sources = interaction.get("sources", "")

                # Guardar el feedback
                result_save_feedback = save_feedback(
                    model_name,
                    use_considerations,
                    n_documents,
                    word_list,
                    feedback_type,
                    score,
                    text,
                    query,
                    context,
                    full_response,
                    sources,
                )

                print("[rt_query] result_save_feedback: ", result_save_feedback)

                if score == "👎" or score == "😞" or score == "🙁":
                    # Eliminar la interacción si el feedback es "pulgar abajo"
                    interactions.pop(interactions.index(interaction))
                    print(f"Interacción ELIMINADA : {interaction_uuid}")
                    print(
                        f"Interacción ELIMINADA, valor actual de session_data \n{json.dumps(session_data, indent=4, default=str)}"
                    )

                # No hacemos nada en caso de "pulgar arriba" más allá de guardar el feedback
                break
    else:
        print(f"No se encontró la sesión para el uuid: {user_session_uuid}")


@router.post("/add_response")
async def add_response(add_response_query: AddResponseQueryModel):
    # print("[rt_query] user_session_uuid: str: ", add_response_query.user_session_uuid)
    # print("[rt_query] interaction_uuid: ", add_response_query.interaction_uuid)
    # print("[rt_query] full_response: ", add_response_query.full_response)

    user_session_uuid = add_response_query.user_session_uuid
    interaction_uuid = add_response_query.interaction_uuid
    full_response = add_response_query.full_response

    if user_session_uuid not in session_data:
        print(f"[rt_query] No se encontró la sesión con UUID: {user_session_uuid}")
        return {"error": "La sesión no existe o ha sido eliminada por inactividad."}

    interaction = next(
        (
            item
            for item in session_data[user_session_uuid]["interactions"]
            if item["interaction_uuid"] == interaction_uuid
        ),
        None,
    )

    # Si se encontró la interacción, agregar la nueva clave 'full_response'
    if interaction:
        interaction["full_response"] = full_response
        # print(f"[rt_query] full_response: {full_response}")
        # print(f"[rt_query] add_response, valor actual de session_data {json.dumps(session_data, indent=4, default=str)}")
    else:
        print(f"No se encontró la interacción con UUID: {interaction_uuid}")
    # session_data[user_session_uuid]['interactions'][interaction_uuid].append(full_response)


@router.post("/get_sources")
async def context_sources(query_model: QueryModel):
    # print("[rt_query] user_session_uuid: ", query_model.user_session_uuid)
    # print("[rt_query] query: ", query_model.query)
    # print("[rt_query] use_considerations: ", query_model.use_considerations)
    # print("[rt_query] n_documents: ", query_model.n_documents)
    # print("[rt_query] word_list: ", query_model.word_list)

    user_session_uuid = query_model.user_session_uuid
    query = query_model.query
    n_documents = query_model.n_documents
    word_list = query_model.word_list

    search_documents_start = time.time()
    response = get_context_sources(query, word_list, n_documents)
    search_documents_time = time.time() - search_documents_start
    context_to_send = response.get("context", "No hay contexto disponible")
    sources_to_send = response.get("sources", "No hay fuentes disponibles")
    considerations_to_send = response.get(
        "considerations", "No hay consideraciones disponibles"
    )

    # Inicializar la sesión si no existe
    if user_session_uuid not in session_data:
        print(f"[rt_query] Iniciando nueva sesión para el usuario: {user_session_uuid}")
        session_data[user_session_uuid] = {
            "interactions": [],  # Lista para almacenar el historial de interacciones
            "last_interaction_time": datetime.now(pytz.timezone(TIME_ZONE)),
        }
    else:
        print(f"[rt_query] Actualizando sesión para el usuario: {user_session_uuid}")
        session_data[user_session_uuid]["last_interaction_time"] = datetime.now(
            pytz.timezone(TIME_ZONE)
        )

    clean_inactive_sessions(user_session_uuid)
    clean_old_sessions()
    clean_old_interactions(user_session_uuid)

    # Agregar la nueva interacción
    interaction = {
        "interaction_uuid": str(uuid.uuid4()),
        "query": query,
        "context": context_to_send,
        "sources": sources_to_send,
        "considerations": considerations_to_send,
        "search_documents_time": search_documents_time,
    }

    session_data[user_session_uuid]["interactions"].append(interaction)

    # print(f"[rt_query] Session Data después de agregar interacción: {json.dumps(session_data, indent=4, default=str)}")  # Solo muestra las claves de session_data

    # print("\n\n-----------------------VERIFICAR SESSION_DATA----------------")
    # print(f"[rt_query] session_data[{user_session_uuid}]: {session_data[user_session_uuid]}")

    # print("\n\n-----------------------VERIFICAR SOURCES DE CADA INTERACCION----------------")
    # for interaction in session_data[user_session_uuid]['interactions']:
    #     print(f"[rt_query] sources: {interaction['sources']}")

    return {
        "interaction_uuid": interaction["interaction_uuid"],
        "sources": interaction["sources"],
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection established.")
    await websocket.accept()

    user_session_uuid = None
    cancel_event = asyncio.Event()

    try:

        db: Session = SessionLocal()
        initial_cpu, initial_memory = get_system_usage()

        while True:
            # Recibiendo el mensaje del cliente (Streamlit)
            data = await websocket.receive_text()

            message_data = json.loads(data)

            user_session_uuid = message_data["user_session_uuid"]
            model_name = message_data.get("model_name")
            use_considerations = message_data.get("use_considerations")

            print("[rt_query] use_considerations: ", use_considerations)
            print("[rt_query] user_session_uuid: ", user_session_uuid)
            print("[rt_query] model_name: ", model_name)

            if session_data[user_session_uuid]["interactions"][-1]["query"] is not None:
                query = session_data[user_session_uuid]["interactions"][-1]["query"]
                historial_interactions = formatted_history(
                    session_data[user_session_uuid]["interactions"]
                )
                context = formatted_context(
                    session_data[user_session_uuid]["interactions"][-1]["context"]
                )
                sources = formatted_sources(
                    session_data[user_session_uuid]["interactions"][-1]["sources"]
                )
                raw_considerations = session_data[user_session_uuid]["interactions"][
                    -1
                ]["considerations"]
                considerations = (
                    formatted_considerations(raw_considerations)
                    if isinstance(raw_considerations, list)
                    else []
                )
                search_documents_time = float(
                    session_data[user_session_uuid]["interactions"][-1][
                        "search_documents_time"
                    ]
                )
                if not isinstance(considerations, list):
                    considerations = []

                response_uuid = str(uuid.uuid4())

                async for chunk in ollama_generator(
                    db,
                    query,
                    model_name,
                    historial_interactions,
                    context,
                    sources,
                    considerations,
                    search_documents_time,
                    use_considerations,
                    initial_cpu,
                    initial_memory,
                    cancel_event,
                ):
                    response_chunk = {
                        "response_uuid": response_uuid,
                        "content": chunk,
                    }
                    # Enviar cada fragmento al cliente con el mismo ID
                    await websocket.send_text(json.dumps(response_chunk))
    except WebSocketDisconnect:
        print("Disconnected client")
        cancel_event.set()
        # Al desconectarse, limpiamos la sesión de inactividad si ha pasado el límite
        if user_session_uuid in session_data:
            last_interaction_time = session_data[user_session_uuid].get(
                "last_interaction_time", datetime.now(pytz.timezone(TIME_ZONE))
            )
            if (
                datetime.now(pytz.timezone(TIME_ZONE)) - last_interaction_time
                > INACTIVITY_LIMIT
            ):
                print(
                    f"[rt_query] Eliminando sesión por inactividad: {user_session_uuid}"
                )
                session_data.pop(user_session_uuid)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Traceback of the error:")
        print(traceback.format_exc())
        cancel_event.set()
    finally:
        db.close()


# @router.post("/ai")
# async def ai_post(query_model: QueryModel):
#     query = query_model.query
#     response = query_service.query_with_gemini(query)
#     return response
