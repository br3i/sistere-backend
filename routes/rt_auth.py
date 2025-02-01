# rt_auth.py
import os
import jwt
import pytz
import bcrypt
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


# Crear un token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    expire = datetime.now(tz) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
