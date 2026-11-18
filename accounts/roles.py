"""Roles y capacidades del sistema HRM Open."""

from django.contrib.auth.models import Group

ROLE_ADMIN = 'Administrador'
ROLE_OPERATOR = 'Operador'
ROLE_COLLABORATOR = 'Colaborador'

ALL_ROLES = (ROLE_ADMIN, ROLE_OPERATOR, ROLE_COLLABORATOR)

ROLE_LABELS = {
    ROLE_ADMIN: 'Administrador — acceso total',
    ROLE_OPERATOR: 'Operador — legajos, reclutamiento, certificados, reportes y recibos',
    ROLE_COLLABORATOR: 'Colaborador — certificados y consulta de recibos propios',
}


def ensure_role_groups():
    """Crea los grupos de rol si no existen."""
    for name in ALL_ROLES:
        Group.objects.get_or_create(name=name)


def get_user_role(user):
    """Devuelve el rol principal del usuario. Superusuario = Administrador."""
    if not getattr(user, 'is_authenticated', False):
        return None
    if user.is_superuser:
        return ROLE_ADMIN

    names = set(user.groups.values_list('name', flat=True))
    for role in ALL_ROLES:
        if role in names:
            return role
    return None


def set_user_role(user, role):
    """Asigna un único rol (grupo) al usuario y limpia los demás roles HRM."""
    ensure_role_groups()
    if role and role not in ALL_ROLES:
        raise ValueError(f'Rol inválido: {role}')

    role_groups = Group.objects.filter(name__in=ALL_ROLES)
    user.groups.remove(*role_groups)

    if role:
        group = Group.objects.get(name=role)
        user.groups.add(group)

    # Mantener coherencia con el admin de Django
    if role == ROLE_ADMIN:
        user.is_staff = True
    elif not user.is_superuser:
        user.is_staff = False
    user.save(update_fields=['is_staff'])


def user_has_role(user, *roles):
    role = get_user_role(user)
    return role in roles


def can_manage_users(user):
    return user_has_role(user, ROLE_ADMIN)


def can_manage_employees(user):
    return user_has_role(user, ROLE_ADMIN, ROLE_OPERATOR)


def can_manage_absences(user):
    return user_has_role(user, ROLE_ADMIN, ROLE_OPERATOR, ROLE_COLLABORATOR)


def can_manage_recruitment(user):
    return user_has_role(user, ROLE_ADMIN, ROLE_OPERATOR)


def can_view_reports(user):
    return user_has_role(user, ROLE_ADMIN, ROLE_OPERATOR)


def can_import_export_employees(user):
    return user_has_role(user, ROLE_ADMIN, ROLE_OPERATOR)


def can_view_payslips(user):
    """Todos los roles pueden acceder a la sección (el alcance se filtra en la vista)."""
    return user_has_role(user, ROLE_ADMIN, ROLE_OPERATOR, ROLE_COLLABORATOR)


def can_upload_payslips(user):
    return user_has_role(user, ROLE_ADMIN, ROLE_OPERATOR)


def can_manage_settings(user):
    return user_has_role(user, ROLE_ADMIN)


def capabilities_for(user):
    return {
        'user_role': get_user_role(user),
        'can_manage_users': can_manage_users(user),
        'can_manage_employees': can_manage_employees(user),
        'can_manage_absences': can_manage_absences(user),
        'can_manage_recruitment': can_manage_recruitment(user),
        'can_view_reports': can_view_reports(user),
        'can_import_export_employees': can_import_export_employees(user),
        'can_view_payslips': can_view_payslips(user),
        'can_upload_payslips': can_upload_payslips(user),
        'can_manage_settings': can_manage_settings(user),
    }
