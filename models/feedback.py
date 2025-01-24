import os
import pytz
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from dotenv import load_dotenv

# Especifica la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Ahora puedes acceder a las variables de entorno
TIME_ZONE = os.getenv("TIME_ZONE", "America/Guayaquil")


class Feedback(Base):
    __tablename__ = "feedbacks"  # Nombre de la tabla en la base de datos

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )  # Identificador único del feedback
    model_name = Column(String, nullable=False)  # Nombre del modelo llm
    query = Column(String, nullable=False)  # La consulta realizada por el usuario
    context = Column(String, nullable=False)  # Contexto entregado por ChromaDB
    full_response = Column(
        String, nullable=False
    )  # El texto completo del documento consultado
    sources = Column(JSON, nullable=False)  # Fuentes relacionadas con el feedback
    use_considerations = Column(
        Boolean, nullable=False
    )  # Consideraciones utilizadas para la respuesta
    n_documents = Column(Integer, nullable=False)  # Número de documentos consultados
    word_list = Column(
        JSON, nullable=False
    )  # Palabras clave utilizadas para la consulta
    feedback_type = Column(String, nullable=False)  # Tipo de feedback
    score = Column(String, nullable=False)  # Calificación dada por el usuario
    text = Column(
        String, nullable=True
    )  # Texto adicional opcional proporcionado por el usuario
    created_at = Column(
        DateTime, default=lambda: datetime.now(pytz.timezone(TIME_ZONE))
    )

    def __repr__(self):
        return f"<Feedback(id={self.id}, model_name={self.model_name}, query={self.query}, context={self.context}, full_response={self.full_response}, sources={self.sources}, use_considerations={self.use_considerations}, n_documents={self.n_documents}, word_list={self.word_list}, feedback_type={self.feedback_type}, score={self.score}, text={self.text}, created_at={self.created_at})>"
