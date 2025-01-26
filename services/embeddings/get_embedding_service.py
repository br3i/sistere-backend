import os
import time
import requests
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
MODEL_EMBEDDING = os.getenv("MODEL_EMBEDDING", "nomic-embed-text:latest")
print(f"[get_embedding] Model: {MODEL_EMBEDDING}")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")


class EmbeddingError(Exception):
    """Excepción personalizada para errores en la generación de embeddings."""

    pass


def get_embeddings(text_chunk, retries=3, delay=2):
    # print("[get_embeddings] valor de text_chunk: ", text_chunk)
    # print("[get_embeddings] tipo de tex_chunk: ", type(text_chunk))
    """
    Obtiene los embeddings para un fragmento de texto.

    Parámetros:
    - text_chunk (str): El fragmento de texto para el cual se quieren obtener embeddings.
    - retries (int): Número de reintentos en caso de fallo.
    - delay (int): Tiempo (en segundos) entre reintentos.

    Retorna:
    - embeddings (list): Lista de embeddings generados.

    Lanza:
    - EmbeddingError: Si no se logran obtener embeddings después de varios intentos.
    """
    if not isinstance(text_chunk, str):
        raise ValueError("El fragmento proporcionado no es una cadena de texto válida.")

    for attempt in range(retries):
        try:
            json_payload = {
                "model": f"{MODEL_EMBEDDING}",
                "prompt": f"{text_chunk}",
            }
            response = requests.post(f"{OLLAMA_URL}/api/embeddings", json=json_payload)
            embeddings = response.json().get("embedding")

            if embeddings is None:
                raise ValueError(
                    f"El modelo no devolvió embeddings válidos. Respuesta: {response}"
                )

            print(f"Embeddings generados exitosamente en el intento {attempt + 1}.")
            return embeddings

        except Exception as e:
            print(f"Error al obtener embeddings en el intento {attempt + 1}: {e}")
            if attempt < retries - 1:
                print(f"Reintentando en {delay} segundos...")
                time.sleep(delay)

    # Si llegamos aquí, todos los intentos fallaron
    raise EmbeddingError("No se pudo generar embeddings después de varios intentos.")
