from typing import Optional, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas


def get_student_by_id(db: Session, student_pk: int) -> Optional[models.Student]:
    """Retrieve a student by primary key ID."""
    return db.query(models.Student).filter(models.Student.id == student_pk).first()


def get_student_by_student_id(db: Session, student_id: str) -> Optional[models.Student]:
    """Retrieve a student by the unique student_id string."""
    return db.query(models.Student).filter(models.Student.student_id == student_id).first()


def get_student_by_email(db: Session, email: str) -> Optional[models.Student]:
    """Retrieve a student by their unique email."""
    return db.query(models.Student).filter(models.Student.email == email).first()


def get_student_by_identifier(db: Session, identifier: str) -> Optional[models.Student]:
    """
    Convenience lookup: searches first by exact student_id string;
    if not found and identifier is numeric, searches by primary key integer id.
    """
    student = get_student_by_student_id(db, student_id=identifier)
    if not student and identifier.isdigit():
        student = get_student_by_id(db, student_pk=int(identifier))
    return student


def get_students(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    course: Optional[str] = None,
    name: Optional[str] = None,
) -> List[models.Student]:
    """
    Retrieve students with optional filtering by course and name, with pagination.
    """
    query = db.query(models.Student)

    if course:
        # Case-insensitive substring match for course
        query = query.filter(models.Student.course.ilike(f"%{course.strip()}%"))

    if name:
        # Case-insensitive substring match for name
        query = query.filter(models.Student.name.ilike(f"%{name.strip()}%"))

    return query.order_by(models.Student.id.asc()).offset(skip).limit(limit).all()


def count_students(db: Session) -> int:
    """Return total number of student records."""
    return db.query(func.count(models.Student.id)).scalar() or 0


def create_student(db: Session, student_in: schemas.StudentCreate) -> models.Student:
    """Create a new student record in SQLite."""
    student_data = student_in.model_dump()
    db_student = models.Student(**student_data)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def update_student(
    db: Session,
    db_student: models.Student,
    student_in: Union[schemas.StudentUpdate, dict],
) -> models.Student:
    """
    Update an existing student record.
    Supports partial updates by excluding unset fields.
    """
    update_data = (
        student_in.model_dump(exclude_unset=True)
        if isinstance(student_in, schemas.StudentUpdate)
        else student_in
    )

    for field, value in update_data.items():
        setattr(db_student, field, value)

    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, db_student: models.Student) -> None:
    """Remove a student record from the database."""
    db.delete(db_student)
    db.commit()


def get_all_students_for_ai(db: Session, max_records: int = 200) -> List[dict]:
    """
    Securely fetch structured student records as plain dictionaries for AI grounding.
    Does NOT run raw SQL from LLM; only queries defined ORM columns.
    """
    students = db.query(models.Student).limit(max_records).all()
    records = []
    for s in students:
        records.append({
            "student_id": s.student_id,
            "name": s.name,
            "dob": s.dob.isoformat() if s.dob else None,
            "email": s.email,
            "phone": s.phone,
            "course": s.course,
            "address": s.address,
            "enrollment_date": s.enrollment_date.isoformat() if s.enrollment_date else None,
        })
    return records
