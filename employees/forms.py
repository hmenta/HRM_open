from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.forms import inlineformset_factory, TextInput, ClearableFileInput
from .models import AbsenceCertificate, AbsenceCertificateDocument, Employee, EmployeeDocument, Payslip

User = get_user_model()


# --- FORMULARIO Y FORMSET PARA EL LEGAJO DEL EMPLEADO ---

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_leg', 'dni', 'cuil', 'first_name', 'last_name', 
            'email', 'phone', 'street', 'street_number', 'floor', 
            'apartment', 'postal_code', 'city', 'state', 'is_active', 'hire_date',
            'area_rel', 'sector_rel', 'position', 'social_work_rel', 'agreement_rel',
            'termination_date', 'termination_reason_rel', 'photo', 'user',
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
            'user': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        taken_ids = list(
            Employee.objects.exclude(user__isnull=True)
            .exclude(pk=getattr(self.instance, 'pk', None))
            .values_list('user_id', flat=True)
        )
        qs = User.objects.filter(is_active=True).exclude(id__in=taken_ids).order_by('username')
        if self.instance and self.instance.user_id:
            qs = (qs | User.objects.filter(pk=self.instance.user_id)).distinct().order_by('username')
        self.fields['user'].queryset = qs
        self.fields['user'].required = False
        self.fields['user'].help_text = 'Vinculá un usuario para que pueda ver sus recibos de sueldo.'


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

# -- FORMULARIO DE CARGA PARA IMPORTAR DATA DE LEGAJOS.

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Seleccionar archivo CSV (UTF-8)",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
        help_text="Asegurate de que el archivo esté codificado en UTF-8 y separado por comas o punto y coma."
    )


MONTH_CHOICES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = []
            for item in data:
                result.append(single_clean(item, initial))
            return result
        return single_clean(data, initial)


class PayslipUploadForm(forms.ModelForm):
    class Meta:
        model = Payslip
        fields = ['employee', 'year', 'month', 'file']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000}),
            'month': forms.Select(choices=MONTH_CHOICES, attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['month'].choices = MONTH_CHOICES
        today = date.today()
        self.fields['year'].initial = today.year
        self.fields['month'].initial = today.month
        self.fields['file'].help_text = 'Solo PDF.'


class PayslipBulkUploadForm(forms.Form):
    year = forms.IntegerField(
        label='Año',
        min_value=2000,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    month = forms.TypedChoiceField(
        label='Mes',
        choices=MONTH_CHOICES,
        coerce=int,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    pdf_files = MultipleFileField(
        label='PDFs individuales',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,application/pdf',
        }),
        help_text='Podés seleccionar varios PDF a la vez.',
    )
    zip_file = forms.FileField(
        label='O un ZIP con PDFs',
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.zip,application/zip'}),
        help_text='El sistema asocia cada archivo por DNI, CUIL o legajo en el nombre.',
    )
    replace_existing = forms.BooleanField(
        label='Reemplazar recibos ya cargados del mismo período',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        self.fields['year'].initial = today.year
        self.fields['month'].initial = today.month

    def clean(self):
        cleaned = super().clean()
        files = self.files.getlist('pdf_files') if hasattr(self, 'files') else []
        zip_file = cleaned.get('zip_file')
        if not files and not zip_file:
            raise forms.ValidationError('Subí al menos un PDF o un archivo ZIP.')
        return cleaned
