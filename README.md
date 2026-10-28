# HRM_open
Human Resourses Management for Small and Medium Businesses

**Requirements:**
    Django>=4.2,<5.0  pip install django 
    psycopg2-binary>=2.9.0
    python-decouple>=3.8 pip install python-decouple
    dj-database-url>=2.1.0
    gunicorn>=21.2.0
    whitenoise>=6.5.0  pip install dj_database_url whitenoise

**How to install on local virtual enviroment for programming:**



**How to apply changes on database: (Execute on Powershell these commands)**
    python manage.py makemigrations employees
    python manage.py migrate
    python manage.py runserver


**Sistema HRM de código abierto, adaptable a escritorio y móvil, preparado para entornos locales y productivos.**

## Requisitos Previos en Windows
1. Tener instalado **Python 3.10+** (marcar la opción de añadir Python al PATH).
2. (Opcional para Docker) **Docker Desktop** instalado y activo.

---

## Instrucciones de Instalación Local (Desarrollo con SQLite)

0. **Clonar o descargar** el repositorio y abrir una terminal (PowerShell o CMD) en la carpeta HRM_Open (o donde se haya descomprimido el paquete).

1. **Instalar dependencias**
pip install -r requirements.txt

2. **Crear y activar un entorno virtual (ejecutar en Powershell)**:
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   Si no se tiene instalado Django, ejecutar: pip install django en Powershell

3. **Aplicar migraciones y crear superusuario**
    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser

4. **Ejecutar servidor de desarrollo**
    python manage.py runserver
    Acceder desde el navegador a: http://127.0.0.1:8000/

## Ejecución con Docker Compose (Producción / PostgreSQL)

1. Instalar Docker Desktop y asegurarse de tenerlo abierto.

2. Ejecutar el siguiente comando en la raíz:

    2. 1- PowerShell
        docker-compose up --build
        En otra terminal, realizar las migraciones dentro del contenedor:

    2. 2- PowerShell
        docker-compose exec web python manage.py migrate
        docker-compose exec web python manage.py createsuperuser
        El sistema estará disponible en http://localhost:8000.

## Copias de Seguridad y Restauración

**SQLite (Desarrollo)**
Backup: Copiar el archivo db.sqlite3 a una ubicación segura.
Restauración: Sobrescribir el archivo db.sqlite3 con la copia de respaldo.

## PostgreSQL (Producción / Docker)
Backup:
en PowerShell
docker-compose exec db pg_dump -U hrm_user hrm_open > backup.sql

Restauración:
en PowerShell
docker-compose exec -T db psql -U hrm_user hrm_open < backup.sql