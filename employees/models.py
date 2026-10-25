from django.db import models

class Employee(models.Model):
    employee_leg = models.CharField(max_length=50, unique=True, verbose_name="Nro. Legajo", blank=True, null=True)
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI", blank=True, null=True)
    cuil = models.CharField(max_length=20, unique=True, verbose_name="CUIL / NIF", blank=True, null=True)
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    position = models.CharField(max_length=100, verbose_name="Cargo")
    department = models.CharField(max_length=100, verbose_name="Departamento")
    hire_date = models.DateField(verbose_name="Fecha de Ingreso")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.position})"

    class Meta:
        verbose_name = "Legajo"
        verbose_name_plural = "Legajos"
        ordering = ['last_name', 'first_name']
