# rt_auth.py
import os
import jwt
import pytz
import bcrypt
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from models.user import User
from models.database import get_db
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")
tz = pytz.timezone(TIME_ZONE)

# Configuración de JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "una_clave_secreta_muy_segura")
SESSION_KEY = os.getenv("SESSION_KEY", "clave_de_sesion_secreta")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

router = APIRouter()


# Modelos de Pydantic
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# Crear un token JWT con firma adicional
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    expire = datetime.now(tz) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Usar el timestamp para la firma en lugar de isoformat
    expire_timestamp = int(expire.timestamp())

    # Crear la firma única basada en el nombre de usuario y la fecha de expiración (en timestamp)
    session_data = f"{data['sub']}:{expire_timestamp}:{SESSION_KEY}"
    signature = hashlib.sha256(session_data.encode()).hexdigest()

    to_encode = data.copy()
    to_encode.update(
        {
            "exp": expire_timestamp,
            "signature": signature,
        }  # Añadimos la firma al payload
    )

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Función para verificar la firma del token
def verify_token_signature(payload: dict):
    try:
        # Obtener la firma del payload
        received_signature = payload.get("signature")

        if not received_signature:
            raise HTTPException(
                status_code=400, detail="Firma no encontrada en el token"
            )

        # Regenerar la firma a partir de los datos en el payload
        expire_timestamp = payload["exp"]  # Tomamos el timestamp del payload
        session_data = f"{payload['sub']}:{expire_timestamp}:{SESSION_KEY}"
        generated_signature = hashlib.sha256(session_data.encode()).hexdigest()

        # Verificar que las firmas coinciden
        if received_signature != generated_signature:
            raise HTTPException(status_code=400, detail="Firma del token inválida")

    except Exception as e:
        raise HTTPException(status_code=400, detail="Token inválido o modificado")


# Endpoint para iniciar sesión
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not bcrypt.checkpw(data.password.encode(), user.password.encode()):
        raise HTTPException(status_code=400, detail="Credenciales inválidas")

    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# Endpoint para validar un token de acceso
@router.get("/validate_token")
async def validate_token(
    token: str = Body(..., embed=True), db: Session = Depends(get_db)
):
    try:
        # Decodificar el token sin verificar la firma (por ahora solo decodificamos)
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False}
        )

        # Verificar la firma del token
        verify_token_signature(payload)

        # Verificación de la expiración
        exp_timestamp = payload.get("exp")
        if datetime.now(tz) > datetime.fromtimestamp(exp_timestamp, tz):
            raise HTTPException(status_code=400, detail="Token expirado")

        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if username is None or user_id is None:
            raise HTTPException(status_code=400, detail="Token inválido")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {"valid": True, "username": username, "user_id": user_id}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Token inválido")
