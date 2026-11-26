from django.conf import settings
from .models import CompanySettings

def company_settings(request):
    # Obtiene el primer registro o crea uno por defecto
    config, created = CompanySettings.objects.get_or_create(id=1, defaults={'name': 'HRM Open'})
    return {
        'company_config': config
    }

# Para el Portal externo de empleos y postulaciones
def portal_settings(request):
    valor = getattr(settings, "PORTAL_ENABLED", False)
    return {
        "portal_enabled": getattr(settings, "PORTAL_ENABLED", False),        
    }