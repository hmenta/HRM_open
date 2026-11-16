from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

ADMIN = "RRHH Administrador"   # todo, incluido borrar y administrar
RECRUITER = "Reclutador"       # crea búsquedas, carga y mueve postulantes
VIEWER = "Consulta"            # solo lectura

ALL_ROLES = (ADMIN, RECRUITER, VIEWER)
EDIT_ROLES = (ADMIN, RECRUITER)


def user_role(user):
    """Devuelve el rol del usuario según su grupo. Superusuarios = Administrador."""
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return ADMIN
    names = set(user.groups.values_list("name", flat=True))
    for role in ALL_ROLES:
        if role in names:
            return role
    return None


def role_required(*roles):
    """Decorador: exige login y que el rol del usuario esté en `roles`."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if user_role(request.user) not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return login_required(wrapper)
    return decorator
