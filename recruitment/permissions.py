"""Compatibilidad de roles de reclutamiento con el módulo accounts."""

from accounts.decorators import role_required
from accounts.roles import (
    ROLE_ADMIN as ADMIN,
    ROLE_OPERATOR as RECRUITER,
    ROLE_ADMIN,
    ROLE_OPERATOR,
    ALL_ROLES as _ALL,
    get_user_role,
)

# Roles con acceso de lectura/escritura al módulo de reclutamiento
ALL_ROLES = (ROLE_ADMIN, ROLE_OPERATOR)
EDIT_ROLES = (ROLE_ADMIN, ROLE_OPERATOR)

# Alias legacy usados en plantillas antiguas
VIEWER = 'Colaborador'

__all__ = [
    'ADMIN',
    'RECRUITER',
    'VIEWER',
    'ALL_ROLES',
    'EDIT_ROLES',
    'get_user_role',
    'role_required',
]
