# models/user.py
import os
import pytz
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")

# Definir los posibles valores para los roles (en lugar de un Enum)
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_VIEWER = "viewer"
ALLOWED_ROLES = [ROLE_ADMIN, ROLE_USER, ROLE_VIEWER]


class User(Base):
    __tablename__ = "users"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    roles = Column(JSONB, default=[])
    created_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )
    updated_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )

    # Relación con el modelo Code
    codes = relationship("Code", back_populates="user", cascade="all, delete-orphan")

    # Relación con el modelo Notification
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    # Método para validar los roles antes de asignarlos
    def set_roles(self, roles):
        if all(role in ALLOWED_ROLES for role in roles):
            self.roles = roles
        else:
            raise ValueError(
                f"Roles inválidos. Los roles permitidos son: {', '.join(ALLOWED_ROLES)}"
            )

    # Definir relaciones si es necesario (no se necesitan para este caso)
    # documents = relationship("Document", back_populates="owner")

    def __repr__(self):
        return f"<User(email={self.email}, first_name={self.first_name}, last_name={self.last_name})>"
