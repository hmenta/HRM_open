from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .roles import ALL_ROLES, ROLE_LABELS, get_user_role

User = get_user_model()


def _role_field():
    return forms.ChoiceField(
        label='Rol',
        choices=[('', '— Seleccionar rol —')] + [(r, ROLE_LABELS[r]) for r in ALL_ROLES],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
    )


class ManagedUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nombre', max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='Apellido', max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='Email', required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    role = _role_field()

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class ManagedUserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Nombre', max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='Apellido', max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='Email', required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    role = _role_field()
    is_active = forms.BooleanField(
        label='Usuario activo', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    new_password = forms.CharField(
        label='Nueva contraseña', required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text='Dejar en blanco para no cambiarla.',
    )
    new_password_confirm = forms.CharField(
        label='Confirmar contraseña', required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        if self.instance and self.instance.pk:
            current = get_user_role(self.instance)
            if current:
                self.fields['role'].initial = current

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password')
        p2 = cleaned.get('new_password_confirm')
        if p1 or p2:
            if p1 != p2:
                self.add_error('new_password_confirm', 'Las contraseñas no coinciden.')
            elif len(p1) < 8:
                self.add_error('new_password', 'La contraseña debe tener al menos 8 caracteres.')
        return cleaned
