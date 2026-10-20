import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import crud
import schemas

# Setup isolated in-memory SQLite engine for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Create fresh tables for every test and tear down afterwards."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Student Database Management API" in data["service"]


def test_create_student_success():
    payload = {
        "student_id": "TEST-001",
        "name": "Jane Doe",
        "dob": "2004-05-15",
        "email": "jane.doe@example.com",
        "phone": "+1-555-1234",
        "course": "Computer Science",
        "address": "123 Campus Dr",
        "enrollment_date": "2024-09-01",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == "TEST-001"
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@example.com"
    assert "id" in data


def test_create_duplicate_student_id():
    payload1 = {
        "student_id": "TEST-DUP-ID",
        "name": "Student One",
        "dob": "2003-01-01",
        "email": "stu1@example.com",
    }
    client.post("/students", json=payload1)

    # Attempt to create another student with the same student_id
    payload2 = {
        "student_id": "TEST-DUP-ID",
        "name": "Student Two",
        "dob": "2003-02-02",
        "email": "stu2@example.com",
    }
    response = client.post("/students", json=payload2)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_duplicate_email():
    payload1 = {
        "student_id": "STU-E1",
        "name": "Student E1",
        "dob": "2003-01-01",
        "email": "duplicate@example.com",
    }
    client.post("/students", json=payload1)

    # Attempt to create another student with the same email
    payload2 = {
        "student_id": "STU-E2",
        "name": "Student E2",
        "dob": "2003-02-02",
        "email": "duplicate@example.com",
    }
    response = client.post("/students", json=payload2)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_invalid_email_format():
    payload = {
        "student_id": "INVALID-EMAIL",
        "name": "Bad Email",
        "dob": "2003-01-01",
        "email": "not-an-email",
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_get_student_by_id_and_identifier():
    create_resp = client.post(
        "/students",
        json={
            "student_id": "STU-FIND-01",
            "name": "Find Me",
            "dob": "2004-10-10",
            "email": "findme@example.com",
        },
    )
    assert create_resp.status_code == 201
    db_id = create_resp.json()["id"]

    # Search by string student_id
    resp1 = client.get("/students/STU-FIND-01")
    assert resp1.status_code == 200
    assert resp1.json()["name"] == "Find Me"

    # Search by integer primary key
    resp2 = client.get(f"/students/{db_id}")
    assert resp2.status_code == 200
    assert resp2.json()["student_id"] == "STU-FIND-01"


def test_get_student_not_found():
    response = client.get("/students/NONEXISTENT-ID")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_students_and_filtering():
    # Insert 3 students
    students = [
        {"student_id": "S1", "name": "Alan Turing", "dob": "2002-01-01", "email": "alan@math.org", "course": "Computer Science"},
        {"student_id": "S2", "name": "Ada Lovelace", "dob": "2003-02-02", "email": "ada@math.org", "course": "Computer Science"},
        {"student_id": "S3", "name": "Marie Curie", "dob": "2001-03-03", "email": "marie@chem.org", "course": "Chemistry"},
    ]
    for s in students:
        client.post("/students", json=s)

    # List all
    all_resp = client.get("/students")
    assert all_resp.status_code == 200
    assert len(all_resp.json()) == 3

    # Filter by course: 'computer'
    course_resp = client.get("/students?course=computer")
    assert course_resp.status_code == 200
    results = course_resp.json()
    assert len(results) == 2
    assert all(r["course"] == "Computer Science" for r in results)

    # Search by name: 'Ada'
    name_resp = client.get("/students?name=ada")
    assert name_resp.status_code == 200
    name_results = name_resp.json()
    assert len(name_results) == 1
    assert name_results[0]["name"] == "Ada Lovelace"


def test_update_student_put_and_patch():
    client.post(
        "/students",
        json={
            "student_id": "UP-001",
            "name": "Original Name",
            "dob": "2004-01-01",
            "email": "orig@example.com",
            "course": "Physics",
        },
    )

    # Partial update via PATCH
    patch_resp = client.patch(
        "/students/UP-001",
        json={"name": "Updated Name", "course": "Astrophysics"},
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["name"] == "Updated Name"
    assert patched_data["course"] == "Astrophysics"
    assert patched_data["email"] == "orig@example.com"  # unchanged

    # Full update via PUT
    put_resp = client.put(
        "/students/UP-001",
        json={"phone": "+1-999-888-7777"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["phone"] == "+1-999-888-7777"


def test_update_student_conflict():
    client.post(
        "/students",
        json={"student_id": "STU-A", "name": "Student A", "dob": "2004-01-01", "email": "a@example.com"},
    )
    client.post(
        "/students",
        json={"student_id": "STU-B", "name": "Student B", "dob": "2004-01-01", "email": "b@example.com"},
    )

    # Try updating STU-A's email to STU-B's email
    conflict_resp = client.put("/students/STU-A", json={"email": "b@example.com"})
    assert conflict_resp.status_code == 400
    assert "already exists" in conflict_resp.json()["detail"]


def test_delete_student():
    client.post(
        "/students",
        json={"student_id": "DEL-01", "name": "To Delete", "dob": "2004-01-01", "email": "del@example.com"},
    )

    # Delete the student
    del_resp = client.delete("/students/DEL-01")
    assert del_resp.status_code == 204

    # Verify student is gone
    get_resp = client.get("/students/DEL-01")
    assert get_resp.status_code == 404


def test_delete_student_not_found():
    del_resp = client.delete("/students/DOESNT_EXIST")
    assert del_resp.status_code == 404


def test_ask_ai_status():
    resp = client.get("/ask-ai/status")
    assert resp.status_code == 200
    assert "ollama_available" in resp.json()
    assert resp.json()["default_model"] == "llama3.2:1b"


def test_ask_ai_handles_offline_gracefully():
    # Calling /ask-ai when Ollama is offline or unconfigured should return 503 instead of 500 crash
    resp = client.post(
        "/ask-ai",
        json={"question": "How many students are enrolled?"},
    )
    # If Ollama is not running, we expect 503 Service Unavailable; if running, 200 OK
    assert resp.status_code in [200, 503]
