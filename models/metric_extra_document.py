from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class MetricExtraDocument(Base):
    __tablename__ = "metrics_extra_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_id = Column(Integer, ForeignKey("metrics.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    save_time = Column(Float, nullable=False)  # Tiempo de guardado
    cpu_save = Column(Float, nullable=False)  # Uso de CPU después de guardar
    memory_save = Column(Float, nullable=False)  # Uso de memoria después de guardar
    process_time = Column(Float, nullable=False)  # Tiempo de procesamiento
    cpu_process = Column(Float, nullable=False)  # Uso de CPU después del procesamiento
    memory_process = Column(Float, nullable=False)  # Memoria después del procesamiento

    metric = relationship("Metric", back_populates="document_metrics")
    document = relationship("Document", back_populates="document_metrics")

    def __repr__(self):
        return f"<MetricExtraDocument(id={self.id}, metric_id={self.metric_id}, save_time={self.save_time}, cpu_save={self.cpu_save}, memory_save={self.memory_save})>"
