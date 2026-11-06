# Usamos una imagen oficial y ligera de Python
FROM python:3.12-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias si hiciera falta
RUN apt-get update && apt-get install -y libpq-dev gcc

# Actualizamos pip e instalamos las dependencias del proyecto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código del proyecto al contenedor
COPY . .

# Puerto por defecto en el que corre Django
EXPOSE 8000

# Comando por defecto para iniciar el servidor de desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]