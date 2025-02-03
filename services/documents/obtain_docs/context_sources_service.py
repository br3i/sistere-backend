import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from models.database import SessionLocal
from models.embedding import Embedding
from services.documents.save_docs.save_requested_document import save_requested_document
from services.documents.treat_word_list.generate_variations import generate_variations
from services.helpers.extract_numbers import extract_numbers
from services.embeddings.get_embedding_service import get_embeddings
from services.embeddings.get_list_collections import get_list_collections


# Función de similitud exacta para search_from_numbers
def calculate_similarity(number_from_query, number_resolution):
    return 1.0 if str(number_from_query) == str(number_resolution) else 0.0


# Función de similitud de Jaccard para search_word_list
def calculate_jaccard_similarity(word_set, document_set):
    intersection = len(word_set.intersection(document_set))
    union = len(word_set.union(document_set))
    return intersection / union if union != 0 else 0.0


def search_from_numbers(numbers_from_query):
    print(
        f"\n\n--------------[search_from_numbers] Buscando documentos con números: {numbers_from_query}"
    )
    db = SessionLocal()

    results = []
    for number in numbers_from_query:
        print(f"[search_from_numbers] Procesando número: {number}")

        # Buscar documentos en la base de datos
        documents = (
            db.query(Embedding)
            .filter(
                (Embedding.embed_metadata["collection_name"].astext == str(number))
                | (Embedding.embed_metadata["number_resolution"].astext == str(number))
            )
            .all()
        )

        print(
            f"[search_from_numbers] Documentos encontrados para '{number}': {len(documents)}"
        )

        # Extraer metadatos de los documentos encontrados
        for doc in documents:
            metadata = doc.embed_metadata
            print(f"[search_from_numbers] Documento encontrado: {metadata}")

            # Calcular similitud entre el número de la consulta y el número de resolución
            similarity = calculate_similarity(number, metadata.get("number_resolution"))
            print(f"[search_from_numbers] Similitud calculada: {similarity}")

            results.append(
                {
                    "document_name": metadata.get("document_name"),
                    "file_path": metadata.get("file_path"),
                    "resolve_page": metadata.get("resolve_page"),
                    "collection_name": metadata.get("collection_name"),
                    "considerations": metadata.get("considerations"),
                    "number_resolution": metadata.get("number_resolution"),
                    "uuid": metadata.get("uuid"),
                    "chunk_index": metadata.get("chunk_index"),
                    "text": metadata.get("text"),
                    "copia": metadata.get("copia"),
                    "similarity": similarity,
                }
            )

    # print(f"[search_from_numbers] Resultados finales: {results}")
    return results


def search_word_list(word_list, collection_name):
    print(
        f"\n\n--------------[search_word_list] Buscando documentos con palabras clave: {word_list}"
    )

    db = SessionLocal()

    all_variations = []

    for word in word_list:
        variations = generate_variations(word)  # Genera variaciones de la palabra
        print(f"[search_word_list] Variaciones generadas para '{word}': {variations}")
        all_variations.extend(variations)  # Agregamos las variaciones a la lista total

    print(
        f"[search_word_list] Lista completa de variaciones para la búsqueda: {all_variations}"
    )

    results = []

    for variation in all_variations:
        print(f"[search_word_list] Buscando la variación: {variation}")

        # Buscar documentos en la base de datos donde "text" contenga la variación
        documents = (
            db.query(Embedding)
            .filter(
                Embedding.embed_metadata["text"].astext.ilike(f"%{variation}%"),
                Embedding.embed_metadata["collection_name"].astext == collection_name,
            )
            .all()
        )

        print(
            f"[search_word_list] Documentos encontrados para '{variation}': {len(documents)}"
        )

        for doc in documents:
            metadata = doc.embed_metadata
            print(
                f"[search_word_list] Documento encontrado con '{variation}': {metadata}"
            )

            # Calcular similitud con Jaccard
            document_words = set(
                metadata.get("text", "").split()
            )  # Palabras del texto del documento
            variation_set = set(variation.split())  # Palabras de la variación

            similarity = calculate_jaccard_similarity(variation_set, document_words)
            print(f"[search_word_list] Similitud de Jaccard calculada: {similarity}")

            results.append(
                {
                    "document_name": metadata.get("document_name"),
                    "file_path": metadata.get("file_path"),
                    "resolve_page": metadata.get("resolve_page"),
                    "collection_name": metadata.get("collection_name"),
                    "considerations": metadata.get("considerations"),
                    "number_resolution": metadata.get("number_resolution"),
                    "uuid": metadata.get("uuid"),
                    "chunk_index": metadata.get("chunk_index"),
                    "text": metadata.get("text"),
                    "copia": metadata.get("copia"),
                    "similarity": similarity,
                }
            )

    print(f"[search_word_list] Resultados finales: {results}")
    return results


