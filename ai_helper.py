import os
import json
from datetime import date
from typing import List, Dict, Any, Optional
import httpx
from fastapi import HTTPException, status

# Configuration defaults, overridable via environment variables
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "45.0"))


async def check_ollama_available(base_url: str = OLLAMA_BASE_URL) -> bool:
    """
    Check if the local Ollama daemon is reachable.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


def build_grounded_prompt(question: str, students: List[Dict[str, Any]], total_count: int) -> str:
    """
    Construct a secure prompt containing sanitized student records as grounded context.
    No dynamic SQL or arbitrary commands are passed or generated.
    """
    context_data = {
        "total_students_in_database": total_count,
        "students": students,
    }

    prompt = f"""You are a helpful, accurate AI assistant for a University Student Management System in India.
Answer the user's question directly and concisely using the verified student database records provided below.

INSTRUCTIONS:
1. Base your answer strictly on the student records in the JSON below. Search fields including name, course, phone (+91), email, address, and date of birth.
2. Be direct, clear, and factual.
3. If asked in Hindi or Hinglish, respond clearly.

STUDENT DATABASE RECORDS:
```json
{json.dumps(context_data, indent=2)}
```

USER QUESTION:
{question}

ANSWER:"""
    return prompt


async def ask_student_ai(
    question: str,
    students: List[Dict[str, Any]],
    total_count: int,
    model: Optional[str] = None,
    base_url: str = OLLAMA_BASE_URL,
) -> str:
    """
    Sends the grounded question to Ollama's /api/generate endpoint.
    Handles network errors, model missing, and timeouts gracefully.
    """
    chosen_model = model or OLLAMA_MODEL
    prompt = build_grounded_prompt(question, students, total_count)

    payload = {
        "model": chosen_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json=payload,
            )

            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        f"Ollama model '{chosen_model}' was not found. "
                        f"Please run 'ollama pull {chosen_model}' in your terminal."
                    ),
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Ollama server returned error: {response.status_code} - {response.text}",
                )

            data = response.json()
            return data.get("response", "").strip()

    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Could not connect to Ollama. Please ensure Ollama is installed and running "
                f"locally at '{base_url}' (e.g., run 'ollama serve'). The core CRUD endpoints "
                "remain fully operational."
            ),
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Ollama generation timed out after {OLLAMA_TIMEOUT}s. Please retry or test with a smaller dataset.",
        )
