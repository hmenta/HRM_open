from django import forms
from django.forms import inlineformset_factory, TextInput, ClearableFileInput
from .models import AbsenceCertificate, AbsenceCertificateDocument, Employee, EmployeeDocument 


# --- FORMULARIO Y FORMSET PARA EL LEGAJO DEL EMPLEADO ---

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_leg', 'dni', 'cuil', 'first_name', 'last_name', 
            'email', 'phone', 'street', 'street_number', 'floor', 
            'apartment', 'postal_code', 'city', 'state', 'is_active', 'hire_date',
            'area_rel', 'sector_rel', 'position', 'social_work_rel', 'agreement_rel',
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
            'area_rel': forms.Select(attrs={'class': 'form-select'}),
            'sector_rel': forms.Select(attrs={'class': 'form-select'}),
            'social_work_rel': forms.Select(attrs={'class': 'form-select'}),
            'agreement_rel': forms.Select(attrs={'class': 'form-select'}),
            'employee_leg': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'cuil': forms.TextInput(attrs={'class': 'form-control'}),
            'termination_reason_rel': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


EmployeeDocumentFormSet = inlineformset_factory(
    Employee,
    EmployeeDocument,
    fields=['title', 'document'],
    extra=1,
    can_delete=True,
    widgets={
        'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: DNI, Título Secundario, Examen Médico'}),
        'document': ClearableFileInput(attrs={'class': 'form-control'}),
    }
)


# --- FORMULARIO Y FORMSETS PARA LOS CERTIFICADOS DE AUSENCIA ---

class AbsenceCertificateForm(forms.ModelForm):
    class Meta:
        model = AbsenceCertificate
        fields = ['employee', 'reason', 'start_date', 'end_date', 'observations']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select select2'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles adicionales...'}),
        }


class AbsenceDocumentForm(forms.ModelForm):
    class Meta:
        model = AbsenceCertificateDocument
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        }


AbsenceDocumentFormSet = inlineformset_factory(
    AbsenceCertificate,
    AbsenceCertificateDocument,
    form=AbsenceDocumentForm,
    extra=1,
    can_delete=True
)


''' OLD CODE from django import forms
from django.forms import inlineformset_factory, TextInput, ClearableFileInput
from .models import AbsenceCertificate, AbsenceCertificateDocument, Employee, EmployeeDocument 


# --- FORMSET PARA GESTIONAR EL LEGAJO DEL EMPLEADO ---

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        # Se removió 'document' de la lista de campos ya que ahora se gestiona de forma relacional[cite: 2]
        fields = [
            'employee_leg', 'dni', 'cuil', 'first_name', 'last_name', 
            'email', 'phone', 'street', 'street_number', 'floor', 
            'apartment', 'postal_code', 'city', 'state', 'is_active', 'hire_date',
            'area_rel', 'sector_rel', 'position', 'social_work_rel', 'agreement_rel',
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
            'area_rel': forms.Select(attrs={'class': 'form-select'}),
            'sector_rel': forms.Select(attrs={'class': 'form-select'}),
            'social_work_rel': forms.Select(attrs={'class': 'form-select'}),
            'agreement_rel': forms.Select(attrs={'class': 'form-select'}),
            'employee_leg': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'cuil': forms.TextInput(attrs={'class': 'form-control'}),
            #'department_rel': forms.Select(attrs={'class': 'form-select'}),
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

# --- FORMSET PARA GESTIONAR LOS CERTIFICADOS DE AUSENCIA ---

class AbsenceCertificateForm(forms.ModelForm):
    class Meta:
        model = AbsenceCertificate
        fields = ['employee', 'reason', 'start_date', 'end_date', 'observations']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select select2'}),  #se quita -enable a select2 para permitir búsqueda abierta de empleados.
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles adicionales...'}),
        }

        # ➔ Formset para gestionar múltiples adjuntos asociados al certificado
        AbsenceDocumentFormSet = inlineformset_factory(
            AbsenceCertificate,
            AbsenceDocument,
            fields=['file'],
            extra=1,
            can_delete=True
        )

class AbsenceDocumentForm(forms.ModelForm):
    class Meta:
        model = AbsenceCertificateDocument
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        }

AbsenceDocumentFormSet = inlineformset_factory(
    AbsenceCertificate,
    AbsenceCertificateDocument,
    form=AbsenceDocumentForm,
    extra=2,
    can_delete=True
)
'''