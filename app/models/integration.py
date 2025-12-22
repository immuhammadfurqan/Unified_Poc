from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class Integration(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    provider = Column(String, nullable=False)  # github, figma, trello
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    provider_metadata = Column(JSON, nullable=True)  # Provider-specific data e.g., {"github_username": "user123"}
    
    user = relationship("User", backref="integrations")

