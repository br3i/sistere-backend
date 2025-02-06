from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class MetricExtraResponse(Base):
    __tablename__ = "metrics_extra_response"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_id = Column(Integer, ForeignKey("metrics.id"), nullable=False)
    load_model_duration = Column(Float, nullable=False)
    number_tokens_prompt = Column(Integer, nullable=False)
    time_evaluating_prompt = Column(Float, nullable=False)
    number_tokens_response = Column(Integer, nullable=False)
    time_generating_response = Column(Float, nullable=False)
    time_searching_documents = Column(Float, nullable=False)

    metric = relationship("Metric", back_populates="response_metrics")

    def __repr__(self):
        return f"<MetricExtraResponse(id={self.id}, metric_id={self.metric_id}, )>"
