from sqlalchemy import Boolean, Column, Integer, String

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="student", nullable=False)
    is_active = Column(Boolean, default=True)