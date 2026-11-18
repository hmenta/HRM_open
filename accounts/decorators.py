from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .roles import get_user_role


def role_required(*allowed_roles):
    """Exige login y que el rol del usuario esté entre los permitidos."""
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if get_user_role(request.user) in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('No tenés permisos para realizar esta acción.')
        return _wrapped
    return decorator


def capability_required(check_fn):
    """Exige login y que la función de capacidad devuelva True."""
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if check_fn(request.user):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('No tenés permisos para realizar esta acción.')
        return _wrapped
    return decorator
