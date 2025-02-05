import uuid
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from .database import Base


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    embedding = Column(Vector(1024), nullable=False)
    embed_metadata = Column(JSON, nullable=False)
    collection_name = Column(String, nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"))

    document = relationship("Document", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, embedding={self.embedding}, metadata={self.embed_metadata}, document_id={self.document_id})>"
