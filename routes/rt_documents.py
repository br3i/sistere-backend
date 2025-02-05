# routes/routes_documents.py
import os
import time
import traceback
from sqlalchemy.orm import Session
from models.database import get_db
from models.document import Document
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    HTTPException,
)
from fastapi.responses import JSONResponse
from models.supabase_client import get_client_supabase
from services.helpers.system_usage import get_system_usage
from services.helpers.clean_filename import clean_filename
from services.documents.save_docs.upload_service import save_document
from services.documents.save_docs.process_any_document_service import process_pdf
from services.metrics.save_metrics.save_metrics_docs import save_metrics_docs
from services.embeddings.get_list_collections import get_list_collections

router = APIRouter()


@router.get("/documents_from_db")
async def get_documents_from_db(db: Session = Depends(get_db)):
    documents = db.query(Document).all()
    return [
        {
            "id": document.id,
            "name": document.name,
            "collection_name": document.collection_name,
            "path": document.path,
            "physical_path": document.physical_path,
            "created_at": document.created_at.isoformat(),
        }
        for document in documents
    ]


@router.get("/list_collections")
async def list_collections():
    collections = get_list_collections()
    if collections:
        # Devolvemos la lista de colecciones
        return {
            "collections": [collection for collection in collections]
        }  # Aplanamos la lista de tuplas
    else:
        return {"message": "No collections found."}


@router.post("/document")
async def document_post(
    collection_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    start_time = time.time()

    # Medición inicial de recursos
    initial_cpu, initial_memory = get_system_usage()

    try:
        print(
            f"[rt_documents] Datos recibidos: collection_name={collection_name}, file={file.filename}"
        )

        # Generar un nombre único para el archivo en Supabase
        if file.filename is None:
            raise HTTPException(status_code=400, detail="Filename is missing")

        cleaned_filename = clean_filename(file.filename.replace(" ", "_"))
        storage_path = f"{collection_name}/{cleaned_filename}"

        # Verificar si el archivo ya existe en la colección
        client_supabase = get_client_supabase()
        response = client_supabase.storage.from_("documents").list(collection_name)
        existing_files = [item["name"] for item in response if "name" in item]

        if cleaned_filename in existing_files:
            elapsed_time = time.time() - start_time
            return JSONResponse(
                {
                    "status": "Documento existente en la colección",
                    "filename": file.filename,
                    "message": f"Este documento ya está registrado en la colección '{collection_name}'.",
                    "execution_time": elapsed_time,
                }
            )

        save_start = time.time()

        # Subir el archivo a Supabase Storage
        upload_start = time.time()
        response = client_supabase.storage.from_("documents").upload(
            storage_path,
            await file.read(),
            file_options={"Content-Type": f"{file.content_type}"},  # type: ignore
        )
        upload_time = time.time() - upload_start

        print("[rt_documents] response: ", response)

        if not response.full_path:
            elapsed_time = time.time() - start_time
            return JSONResponse(
                {
                    "status": "Error",
                    "message": f"No se pudo subir el archivo '{file.filename}'.",
                    "execution_time": elapsed_time,
                }
            )

        # Obtener la URL pública del archivo
        public_url = client_supabase.storage.from_("documents").get_public_url(
            storage_path
        )
        print("[public_url] ", public_url)

        if not public_url:
            elapsed_time = time.time() - start_time
            final_cpu, final_memory = get_system_usage()
            return JSONResponse(
                {
                    "status": "Error",
                    "message": "No se pudo guardar el archivo.",
                    "execution_time": elapsed_time,
                    "cpu_usage": {"initial": initial_cpu, "final": final_cpu},
                    "memory_usage": {"initial": initial_memory, "final": final_memory},
                }
            )

        result = await save_document(
            file, collection_name, public_url, physical_path=None
        )

        if result is None:
            elapsed_time = time.time() - start_time
            final_cpu, final_memory = get_system_usage()
            return JSONResponse(
                {
                    "status": "Error",
                    "message": "No se pudo guardar el archivo.",
                    "execution_time": elapsed_time,
                    "cpu_usage": {"initial": initial_cpu, "final": final_cpu},
                    "memory_usage": {"initial": initial_memory, "final": final_memory},
                }
            )
        document = result
        save_time = time.time() - save_start

        # Medir recursos después de guardar
        save_cpu, save_memory = get_system_usage()

        print("[rt_documents] file_path: ", public_url)
        print("[rt_documents] document: ", document)

        # Medir recursos después del procesamiento
        process_cpu, process_memory = get_system_usage()

        # Simular el procesamiento del documento
        process_start = time.time()
        doc_len, chunk_len = process_pdf(
            file, public_url, collection_name, document.id  # type: ignore
        )

        process_time = time.time() - process_start

        # Medición de recursos después del procesamiento
        final_cpu, final_memory = get_system_usage()
        total_time = time.time() - start_time

        # Preparar datos de métricas
        execution_times = {
            "upload_time": upload_time,
            "process_time": process_time,
            "total_time": total_time,
            "save_time": save_time,
        }
        cpu_usage = {
            "initial": initial_cpu,
            "save": save_cpu,
            "process": process_cpu,
            "final": final_cpu,
        }

        memory_usage = {
            "initial": initial_memory,
            "save": save_memory,
            "process": process_memory,
            "final": final_memory,
        }

        save_metrics_docs(
            db, document.id, execution_times, cpu_usage, memory_usage  # type: ignore
        )

        # Retornar respuesta exitosa
        return JSONResponse(
            {
                "status": "Successfully Uploaded",
                "filename": file.filename,
                "collection_name": collection_name,
                "file_url": public_url,
                "doc_len": doc_len,
                "chunks": chunk_len,
                "execution_times": execution_times,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "message": "El archivo se subió y procesó correctamente.",
            }
        )

    except Exception as e:
        elapsed_time = time.time() - start_time
        final_cpu, final_memory = get_system_usage()
        print(f"Error en document_post: {e}")
        print("Traceback completo:")
        traceback.print_exc()
        return JSONResponse(
            {
                "status": "Error",
                "message": "Ocurrió un error procesando el archivo.",
                "execution_time": elapsed_time,
                "cpu_usage": {"initial": initial_cpu, "final": final_cpu},
                "memory_usage": {"initial": initial_memory, "final": final_memory},
            }
        )


@router.put("/edit_document/{document_id}")
async def edit_document(
    document_id: int,
    name: str = Form(...),
    collection_name: str = Form(...),
    created_at: str = Form(...),
    db: Session = Depends(get_db),
):
    print(
        "[edit_document] llega con los valores: ",
        document_id,
        name,
        collection_name,
        created_at,
    )

    # Buscar el documento por su ID
    document = db.query(Document).filter(Document.id == document_id).first()

    # Si el documento no existe, devolver un error
    if not document:
        print("No encuentra el documento")
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Obtener el path actual del documento
    old_path = document.path

    # Actualizar los valores del documento con los nuevos datos
    try:
        # Actualizar campos
        document.name = name  # type: ignore
        document.collection_name = collection_name  # type: ignore
        document.created_at = created_at  # type: ignore

        # Actualizar el campo 'path' basándose en el nuevo 'name'
        new_path = f"./documents/{name}"
        document.path = new_path  # type: ignore # El nuevo path basado en el nombre recibido
        # Renombrar el archivo físico si el nombre del documento ha cambiado
        if str(old_path) != str(new_path) and os.path.exists(str(old_path)):
            # Renombrar el archivo físico en el sistema
            os.rename(str(old_path), str(new_path))

        # Guardar los cambios en la base de datos
        db.commit()
        db.refresh(document)  # Recargar el documento actualizado

        # Retornar respuesta exitosa
        return {
            "status": "Successfully Updated",
            "document_id": document.id,
            "name": document.name,
            "collection_name": document.collection_name,
            "path": document.path,
            "created_at": document.created_at.isoformat(),
            "message": "Documento actualizado correctamente.",
        }
    except Exception as e:
        db.rollback()  # Si ocurre un error, deshacer los cambios
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar el documento. Intente nuevamente.",
        )
    finally:
        db.close()


