from django.db import models

class CompanySettings(models.Model):
    name = models.CharField(max_length=150, default="Empresa Demostración S.A.")
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresa"
