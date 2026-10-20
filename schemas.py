from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class StudentBase(BaseModel):
    """Base student schema with shared attributes across creation and response."""
    student_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique student identifier (e.g., STU-2024-001)",
        examples=["STU-2024-001"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the student",
        examples=["Aarav Sharma"],
    )
    dob: date = Field(
        ...,
        description="Date of birth in YYYY-MM-DD format",
        examples=["2004-03-12"],
    )
    email: EmailStr = Field(
        ...,
        description="Unique, valid student email address",
        examples=["aarav.sharma@university.edu.in"],
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Contact phone number with country code",
        examples=["+91-98765-43210"],
    )
    course: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Enrolled program or course name",
        examples=["Computer Science & Engineering"],
    )
    address: Optional[str] = Field(
        default=None,
        description="Residential address",
        examples=["Flat 402, Shanti Niketan Apts, Powai, Mumbai, Maharashtra - 400076"],
    )
    enrollment_date: Optional[date] = Field(
        default_factory=date.today,
        description="Date of enrollment; defaults to today if not provided",
        examples=["2024-08-01"],
    )


class StudentCreate(StudentBase):
    """Schema used when creating a new student record."""
    pass


class StudentUpdate(BaseModel):
    """Schema used when updating student record attributes (supports partial/full updates)."""
    student_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Unique student identifier",
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Full name of the student",
    )
    dob: Optional[date] = Field(
        default=None,
        description="Date of birth in YYYY-MM-DD format",
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Unique, valid student email address",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Contact phone number",
    )
    course: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Enrolled program or course name",
    )
    address: Optional[str] = Field(
        default=None,
        description="Residential address",
    )
    enrollment_date: Optional[date] = Field(
        default=None,
        description="Date of enrollment",
    )


class StudentResponse(StudentBase):
    """Response schema returned to clients representing a student entity."""
    id: int = Field(..., description="Internal auto-increment primary key")

    model_config = ConfigDict(from_attributes=True)


class AskAIRequest(BaseModel):
    """Request payload for the natural language Ask-AI endpoint."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language question about student records",
        examples=["Computer Science me kitne students enrolled hain?"],
    )
    model: Optional[str] = Field(
        default=None,
        description="Optional Ollama model name (defaults to llama3.2:1b)",
        examples=["llama3.2:1b"],
    )


class AskAIResponse(BaseModel):
    """Response payload for the Ask-AI endpoint."""
    question: str
    answer: str
    model: str
    total_students_in_db: int
    records_analyzed: int
