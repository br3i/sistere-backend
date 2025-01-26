# routes/routes_documents.py
import time
import os
import io
import base64
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.document import Document
from urllib.parse import unquote
from fastapi import (
    APIRouter,
    File,
    Form,
    UploadFile,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from services.embeddings.get_create_collection import get_collection, create_collection

# from services.helpers.return_collection import return_collection
from services.helpers.system_usage import get_system_usage
from services.helpers.get_image_page import extract_page_image
from services.helpers.clean_filename import clean_filename
from services.documents.save_docs.upload_service import (
    check_document_exists,
    save_document,
)
from services.documents.save_docs.process_any_document_service import process_pdf
from models.supabase_client import supabase
from services.metrics.save_metrics.save_metrics_docs import save_metrics_docs

#!!!!!!!!!!!CORREGIR EL USO DE GET_DOCUMENTS, que sea solo aqui
from services.documents.obtain_docs.get_documents_service import get_documents

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documents")

router = APIRouter()


@router.get("/documents_directory")
async def get_files():
    documents = get_documents()
    return documents


@router.get("/documents_from_db")
async def get_documents_from_db():
    db: Session = SessionLocal()
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


# @router.get("/get_page_image")
# async def get_page_image(file_path: str, resolve_page: int):
#     try:
#         # Verificar si el archivo existe en el directorio
#         file_path = os.path.relpath(file_path, start="documents")
#         full_path = os.path.join(DOCUMENTS_PATH, file_path)
#         if not os.path.exists(full_path):
#             raise HTTPException(status_code=404, detail="Archivo no encontrado")

#         # Obtener la imagen de la página solicitada
#         image = extract_page_image(full_path, resolve_page)

#         # Convertir la imagen a un formato adecuado para enviarla como respuesta
#         img_byte_arr = io.BytesIO()
#         image.save(img_byte_arr, format="PNG")
#         img_byte_arr.seek(0)

#         return StreamingResponse(img_byte_arr, media_type="image/png")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/get_page_images")
async def get_page_images(websocket: WebSocket):
    await websocket.accept()
    try:
        # Recibir datos de las solicitudes como una lista
        data = await websocket.receive_json()
        print("[rt_documents] data: ", data)

        for request in data:
            try:
                file_path = request["file_path"]
                resolve_page = request["resolve_page"]

                # Verificar que el archivo existe
                file_path = os.path.relpath(file_path, start="documents")
                full_path = os.path.join("documents", file_path)
                if not os.path.exists(full_path):
                    # Enviar un mensaje de error para este archivo/página
                    await websocket.send_json(
                        {
                            "error": f"Archivo no encontrado: {file_path}",
                            "file_path": file_path,
                            "resolve_page": resolve_page,
                        }
                    )
                    continue

                # Extraer la imagen de la página
                image = extract_page_image(full_path, resolve_page)

                # Convertir la imagen a base64 para enviarla por WebSocket
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="PNG")
                img_byte_arr.seek(0)
                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

                # Enviar la imagen y los metadatos como respuesta
                await websocket.send_json(
                    {
                        "file_path": file_path,
                        "document_name": os.path.basename(file_path),
                        "resolve_page": resolve_page,
                        "image": img_base64,
                    }
                )
            except Exception as e:
                # Enviar un mensaje de error en caso de fallo
                await websocket.send_json(
                    {
                        "error": str(e),
                        "file_path": request.get("file_path", "Desconocido"),
                        "resolve_page": request.get("resolve_page", "Desconocido"),
                    }
                )

    except WebSocketDisconnect:
        print("WebSocket desconectado")
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        await websocket.close()


@router.get("/document/{filename}")
async def serve_document(filename: str):
    # print('[rt_document] Llega a la función de serve_document')
    file_path = os.path.join(DOCUMENTS_PATH, unquote(filename))
    # print(f'[rt_document] document_directory: {DOCUMENTS_PATH}, file_path: {file_path}')

    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf")
    else:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")


@router.post("/document")
async def document_post(collection_name: str = Form(...), file: UploadFile = File(...)):
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
        response = supabase.storage.from_("documents").list(collection_name)
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

        # Subir el archivo a Supabase Storage
        upload_start = time.time()
        response = supabase.storage.from_("documents").upload(
            storage_path, await file.read()
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
        public_url = supabase.storage.from_("documents").get_public_url(storage_path)
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

        save_start = time.time()
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
        }

        cpu_usage = {"initial": initial_cpu, "final": final_cpu}
        memory_usage = {"initial": initial_memory, "final": final_memory}

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
):
    print(
        "[edit_document] llega con los valores: ",
        document_id,
        name,
        collection_name,
        created_at,
    )
    db: Session = SessionLocal()

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


@router.delete("/delete_document/{document_id}")
async def delete_document(document_id: int):
    print("[rt_documents] delete_document()")
    print(f"[rt_documents] valor de document_id : {document_id}")
    db: Session = SessionLocal()

    try:
        # Buscar el documento por su ID
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        # Eliminar el archivo físico del sistema (si existe)
        if os.path.exists(str(document.path)):
            os.remove(str(document.path))

        if document.embeddings_uuids:  # type: ignore
            print("[rt_documents] ingresa en el condicional")
            collection = get_collection(document.collection_name)

            # collection = return_collection(document.collection_name)
            print(f"[rt_documents] collection: {collection}")
            embeddings_to_delete = document.embeddings_uuids
            print(f"[rt_documents] embeddings_to_delete: {embeddings_to_delete}")

            for id_embedding in embeddings_to_delete:
                try:
                    if collection is not None:
                        collection.delete(ids=id_embedding)  # type: ignore
                        print(
                            f"Embeddings con ID {id_embedding} eliminado exitosamente."
                        )
                    else:
                        print(f"Collection not found for document {document.id}")
                except Exception as e:
                    print(f"Error al eliminar embedding con ID {id_embedding}: {e}")
        else:
            raise HTTPException(
                status_code=404, detail="Embeddings no encontrados para el documento"
            )

        # Eliminar el registro de la base de datos
        db.delete(document)
        db.commit()

        return {
            "status": "Successfully Deleted",
            "document_id": document_id,
            "message": f"El documento '{document.name}' fue eliminado correctamente.",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar el documento: {str(e)}"
        )
    finally:
        db.close()
