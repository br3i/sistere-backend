import chromadb
from chromadb.api.shared_system_client import SharedSystemClient


# Crear cliente para conectarse a Chroma
def chroma_client():
    client = chromadb.HttpClient(host="localhost", port=8000)
    # Limpiar la caché del sistema
    SharedSystemClient.clear_system_cache()
    return client
