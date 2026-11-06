import os
from django.db import models
from django.utils import timezone

# --- MODELOS PARA CAMPOS MAESTROS PARAMETRIZABLES ---

class SocialWork(models.Model):
    """Modelo para parametrizar las Obras Sociales"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Obra Social")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Obra Social"
        verbose_name_plural = "Obras Sociales"
        ordering = ['name']

class CollectiveAgreement(models.Model):
    """Modelo para parametrizar los Convenios Colectivos"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Convenio")

    def __str__(self):
        return self.name

    class Meta:
            verbose_name = "Convenio Colectivo"
            verbose_name_plural = "Convenios"
            ordering = ['name']

class Area(models.Model):
    """Modelo para parametrizar las Áreas organizacionales"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Área")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ['name']

class Sector(models.Model):
    """Modelo para parametrizar los Sectores dentro de las áreas"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Sector")
    area_rel = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='sectors', verbose_name="Área a la que pertenece", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectores"
        ordering = ['name']

# --- MODELO CON DEPARTAMENTO UNICO ---
#
#class DepartmentCatalog(models.Model):
#    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Departamento")
#
#    def __str__(self):
#        return self.name
#
#    class Meta:
#        verbose_name = "Departamento"
#        verbose_name_plural = "Departamentos"
#        ordering = ['name']


# --- CATALOGO DE MOTIVOS DE FIN DE CONTRATO DE TRABAJO --- 

class TerminationReasonCatalog(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Motivo de Baja")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Motivo de Baja"
        verbose_name_plural = "Motivos de Baja"
        ordering = ['name']


#  --- MODELO PRINCIPAL DE LEGAJO EMPLEADO ---

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
    position = models.CharField(max_length=100, verbose_name="Posición")
    area_rel = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Área")
    sector_rel = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sector")
    social_work_rel = models.ForeignKey(SocialWork, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Obra Social")
    agreement_rel = models.ForeignKey(CollectiveAgreement, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Convenio")
    
    # --- habilitar solo para modelo de departamento único --- 
    #department_rel = models.ForeignKey(
    #    DepartmentCatalog, 
    #    on_delete=models.SET_NULL, 
    #    null=True, 
    #    blank=True, 
    #    verbose_name="Departamento")
    
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

    # Archivos multimedia (Se mantiene la foto del colaborador)
    photo = models.ImageField(upload_to='employees/photos/', verbose_name="Fotografía", blank=True, null=True)
    
    # ⚠️ CAMBIO CLAVE: Se eliminó el campo 'document' individual de aquí.
    # Ahora la documentación se gestiona de forma relacional mediante el modelo 'EmployeeDocument' de abajo.
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.position})"

    class Meta:
        verbose_name = "Legajo"
        verbose_name_plural = "Legajos"
        ordering = ['last_name', 'first_name']


# --- MODELO CONFIGURACIÓN EMPRESA ---
class CompanySettings(models.Model):
    company_name = models.CharField(max_length=100, default="HRM Open", verbose_name="Nombre de la Empresa")
    logo = models.ImageField(upload_to='company/', blank=True, null=True, verbose_name="Logo de la Empresa (JPG/PNG)")

    def save(self, *args, **kwargs):
        # Patrón Singleton: Forzamos el ID 1 para que sea un registro único
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración General de la Empresa"



# =========================================================================
# MODELO RELACIONADO PARA SOPORTAR MÚLTIPLES DOCUMENTOS POR LEGAJO
# =========================================================================
class EmployeeDocument(models.Model):
    # Relación ForeignKey: permite asociar múltiples archivos a un mismo empleado
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='documents', 
        verbose_name="Legajo"
    )
    # Título o etiqueta descriptiva del archivo (Ej: DNI, Examen Médico, Título, etc.)
    title = models.CharField(
        max_length=100, 
        verbose_name="Título (Ej: DNI, Examen Médico, Certificado, etc)"
    )
    # Archivo físico en formato PDF o imagen
    document = models.FileField(
        upload_to='employees/docs/', 
        verbose_name="Archivo PDF / Imagen"
    )
    # Fecha y hora automática de carga
    uploaded_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de carga"
    )

    def __str__(self):
        return f"{self.title} - {self.employee}"

# --- MODULO PARA GESTIONAR CERTIFICADOS DE AUSENCIAS ---

def absence_document_path(instance, filename):
    # Organiza las descargas en: media/absence_certificates/legajo_<id>/<filename>
    return f'absence_certificates/legajo_{instance.certificate.employee.id}/{filename}'

# Modelo del certificado
class AbsenceCertificate(models.Model):

    REASON_CHOICES = [
            ('Enfermedad', 'Enfermedad'),
            ('Accidente', 'Accidente'),
            ('Trámite Personal', 'Trámite Personal'),
            ('Estudio', 'Estudio'),
            ('Familiar', 'Familiar'),
            ('Otro', 'Otro'),
        ]

    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, verbose_name="Empleado")
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, verbose_name="Motivo")
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    end_date = models.DateField(verbose_name="Fecha de Fin")
    observations = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Ausencia de {self.employee} ({self.start_date} al {self.end_date})"

# Modelo ÚNICO para los documentos adjuntos
class AbsenceCertificateDocument(models.Model):
    absence_certificate = models.ForeignKey(AbsenceCertificate, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='absences/', verbose_name="Archivo Adjunto")
    
    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.filename

''' OLD
class AbsenceCertificateDocument(models.Model):
    """Modelo adjunto para soportar múltiples archivos (PDF, JPG, PNG) por certificado"""
    certificate = models.ForeignKey(
        AbsenceCertificate, 
        on_delete=models.CASCADE, 
        related_name='documents', 
        verbose_name="Certificado"
    )
    file = models.FileField(upload_to=absence_document_path, verbose_name="Archivo (PDF / Imagen)")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Subida")

    class Meta:
        verbose_name = "Documento Adjunto de Ausencia"
        verbose_name_plural = "Documentos Adjuntos de Ausencia"

    def filename(self):
        return os.path.basename(self.file.name)
'''

#class AbsenceCertificate(models.Model):
#    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, verbose_name="Empleado")
#    reason = models.CharField(max_length=50, verbose_name="Motivo")
#    start_date = models.DateField(verbose_name="Fecha de Inicio")
#    end_date = models.DateField(verbose_name="Fecha de Fin")
#    observations = models.TextField(blank=True, null=True, verbose_name="Observaciones")
#    created_at = models.DateTimeField(auto_now_add=True)
#
#    def __str__(self):
#        return f"Ausencia de {self.employee} ({self.start_date} al {self.end_date})"

''' OLD CODE
class AbsenceDocument(models.Model):
    absence_certificate = models.ForeignKey(AbsenceCertificate, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='absences/', verbose_name="Archivo Adjunto")
    
    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.filename
'''
