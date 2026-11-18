import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class CompanySettings(models.Model):
    name = models.CharField(max_length=150, default="Demo S.A.")
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresa"


DEFAULT_EMAIL_HTML = """<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>{{ subject }}</title></head>
<body style="margin:0;padding:0;background:#f4f6f8;font-family:Segoe UI,Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f6f8;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb;">
        <tr>
          <td style="background:#212529;color:#ffffff;padding:20px 24px;font-size:18px;font-weight:600;">
            {{ company_name }}
          </td>
        </tr>
        <tr>
          <td style="padding:24px;">
            <h2 style="margin:0 0 12px;color:#111827;font-size:20px;">{{ subject }}</h2>
            <div style="color:#374151;font-size:15px;line-height:1.55;">{{ body }}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 24px;background:#f9fafb;color:#6b7280;font-size:12px;">
            Notificación automática de HRM Open · {{ year }}
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


class EmailSettings(models.Model):
    """Configuración SMTP y plantilla HTML para notificaciones (singleton)."""

    from_email = models.EmailField('Remitente (From)', blank=True)
    from_name = models.CharField('Nombre del remitente', max_length=120, blank=True, default='HRM Open')
    host = models.CharField('Servidor SMTP', max_length=255, blank=True, default='smtp.gmail.com')
    port = models.PositiveIntegerField('Puerto', default=587)
    username = models.CharField('Usuario SMTP', max_length=255, blank=True)
    password = models.CharField('Contraseña / App Password', max_length=255, blank=True)
    use_tls = models.BooleanField('Usar TLS', default=True)
    use_ssl = models.BooleanField('Usar SSL', default=False)
    html_template = models.TextField(
        'Plantilla HTML del correo',
        blank=True,
        default=DEFAULT_EMAIL_HTML,
        help_text='Variables: {{ company_name }}, {{ subject }}, {{ body }}, {{ year }}',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de correo'
        verbose_name_plural = 'Configuración de correo'

    def save(self, *args, **kwargs):
        self.pk = 1
        if not self.html_template.strip():
            self.html_template = DEFAULT_EMAIL_HTML
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Configuración de correo'


class ApiCredential(models.Model):
    """Credenciales para integración ERP / liquidación de sueldos."""

    name = models.CharField('Nombre / sistema', max_length=120)
    api_key = models.CharField('API Key', max_length=64, unique=True, editable=False)
    token_hash = models.CharField('Hash del token', max_length=128, editable=False)
    token_prefix = models.CharField('Prefijo del token', max_length=12, blank=True, editable=False)
    is_active = models.BooleanField('Activa', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_api_credentials',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Credencial API'
        verbose_name_plural = 'Credenciales API'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.api_key[:12]}…)'

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    @classmethod
    def generate(cls, name: str, created_by=None):
        api_key = f'hrm_{secrets.token_urlsafe(18)}'
        raw_token = secrets.token_urlsafe(32)
        obj = cls(
            name=name,
            api_key=api_key,
            token_hash=cls.hash_token(raw_token),
            token_prefix=raw_token[:8],
            created_by=created_by,
        )
        obj.save()
        return obj, raw_token

    def verify_token(self, raw_token: str) -> bool:
        return secrets.compare_digest(self.token_hash, self.hash_token(raw_token or ''))

    def mark_used(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class NotificationEvent(models.TextChoices):
    CERTIFICATE_UPLOADED = 'certificate_uploaded', 'Colaborador cargó un certificado'
    PAYSLIP_AVAILABLE = 'payslip_available', 'Nuevo recibo de sueldo'
    NEW_CV = 'new_cv', 'Nuevo CV / postulación ingresada'


class NotificationRule(models.Model):
    """Define a quién se notifica cada evento del sistema."""

    event = models.CharField(
        'Evento',
        max_length=64,
        choices=NotificationEvent.choices,
        unique=True,
    )
    is_active = models.BooleanField('Activa', default=True)
    subject_template = models.CharField(
        'Asunto',
        max_length=200,
        help_text='Podés usar variables según el evento, ej: {{ employee }}, {{ period }}',
    )
    body_template = models.TextField(
        'Cuerpo del mensaje',
        help_text='Texto/HTML corto que se inserta en la plantilla general como {{ body }}',
    )
    recipient_emails = models.TextField(
        'Emails adicionales',
        blank=True,
        help_text='Separados por coma. Ej: rrhh@empresa.com, gerencia@empresa.com',
    )
    notify_admins = models.BooleanField('Notificar a Administradores', default=True)
    notify_operators = models.BooleanField('Notificar a Operadores', default=False)
    notify_employee = models.BooleanField(
        'Notificar al colaborador involucrado',
        default=False,
        help_text='Útil para avisarle que tiene un nuevo recibo.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Regla de notificación'
        verbose_name_plural = 'Reglas de notificación'
        ordering = ['event']

    def __str__(self):
        return self.get_event_display()
