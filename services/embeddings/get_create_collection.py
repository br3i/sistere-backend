from services.helpers.chroma_client import chroma_client


# Función para obtener todas las colecciones
def get_list_collections():
    try:
        # Intentar obtener la colección
        client = chroma_client()
        collections = client.list_collections()
        if collections is None:
            return None
        return collections
    except Exception as e:
        print(f"[process_resolve_and_articles] Error al obtener las colecciones: {e}")
        return None


# Función para obtener una colección
def get_collection(collection_name):
    print("[get_collection] collection_name: ", collection_name)
    try:
        # Intentar obtener la colección
        client = chroma_client()
        collection = client.get_collection(name=collection_name)
        if collection is None:
            print(
                f"[process_resolve_and_articles] No se pudo encontrar la colección '{collection_name}'."
            )
            return None
        return collection
    except Exception as e:
        print(f"[process_resolve_and_articles] Error al obtener la colección: {e}")
        return None


# Función para crear una colección
def create_collection(collection_name):
    print("[get_collection] create_collection: ", collection_name)
    try:
        # Crear una nueva colección
        client = chroma_client()
        collection = client.create_collection(
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
        return collection
    except Exception as e:
        print(f"[process_resolve_and_articles] Error al crear la colección: {e}")
        return None
