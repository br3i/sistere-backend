from uuid import UUID
from sqlalchemy import func
from models.document import Document
from models.embedding import Embedding
from services.embeddings.get_embedding_service import get_embeddings


def save_embeddings(chunk, collection_name, document_metadata, id_document, db):
    print(f"\n\n\n\n------------------[save_embeddings]-------------------")
    # print(f"[save_embeddings] collection: {collection}")
    # print(f"[save_embeddings] collection type: {type(collection)}")

    # print("\n[save_embedding_service] id_document: ", id_document)
    # print("\n[save_embedding_service] db: ", db)
    # print(
    #     "\n[save_embedding_service] document_metadata['uuid']: ",
    #     document_metadata["uuid"],
    # )

    # print(f"\nValor de chunk: \n{chunk}")
    # print(f"\nValor de chunk[0]: \n{chunk[0]}")
    # print(f"\nValor de collection: \n{collection}")
    # print(f"\nValor de document_metadata: \n{json.dumps(document_metadata, indent=4)}")
    # print(
    #     f"\nValor de chunk_index: {document_metadata['chunk_index']} \n(Tipo: {type(document_metadata['chunk_index'])})"
    # )

    try:
        # Llamada a Ollama para obtener el embedding del fragmento
        embedding = get_embeddings(chunk[0])
        print(f"[save_embedding_service] embedding: {embedding}")

        # Comprobamos si el embedding se generó correctamente
        if not embedding:
            raise ValueError(
                "Error al generar el embedding: el resultado está vacío o no es válido."
            )

        # Guardar el embedding en Supabase (en la tabla embeddings)
        new_embedding = Embedding(
            embedding=embedding,  # El vector de embedding
            embed_metadata=document_metadata,  # La metadata asociada
            collection_name=collection_name,
            document_id=id_document,  # Asociar el embedding al documento
        )

        db.add(new_embedding)
        db.commit()

        print(
            f"Embedding guardado para el fragmento {document_metadata['chunk_index']}."
        )

        try:
            # Recuperar el documento correspondiente
            document = db.query(Document).filter_by(id=id_document).first()
            print("[\n\nACTUALIZAR EMBEDDING]")
            print("[save_embeddings] document antes de actualizar: ", document)
            print(
                "[save_embeddings] document.embeddings_uuids antes de actualizar: ",
                document.embeddings_uuids,
            )
            print(
                "[save_embeddings] document_metadata['uuid']: ",
                document_metadata["uuid"],
            )

            if not document:
                raise ValueError(
                    f"Documento con ID {id_document} no encontrado en la base de datos."
                )

            if document.embeddings_uuids is None:
                document.embeddings_uuids = []

            # print(f"[save_embeddings] Añadiendo UUID: {document_metadata['uuid']}")
            document.embeddings_uuids = func.array_append(
                document.embeddings_uuids, new_embedding.id
            )

            print(
                f"[save_embeddings] document.embeddings_uuids después de append: {document.embeddings_uuids}"
            )

            db.commit()
            # Imprime el estado del documento después de la actualización
            print("[save_embeddings] document después de actualizar: ", document)
            print(
                "[save_embeddings] document.embeddings_uuids después de actualizar: ",
                document.embeddings_uuids,
            )

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
