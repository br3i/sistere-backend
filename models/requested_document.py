import os
import pytz
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")


class RequestedDocument(Base):
    __tablename__ = "requested_documents"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_requested_at = Column(DateTime, default=datetime.now(pytz.timezone(TIME_ZONE)))
    requested_count = Column(Integer, default=1)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    # Relación con el modelo Document
    document = relationship(
        "Document", back_populates="requests", overlaps="document_ref"
    )

    def __repr__(self):
        return f"<RequestedDocument(id={self.id}, document_id={self.document_id}, last_requested_at={self.last_requested_at}, requested_count={self.requested_count})>"
