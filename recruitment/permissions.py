from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

ADMIN = "RRHH Administrador"   # todo, incluido borrar y administrar
RECRUITER = "Reclutador"       # crea búsquedas, carga y mueve postulantes
VIEWER = "Consulta"            # solo lectura

ALL_ROLES = (ADMIN, RECRUITER, VIEWER)
EDIT_ROLES = (ADMIN, RECRUITER)


def get_user_role(user):
    """Mapea los permisos nativos de Django a los roles de RRHH del sistema integrando los roles del módulo de Recruiting."""
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return ADMIN
    if user.is_staff:
        return RECRUITER
    return VIEWER

    """Devuelve el rol del usuario según su grupo. Superusuarios = Administrador.
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return ADMIN
    names = set(user.groups.values_list("name", flat=True))
    for role in ALL_ROLES:
        if role in names:
            return role
    return None """


def role_required(*allowed_roles):
    """Decorador que valida si el rol del usuario (derivado de Django) está permitido."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_role = get_user_role(request.user)
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("No tenés permisos para realizar esta acción.")
        return _wrapped_view
    return decorator

    """Decorador: exige login y que el rol del usuario esté en `roles`.
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if user_role(request.user) not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return login_required(wrapper)
    return decorator """
