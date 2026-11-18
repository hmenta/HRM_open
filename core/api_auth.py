from functools import wraps

from django.http import JsonResponse

from .models import ApiCredential


def _extract_credentials(request):
    api_key = request.headers.get('X-API-Key') or request.META.get('HTTP_X_API_KEY')
    api_token = request.headers.get('X-API-Token') or request.META.get('HTTP_X_API_TOKEN')

    # También aceptar Authorization: Bearer <token> junto con X-API-Key
    auth = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION', '')
    if not api_token and auth.lower().startswith('bearer '):
        api_token = auth[7:].strip()

    # Fallback query/form (útil en pruebas; preferir headers en producción)
    if not api_key:
        api_key = request.GET.get('api_key') or request.POST.get('api_key')
    if not api_token:
        api_token = request.GET.get('api_token') or request.POST.get('api_token')

    return (api_key or '').strip(), (api_token or '').strip()


def api_credential_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        api_key, api_token = _extract_credentials(request)
        if not api_key or not api_token:
            return JsonResponse(
                {'ok': False, 'error': 'Faltan credenciales. Enviá headers X-API-Key y X-API-Token.'},
                status=401,
            )
        try:
            cred = ApiCredential.objects.get(api_key=api_key, is_active=True)
        except ApiCredential.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'API Key inválida o inactiva.'}, status=401)
        if not cred.verify_token(api_token):
            return JsonResponse({'ok': False, 'error': 'API Token inválido.'}, status=401)
        cred.mark_used()
        request.api_credential = cred
        return view_func(request, *args, **kwargs)
    return _wrapped
