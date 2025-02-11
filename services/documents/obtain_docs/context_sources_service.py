import os
import json
import time
import numpy as np
from services.documents.save_docs.save_requested_document import save_requested_document
from services.documents.treat_word_list.generate_variations import generate_variations
from services.helpers.return_collection import return_collection
from services.helpers.extract_numbers import extract_numbers
from services.nr_database.nr_connection_service import get_collection_names
from services.embeddings.get_embedding_service import get_embeddings


def get_context_sources(query: str, word_list, n_documents):
    print(
        f"\n\n--------------[contex_sources_service] Iniciando búsqueda con query: {query}"
    )
    # print(f"[context_sources_service] Número de documentos a buscar: {n_documents}")
    # print(f"[context_sources_service] n_documents type: {type(n_documents)}")
    n_documents = int(n_documents)
    # print(f"[context_sources_service] n_documents type: {type(n_documents)}")
    # print(f"[context_sources_service] word_list type: {type(word_list)}")
    # print(f"[context_sources_service] word_list: {word_list}")

    try:
        # Obtener colecciones disponibles
        collection_names = get_collection_names()
        print(f"Valor de colecction names que se obtiene: {collection_names}")
        if not collection_names:
            return {"error": "No se encontraron colecciones en la base de datos."}

        # Generar embedding para la consulta
        query_embedding = get_embeddings(query)
        # print(f"[QUERY_PDF] Embedding generado para la consulta: {query_embedding}")

        # Buscar documentos relevantes en todas las colecciones
        all_documents_global = []
        sources_global = []
        considerations_global = []
        metadata_filters = {}
        full_text_filters = {"$or": []}

        numbers_from_query = extract_numbers(query)

        # print(f"[CONTEX-SOURCES-SERVICE] Word_list to Contain: {word_list}")
        # print("[CONTEX-SOURCES-SERVICE] Resolución y año extraídos: ", year, resolution)

        if len(numbers_from_query) > 0:
            # Crear dinámicamente los elementos dentro de $or
            or_filters = []
            for number in numbers_from_query:
                or_filters.append({"collection_name": {"$eq": str(number)}})
                or_filters.append({"number_resolution": {"$eq": str(number)}})

            metadata_filters = {"$or": or_filters}

        print(
            "[CONTEXT-SOURCES-SERVICE] Filtros de metadata: ",
            json.dumps(metadata_filters, indent=4, default=str),
        )
        print("[CONTEXT-SOURCES-SERVICE] Lend word_list: ", len(word_list))

        if len(word_list) != 0:
            for word in word_list:  # Iteramos sobre cada palabra en la lista original
                variations = generate_variations(
                    word
                )  # Generamos las variaciones de la palabra
                for variation in variations:  # Iteramos sobre cada variación generada
                    full_text_filters["$or"].append(
                        {"$contains": variation}
                    )  # Agregamos cada variación como un nuevo registro
        else:
            full_text_filters = {}

        print(
            "[CONTEXT-SOURCES-SERVICE] filtros de where_documents: ",
            json.dumps(full_text_filters, indent=4, default=str),
        )

        for collection_name in collection_names:
            print(f"[contex_sources_service] Buscando en colección: {collection_name}")
            collection = return_collection(collection_name)
            print(f"[contex_sources_service] Tipo de collection: {type(collection)}")

            search_results = collection.query(  # type: ignore
                query_embeddings=[query_embedding],
                n_results=n_documents,
                where=metadata_filters,  # type: ignore
                where_document=full_text_filters,  # type: ignore
                include=["documents", "metadatas", "distances"],  # type: ignore
            )
            # print(f"\nRESULTS\n\n------[contex_sources_service] Resultado de search_results {json.dumps(search_results, indent=4, default=str)}")

            # Verificar si 'documents' contiene resultados y procesarlos
            if (
                "documents" in search_results
                and search_results["documents"]
                and search_results["metadatas"]
                and search_results["distances"]
            ):
                # Obtener los documentos de 'documents'
                documents = search_results["documents"][
                    0
                ]  # Acceder al primer conjunto de documentos
                # print("\n\n\n CONSEGUIR DOCUMENTS: \n", documents)
                metadatas = search_results["metadatas"][
                    0
                ]  # Obtener los metadatos correspondientes
                # print("\n\n\n CONSEGUIR METADATAS: \n", metadatas)
                distances = search_results["distances"][
                    0
                ]  # Obtener las distancias correspondientes

                # print(f"----\nDocumentos\n\n[contex_sources_service] Documentos encontrados en {collection_name}: {documents}")

                # Almacenar los textos de los documentos encontrados y las fuentes
                for i, doc in enumerate(documents):
                    if doc:  # Verificar que el documento no sea None o vacío
                        # Obtener metadatos correspondientes
                        document_metadata = metadatas[i]
                        considerations = document_metadata.get("considerations", "")
                        copia = document_metadata.get("copia", "")
                        resolve_page = document_metadata.get("resolve_page", "")
                        file_path = document_metadata.get("file_path", "")
                        document_name = document_metadata.get("document_name", "")

                        # Agregar documento y metadatos a las listas correspondientes
                        all_documents_global.append(
                            {
                                "document_name": document_name,
                                "content": doc,
                                "resolve_page": resolve_page,
                                "distance": distances[i],
                            }
                        )

                        # Agregar metadatos a la lista de fuentes
                        sources_global.append(
                            {
                                "file_path": file_path,
                                "document_name": document_name,
                                "resolve_page": resolve_page,
                            }
                        )

                        considerations_global.append(
                            {
                                "document_name": document_name,
                                "considerations": considerations,
                                "copia": copia,
                            }
                        )

                        # Imprimir para depuración
                        print(
                            f"[cntx-src-srv] Documento: {document_name}, Página: {resolve_page}, Distancia: {distances[i]}"
                        )

                    else:
                        print(
                            f"[contex_sources_service] El documento está vacío o es None"
                        )
            else:
                print(
                    f"\n\n-----[contex_sources_service] No se encontraron documentos en la colección {collection_name}"
                )

        # Una vez que se han procesado todas las colecciones, puedes ordenar y generar el contexto global
        if all_documents_global:
            all_documents_global.sort(key=lambda x: x["distance"])
            context = ", ".join(
                [
                    f"{doc['document_name']} [{doc['content']}]"
                    for doc in all_documents_global
                ]
            )
            print("\n\n----------------------CONTEXTO--------------------")
            print(
                f"[contex_sources_service] all_documents combinado: {context}\n\n\n\n"
                f"[contex_sources_service] context_len: {len(context)}\n\n\n\n"
            )
            # print("\n\n----------------------SOURCES--------------------")
            # print(f"[contex_sources_service] sources combinado: {json.dumps(sources_global, indent=4, default=str)}\n\n\n\n")
            # print("\n\n----------------------CONSIDERATIONS--------------------")
            # print(f"[contex_sources_service] consideratios combinado: {json.dumps(considerations_global, indent=4, default=str)}\n\n\n\n")

            save_requested_document(sources_global[:n_documents])

            return {
                "context": context,
                "sources": sources_global[:n_documents],
                "considerations": considerations_global,
            }
        else:
            return {"context": "", "sources": [], "considerations": []}

    except Exception as e:
        print(f"[contex_sources_service] Error al procesar la consulta: {str(e)}")
        return {"error": f"Error al procesar la consulta: {str(e)}"}
