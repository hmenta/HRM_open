from django.conf import settings
from django.db import models


class Position(models.Model):
    """Búsqueda laboral."""

    class Status(models.TextChoices):
        OPEN = "abierta", "Abierta"
        PAUSED = "pausada", "Pausada"
        CLOSED = "cerrada", "Cerrada"

    title = models.CharField("Título", max_length=150)
    client = models.CharField("Cliente / Área", max_length=150, blank=True)
    description = models.TextField("Descripción", blank=True)
    requirements = models.TextField("Requisitos", blank=True)
    status = models.CharField("Estado", max_length=10, choices=Status.choices, default=Status.OPEN)
    start_date = models.DateField("Fecha de inicio", null=True, blank=True)
    closing_date = models.DateField("Fecha de cierre", null=True, blank=True)
    vacancies = models.PositiveSmallIntegerField("Vacantes", default=1)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Responsable", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="positions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "búsqueda"

    def __str__(self):
        return self.title


class Candidate(models.Model):
    """Postulante (perfil único por email)."""

    class Source(models.TextChoices):
        MANUAL = "manual", "Carga manual"
        PORTAL = "portal", "Portal de candidatos"

    first_name = models.CharField("Nombre", max_length=100)
    last_name = models.CharField("Apellido", max_length=100)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Teléfono", max_length=40, blank=True)
    location = models.CharField("Ubicación", max_length=150, blank=True)
    linkedin = models.URLField("LinkedIn", blank=True)
    current_title = models.CharField("Puesto actual", max_length=150, blank=True)
    years_experience = models.PositiveSmallIntegerField("Años de experiencia", null=True, blank=True)
    skills = models.TextField("Habilidades", blank=True)
    education = models.TextField("Formación", blank=True)
    summary = models.TextField("Resumen profesional", blank=True)
    cv_file = models.FileField("CV", upload_to="cvs/%Y/%m/", blank=True)
    cv_text = models.TextField("Texto del CV (para búsquedas)", blank=True)
    source = models.CharField("Origen", max_length=10, choices=Source.choices, default=Source.MANUAL)
    consent_given = models.BooleanField("Consentimiento de datos", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "postulante"

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class Application(models.Model):
    """Postulación de un candidato a una búsqueda, con etapa dentro del flujo."""

    class Stage(models.TextChoices):
        NEW = "nuevo", "Nuevo"
        REVIEW = "en_revision", "En revisión"
        INTERVIEW_1 = "entrevista_1", "1° Entrevista"
        INTERVIEW_2 = "entrevista_2", "2° Entrevista"
        PSICO = "psico", "Psicotécnico"
        MEDICAL = "medico", "En Médico"
        OFFER = "oferta", "Oferta"
        HIRED = "contratado", "Contratado"
        NO_APLICA = "no_aplica", "No Aplica"
        BAJA = "baja", "Baja"

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="applications")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="applications")
    stage = models.CharField("Etapa", max_length=20, choices=Stage.choices, default=Stage.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["candidate", "position"], name="uniq_candidate_position"),
        ]

    def __str__(self):
        return f"{self.candidate} → {self.position}"


class StageLog(models.Model):
    """Historial de cambios de etapa (auditoría del flujo)."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="logs")
    from_stage = models.CharField(max_length=20, blank=True)
    to_stage = models.CharField(max_length=20, choices=Application.Stage.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    comment = models.CharField("Comentario", max_length=300, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]
