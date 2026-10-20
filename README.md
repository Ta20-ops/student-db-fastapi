# 🎓 EduTrack — Student Database Management API & AI Dashboard

A modern, production-grade **Full-Stack Student Management Portal** powered by **FastAPI**, **SQLite (SQLAlchemy ORM)**, **Pydantic v2**, a **sleek Glassmorphism Web Dashboard**, and an **integrated Ollama AI Assistant (`llama3.2:1b`)**.

---

## 📋 Table of Contents
- [✨ Key Features](#-key-features)
- [🖥️ Interactive Web Dashboard](#️-interactive-web-dashboard)
- [📂 Project Architecture](#-project-architecture)
- [🚀 Quickstart](#-quickstart)
- [🤖 Ollama AI Natural Language Assistant](#-ollama-ai-natural-language-assistant)
- [📡 API Reference & cURL Samples](#-api-reference--curl-samples)
- [🧪 Automated Test Suite](#-automated-test-suite)

---

## ✨ Key Features

- **🎨 Modern Dark Web Dashboard**: Ultra-premium UI built with Vanilla HTML5/CSS3/JavaScript featuring glassmorphism, responsive metrics, search debounce, course filters, view toggle (table vs grid), and interactive modals.
- **⚡ Full RESTful CRUD**: Create, Read, Update (`PUT`/`PATCH`), and Delete (`DELETE`) student records with strict status codes (`200`, `201`, `204`, `400`, `404`, `422`).
- **🛡️ Strong Data Validation**: Pydantic v2 schemas validating RFC-compliant email addresses, dates (`YYYY-MM-DD`), and unique ID constraints.
- **🤖 Grounded Ollama AI Assistant**: Integrated `llama3.2:1b` model answering natural language queries safely using structured ORM database context—**zero raw SQL injection risks**.
- **🔍 Fast Search & Filtering**: Case-insensitive search on student names and filtering on academic courses with offset pagination.
- **🧪 100% Automated Test Coverage**: 14/14 Pytest tests running on an isolated in-memory SQLite database.

---

## 🖥️ Interactive Web Dashboard

When the backend runs, navigate to **`http://localhost:8000/`** or **`http://127.0.0.1:8000/`** to access the dashboard.

### Dashboard Highlights:
1. **Analytics Header**: Real-time counter of total enrolled students, distinct courses, recent admissions, and live Ollama connectivity status.
2. **Search & Filters**: Type to instantly filter students by name, select specific courses, or switch between standard **Table View** and **Card Grid View**.
3. **Student Profile Modal**: Add new students or edit existing records. Duplicate `student_id` or `email` errors from the API are clearly displayed in real-time.
4. **Delete Safety Modal**: Requires confirmation before sending `DELETE` requests.
5. **AI Assistant Drawer**: Slide-over chat interface with suggested quick prompts (e.g. *"Total enrolled students"*, *"CS students count"*, *"Born after 2004"*).

---

## 📂 Project Architecture

```text
student-db-fastapi/
├── main.py              # FastAPI app, route handlers, static file mounting & CORS
├── database.py          # SQLAlchemy SQLite engine & get_db dependency
├── models.py            # SQLAlchemy Student ORM model definition
├── schemas.py           # Pydantic v2 schemas for request validation & responses
├── crud.py              # Business logic & ORM database operations
├── ai_helper.py         # Modular Ollama LLM integration & prompt grounding
├── seed.py              # Seeding script with realistic student profiles
├── test_main.py         # 14 Pytest integration & unit tests
├── requirements.txt     # Pinned Python package dependencies
├── .env.example         # Environment template
├── static/
│   ├── index.html       # Semantic HTML5 dashboard layout
│   ├── style.css        # Vanilla CSS design system (glassmorphism & dark theme)
│   └── app.js           # Vanilla JavaScript SPA logic & API connector
└── README.md            # Comprehensive project documentation
```

---

## 🚀 Quickstart

### 1. Activate Environment
```bash
cd /Users/krish/.gemini/antigravity-ide/scratch/student-db-fastapi
source .venv/bin/activate
```

### 2. Start the Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open in Browser
- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🤖 Ollama AI Natural Language Assistant

Ollama is running locally in the background with the lightweight **`llama3.2:1b`** model installed.

### How it Works:
1. Natural language questions are sent to `POST /ask-ai`.
2. The server queries SQLite using SQLAlchemy (no raw SQL from the user or LLM).
3. The records are serialized into a clean JSON context and passed with strict grounding rules to `llama3.2:1b`.
4. The AI returns a concise, factual answer based strictly on verified database records.

### Sample AI cURL:
```bash
curl -X POST "http://localhost:8000/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many students are enrolled in Computer Science?"}'
```

**Response:**
```json
{
  "question": "How many students are enrolled in Computer Science?",
  "answer": "Based on the provided JSON data, there are 3 students enrolled in Computer Science:\n\n1. Alice Johnson (STU-2024-001)\n2. Brian Smith (STU-2024-002)\n3. Catherine Lee (STU-2024-003)",
  "model": "llama3.2:1b",
  "total_students_in_db": 5,
  "records_analyzed": 5
}
```

---

## 📡 API Reference & cURL Samples

### 1. Create a Student
```bash
curl -X POST "http://localhost:8000/students" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU-2024-006",
    "name": "Jordan Hayes",
    "dob": "2003-04-18",
    "email": "jordan.hayes@university.edu",
    "phone": "+1-555-0188",
    "course": "Robotics Engineering",
    "enrollment_date": "2024-09-01"
  }'
```

### 2. List Students (with Filtering)
```bash
# Filter by course substring (e.g. computer)
curl -X GET "http://localhost:8000/students?course=computer"

# Search by student name
curl -X GET "http://localhost:8000/students?name=alice"
```

### 3. Fetch Single Student
```bash
curl -X GET "http://localhost:8000/students/STU-2024-001"
```

### 4. Update Student Record
```bash
curl -X PATCH "http://localhost:8000/students/STU-2024-001" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1-555-9999", "course": "Advanced Robotics"}'
```

### 5. Delete Student Record
```bash
curl -X DELETE "http://localhost:8000/students/STU-2024-006"
```

---

## 🧪 Automated Test Suite

Run all tests in isolation:
```bash
pytest -v
```

Expected output:
```text
test_main.py::test_root_endpoint PASSED
test_main.py::test_create_student_success PASSED
test_main.py::test_create_duplicate_student_id PASSED
test_main.py::test_create_duplicate_email PASSED
test_main.py::test_create_invalid_email_format PASSED
test_main.py::test_get_student_by_id_and_identifier PASSED
test_main.py::test_get_student_not_found PASSED
test_main.py::test_list_students_and_filtering PASSED
test_main.py::test_update_student_put_and_patch PASSED
test_main.py::test_update_student_conflict PASSED
test_main.py::test_delete_student PASSED
test_main.py::test_delete_student_not_found PASSED
test_main.py::test_ask_ai_status PASSED
test_main.py::test_ask_ai_handles_offline_gracefully PASSED

======================== 14 passed in 2.79s =========================
```
