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
from services.helpers.return_collection import return_collection
from services.helpers.system_usage import get_system_usage
from services.helpers.get_image_page import extract_page_image
from services.documents.save_docs.upload_service import (
    check_document_exists,
    save_document,
)
from services.documents.save_docs.process_any_document_service import process_pdf
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
    db: Session = SessionLocal()
    start_time = time.time()

    # Medición inicial de recursos
    initial_cpu, initial_memory = get_system_usage()

    try:
        print(
            f"[rt_documents] Datos recibidos: collection_name={collection_name}, file={file.filename}"
        )

        # Identificador único
        document_name = file.filename  # Usando el nombre del archivo como identificador
        exists = check_document_exists(document_name, collection_name)
        # print(f"[rt_documents] Lo que retorna la comprobación de existencia es: {exists}")

        # Si el documento ya existe, retornar el mensaje correspondiente
        if exists:
            elapsed_time = time.time() - start_time
            final_cpu, final_memory = get_system_usage()
            return JSONResponse(
                {
                    "status": f"Documento existente en la collection {collection_name}",
                    "filename": file.filename,
                    "message": f"Este documento ya está registrado en la colección '{collection_name}'.",
                    "execution_time": elapsed_time,
                }
            )

        # Si el documento no existe, guardar el archivo
        save_start = time.time()
        result = save_document(file, collection_name, physical_path=None)
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
        file_path, document = result
        save_time = time.time() - save_start

        # Medir recursos después de guardar
        save_cpu, save_memory = get_system_usage()

        print("[rt_documents] file_path: ", file_path)
        print("[rt_documents] document: ", document)

        if not file_path:
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

        #!!!!!! -> implementar para más tipos de archivos
        # if file.filename.lower().endswith(('.pdf')):
        #     doc_len, chunk_len = process_pdf(file_path, collection_name, document.id)
        # elif file.filename.lower().endswith(('.docx', '.doc')):
        #     doc_len, chunk_len = process_word_document(file_path, collection_name)
        # elif file.filename.lower().endswith(('.txt', '.rtf', '.odf')):
        #     doc_len, chunk_len = process_text_document(file_path, collection_name)
        # elif file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp')):
        #     doc_len, chunk_len = process_image(file_path, collection_name)
        # elif file.filename.lower().endswith(('.ppt', '.pptx')):
        #     doc_len, chunk_len = process_ppt(file_path, collection_name)
        # elif file.filename.lower().endswith(('.xls', '.xlsx')):
        #     doc_len, chunk_len = process_excel(file_path, collection_name)
        #!!!!
        # else:
        #     return {"status": "Error", "message": "Formato de archivo no soportado."}
        #!!!!

        process_start = time.time()
        doc_len, chunk_len = process_pdf(file_path, collection_name, document.id)  # type: ignore
        process_time = time.time() - process_start

        # Medir recursos después del procesamiento
        process_cpu, process_memory = get_system_usage()

        if doc_len == 0 and chunk_len == 0:
            elapsed_time = time.time() - start_time
            final_cpu, final_memory = get_system_usage()
            return JSONResponse(
                {
                    "status": "Error",
                    "message": "Error al procesar el archivo.",
                    "execution_time": elapsed_time,
                    "cpu_usage": {"initial": initial_cpu, "final": final_cpu},
                    "memory_usage": {"initial": initial_memory, "final": final_memory},
                }
            )

        total_time = time.time() - start_time
        final_cpu, final_memory = get_system_usage()

        # Preparar los datos para save_metrics
        execution_times = {
            "total_time": total_time,
            "save_time": save_time,
            "process_time": process_time,
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

        # Si todo va bien, retornar un mensaje de éxito con los datos asociados
        return JSONResponse(
            {
                "status": "Successfully Uploaded",
                "filename": file.filename,
                "collection_name": collection_name,
                "doc_len": doc_len,
                "chunks": chunk_len,
                "message": "El archivo se subió y procesó correctamente.",
                "execution_times": execution_times,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
            }
        )

    except Exception as e:
        elapsed_time = time.time() - start_time
        final_cpu, final_memory = get_system_usage()
        print(f"Error en document_post: {e}")

        # Intentamos recargar el objeto document desde la base de datos
        try:
            document = db.query(Document).filter_by(id=document.id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Documento no encontrado.")
        except Exception as db_error:
            print(f"Error al recargar el documento desde la base de datos: {db_error}")
            # Si ocurre un error al recargar el documento, puedes devolver el error apropiado
            return JSONResponse(
                {
                    "status": "Error",
                    "message": "Error al recuperar el documento desde la base de datos.",
                    "execution_time": elapsed_time,
                    "cpu_usage": {"initial": initial_cpu, "final": final_cpu},
                    "memory_usage": {"initial": initial_memory, "final": final_memory},
                }
            )

        if "document" in locals():
            # Borrar el archivo físico si se guardó
            if os.path.exists(file_path):
                os.remove(file_path)

            # Si el documento tiene embeddings, eliminarlos
            print(f"[rt_documents] exception, document: {document}")
            if document.embeddings_uuids:  # type: ignore
                print(
                    "[rt_documents] El documento tiene embeddings, intentando eliminarlos."
                )
                collection = return_collection(document.collection_name)
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
                    except Exception as embedding_error:
                        print(
                            f"Error al eliminar embedding con ID {id_embedding}: {embedding_error}"
                        )

            # Eliminar el registro de la base de datos
            db.delete(document)
            db.commit()

        db.rollback()  # Si ocurre un error, deshacer los cambios
        return JSONResponse(
            {
                "status": "Error",
                "message": "Ocurrió un error procesando el archivo.",
                "execution_time": elapsed_time,
                "cpu_usage": {"initial": initial_cpu, "final": final_cpu},
                "memory_usage": {"initial": initial_memory, "final": final_memory},
            }
        )
    finally:
        db.close()


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
            collection = return_collection(document.collection_name)
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