def search_embedding_query(query_embedding, collection_name):
    print(
        f"\n\n--------------[search_embedding_query] Buscando documentos por embeddings"
    )

    db = SessionLocal()

    # Consultar los documentos dentro de la colección
    documents = (
        db.query(Embedding)
        .filter(Embedding.embed_metadata["collection_name"].astext == collection_name)
        .all()
    )

    print(
        f"[search_embedding_query] Documentos en la colección '{collection_name}': {len(documents)}"
    )

    results = []

    for doc in documents:
        stored_embedding = np.array(doc.embedding).reshape(
            1, -1
        )  # Asegurar forma correcta
        query_embedding = np.array(query_embedding).reshape(1, -1)

        similarity = cosine_similarity(query_embedding, stored_embedding)[0][0]

        metadata = doc.embed_metadata
        results.append(
            {
                "similarity": similarity,
                "document_name": metadata.get("document_name"),
                "file_path": metadata.get("file_path"),
                "resolve_page": metadata.get("resolve_page"),
                "collection_name": metadata.get("collection_name"),
                "considerations": metadata.get("considerations"),
                "number_resolution": metadata.get("number_resolution"),
                "uuid": metadata.get("uuid"),
                "chunk_index": metadata.get("chunk_index"),
                "text": metadata.get("text"),
                "copia": metadata.get("copia"),
            }
        )

    # Ordenar resultados por similitud de mayor a menor
    results.sort(key=lambda x: x["similarity"], reverse=True)

    print(f"[search_embedding_query] Resultados finales: {results}")
    return results


