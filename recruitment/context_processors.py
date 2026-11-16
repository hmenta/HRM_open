def recruitment_roles(request):
    """
    Inyecta el rol del usuario en el contexto de las plantillas de reclutamiento
    basándose en los grupos de Django o si es superusuario.
    """
    role = "Invitado"
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.groups.filter(name="RRHH Administrador").exists():
            role = "RRHH Administrador"
        elif request.user.groups.filter(name="Reclutador").exists():
            role = "Reclutador"
        else:
            role = "Colaborador"
    return {"user_role": role}