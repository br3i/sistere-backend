# models/code.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import os
import enum
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")


# Definir los posibles valores para el estado del código
# class CodeStatus(str, Enum):
class CodeStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    used = "used"
    unused = "unused"


class Code(Base):
    __tablename__ = "codes"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)  # El código en sí
    status = Column(Enum(CodeStatus), default=CodeStatus.active)  # Estado del código
    created_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )  # Fecha de creación del código
    expires_at = Column(DateTime)  # Fecha de caducidad del código
    used_at = Column(DateTime, nullable=True)  # Fecha de uso, si aplica

    # Clave foránea que conecta el código con el usuario
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # Relación con el modelo User

    # Relación inversa con el modelo User
    user = relationship("User", back_populates="codes")

    def __repr__(self):
        return f"<Code(code={self.code}, status={self.status}, created_at={self.created_at}, expires_at={self.expires_at}, used_at={self.used_at})>"

    def is_expired(self):
        """Verificar si el código ha expirado"""
        if self.expires_at is not None:
            # Obtener el valor real de expires_at y compararlo
            now = datetime.now(pytz.timezone(TIME_ZONE))
            return self.expires_at < now
        return False

    def __init__(self, **kwargs):
        # Asignar automáticamente expires_at si no se proporciona
        if "expires_at" not in kwargs:
            kwargs["expires_at"] = datetime.now(pytz.timezone(TIME_ZONE)) + timedelta(
                minutes=15
            )
        super().__init__(**kwargs)
