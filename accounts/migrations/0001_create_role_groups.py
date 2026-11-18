from django.db import migrations


ROLE_NAMES = ('Administrador', 'Operador', 'Colaborador')


def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ROLE_NAMES:
        Group.objects.get_or_create(name=name)


def remove_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=ROLE_NAMES).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_roles, remove_roles),
    ]
