from django.core.management.base import BaseCommand

from accounts.roles import ALL_ROLES, ensure_role_groups


class Command(BaseCommand):
    help = 'Crea los grupos de rol Administrador, Operador y Colaborador'

    def handle(self, *args, **options):
        ensure_role_groups()
        self.stdout.write(self.style.SUCCESS(
            'Roles disponibles: ' + ', '.join(ALL_ROLES)
        ))
