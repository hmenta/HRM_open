from .models import CompanySettings

def company_settings(request):
    company, _ = CompanySettings.objects.get_or_create(pk=1)
    return {'company': company}
