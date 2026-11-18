"""Envío de notificaciones según reglas configuradas."""

import logging
from email.utils import formataddr

from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import Context, Template
from django.utils import timezone

from accounts.roles import ROLE_ADMIN, ROLE_OPERATOR

from .models import EmailSettings, NotificationEvent, NotificationRule

logger = logging.getLogger(__name__)
User = get_user_model()


DEFAULT_RULES = [
    {
        'event': NotificationEvent.CERTIFICATE_UPLOADED,
        'subject_template': 'Nuevo certificado de ausencia — {{ employee }}',
        'body_template': (
            '<p>Se cargó un certificado de ausencia.</p>'
            '<p><strong>Colaborador:</strong> {{ employee }}<br>'
            '<strong>Motivo:</strong> {{ reason }}<br>'
            '<strong>Período:</strong> {{ start_date }} al {{ end_date }}</p>'
        ),
        'notify_admins': True,
        'notify_operators': True,
        'notify_employee': False,
    },
    {
        'event': NotificationEvent.PAYSLIP_AVAILABLE,
        'subject_template': 'Tenés un nuevo recibo de sueldo — {{ period }}',
        'body_template': (
            '<p>Hay un nuevo recibo de sueldo disponible.</p>'
            '<p><strong>Colaborador:</strong> {{ employee }}<br>'
            '<strong>Período:</strong> {{ period }}</p>'
            '<p>Ingresá al sistema para verlo o descargarlo.</p>'
        ),
        'notify_admins': False,
        'notify_operators': False,
        'notify_employee': True,
    },
    {
        'event': NotificationEvent.NEW_CV,
        'subject_template': 'Nuevo CV ingresado — {{ candidate }}',
        'body_template': (
            '<p>Se recibió una nueva postulación / CV.</p>'
            '<p><strong>Candidato:</strong> {{ candidate }}<br>'
            '<strong>Email:</strong> {{ email }}<br>'
            '<strong>Búsqueda:</strong> {{ position }}</p>'
        ),
        'notify_admins': True,
        'notify_operators': True,
        'notify_employee': False,
    },
]


def ensure_default_notification_rules():
    for data in DEFAULT_RULES:
        NotificationRule.objects.get_or_create(
            event=data['event'],
            defaults={
                'is_active': True,
                'subject_template': data['subject_template'],
                'body_template': data['body_template'],
                'notify_admins': data['notify_admins'],
                'notify_operators': data['notify_operators'],
                'notify_employee': data['notify_employee'],
            },
        )


def _render(template_str, context_dict):
    return Template(template_str or '').render(Context(context_dict))


def _emails_from_roles(*role_names):
    emails = set()
    for user in User.objects.filter(is_active=True, groups__name__in=role_names).distinct():
        if user.email:
            emails.add(user.email.strip().lower())
        if user.is_superuser and ROLE_ADMIN in role_names and user.email:
            emails.add(user.email.strip().lower())
    # Superusers always count as admins
    if ROLE_ADMIN in role_names:
        for user in User.objects.filter(is_active=True, is_superuser=True):
            if user.email:
                emails.add(user.email.strip().lower())
    return emails


def _parse_extra_emails(raw):
    if not raw:
        return set()
    parts = raw.replace(';', ',').split(',')
    return {p.strip().lower() for p in parts if p.strip() and '@' in p}


def resolve_recipients(rule, context_dict):
    emails = set()
    emails |= _parse_extra_emails(rule.recipient_emails)
    roles = []
    if rule.notify_admins:
        roles.append(ROLE_ADMIN)
    if rule.notify_operators:
        roles.append(ROLE_OPERATOR)
    if roles:
        emails |= _emails_from_roles(*roles)
    if rule.notify_employee:
        emp_email = (context_dict.get('employee_email') or '').strip().lower()
        if emp_email:
            emails.add(emp_email)
    return sorted(emails)


def send_notification(event, context_dict=None):
    """
    Dispara una notificación por evento.
    No interrumpe el flujo principal si falla el envío.
    """
    context_dict = dict(context_dict or {})
    try:
        ensure_default_notification_rules()
        rule = NotificationRule.objects.filter(event=event, is_active=True).first()
        if not rule:
            return False

        email_cfg = EmailSettings.load()
        if not email_cfg.host or not email_cfg.from_email:
            logger.warning('Notificación %s omitida: correo no configurado', event)
            return False

        context_dict.setdefault('company_name', email_cfg.from_name or 'HRM Open')
        context_dict.setdefault('year', timezone.now().year)

        subject = _render(rule.subject_template, context_dict)
        body_html = _render(rule.body_template, context_dict)
        wrapped = _render(
            email_cfg.html_template,
            {
                **context_dict,
                'subject': subject,
                'body': body_html,
            },
        )

        recipients = resolve_recipients(rule, context_dict)
        if not recipients:
            logger.info('Notificación %s sin destinatarios', event)
            return False

        connection = get_connection(
            host=email_cfg.host,
            port=email_cfg.port,
            username=email_cfg.username or None,
            password=email_cfg.password or None,
            use_tls=email_cfg.use_tls,
            use_ssl=email_cfg.use_ssl,
            fail_silently=False,
        )
        from_email = formataddr((email_cfg.from_name or 'HRM Open', email_cfg.from_email))
        msg = EmailMultiAlternatives(
            subject=subject,
            body='Este mensaje requiere un cliente con HTML.',
            from_email=from_email,
            to=recipients,
            connection=connection,
        )
        msg.attach_alternative(wrapped, 'text/html')
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Error enviando notificación %s', event)
        return False


def notify_certificate_uploaded(certificate):
    employee = certificate.employee
    return send_notification(
        NotificationEvent.CERTIFICATE_UPLOADED,
        {
            'employee': str(employee),
            'employee_email': getattr(employee, 'email', '') or '',
            'reason': certificate.reason,
            'start_date': certificate.start_date,
            'end_date': certificate.end_date,
        },
    )


def notify_payslip_available(payslip):
    employee = payslip.employee
    return send_notification(
        NotificationEvent.PAYSLIP_AVAILABLE,
        {
            'employee': str(employee),
            'employee_email': getattr(employee, 'email', '') or '',
            'period': payslip.period_label,
            'year': payslip.year,
            'month': payslip.month,
        },
    )


def notify_new_cv(candidate, position=None):
    return send_notification(
        NotificationEvent.NEW_CV,
        {
            'candidate': str(candidate),
            'email': candidate.email,
            'position': str(position) if position else 'Sin búsqueda asignada',
        },
    )
