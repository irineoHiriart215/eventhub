#Imagen base optimizada, con python
FROM python:3.11-slim

#Instalo paquetes necesarios para compilar y dependencias de python.
RUN apt-get update && apt.get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/*

#Establecer el directorio de trabajo en el contenedor
WORKDIR /app

#Copiar solo los archivos necesarios primero, para aprovechar la cache
COPY requirements.txt .

#Instalar dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

#Copiar el resto de la aplicacion
COPY . .

#Expone el puerto de Django
EXPOSE 8000

#Comando para que corra la aplicacion
CMD ["sh", "-c", "python manage migrate && python manage.py runserver 0.0.0.0:8000"]