"""
Database Seeding Script
Populates the SQLite database with realistic Indian student records for testing and demonstration.
"""
from datetime import date
from database import SessionLocal, create_tables
import models
import crud
import schemas

SAMPLE_STUDENTS = [
    {
        "student_id": "STU-2024-001",
        "name": "Aarav Sharma",
        "dob": date(2004, 3, 12),
        "email": "aarav.sharma@university.edu.in",
        "phone": "+91-98765-43210",
        "course": "Computer Science & Engineering",
        "address": "Flat 402, Shanti Niketan Apts, Powai, Mumbai, Maharashtra - 400076",
        "enrollment_date": date(2024, 8, 1),
    },
    {
        "student_id": "STU-2024-002",
        "name": "Ananya Iyer",
        "dob": date(2003, 11, 20),
        "email": "ananya.iyer@university.edu.in",
        "phone": "+91-98123-45678",
        "course": "Data Science & Analytics",
        "address": "12/A, Gandhi Nagar, Adyar, Chennai, Tamil Nadu - 600020",
        "enrollment_date": date(2024, 8, 1),
    },
    {
        "student_id": "STU-2024-003",
        "name": "Rohan Verma",
        "dob": date(2005, 1, 14),
        "email": "rohan.verma@university.edu.in",
        "phone": "+91-99887-76655",
        "course": "Computer Science & Engineering",
        "address": "B-104, Green Glen Layout, Bellandur, Bengaluru, Karnataka - 560103",
        "enrollment_date": date(2025, 1, 10),
    },
    {
        "student_id": "STU-2024-004",
        "name": "Priya Patel",
        "dob": date(2002, 7, 9),
        "email": "priya.patel@university.edu.in",
        "phone": "+91-97234-56789",
        "course": "Cybersecurity & Digital Forensics",
        "address": "45 Navrangpura, Near University Circle, Ahmedabad, Gujarat - 380009",
        "enrollment_date": date(2023, 8, 1),
    },
    {
        "student_id": "STU-2024-005",
        "name": "Kabir Sen",
        "dob": date(2005, 9, 25),
        "email": "kabir.sen@university.edu.in",
        "phone": "+91-98301-23456",
        "course": "Artificial Intelligence & Machine Learning",
        "address": "88 Southern Avenue, Lake Market, Kolkata, West Bengal - 700029",
        "enrollment_date": date(2025, 8, 1),
    },
]


def seed_database(clear_existing: bool = True):
    create_tables()
    db = SessionLocal()
    try:
        if clear_existing:
            # Clear previous entries to cleanly replace with Indian records
            db.query(models.Student).delete()
            db.commit()
            print("Cleared existing student records.")

        added_count = 0
        for student_dict in SAMPLE_STUDENTS:
            student_schema = schemas.StudentCreate(**student_dict)
            crud.create_student(db, student_schema)
            added_count += 1
            print(f"Created student: {student_dict['student_id']} - {student_dict['name']} ({student_dict['phone']})")

        print(f"\nSeeding complete! Successfully added {added_count} Indian student record(s).")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(clear_existing=True)
