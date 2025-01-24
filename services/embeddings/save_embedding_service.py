import time
from sqlalchemy import func
from models.document import Document
from services.embeddings.get_embedding_service import get_embeddings


def save_embeddings(chunk, collection, document_metadata, id_document, db):
    # print(f"\n\n\n\n------------------[save_embeddings]-------------------")
    # print("\n[save_embedding_service] id_document: ", id_document)
    # print("\n[save_embedding_service] db: ", db)
    # print("\n[save_embedding_service] document_metadata['uuid']: ", document_metadata['uuid'])

    # print(f"\nValor de chunk: \n{chunk}")
    # print(f"\Valor de chunk[0]: \n{chunk[0]}")
    # print(f"\nValor de collection: \n{collection}")
    # print(f"\nValor de document_metadata: {document_metadata}")
    # print(f"\nValor de page_number: \n{document_metadata['considerations'][0]['page_number']} (Tipo: {type(document_metadata['considerations'][0]['page_number'])})")
    # print(f"\nValor de chunk_index: \n{document_metadata['chunk_index']} (Tipo: {type(document_metadata['chunk_index'])})")

    try:
        # Llamada a Ollama para obtener el embedding del fragmento
        embedding = get_embeddings(chunk[0])  # Obtenemos el embedding

        # Comprobamos si el embedding se generó correctamente
        if not embedding:
            raise ValueError(
                "Error al generar el embedding: el resultado está vacío o no es válido."
            )

        # Aplanar los metadatos de las consideraciones en una cadena simple
        simplified_metadata = document_metadata.copy()
        if "considerations" in simplified_metadata:
            simplified_metadata["considerations"] = " | ".join(
                c["consideration"]  # Solo tomamos la consideración, sin la página
                for c in simplified_metadata["considerations"]
            )

        # Guardamos el embedding en la colección Chroma
        collection.add(
            ids=[str(document_metadata["uuid"])],  # ID único para cada fragmento
            embeddings=[embedding],  # El embedding generado
            documents=[chunk[0]],  # El fragmento de texto
            metadatas=[simplified_metadata],  # Los metadatos asociados
        )

        # print(
        #     f"Embedding guardado para el fragmento {document_metadata['chunk_index']}."
        # )

        try:
            # Recuperar el documento correspondiente
            document = db.query(Document).filter_by(id=id_document).first()
            # print("[\n\nACTUALIZAR EMBEDDING]")
            # print("[save_embeddings] document antes de actualizar: ", document)
            # print("[save_embeddings] document.embeddings_uuids antes de actualizar: ", document.embeddings_uuids)
            # print("[save_embeddings] document_metadata['uuid']: ", document_metadata['uuid'])

            if not document:
                raise ValueError(
                    f"Documento con ID {id_document} no encontrado en la base de datos."
                )

            if document.embeddings_uuids is None:
                document.embeddings_uuids = []

            # print(f"[save_embeddings] Añadiendo UUID: {document_metadata['uuid']}")
            document.embeddings_uuids = func.array_append(
                document.embeddings_uuids, str(document_metadata["uuid"])
            )

            # print(f"[save_embeddings] document.embeddings_uuids después de append: {document.embeddings_uuids}")

            db.commit()
            # # Imprime el estado del documento después de la actualización
            # print("[save_embeddings] document después de actualizar: ", document)
            # print("[save_embeddings] document.embeddings_uuids después de actualizar: ", document.embeddings_uuids)

            print(
                f"Documento actualizado en embedding_uuid {document_metadata['chunk_index']}."
            )
        except Exception as db_error:
            db.rollback()  # Revertir cualquier cambio en caso de error
            print(f"Error al guardar datos en la base de datos: {db_error}")
    except ValueError as ve:
        print(f"Error de validación: {ve}")
    except Exception as e:
        print(f"Error inesperado al guardar embeddings: {e}")
