import uuid
from sqlalchemy import Column, Integer, ForeignKey, Float, String
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship
from .database import Base


class Embedding(Base):
    __tablename__ = "embeddings"  # Nombre de la tabla en la base de datos

    id = Column(UUID, primary_key=True, default=uuid.uuid4)  # Usamos UUID como ID
    embedding = Column(ARRAY(Float), nullable=False)  # El vector de embeddings
    embed_metadata = Column(JSON, nullable=False)  # La metadata asociada
    collection_name = Column(String, nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"))

    document = relationship("Document", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, embedding={self.embedding}, metadata={self.embed_metadata}, document_id={self.document_id})>"
