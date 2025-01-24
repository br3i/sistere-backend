import os
import pytz
import bcrypt
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from models.user import User
from models.user import ALLOWED_ROLES
from models.database import SessionLocal
from sqlalchemy.orm import Session

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")
tz = pytz.timezone(TIME_ZONE)

router = APIRouter()  # Aquí debe ser APIRouter, no FastAPI


class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    roles: list


# Pydantic model para la respuesta del usuario
class UpdateUserRequest(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    roles: list

    class Config:
        from_attributes = True


# Pydantic model para la solicitud de cambio de contraseña
class ChangePasswordRequest(BaseModel):
    password: str


# Pydantic model para la respuesta del usuario
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    roles: list
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Helper function to get a user by any field
def get_user_by_field(field_name: str, value: str, db: Session) -> User:
    print(f"[rt_user] valores: field_name: {field_name} value: {value} db: {db}")
    user = db.query(User).filter(getattr(User, field_name) == value).first()
    if not user:
        raise HTTPException(
            status_code=404, detail=f"No se encontró un usuario asociado con: {value}"
        )
    return user


# Endpoint para obtener todos los usuarios
@router.get("/users", response_model=list[UserResponse])
async def get_all_users():
    db: Session = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()  # Consulta todos los usuarios
        return [
            UserResponse(
                id=user.id,  # type: ignore
                email=user.email,  # type: ignore
                username=user.username,  # type: ignore
                first_name=user.first_name,  # type: ignore
                last_name=user.last_name,  # type: ignore
                password=user.password,  # type: ignore
                roles=user.roles,  # type: ignore
                created_at=user.created_at,  # type: ignore
                updated_at=user.updated_at,  # type: ignore
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener usuarios")
    finally:
        db.close()


# Endpoint para buscar por ID
@router.get("/user/id/{user_id}")
async def get_user_by_id(user_id: int):
    db: Session = SessionLocal()
    try:
        user = get_user_by_field("id", str(user_id), db)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            password=user.password,
            roles=user.roles,
            created_at=user.created_at,
        )  # type: ignore
    finally:
        db.close()


# Endpoint para buscar por email
@router.get("/user/email/{email}")
async def get_user_by_email(email: str):
    db: Session = SessionLocal()
    try:
        user = get_user_by_field("email", email, db)
        return UserResponse(
            id=user.id,  # type: ignore
            email=user.email,  # type: ignore
            username=user.username,  # type: ignore
            first_name=user.first_name,  # type: ignore
            last_name=user.last_name,  # type: ignore
            password=user.password,  # type: ignore
            roles=user.roles,  # type: ignore
            created_at=user.created_at,  # type: ignore
            updated_at=user.updated_at,  # type: ignore
        )
    finally:
        db.close()


# Endpoint para buscar por username
@router.get("/user/username/{username}")
async def get_user_by_username(username: str):
    db: Session = SessionLocal()
    try:
        user = get_user_by_field("username", username, db)
        return UserResponse(
            id=user.id,  # type: ignore
            email=user.email,  # type: ignore
            username=user.username,  # type: ignore
            first_name=user.first_name,  # type: ignore
            last_name=user.last_name,  # type: ignore
            password=user.password,  # type: ignore
            roles=user.roles,  # type: ignore
            created_at=user.created_at,  # type: ignore
            updated_at=user.updated_at,  # type: ignore
        )
    finally:
        db.close()


# Endpoint para buscar los roles
@router.get("/user_roles")
async def get_roles():
    db: Session = SessionLocal()
    try:
        return {"roles": ALLOWED_ROLES}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener los roles")
    finally:
        db.close()


@router.post("/create-user", response_model=UserResponse)
async def create_user(data: CreateUserRequest):
    db: Session = SessionLocal()

    # Verificar si el usuario ya existe (por email o username)
    existing_user = (
        db.query(User)
        .filter((User.email == data.email) | (User.username == data.username))
        .first()
    )
    if existing_user:
        db.close()
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    # Crear el nuevo usuario
    new_user = User(
        email=data.email,
        username=data.username,
        first_name=data.first_name,
        last_name=data.last_name,
        password=bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode(),
        roles=data.roles,
        created_at=datetime.now(tz),
        updated_at=datetime.now(tz),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    return UserResponse(
        id=new_user.id,  # type: ignore
        email=new_user.email,  # type: ignore
        username=new_user.username,  # type: ignore
        first_name=new_user.first_name,  # type: ignore
        last_name=new_user.last_name,  # type: ignore
        password=new_user.password,  # type: ignore
        roles=new_user.roles,  # type: ignore
        created_at=new_user.created_at,  # type: ignore
        updated_at=new_user.updated_at,  # type: ignore
    )


# Endpoint para actualizar usuario
@router.put("/edit_user/{user_id}")
async def update_user(user_id: int, data: UpdateUserRequest):
    print(f"[edit_user] datos que llegan : {data}")
    # Buscar el usuario a actualizar
    db: Session = SessionLocal()

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Actualizar los datos del usuario
    user.email = data.email  # type: ignore
    user.username = data.username  # type: ignore
    user.first_name = data.first_name  # type: ignore
    user.last_name = data.last_name  # type: ignore
    user.roles = data.roles

    user.updated_at = datetime.now(tz)  # type: ignore

    print(
        f"[edit_user_test] valores nuevos tras actualizar: user.email: {user.email}, user.username: {user.username}, user.first_name: {user.first_name}, user.last_name: {user.last_name}, user.roles: {user.roles}, user.updated_at: {user.updated_at}"
    )

    # Guardar los cambios en la base de datos
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,  # type: ignore
        email=user.email,  # type: ignore
        username=user.username,  # type: ignore
        first_name=user.first_name,  # type: ignore
        last_name=user.last_name,  # type: ignore
        password=user.password,  # type: ignore
        roles=user.roles,
        created_at=user.created_at,  # type: ignore
        updated_at=user.updated_at,  # type: ignore
    )


@router.put("/change-password/{user_id}")
async def change_password(user_id: int, data: ChangePasswordRequest):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Actualizar la contraseña (en producción deberías cifrarla)
    user.password = data.password  # type: ignore
    db.commit()
    db.close()

    return {"message": "Contraseña actualizada exitosamente"}


@router.delete("/delete_user/{user_id}")
async def delete_user(user_id: int):
    db: Session = SessionLocal()
    try:
        # Buscar el usuario por su ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        username = user.username
        # Eliminar el usuario de la base de datos
        db.delete(user)
        db.commit()

        return {"message": f"Usuario con username {username} eliminado exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al eliminar usuario")
    finally:
        db.close()
