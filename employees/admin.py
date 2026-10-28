from django.contrib import admin
from .models import Employee, DepartmentCatalog, TerminationReasonCatalog

admin.site.register(Employee)
admin.site.register(DepartmentCatalog)
admin.site.register(TerminationReasonCatalog)

from .models import CompanySettings

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Evita que creen más de un registro de configuración
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)