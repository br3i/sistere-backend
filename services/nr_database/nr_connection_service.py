import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import os

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.env")
load_dotenv(dotenv_path)
# Ahora puedes acceder a las variables de entorno
NO_RELATIONAL_DATABASE_PATH = os.getenv("NO_RELATIONAL_DATABASE_PATH", "./db_nr")
# Inicializa el cliente de Chroma, lo podemos hacer aquí para que se reutilice en todo el proyecto
client = chromadb.PersistentClient(
    path=NO_RELATIONAL_DATABASE_PATH,  # Ruta persistente de la base de datos
    settings=Settings(persist_directory=NO_RELATIONAL_DATABASE_PATH),
)


# Funciónn para obtener una collection
def get_collection(collection_name):
    try:
        return client.get_collection(name=collection_name)
    except ValueError:
        return None
        # raise ValueError(f"La colección '{collection_name}' no existe.")


# Función para obtener todos los nombres de las colecciones
def get_collection_names():
    try:
        # Obtener todas las colecciones en la base de datos
        collections = (
            client.list_collections()
        )  # Obtiene todas las colecciones existentes
        collection_names = [collection.name for collection in collections]
        return collection_names
    except Exception as e:
        print(f"Error al obtener las colecciones: {e}")
        return []


# Función para crear una collection
def create_collection(collection_name):
    try:
        return client.create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:M": 100,
                "hnsw:search_ef": 300,
                # "hnsw:num_threads": 4,
                # "hnsw:resize_factor": 1.2,
                # "hnsw:batch_size": 100,
                "hnsw:sync_threshold": 3000,
            },
        )
    except Exception as e:
        raise Exception(f"Error al crear la colección '{collection_name}': {str(e)}")
