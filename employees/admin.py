from django.contrib import admin
from .models import Employee, DepartmentCatalog, TerminationReasonCatalog

admin.site.register(Employee)
admin.site.register(DepartmentCatalog)
admin.site.register(TerminationReasonCatalog)