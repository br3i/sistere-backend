import os
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import pytz
import enum
from dotenv import load_dotenv

# Cargar las variables de entorno
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Definir la zona horaria
TIME_ZONE = os.getenv(
    "TIME_ZONE", "UTC"
)  # Valor predeterminado es "UTC" si no se encuentra en el archivo .env


# Definir los posibles valores de kinds
class KindNotification(str, enum.Enum):
    urgent = "urgent"
    normal = "normal"
    reminder = "reminder"
    informative = "informative"
    alert = "alert"


class Notification(Base):
    __tablename__ = "notifications"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)  # Título de la notificación
    message = Column(String, nullable=False)  # Mensaje principal de la notificación
    roles = Column(
        JSONB, nullable=False
    )  # Roles destinatarios (e.g., ["admin", "user"])
    kind = Column(
        Enum(KindNotification), default=KindNotification.normal
    )  # Tipo de notificación (e.g., "urgent", "normal", etc.)
    created_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )
    updated_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )

    def __repr__(self):
        return (
            f"<Notification(title={self.title}, roles={self.roles}, kind={self.kind})>"
        )
