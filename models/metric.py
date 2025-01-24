import os
import pytz
from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")


class Metric(Base):
    __tablename__ = "metrics"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True, autoincrement=True)
    total_time = Column(Float, nullable=False)  # Tiempo total de ejecución
    cpu_initial = Column(Float, nullable=False)  # Uso de CPU inicial
    cpu_final = Column(Float, nullable=False)  # Uso de CPU final
    memory_initial = Column(Float, nullable=False)  # Uso de memoria inicial
    memory_final = Column(Float, nullable=False)  # Uso de memoria final
    created_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )  # Fecha de creación de la métrica

    document_metrics = relationship(
        "MetricExtraDocument",
        back_populates="metric",
        cascade="all, delete-orphan",
        uselist=False,
    )

    response_metrics = relationship(
        "MetricExtraResponse",
        back_populates="metric",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self):
        return f"<Metrics(id={self.id}, total_time={self.total_time}, created_at={self.created_at})>"
