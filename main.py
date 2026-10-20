from contextlib import asynccontextmanager
import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
import crud
from database import get_db, create_tables
from ai_helper import ask_student_ai, check_ollama_available


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler:
    Ensures database tables are created automatically on application startup.
    """
    create_tables()
    yield


app = FastAPI(
    title="Student Database Management API",
    description=(
        "Production-ready Student Database CRUD service built with FastAPI, "
        "SQLite (SQLAlchemy ORM), Pydantic v2, and integrated Ollama AI Assistant."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Enable Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets if the folder exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get(
    "/",
    tags=["Root"],
    summary="Web Dashboard & Health info",
)
def root(request: Request):
    """
    Smart root handler:
    - If accessed from a web browser (Accept: text/html), renders the interactive Frontend Dashboard.
    - If accessed by API clients or tests (Accept: application/json), returns API health metadata.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {
        "status": "healthy",
        "service": "Student Database Management API",
        "version": "1.0.0",
        "dashboard": "/dashboard",
        "documentation": "/docs",
        "redoc": "/redoc",
    }


@app.get(
    "/dashboard",
    include_in_schema=False,
)
def serve_dashboard():
    """Direct route to the EduTrack interactive Frontend Dashboard."""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Dashboard static files not found."}


# Convenience routes for direct static assets
@app.get("/style.css", include_in_schema=False)
def serve_css():
    return FileResponse("static/style.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def serve_js():
    return FileResponse("static/app.js", media_type="application/javascript")


# ---------------------------------------------------------------------------
# Student CRUD Endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/students",
    response_model=schemas.StudentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Students"],
    summary="Create a new student",
)
def create_student(
    student_in: schemas.StudentCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new student record.

    Validates:
    - `student_id` must be unique (HTTP 400 if duplicate exists).
    - `email` must be unique (HTTP 400 if duplicate exists).
    - `dob` must be a valid date in YYYY-MM-DD format.
    """
    # Check for duplicate student_id
    if crud.get_student_by_student_id(db, student_id=student_in.student_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student record with student_id '{student_in.student_id}' already exists.",
        )

    # Check for duplicate email
    if crud.get_student_by_email(db, email=student_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student record with email '{student_in.email}' already exists.",
        )

    return crud.create_student(db=db, student_in=student_in)


@app.get(
    "/students",
    response_model=List[schemas.StudentResponse],
    tags=["Students"],
    summary="List all students with optional filtering and pagination",
)
def list_students(
    course: Optional[str] = Query(
        default=None,
        description="Filter students by course name (case-insensitive substring match)",
    ),
    name: Optional[str] = Query(
        default=None,
        description="Search students by name (case-insensitive substring match)",
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip for pagination",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of records to return",
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve all students with optional filters for `course` and `name` search,
    along with `skip` and `limit` pagination parameters.
    """
    return crud.get_students(
        db=db,
        skip=skip,
        limit=limit,
        course=course,
        name=name,
    )


@app.get(
    "/students/{student_id}",
    response_model=schemas.StudentResponse,
    tags=["Students"],
    summary="Fetch a single student profile",
)
def get_student(
    student_id: str,
    db: Session = Depends(get_db),
):
    """
    Fetch a student by `student_id` (e.g. 'STU-101' or internal primary key ID).
    Returns 404 Not Found if the record does not exist.
    """
    student = crud.get_student_by_identifier(db, identifier=student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier '{student_id}' not found.",
        )
    return student


@app.put(
    "/students/{student_id}",
    response_model=schemas.StudentResponse,
    tags=["Students"],
    summary="Update a student profile (Full/Partial update)",
)
def update_student_put(
    student_id: str,
    student_in: schemas.StudentUpdate,
    db: Session = Depends(get_db),
):
    """
    Update student details by `student_id`.
    Returns 404 if not found.
    Validates uniqueness of `student_id` and `email` if they are being updated.
    """
    student = crud.get_student_by_identifier(db, identifier=student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier '{student_id}' not found.",
        )

    # If updating student_id, ensure no conflict with another student
    if student_in.student_id and student_in.student_id != student.student_id:
        existing_stu = crud.get_student_by_student_id(db, student_id=student_in.student_id)
        if existing_stu and existing_stu.id != student.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another student with student_id '{student_in.student_id}' already exists.",
            )

    # If updating email, ensure no conflict with another student
    if student_in.email and student_in.email != student.email:
        existing_email = crud.get_student_by_email(db, email=student_in.email)
        if existing_email and existing_email.id != student.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another student with email '{student_in.email}' already exists.",
            )

    return crud.update_student(db=db, db_student=student, student_in=student_in)


@app.patch(
    "/students/{student_id}",
    response_model=schemas.StudentResponse,
    tags=["Students"],
    summary="Partially update a student profile",
)
def update_student_patch(
    student_id: str,
    student_in: schemas.StudentUpdate,
    db: Session = Depends(get_db),
):
    """
    Alias endpoint for PATCH /students/{student_id}.
    Allows updating a subset of student fields.
    """
    return update_student_put(student_id=student_id, student_in=student_in, db=db)


@app.delete(
    "/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Students"],
    summary="Delete a student record",
)
def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
):
    """
    Remove a student record by `student_id`.
    Returns HTTP 204 No Content on success, or 404 Not Found if not found.
    """
    student = crud.get_student_by_identifier(db, identifier=student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier '{student_id}' not found.",
        )

    crud.delete_student(db=db, db_student=student)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Optional Bonus Extension: Ollama AI Grounded Q&A
# ---------------------------------------------------------------------------


@app.post(
    "/ask-ai",
    response_model=schemas.AskAIResponse,
    tags=["AI Assistant"],
    summary="Query student database using Natural Language via Ollama",
)
async def ask_ai_endpoint(
    payload: schemas.AskAIRequest,
    db: Session = Depends(get_db),
):
    """
    Accepts natural language questions about students.
    Securely fetches student records from SQLite (no raw SQL execution)
    and passes them as grounded context to a local Ollama model (llama3.2:1b).
    """
    total_count = crud.count_students(db)
    records = crud.get_all_students_for_ai(db, max_records=200)

    model_name = payload.model or "llama3.2:1b"
    answer = await ask_student_ai(
        question=payload.question,
        students=records,
        total_count=total_count,
        model=model_name,
    )

    return schemas.AskAIResponse(
        question=payload.question,
        answer=answer,
        model=model_name,
        total_students_in_db=total_count,
        records_analyzed=len(records),
    )


@app.get(
    "/ask-ai/status",
    tags=["AI Assistant"],
    summary="Check local Ollama daemon connectivity",
)
async def ask_ai_status():
    """
    Utility check to see if the local Ollama instance is accessible.
    """
    is_available = await check_ollama_available()
    return {
        "ollama_available": is_available,
        "default_model": "llama3.2:1b",
        "instructions": (
            "Ready to use" if is_available
            else "Ollama is not running. Run 'ollama serve' and 'ollama pull llama3.2:1b' to activate."
        ),
    }
