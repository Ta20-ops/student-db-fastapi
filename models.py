from datetime import date
from sqlalchemy import Column, Integer, String, Date, Text
from database import Base


class Student(Base):
    """
    SQLAlchemy ORM Model representing the 'students' table in SQLite.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False, index=True)
    dob = Column(Date, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(30), nullable=True)
    course = Column(String(100), nullable=True, index=True)
    address = Column(Text, nullable=True)
    enrollment_date = Column(Date, nullable=False, default=date.today)

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.name}', email='{self.email}')>"
