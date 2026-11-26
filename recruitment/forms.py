from django import forms

from .models import Application, Candidate, Position

ALLOWED_CV_EXT = (".pdf", ".docx")
MAX_CV_MB = 5


def validate_cv(uploaded):
    if not uploaded.name.lower().endswith(ALLOWED_CV_EXT):
        raise forms.ValidationError("El CV debe ser PDF o DOCX.")
    if uploaded.size > MAX_CV_MB * 1024 * 1024:
        raise forms.ValidationError(f"El archivo supera {MAX_CV_MB} MB.")


class BootstrapMixin:
    """Agrega las clases de Bootstrap a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"


class PositionForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Position
        fields = [
            "title",
            "client",
            "status",
            "start_date",
            "closing_date",
            "description",
            "requirements",
            "vacancies",
            "owner",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
            "closing_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            if isinstance(field.widget, forms.Select):
                if "form-select" not in css:
                    field.widget.attrs["class"] = f"{css} form-select".strip()
            else:
                if "form-control" not in css:
                    field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean(self):
        cleaned_data = super().clean()

        vacancies = cleaned_data.get("vacancies")
        if vacancies is not None and vacancies < 1:
            self.add_error("vacancies", "La cantidad de vacantes debe ser al menos 1.")
        
        start_date = cleaned_data.get("start_date")
        closing_date = cleaned_data.get("closing_date")
        if start_date and closing_date and closing_date < start_date:
            self.add_error("closing_date", "La fecha de cierre no puede ser anterior a la fecha de inicio.")
        return cleaned_data

class CandidateForm(BootstrapMixin, forms.ModelForm):
    clear_cv = forms.BooleanField(
        required=False,
        label="Eliminar CV actual",
    )

    class Meta:
        model = Candidate
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "location",
            "linkedin",
            "current_title",
            "years_experience",
            "skills",
            "education",
            "summary",
            "cv_file",
        ]
        widgets = {
            "skills": forms.Textarea(attrs={"rows": 2}),
            "education": forms.Textarea(attrs={"rows": 3}),
            "summary": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        has_cv = bool(
            self.instance
            and self.instance.pk
            and self.instance.cv_file
            and self.instance.cv_file.name
        )
        if not has_cv:
            self.fields["clear_cv"].widget = forms.HiddenInput()

    def clean_cv_file(self):
        f = self.cleaned_data.get("cv_file")
        if f and hasattr(f, "name") and hasattr(f, "size"):
            validate_cv(f)
        return f

    def save(self, commit=True):
        clear = self.cleaned_data.get("clear_cv", False)
        uploaded_cv = self.cleaned_data.get("cv_file")

        candidate = super().save(commit=False)

        old_cv = None
        if self.instance and self.instance.pk:
            try:
                old_obj = Candidate.objects.get(pk=self.instance.pk)
                if old_obj.cv_file and old_obj.cv_file.name:
                    old_cv = old_obj.cv_file
            except Candidate.DoesNotExist:
                pass

        if clear:
            if old_cv:
                old_cv.delete(save=False)
            elif candidate.cv_file and candidate.cv_file.name:
                candidate.cv_file.delete(save=False)
            candidate.cv_file = None
        elif uploaded_cv and old_cv and old_cv.name != uploaded_cv.name:
            old_cv.delete(save=False)

        if commit:
            candidate.save()
            self.save_m2m()

        return candidate


class PortalApplyForm(BootstrapMixin, forms.Form):
    first_name = forms.CharField(label="Nombre", max_length=100)
    last_name = forms.CharField(label="Apellido", max_length=100)
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Teléfono", max_length=40, required=False)
    position = forms.ModelChoiceField(
        label="Búsqueda (opcional)",
        queryset=Position.objects.filter(status=Position.Status.OPEN),
        required=False,
        empty_label="Base general de talentos",
    )
    cv_file = forms.FileField(label="Tu CV (PDF o DOCX, máx. 5 MB)")
    consent = forms.BooleanField(
        label="Acepto que mis datos sean tratados con fines de selección de personal.",
        required=True,
    )

    def clean_cv_file(self):
        f = self.cleaned_data["cv_file"]
        validate_cv(f)
        return f