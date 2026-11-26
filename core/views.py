from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import capability_required
from accounts.roles import can_manage_settings, can_manage_absences

from .forms import ApiCredentialCreateForm, EmailSettingsForm, NotificationRuleForm
from .models import ApiCredential, EmailSettings, NotificationRule
from .notifications import ensure_default_notification_rules
from .models import NotificationEvent

### ------- ATENCION: Algunas vistas se encuentran en views.py del módulo employees ----------- ###

@capability_required(can_manage_settings)
def settings_hub_view(request):
    ensure_default_notification_rules()
    return render(request, 'settings/hub.html', {
        'email_settings': EmailSettings.load(),
        'api_credentials': ApiCredential.objects.all()[:20],
        'notification_rules': NotificationRule.objects.all(),
    })


@capability_required(can_manage_settings)
def settings_email_view(request):
    cfg = EmailSettings.load()
    if request.method == 'POST':
        form = EmailSettingsForm(request.POST, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración de correo guardada.')
            return redirect('settings_email')
    else:
        form = EmailSettingsForm(instance=cfg)

    return render(request, 'settings/email.html', {'form': form})


@capability_required(can_manage_settings)
def settings_email_test_view(request):
    if request.method != 'POST':
        return redirect('settings_email')

    to_email = (request.POST.get('test_email') or request.user.email or '').strip()
    if not to_email:
        messages.error(request, 'Indicá un email de prueba.')
        return redirect('settings_email')

    # Reutiliza el motor de notificaciones con una regla temporal en memoria vía send directo
    from email.utils import formataddr
    from django.core.mail import EmailMultiAlternatives, get_connection
    from django.template import Context, Template
    from django.utils import timezone

    cfg = EmailSettings.load()
    if not cfg.host or not cfg.from_email:
        messages.error(request, 'Completá servidor SMTP y remitente antes de probar.')
        return redirect('settings_email')

    try:
        subject = 'Prueba de correo — HRM Open'
        body = '<p>Este es un correo de prueba de la configuración SMTP.</p>'
        html = Template(cfg.html_template).render(Context({
            'company_name': cfg.from_name or 'HRM Open',
            'subject': subject,
            'body': body,
            'year': timezone.now().year,
        }))
        connection = get_connection(
            host=cfg.host,
            port=cfg.port,
            username=cfg.username or None,
            password=cfg.password or None,
            use_tls=cfg.use_tls,
            use_ssl=cfg.use_ssl,
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body='Prueba HTML',
            from_email=formataddr((cfg.from_name or 'HRM Open', cfg.from_email)),
            to=[to_email],
            connection=connection,
        )
        msg.attach_alternative(html, 'text/html')
        msg.send(fail_silently=False)
        messages.success(request, f'Correo de prueba enviado a {to_email}.')
    except Exception as exc:
        messages.error(request, f'No se pudo enviar: {exc}')

    return redirect('settings_email')


@capability_required(can_manage_settings)
def settings_api_view(request):
    form = ApiCredentialCreateForm()
    new_secret = request.session.pop('new_api_secret', None)

    if request.method == 'POST':
        form = ApiCredentialCreateForm(request.POST)
        if form.is_valid():
            cred, raw_token = ApiCredential.generate(
                name=form.cleaned_data['name'],
                created_by=request.user,
            )
            request.session['new_api_secret'] = {
                'name': cred.name,
                'api_key': cred.api_key,
                'api_token': raw_token,
            }
            messages.success(request, 'Credencial creada. Guardá el token: solo se muestra una vez.')
            return redirect('settings_api')

    return render(request, 'settings/api.html', {
        'form': form,
        'credentials': ApiCredential.objects.all(),
        'new_secret': new_secret,
    })


@capability_required(can_manage_settings)
def settings_api_toggle_view(request, pk):
    if request.method != 'POST':
        return redirect('settings_api')
    cred = get_object_or_404(ApiCredential, pk=pk)
    cred.is_active = not cred.is_active
    cred.save(update_fields=['is_active'])
    messages.success(request, f'Credencial “{cred.name}” {"activada" if cred.is_active else "desactivada"}.')
    return redirect('settings_api')


@capability_required(can_manage_settings)
def settings_api_delete_view(request, pk):
    if request.method != 'POST':
        return redirect('settings_api')
    cred = get_object_or_404(ApiCredential, pk=pk)
    name = cred.name
    cred.delete()
    messages.success(request, f'Credencial “{name}” eliminada.')
    return redirect('settings_api')


@capability_required(can_manage_settings)
def settings_notifications_view(request):
    ensure_default_notification_rules()
    rules = list(NotificationRule.objects.all())
    forms = []

    if request.method == 'POST':
        rule_id = request.POST.get('rule_id')
        rule = get_object_or_404(NotificationRule, pk=rule_id)
        prefix = f'r{rule.pk}'
        form = NotificationRuleForm(request.POST, instance=rule, prefix=prefix)
        if form.is_valid():
            form.save()
            messages.success(request, f'Regla “{rule.get_event_display()}” actualizada.')
            return redirect('settings_notifications')
        for r in rules:
            if r.pk == rule.pk:
                forms.append((r, form))
            else:
                forms.append((r, NotificationRuleForm(instance=r, prefix=f'r{r.pk}')))
    else:
        for r in rules:
            forms.append((r, NotificationRuleForm(instance=r, prefix=f'r{r.pk}')))

    return render(request, 'settings/notifications.html', {
        'rule_forms': forms,
        'events_help': {
            NotificationEvent.CERTIFICATE_UPLOADED: 'Cuando un colaborador carga un certificado de ausencia.',
            NotificationEvent.PAYSLIP_AVAILABLE: 'Cuando se carga un recibo (web o API).',
            NotificationEvent.NEW_CV: 'Cuando ingresa un CV / postulación por el portal.',
        },
    })

