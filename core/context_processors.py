from .models import CompanySettings

def company_settings(request):
    # Obtiene el primer registro o crea uno por defecto
    config, created = CompanySettings.objects.get_or_create(id=1, defaults={'name': 'HRM Open'})
    return {
        'company_config': config
    }
