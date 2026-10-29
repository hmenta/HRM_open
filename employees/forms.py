from django import forms
from django.forms import inlineformset_factory, TextInput, ClearableFileInput
from .models import Employee, EmployeeDocument

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        # Se removió 'document' de la lista de campos ya que ahora se gestiona de forma relacional[cite: 2]
        fields = [
            'employee_leg', 'dni', 'cuil', 'first_name', 'last_name', 
            'email', 'phone', 'street', 'street_number', 'floor', 
            'apartment', 'postal_code', 'city', 'state', 'position', 
            'department_rel', 'hire_date', 'is_active', 
            'termination_date', 'termination_reason_rel', 'photo'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'termination_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'street_number': forms.TextInput(attrs={'class': 'form-control'}),
            'floor': forms.TextInput(attrs={'class': 'form-control'}),
            'apartment': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_leg': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'cuil': forms.TextInput(attrs={'class': 'form-control'}),
            'department_rel': forms.Select(attrs={'class': 'form-select'}),
            'termination_reason_rel': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            # Se eliminó el widget del campo 'document' individual.
        }


# =========================================================================
# FORMSET PARA GESTIONAR MÚLTIPLES DOCUMENTOS ADJUNTOS EN LA MISMA VISTA
# =========================================================================
EmployeeDocumentFormSet = inlineformset_factory(
    Employee,
    EmployeeDocument,
    fields=['title', 'document'],
    extra=1,          # Muestra por defecto una línea vacía para adjuntar un nuevo documento
    can_delete=True,   # Habilita la opción de tildar para eliminar documentos existentes
    widgets={
        'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: DNI, Título Secundario, Examen Médico'}),
        'document': ClearableFileInput(attrs={'class': 'form-control'}),
    }
)