from .models import CompanySettings

def company_context(request):
    return {
        'company': CompanySettings.load()
    }