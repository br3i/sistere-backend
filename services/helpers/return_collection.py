from services.nr_database.nr_connection_service import (
    get_collection,
    create_collection,
    get_collection_names,
)


def return_collection(collection_name):
    collection = get_collection(collection_name)
    if collection is None:
        collection = create_collection(collection_name)
        if collection is None:
            print(f"Error al crear la colección {collection_name}")
            return None
        return collection
    return collection


def get_list_collections():
    return get_collection_names()
