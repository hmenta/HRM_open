from .roles import capabilities_for


def role_context(request):
    """Inyecta rol y capacidades en todas las plantillas."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'user_role': None,
            'can_manage_users': False,
            'can_manage_employees': False,
            'can_manage_absences': False,
            'can_manage_recruitment': False,
            'can_view_reports': False,
            'can_import_export_employees': False,
            'can_view_payslips': False,
            'can_upload_payslips': False,
            'can_manage_settings': False,
        }
    return capabilities_for(user)
