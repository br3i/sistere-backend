from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.embedding import Embedding


# Función para obtener todas las colecciones
def get_list_collections():
    try:
        # Crear la sesión manualmente
        db = SessionLocal()  # Usamos directamente la sesión de la base de datos

        print(f"[DEBUG] Tipo de db: {type(db)}")

        # Intentar obtener la colección
        collections = db.query(Embedding.collection_name).distinct().all()
        print(f"[DEBUG] Collections obtenidas: {collections}")

        db.close()  # Cerrar la sesión después de la consulta

        if collections is None:
            return None

        # Convertir la lista de tuplas en una lista de nombres
        collection_names = [
            collection[0] for collection in collections
        ]  # Extrayendo el primer elemento de cada tupla
        return collection_names
    except Exception as e:
        print(f"[get_list_collections] Error al obtener las colecciones: {e}")
        return None
