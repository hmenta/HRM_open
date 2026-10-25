from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_leg', 'dni', 'cuil', 
            'first_name', 'last_name', 'email', 
            'position', 'department', 'hire_date', 'is_active',
            'termination_date', 'termination_reason'
        ]
        widgets = {
            'employee_leg': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'cuil': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'termination_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'termination_reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Renuncia, Despido, Jubilación...'}),
        }