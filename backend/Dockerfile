# imagen de Python 3.12 ligera
FROM python:3.12-slim

# se fuerza a que la salida de la consola sea inmediata
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# el directorio de trabajo dentro del contenedor
WORKDIR /app

# se toman las dependencias y se instalan
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# se toma todo el codigo de el backend
COPY . /app/


EXPOSE 8000
