import os
import pytz
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union, Optional
from sqlalchemy.orm import Session
from models.code import Code, CodeStatus
from models.user import User
from models.database import SessionLocal
from datetime import datetime
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")
tz = pytz.timezone(TIME_ZONE)

router = APIRouter()


# Pydantic model para la solicitud de creación de código
class CreateCodeRequest(BaseModel):
    code: str
    user_id: int

    class Config:
        from_attributes = True


# Pydantic model para la respuesta del código
class CodeResponse(BaseModel):
    id: int
    code: str
    status: CodeStatus
    created_at: datetime
    expires_at: datetime
    used_at: Optional[datetime]

    class Config:
        from_attributes = True


class CreateCodeResponse(BaseModel):
    id: int
    code: str
    status: CodeStatus
    created_at: datetime
    expires_at: datetime
    used_at: Optional[datetime]
    user_id: int

    class Config:
        from_attributes = True


class VerifyCodeRequest(BaseModel):
    code: str


class UpdateCodeStatusRequest(BaseModel):
    status: CodeStatus


# Helper function to get a code by any field
def get_code_by_field(field_name: str, value: Union[str, int], db: Session) -> Code:
    code = db.query(Code).filter(getattr(Code, field_name) == value).first()
    if not code:
        raise HTTPException(
            status_code=404, detail=f"Código no encontrado por {field_name}: {value}"
        )
    return code


# Helper function to update the code status
def update_code_status_in_db(code: Code, status: CodeStatus, db: Session) -> None:
    print("[rt_code_up] code: ", code)
    print("[rt_code_up] status: ", status)
    code.status = status.value  # type: ignore
    if status == CodeStatus.used:
        code.used_at = datetime.now(  # type: ignore
            tz
        )  # Si el estado es 'usado', registrar la fecha de uso
    db.commit()


# Endpoint para buscar por ID
@router.get("/code/id/{code_id}", response_model=CodeResponse)
async def get_code_by_id(code_id: int):
    db: Session = SessionLocal()  # Crear la sesión de base de datos
    try:
        code = get_code_by_field("id", code_id, db)
        return CodeResponse(
            id=code.id,  # type: ignore
            code=code.code,  # type: ignore
            status=code.status,  # type: ignore
            created_at=code.created_at,  # type: ignore
            expires_at=code.expires_at,  # type: ignore
            used_at=code.used_at,  # type: ignore
        )
    finally:
        db.close()  # Asegura que se cierre la sesión


# Endpoint para buscar por código
@router.get("/code/{code}", response_model=CodeResponse)
async def get_code_by_code(code: str):
    db: Session = SessionLocal()  # Crear la sesión de base de datos
    try:
        code_data = get_code_by_field("code", code, db)
        return CodeResponse(
            id=code_data.id,  # type: ignore
            code=code_data.code,  # type: ignore
            status=code_data.status,  # type: ignore
            created_at=code_data.created_at,  # type: ignore
            expires_at=code_data.expires_at,  # type: ignore
            used_at=code_data.used_at,  # type: ignore
        )
    finally:
        db.close()  # Asegura que se cierre la sesión


# Endpoint para crear un nuevo código
@router.post("/create-code", response_model=CreateCodeResponse)
async def create_code(data: CreateCodeRequest):
    # Llega a la función con estos valores:
    print("[create-code] Llega con estos valores: ", data)
    db: Session = SessionLocal()  # Crear la sesión de base de datos

    # Verificar si el código ya existe
    existing_code = db.query(Code).filter(Code.code == data.code).first()
    if existing_code:
        db.close()
        raise HTTPException(status_code=400, detail="El código ya existe")

    # Verificar que el usuario exista
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Crear el nuevo código, ahora la lógica de expires_at está en el modelo
    new_code = Code(
        code=data.code,  # El código recibido
        user_id=data.user_id,  # Asignar el user_id al código
    )

    db.add(new_code)
    db.commit()
    db.refresh(new_code)
    db.close()  # Cerrar la sesión

    return CreateCodeResponse(
        id=new_code.id,  # type: ignore
        code=new_code.code,  # type: ignore
        status=new_code.status,  # type: ignore
        created_at=new_code.created_at,  # type: ignore
        expires_at=new_code.expires_at,  # type: ignore
        used_at=new_code.used_at,  # type: ignore
        user_id=new_code.user_id,  # type: ignore
    )


# Endpoint para verificar si un código es válido
@router.post("/verify-code")
async def verify_code(data: VerifyCodeRequest):
    db: Session = SessionLocal()  # Crear la sesión de base de datos
    try:
        # Consultar el código en la base de datos
        code_data = get_code_by_field("code", data.code, db)

        # Comprobar si el código está activo
        if code_data.status != CodeStatus.active:  # type: ignore
            raise HTTPException(status_code=400, detail="El código no está activo.")

        # Obtener la fecha y hora actual en la zona horaria UTC (aware)
        current_time = datetime.now(tz)

        # Si expires_at es naive, asignarle zona horaria UTC
        if code_data.expires_at.tzinfo is None:
            code_data.expires_at = tz.localize(code_data.expires_at)  # type: ignore

        # Verificar si el código ha expirado
        if current_time > code_data.expires_at:  # type: ignore
            # Si el código ha expirado, actualizar su estado a 'expired'
            update_code_status_in_db(code_data, CodeStatus.expired, db)
            return {"success": False, "message": "El código ha expirado."}

        return {"success": True, "message": "Código válido"}

    finally:
        db.close()  # Asegura que se cierre la sesión


# Endpoint para actualizar el estado de un código (por ejemplo, marcarlo como "usado")
@router.put("/update-code-status/{code_id}")
async def update_code_status(code_id: int, request: UpdateCodeStatusRequest):
    db: Session = SessionLocal()  # Crear la sesión de base de datos
    try:
        # Obtener el código de la base de datos
        code = get_code_by_field("id", code_id, db)
        # Actualizar el estado del código
        update_code_status_in_db(code, request.status, db)
        return {
            "success": True,
            "message": f"Estado del código {code_id} actualizado a {request.status}",
        }
    finally:
        db.close()  # Asegura que se cierre la sesión


# Endpoint para verificar si un código ha expirado
@router.get("/code/{code}/expired")
async def is_code_expired(code: str):
    db: Session = SessionLocal()  # Crear la sesión de base de datos
    try:
        code_data = get_code_by_field("code", code, db)
        return {"expired": code_data.is_expired()}
    finally:
        db.close()  # Asegura que se cierre la sesión
