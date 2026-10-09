from sqlalchemy import Boolean, Column, Integer, String, Text

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    capacity = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)