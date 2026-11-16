import logging

from django.db import transaction
from django.utils import timezone

from cv_agent.parser import parse_cv

from .models import Application, Candidate, StageLog

logger = logging.getLogger(__name__)

# Campos que el agente puede completar, sin pisar lo que ya cargó alguien.
FILL_FIELDS = [
    "first_name", "last_name", "phone", "location", "linkedin", "current_title",
    "years_experience", "skills", "education", "summary",
]


def enrich_from_cv(candidate):
    """Lee el CV guardado con el agente local y completa los campos vacíos."""
    if not candidate.cv_file:
        return False
    try:
        data = parse_cv(candidate.cv_file.path)
    except Exception:
        logger.exception("No se pudo leer el CV del candidato %s", candidate.pk)
        return False

    for field in FILL_FIELDS:
        value = data.get(field)
        if value and not getattr(candidate, field):
            setattr(candidate, field, value)
    candidate.cv_text = data.get("cv_text", "")
    candidate.save()
    return True


def save_portal_candidate(data):
    """Guarda una postulación del portal público."""
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
                candidate=candidate, position=position,
            )
            if created:
                StageLog.objects.create(
                    application=application, from_stage="",
                    to_stage=Application.Stage.NEW, comment="Postulación desde portal",
                )

    enrich_from_cv(candidate)
    return candidate
