import os
import pytz
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from .database import Base
from sqlalchemy.orm import relationship
from datetime import datetime
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")


class Document(Base):
    __tablename__ = "documents"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    collection_name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    physical_path = Column(String, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )
    updated_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )
    embeddings_uuids = Column(ARRAY(String), default=list)

    requests = relationship(
        "RequestedDocument",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    document_metrics = relationship(
        "MetricExtraDocument", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document(id={self.id}, name={self.name}, collection_name={self.collection_name}, created_at={self.created_at}, embeddings_uuids={self.embeddings_uuids})>"
