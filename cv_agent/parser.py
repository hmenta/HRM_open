import json
import os
import re
from typing import Any
from urllib.parse import urlparse

import pdfplumber
import requests
from django.conf import settings
from docx import Document
from pypdf import PdfReader

# Límite de caracteres enviados al LLM local para mantener tiempos de respuesta razonables
MAX_CV_CHARS = 12000

# Estructura base alineada con los campos de Candidate en recruitment/models.py
EMPTY_PARSED_CV: dict[str, Any] = {
    "first_name": "",
    "last_name": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "current_title": "",
    "years_experience": None,
    "skills": "",
    "education": "",
    "summary": "",
    "cv_text": "",
}


def _get_ollama_config() -> tuple[str, str, int]:
    """Obtiene la configuración de Ollama desde Django settings o variables de entorno."""
    url = getattr(
        settings,
        "OLLAMA_BASE_URL",
        os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/generate"),
    )
    model = getattr(
        settings,
        "OLLAMA_CV_MODEL",
        os.getenv("OLLAMA_CV_MODEL", "qwen2.5:7b"),
    )
    timeout = int(
        getattr(
            settings,
            "OLLAMA_TIMEOUT_SECONDS",
            os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"),
        )
    )
    return url, model, timeout


def _extract_pdf_text(file_path: str) -> str:
    """Extrae texto de un PDF con pypdf y usa pdfplumber como respaldo si el texto es escaso."""
    chunks: list[str] = []

    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                chunks.append(txt.strip())
    except Exception:
        chunks = []

    combined = "\n\n".join(chunks).strip()

    # Si pypdf devuelve muy poco texto, probamos pdfplumber (útil en columnas o tablas)
    if len(combined) < 80:
        plumber_chunks: list[str] = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text() or ""
                    if txt.strip():
                        plumber_chunks.append(txt.strip())
            if plumber_chunks:
                combined = "\n\n".join(plumber_chunks).strip()
        except Exception:
            pass

    return combined


def _extract_docx_text(file_path: str) -> str:
    """Extrae párrafos y filas de tablas de un archivo .docx."""
    doc = Document(file_path)
    parts: list[str] = []

    for paragraph in doc.paragraphs:
        if paragraph.text and paragraph.text.strip():
            parts.append(paragraph.text.strip())

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text and cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    return "\n".join(parts).strip()


def extract_text_from_cv(file_path: str) -> str:
    """Extrae y normaliza el texto plano de un archivo PDF o DOCX."""
    if not file_path or not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        raw_text = _extract_pdf_text(file_path)
    elif ext == ".docx":
        raw_text = _extract_docx_text(file_path)
    else:
        return ""

    # Normalizamos espacios horizontales y limitamos saltos de línea consecutivos
    raw_text = re.sub(r"[ \t]+", " ", raw_text)
    raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)
    return raw_text.strip()


def _normalize_linkedin(value: Any) -> str:
    """Devuelve una URL válida de LinkedIn o cadena vacía si no corresponde."""
    if not isinstance(value, str):
        return ""
    cleaned = value.strip()
    if not cleaned:
        return ""
    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"
    parsed = urlparse(cleaned)
    if parsed.scheme in ("http", "https") and "linkedin.com" in parsed.netloc.lower():
        return cleaned[:200]
    return ""


def _normalize_years(value: Any) -> int | None:
    """Convierte años de experiencia a entero válido (0..60) o None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= 60 else None
    if isinstance(value, float):
        rounded = round(value)
        return rounded if 0 <= rounded <= 60 else None
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            years = int(match.group())
            return years if 0 <= years <= 60 else None
    return None


def _clean_str(value: Any, max_len: int | None = None) -> str:
    """Limpia valores textuales y descarta marcadores genéricos de dato faltante."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in ("null", "none", "n/a", "no especificado", "sin dato"):
        return ""
    return text[:max_len] if max_len else text


def _call_ollama_json(cv_text: str) -> dict[str, Any]:
    """Envía el texto del CV a Ollama y exige respuesta en formato JSON."""
    url, model, timeout = _get_ollama_config()

    prompt = f"""Eres un asistente de Recursos Humanos especializado en extraer datos estructurados de CVs.
Lee el texto del CV y devuelve ÚNICAMENTE un objeto JSON válido con estas claves exactas:
- "first_name": string (nombre)
- "last_name": string (apellido)
- "phone": string (teléfono)
- "location": string (ciudad, provincia/región o país)
- "linkedin": string (URL de LinkedIn)
- "current_title": string (puesto actual o más reciente)
- "years_experience": integer o null (años totales aproximados de experiencia laboral)
- "skills": string (habilidades principales)
- "education": string (formación académica y cursos relevantes)
- "summary": string (resumen breve del perfil en 2-3 líneas, en el idioma del CV)

Reglas:
1. No inventes información que no figure en el CV. Si falta un dato, usa "" (o null en years_experience).
2. Responde solo con JSON válido, sin explicaciones extra ni bloques markdown.

Texto del CV:
\"\"\"
{cv_text[:MAX_CV_CHARS]}
\"\"\"
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,
        },
    }

    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    body = response.json()
    return json.loads(body.get("response", "{}"))


def parse_cv(file_path: str) -> dict[str, Any]:
    """
    Extrae texto de un CV (PDF/DOCX) y lo estructura con el LLM local de Ollama.
    Si Ollama no responde o falla, conserva al menos `cv_text` para no perder la búsqueda textual.
    """
    result = dict(EMPTY_PARSED_CV)
    cv_text = extract_text_from_cv(file_path)
    result["cv_text"] = cv_text

    if not cv_text:
        return result

    try:
        raw_data = _call_ollama_json(cv_text)
    except Exception:
        return result

    result["first_name"] = _clean_str(raw_data.get("first_name"), max_len=100)
    result["last_name"] = _clean_str(raw_data.get("last_name"), max_len=100)
    result["phone"] = _clean_str(raw_data.get("phone"), max_len=40)
    result["location"] = _clean_str(raw_data.get("location"), max_len=150)
    result["linkedin"] = _normalize_linkedin(raw_data.get("linkedin"))
    result["current_title"] = _clean_str(raw_data.get("current_title"), max_len=150)
    result["years_experience"] = _normalize_years(raw_data.get("years_experience"))
    result["skills"] = _clean_str(raw_data.get("skills"))
    result["education"] = _clean_str(raw_data.get("education"))
    result["summary"] = _clean_str(raw_data.get("summary"))

    return result