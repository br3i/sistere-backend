from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.nr_database.nr_connection_service import get_collection_names

#!!!!!! APLICAR PARA GEMINI
# import services.query_service

router = APIRouter()


class QueryModel(BaseModel):
    query: str


@router.get("/collection_names")
async def rt_get_collection_names():
    # Lógica para obtener las colecciones desde tu base de datos
    collection_names = get_collection_names()
    print("[rt_db_nr] Las colecciones que se obtienen de la base: ", collection_names)
    return JSONResponse(content={"collections": collection_names})
