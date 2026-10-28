from django.db import models

class DepartmentCatalog(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Departamento")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['name']


class TerminationReasonCatalog(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Motivo de Baja")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Motivo de Baja"
        verbose_name_plural = "Motivos de Baja"
        ordering = ['name']


class Employee(models.Model):
    # Identificación
    employee_leg = models.CharField(max_length=50, unique=True, verbose_name="Nro. Legajo", blank=True, null=True)
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI", blank=True, null=True)
    cuil = models.CharField(max_length=20, unique=True, verbose_name="CUIL / NIF", blank=True, null=True)
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    phone = models.CharField(max_length=50, verbose_name="Teléfono de Contacto", blank=True, null=True)
    
    # Domicilio
    street = models.CharField(max_length=150, verbose_name="Calle", blank=True, null=True)
    street_number = models.CharField(max_length=20, verbose_name="Número", blank=True, null=True)
    floor = models.CharField(max_length=10, verbose_name="Piso", blank=True, null=True)
    apartment = models.CharField(max_length=10, verbose_name="Dpto.", blank=True, null=True)
    postal_code = models.CharField(max_length=20, verbose_name="Código Postal", blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name="Localidad", blank=True, null=True)
    state = models.CharField(max_length=100, verbose_name="Provincia / Estado", blank=True, null=True)

    # Laboral
    position = models.CharField(max_length=100, verbose_name="Cargo")
    department_rel = models.ForeignKey(
        DepartmentCatalog, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Departamento"
    )
    hire_date = models.DateField(verbose_name="Fecha de Ingreso")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Egreso
    termination_date = models.DateField(verbose_name="Fecha de Egreso", blank=True, null=True)
    termination_reason_rel = models.ForeignKey(
        TerminationReasonCatalog, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Motivo de Baja"
    )

    # Archivos multimedia y documentos
    photo = models.ImageField(upload_to='employees/photos/', verbose_name="Fotografía", blank=True, null=True)
    document = models.FileField(upload_to='employees/docs/', verbose_name="Documentación adjunta (PDF/Doc)", blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.position})"

    class Meta:
        verbose_name = "Legajo"
        verbose_name_plural = "Legajos"
        ordering = ['last_name', 'first_name']


# Registro de configuración de Empresa
class CompanySettings(models.Model):
    company_name = models.CharField(max_length=100, default="HRM Open", verbose_name="Nombre de la Empresa")
    logo = models.ImageField(upload_to='company/', blank=True, null=True, verbose_name="Logo de la Empresa (JPG/PNG)")

    def save(self, *args, **kwargs):
        # Patrón Singleton: En principio, forzamos el ID 1 para que sea un registro único
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración General de la Empresa"