import json
import bcrypt
import os
import pytz
from sqlalchemy.orm import Session
from models.database import SessionLocal
from .database import Base, engine
from .user import User
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

EMAIL_ADMINISTRADOR = os.getenv("EMAIL_ADMINISTRADOR", "Not Found")
USERNAME_ADMINISTRADOR = os.getenv("USERNAME_ADMINISTRADOR", "Not Found")
NOMBRE_ADMINISTRADOR = os.getenv("NOMBRE_ADMINISTRADOR", "Not Found")
APELLIDO_ADMINISTRADOR = os.getenv("APELLIDO_ADMINISTRADOR", "Not Found")
CONTRASENA_ADMINISTRADOR = os.getenv("CONTRASENA_ADMINISTRADOR", "Not Found")
CONTRASENA_ADMINISTRADOR_HASH = bcrypt.hashpw(
    CONTRASENA_ADMINISTRADOR.encode(), bcrypt.gensalt()
).decode()
ROLES_ADMINISTRADOR = json.loads(
    os.getenv("ROLES_ADMINISTRADOR", '["admin", "user", "viewer"]')
)
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")
tz = pytz.timezone(TIME_ZONE)


# Crear tablas si no existen
def init_db(reset=False):
    db: Session = SessionLocal()

    if reset:
        print("Reiniciando la base de datos...")
        Base.metadata.drop_all(bind=engine)  # Elimina todas las tablas existentes
    Base.metadata.create_all(bind=engine)  # Crea las tablas si no existen

    # Verificar si ya existe un usuario administrador
    admin_user = db.query(User).filter(User.roles.op("@>")(["admin"])).first()

    if not admin_user:
        # Si no existe, crear uno nuevo
        print("Creando el primer usuario administrador...")
        new_admin = User(
            email=EMAIL_ADMINISTRADOR,
            username=USERNAME_ADMINISTRADOR,
            first_name=NOMBRE_ADMINISTRADOR,
            last_name=APELLIDO_ADMINISTRADOR,
            password=CONTRASENA_ADMINISTRADOR_HASH,
            roles=ROLES_ADMINISTRADOR,
            created_at=datetime.now(tz),
            updated_at=datetime.now(tz),
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print("Usuario administrador creado.")

    db.close()  # Cerrar la sesión
    print("Base de datos inicializada correctamente.")
