#Imagen base optimizada, con python
FROM python:3.11-slim

#Establecer el directorio de trabajo en el contenedor
WORKDIR /app

#Copiar solo los archivos necesarios primero, para aprovechar la cache
COPY requirements.txt .

#Instalo paquetes necesarios para compilar y dependencias de python.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libffi-dev libssl-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential libffi-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/pip

RUN find . -name "*.pyc" -delete

#Copiar el resto de la aplicacion
COPY . .

#Expone el puerto de Django
EXPOSE 8000

#Comando para que corra la aplicacion
CMD ["/bin/sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]