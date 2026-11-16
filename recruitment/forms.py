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
        fields = ["title", "client", "description", "requirements", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "requirements": forms.Textarea(attrs={"rows": 4}),
        }


class CandidateForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            "first_name", "last_name", "email", "phone", "location", "linkedin",
            "current_title", "years_experience", "skills", "education", "summary", "cv_file",
        ]
        widgets = {
            "skills": forms.Textarea(attrs={"rows": 2}),
            "education": forms.Textarea(attrs={"rows": 3}),
            "summary": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_cv_file(self):
        f = self.cleaned_data.get("cv_file")
        if f and hasattr(f, "name") and hasattr(f, "size"):
            validate_cv(f)
        return f


class PortalApplyForm(BootstrapMixin, forms.Form):
    first_name = forms.CharField(label="Nombre", max_length=100)
    last_name = forms.CharField(label="Apellido", max_length=100)
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Teléfono", max_length=40, required=False)
    position = forms.ModelChoiceField(
        label="Búsqueda (opcional)",
        queryset=Position.objects.filter(status=Position.Status.OPEN),
        required=False,
        empty_label="Banco general de talentos",
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
