# uvicorn app-fa:app --reload --host 0.0.0.0 --port 8080
# uvicorn app-fa:app --reload --host 0.0.0.0 --port 8080 --workers 4

# app-fa.py
import os
from fastapi import FastAPI
from routes.rt_code import router as code_router
from routes.rt_documents import router as documents_router
from routes.rt_notification import router as notification_router
from routes.rt_query import router as query_router
from routes.rt_requested_document import router as requested_document_router
from routes.rt_user import router as user_router
from models import init_db
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializa FastAPI
app = FastAPI()

# Inicializar la base de datos
reset_db = (
    os.getenv("RESET_DB", "false").lower() == "true"
)  # Leer de las variables de entorno
init_db(reset=reset_db)

# Incluir las rutas
app.include_router(code_router)
app.include_router(documents_router)
app.include_router(notification_router)
app.include_router(query_router)
app.include_router(requested_document_router)
app.include_router(user_router)

# Puedes seguir añadiendo más routers de acuerdo a la organización de tus rutas
