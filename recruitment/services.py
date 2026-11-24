import logging
import os
import tempfile

from django.db import transaction

from cv_agent.parser import parse_cv

from .models import Application, Candidate, StageLog

logger = logging.getLogger(__name__)

# Campos del perfil que el agente local puede completar desde el CV
FILL_FIELDS = [
    "first_name",
    "last_name",
    "phone",
    "location",
    "linkedin",
    "current_title",
    "years_experience",
    "skills",
    "education",
    "summary",
]


def _has_value(value) -> bool:
    """Considera válido cualquier valor distinto de None y de cadena vacía (incluye 0)."""
    return value is not None and value != ""


def _write_temp_cv_file(uploaded_file) -> str:
    """Guarda temporalmente un archivo subido en disco para analizarlo con parse_cv."""
    ext = os.path.splitext(uploaded_file.name or "")[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        return tmp.name


def extract_cv_data_from_upload(uploaded_file) -> dict:
    """Ejecuta el agente local sobre un archivo subido en memoria/request y limpia el temporal."""
    temp_path = ""
    try:
        temp_path = _write_temp_cv_file(uploaded_file)
        return parse_cv(temp_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                logger.warning("No se pudo eliminar archivo temporal de CV: %s", temp_path)


def merge_extracted_into_post_data(post_data, extracted: dict) -> tuple:
    """Completa campos vacíos del POST con lo extraído por IA sin pisar valores ingresados."""
    mutable_data = post_data.copy()
    filled_count = 0

    for field in FILL_FIELDS:
        current_val = (mutable_data.get(field) or "").strip()
        ai_val = extracted.get(field)
        if not current_val and _has_value(ai_val):
            mutable_data[field] = str(ai_val)
            filled_count += 1

    return mutable_data, filled_count


def enrich_from_cv(candidate: Candidate, overwrite: bool = False) -> bool:
    """
    Ejecuta el agente local sobre `candidate.cv_file`.
    - Con `overwrite=False`: completa solo los campos vacíos y actualiza `cv_text`.
    - Con `overwrite=True`: reemplaza los campos con valor extraído del CV.
    """
    if not candidate.cv_file or not candidate.cv_file.name:
        return False

    try:
        parsed = parse_cv(candidate.cv_file.path)
    except Exception:
        logger.exception("Error al parsear el CV del postulante pk=%s", candidate.pk)
        return False

    changed_fields: list[str] = []

    for field in FILL_FIELDS:
        extracted = parsed.get(field)
        current = getattr(candidate, field)

        if not _has_value(extracted):
            continue

        if overwrite or not _has_value(current):
            setattr(candidate, field, extracted)
            changed_fields.append(field)

    cv_text = parsed.get("cv_text", "")
    if cv_text:
        candidate.cv_text = cv_text
        changed_fields.append("cv_text")

    if changed_fields:
        unique_fields = list(dict.fromkeys(changed_fields))
        candidate.save(update_fields=unique_fields + ["updated_at"])
        logger.info(
            "Postulante pk=%s enriquecido desde CV. Campos: %s",
            candidate.pk,
            ", ".join(unique_fields),
        )
        return True

    return False


def save_portal_candidate(data: dict) -> Candidate:
    """Crea o actualiza un postulante desde el portal público y dispara el agente local."""
    email = data["email"].strip().lower()

    with transaction.atomic():
        candidate, _ = Candidate.objects.get_or_create(
            email=email,
            defaults={
                "first_name": data["first_name"].strip(),
                "last_name": data["last_name"].strip(),
                "source": Candidate.Source.PORTAL,
                "consent_given": True,
            },
        )
        candidate.cv_file = data["cv_file"]
        candidate.phone = candidate.phone or data.get("phone", "")
        candidate.consent_given = True
        candidate.save()

        position = data.get("position")
        if position:
            application, created = Application.objects.get_or_create(
                candidate=candidate,
                position=position,
            )
            if created:
                StageLog.objects.create(
                    application=application,
                    from_stage="",
                    to_stage=Application.Stage.NEW,
                    comment="Postulación desde portal",
                )

    # Ejecutamos el análisis fuera de la transacción para no retener bloqueos de BD
    enrich_from_cv(candidate, overwrite=False)

    try:
        from core.notifications import notify_new_cv

        notify_new_cv(candidate, position=data.get("position"))
    except Exception:
        logger.exception("No se pudo enviar la notificación de nuevo CV")

    return candidate