# @router.delete("/delete_document/{document_id}")
# async def delete_document(document_id: int):
#     print("[rt_documents] delete_document()")
#     print(f"[rt_documents] valor de document_id : {document_id}")
#     db: Session = SessionLocal()

#     try:
#         # Buscar el documento por su ID
#         document = db.query(Document).filter(Document.id == document_id).first()

#         if not document:
#             raise HTTPException(status_code=404, detail="Documento no encontrado")

#         # Eliminar el archivo físico del sistema (si existe)
#         if os.path.exists(str(document.path)):
#             os.remove(str(document.path))

#         if document.embeddings_uuids:  # type: ignore
#             print("[rt_documents] ingresa en el condicional")
#             collection = get_collection(document.collection_name)

#             # collection = return_collection(document.collection_name)
#             print(f"[rt_documents] collection: {collection}")
#             embeddings_to_delete = document.embeddings_uuids
#             print(f"[rt_documents] embeddings_to_delete: {embeddings_to_delete}")

#             for id_embedding in embeddings_to_delete:
#                 try:
#                     if collection is not None:
#                         collection.delete(ids=id_embedding)  # type: ignore
#                         print(
#                             f"Embeddings con ID {id_embedding} eliminado exitosamente."
#                         )
#                     else:
#                         print(f"Collection not found for document {document.id}")
#                 except Exception as e:
#                     print(f"Error al eliminar embedding con ID {id_embedding}: {e}")
#         else:
#             raise HTTPException(
#                 status_code=404, detail="Embeddings no encontrados para el documento"
#             )

#         # Eliminar el registro de la base de datos
#         db.delete(document)
#         db.commit()

#         return {
#             "status": "Successfully Deleted",
#             "document_id": document_id,
#             "message": f"El documento '{document.name}' fue eliminado correctamente.",
#         }

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500, detail=f"Error al eliminar el documento: {str(e)}"
#         )
#     finally:
#         db.close()
