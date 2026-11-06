import os

# Estructura de archivos y contenido inicial para HRM Open
files = {
    "requirements.txt": """Django>=4.2,<5.0
psycopg2-binary>=2.9.0
python-decouple>=3.8
dj-database-url>=2.1.0
gunicorn>=21.2.0
whitenoise>=6.5.0
""",
    ".env.example": """DEBUG=True
SECRET_KEY=django-insecure-cambiar-esta-clave-en-produccion
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
""",
    ".gitignore": """venv/
__pycache__/
db.sqlite3
.env
staticfiles/
*.pyc
""",
    "hrm_open/__init__.py": "",
    "hrm_open/settings.py": """import os
from pathlib import Path
import dj_database_url
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-key')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'accounts',
    'employees',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hrm_open.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.company_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'hrm_open.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-AR'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
""",
    "hrm_open/urls.py": """from django.contrib import admin
from django.urls import path, include
from employees.views import dashboard_view, employee_list_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('employees/', employee_list_view, name='employee_list'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]
""",
    "hrm_open/wsgi.py": """import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrm_open.settings')
application = get_wsgi_application()
""",
    "core/__init__.py": "",
    "core/models.py": """from django.db import models

class CompanySettings(models.Model):
    name = models.CharField(max_length=150, default="Empresa Demostración S.A.")
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresa"
""",
    "core/context_processors.py": """from .models import CompanySettings

def company_settings(request):
    company, _ = CompanySettings.objects.get_or_create(pk=1)
    return {'company': company}
""",
    "accounts/__init__.py": "",
    "employees/__init__.py": "",
    "employees/models.py": """from django.db import models

class Employee(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    position = models.CharField(max_length=100, verbose_name="Cargo")
    department = models.CharField(max_length=100, verbose_name="Departamento")
    hire_date = models.DateField(verbose_name="Fecha de Ingreso")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.position})"

    class Meta:
        verbose_name = "Legajo"
        verbose_name_plural = "Legajos"
        ordering = ['last_name', 'first_name']
""",
    "employees/views.py": """from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from .models import Employee

@login_required
def dashboard_view(request):
    total_employees = Employee.objects.filter(is_active=True).count()
    context = {
        'total_employees': total_employees,
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def employee_list_view(request):
    query = request.GET.get('q', '')
    employees = Employee.objects.all()
    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(position__icontains=query) |
            Q(department__icontains=query)
        )
    return render(request, 'employees/employee_list.html', {'employees': employees, 'query': query})
""",
    "templates/accounts/login.html": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iniciar Sesión - HRM Open</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center py-4" style="height: 100vh;">
    <main class="form-signin w-100 m-auto" style="max-width: 380px;">
        <div class="card shadow-sm p-4">
            <h1 class="h3 mb-3 fw-normal text-center">**HRM Open**</h1>
            <form method="post">
                {% csrf_token %}
                {% if form.errors %}
                    <div class="alert alert-danger py-2">Usuario o contraseña incorrectos.</div>
                {% endif %}
                <div class="form-floating mb-3">
                    <input type="text" name="username" class="form-control" id="id_username" placeholder="Usuario" required autofocus>
                    <label for="id_username">Usuario</label>
                </div>
                <div class="form-floating mb-3">
                    <input type="password" name="password" class="form-control" id="id_password" placeholder="Contraseña" required>
                    <label for="id_password">Contraseña</label>
                </div>
                <button class="w-100 btn btn-lg btn-primary" type="submit">Ingresar</button>
            </form>
        </div>
    </main>
</body>
</html>
""",
    "templates/dashboard/index.html": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel - {{ company.name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">{{ company.name }} (HRM Open)</a>
            <div class="d-flex">
                <span class="navbar-text text-light me-3">Hola, {{ request.user.username }}</span>
                <form action="{% url 'logout' %}" method="post" class="d-inline">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-outline-light btn-sm">Cerrar Sesión</button>
                </form>
            </div>
        </div>
    </nav>
    <div class="container my-4">
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="p-4 bg-white rounded shadow-sm">
                    <h2>Bienvenido al Panel de Control</h2>
                    <p class="text-muted">Sistema modular de recursos humanos.</p>
                    <hr>
                    <a href="{% url 'employee_list' %}" class="btn btn-primary">Ver Legajos ({{ total_employees }})</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
""",
    "templates/employees/employee_list.html": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Legajos - {{ company.name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'dashboard' %}">← Volver al Panel</a>
        </div>
    </nav>
    <div class="container my-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2>Legajos de Personal</h2>
        </div>
        <div class="card shadow-sm p-3 mb-4">
            <form method="get" class="row g-3">
                <div class="col-md-10">
                    <input type="text" name="q" class="form-control" placeholder="Buscar por nombre, apellido, cargo o departamento..." value="{{ query }}">
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-secondary w-100">Buscar</button>
                </div>
            </form>
        </div>
        <div class="card shadow-sm p-3">
            <div class="table-responsive">
                <table class="table table-striped align-middle">
                    <thead>
                        <tr>
                            <th>Apellido y Nombre</th>
                            <th>Cargo</th>
                            <th>Departamento</th>
                            <th>Correo</th>
                            <th>Ingreso</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for emp in employees %}
                        <tr>
                            <td>{{ emp.last_name }}, {{ emp.first_name }}</td>
                            <td>{{ emp.position }}</td>
                            <td>{{ emp.department }}</td>
                            <td>{{ emp.email }}</td>
                            <td>{{ emp.hire_date }}</td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="5" class="text-center py-4 text-muted">No se encontraron legajos.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
""",
    "manage.py": """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrm_open.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""
}

for path, content in files.items():
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# Copiar .env.example a .env si no existe
if not os.path.exists(".env"):
    with open(".env.example", "r", encoding="utf-8") as src, open(".env", "w", encoding="utf-8") as dst:
        dst.write(src.read())

print("¡Estructura de archivos creada exitosamente!")