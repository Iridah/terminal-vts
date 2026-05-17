#dockerfile
# Usa una imagen liviana de Python
FROM python:3.12-slim

# Evita que Python genere archivos .pyc y permite log en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias para psycopg2 (Postgres)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copiamos e instalamos los requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Exponemos el puerto de Django
EXPOSE 8000

# Comando para iniciar el dashboard (v2.3)
CMD ["python", "PORTAL/manage.py", "runserver", "0.0.0.0:8000"]