def get_context_sources(query: str, word_list, n_documents):
    print(
        f"\n\n--------------[get_context_sources] Iniciando búsqueda con query: {query}"
    )
    print(f"[get_context_sources] Número de documentos a buscar: {n_documents}")
    print(f"[get_context_sources] n_documents type: {type(n_documents)}")

    n_documents = int(n_documents)

    print(f"[get_context_sources] n_documents convertido a int: {type(n_documents)}")
    print(f"[get_context_sources] word_list type: {type(word_list)}")
    print(f"[get_context_sources] word_list: {word_list}")

    try:
        db = SessionLocal()

        # Obtener colecciones disponibles
        collection_names = get_list_collections()
        print(f"[get_context_sources] Colecciones disponibles: {collection_names}")

        if not collection_names:
            return {"error": "No se encontraron colecciones en la base de datos."}

        # Generar embedding para la consulta
        query_embedding = get_embeddings(query)

        # Extraer números de la consulta
        numbers_from_query = extract_numbers(query)
        print(
            f"[get_context_sources] Números extraídos de la consulta: {numbers_from_query}"
        )

        numbers_search_results = []
        word_list_search_results = []
        embedding_search_results = []

        all_documents_global = []
        sources_global = []
        considerations_global = []

        for collection_name in collection_names:
            # Si hay números en la consulta, buscar en la base de datos
            if len(numbers_from_query) > 0:
                numbers_search_results = search_from_numbers(numbers_from_query)
                # print(
                #     f"[get_context_sources] Resultados de búsqueda por números: {json.dumps(numbers_search_results, indent=4, default=str)}"
                # )

            if len(word_list) > 0:
                word_list_search_results = search_word_list(word_list, collection_name)
                # print(
                #     f"[get_context_sources] Resultados de búsqueda por word_list: {json.dumps(word_list_search_results, indent=4, default=str)}"
                # )

            if query_embedding:
                embedding_search_results = search_embedding_query(
                    query_embedding, collection_name
                )
                # print(
                #     f"[get_context_sources] Resultados de búsqueda por embedding: {json.dumps(embedding_search_results, indent=4, default=str)}"
                # )

            # Aquí procesamos los resultados obtenidos y los almacenamos en las listas globales
            # Procesar los resultados de la búsqueda por números
            for result in numbers_search_results:
                # Procesa el documento y almacénalo en las listas globales
                document = result.get("document_name", "")
                resolve_page = result.get("resolve_page", "")
                similarity = result.get("similarity", 0)
                all_documents_global.append(
                    {
                        "document_name": document,
                        "content": result.get("text", ""),
                        "resolve_page": resolve_page,
                        "similarity": similarity,
                    }
                )
                sources_global.append(
                    {
                        "file_path": result.get("file_path", ""),
                        "document_name": document,
                        "resolve_page": resolve_page,
                    }
                )
                considerations_global.append(
                    {
                        "document_name": document,
                        "considerations": result.get("considerations", []),
                        "copia": result.get("copia", ""),
                    }
                )

            # Procesar los resultados de la búsqueda por word_list
            for result in word_list_search_results:
                document = result.get("document_name", "")
                resolve_page = result.get("resolve_page", "")
                similarity = result.get("similarity", 0)
                all_documents_global.append(
                    {
                        "document_name": document,
                        "content": result.get("text", ""),
                        "resolve_page": resolve_page,
                        "similarity": similarity,
                    }
                )
                sources_global.append(
                    {
                        "file_path": result.get("file_path", ""),
                        "document_name": document,
                        "resolve_page": resolve_page,
                    }
                )
                considerations_global.append(
                    {
                        "document_name": document,
                        "considerations": result.get("considerations", []),
                        "copia": result.get("copia", ""),
                    }
                )

            # Procesar los resultados de la búsqueda por embeddings
            for result in embedding_search_results:
                document = result.get("document_name", "")
                resolve_page = result.get("resolve_page", "")
                similarity = result.get("similarity", 0)
                all_documents_global.append(
                    {
                        "document_name": document,
                        "content": result.get("text", ""),
                        "resolve_page": resolve_page,
                        "similarity": similarity,
                    }
                )
                sources_global.append(
                    {
                        "file_path": result.get("file_path", ""),
                        "document_name": document,
                        "resolve_page": resolve_page,
                    }
                )
                considerations_global.append(
                    {
                        "document_name": document,
                        "considerations": result.get("considerations", []),
                        "copia": result.get("copia", ""),
                    }
                )

        # 1. Generar índices para mantener la relación entre documentos y sources
        indices = list(range(len(all_documents_global)))

        # 2. Ordenar índices por distancia (menor primero)
        indices.sort(key=lambda i: all_documents_global[i]["similarity"], reverse=True)

        # 3. Seleccionar los primeros 'n_documents' índices
        top_indices = indices[:n_documents]

        # 4. Filtrar documentos y sources usando los índices ordenados
        all_documents_global = [all_documents_global[i] for i in top_indices]
        selected_sources = [sources_global[i] for i in top_indices]

        # 5. Generar el contexto
        context = ", ".join(
            [
                f"{doc['document_name']} [{doc['content']}]"
                for doc in all_documents_global
            ]
        )

        # Depuración
        # print(f"[get_context_sources] Contexto combinado: {context}")
        # print(
        #     f"[get_context_sources] Sources combinado: {json.dumps(sources_global, indent=4, default=str)}"
        # )
        # print(
        #     f"[get_context_sources] Considerations combinado: {json.dumps(considerations_global, indent=4, default=str)}"
        # )

        save_requested_document(selected_sources)

        return {
            "context": context,
            "sources": selected_sources,
            "considerations": considerations_global,
        }

    except Exception as e:
        print(f"[get_context_sources] Error: {e}")
        return {"error": str(e)}

    finally:
        db.close()
