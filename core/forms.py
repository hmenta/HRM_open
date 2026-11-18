from django import forms

from .models import ApiCredential, EmailSettings, NotificationRule


class EmailSettingsForm(forms.ModelForm):
    class Meta:
        model = EmailSettings
        fields = [
            'from_name', 'from_email', 'host', 'port', 'username', 'password',
            'use_tls', 'use_ssl', 'html_template',
        ]
        widgets = {
            'from_name': forms.TextInput(attrs={'class': 'form-control'}),
            'from_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'host': forms.TextInput(attrs={'class': 'form-control'}),
            'port': forms.NumberInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}, render_value=True),
            'use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'use_ssl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'html_template': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 16}),
        }


class ApiCredentialCreateForm(forms.Form):
    name = forms.CharField(
        label='Nombre del sistema / integración',
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Softland / Tango / Liquidación interna'}),
    )


class NotificationRuleForm(forms.ModelForm):
    class Meta:
        model = NotificationRule
        fields = [
            'is_active', 'subject_template', 'body_template', 'recipient_emails',
            'notify_admins', 'notify_operators', 'notify_employee',
        ]
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'subject_template': forms.TextInput(attrs={'class': 'form-control'}),
            'body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'recipient_emails': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'rrhh@empresa.com, gerencia@empresa.com',
            }),
            'notify_admins': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_operators': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
