from services.nr_database.nr_connection_service import get_collection, create_collection

def return_collection(collection_name):
    collection = get_collection(collection_name)
    if collection is None:
        collection = create_collection(collection_name)
        if collection is None:
            print(f"Error al crear la colección {collection_name}")
            return None
        return collection
    return collection