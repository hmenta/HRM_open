from django.contrib import admin
from .models import Employee, TerminationReasonCatalog, Area, Sector, SocialWork, CollectiveAgreement

# Registramos los modelos / campos en el admin de Django

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'position', 'area_rel', 'sector_rel', 'is_active')

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'area_rel')

@admin.register(SocialWork)
class SocialWorkAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(CollectiveAgreement)
class CollectiveAgreementAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(TerminationReasonCatalog)
class TerminationReasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


# --- ADMINISTRACION DE LA COMPAÑÍA ---
from .models import CompanySettings

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Evita que creen más de un registro de configuración
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)