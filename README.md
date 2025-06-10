# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

## Dependencias

-   python 3
-   Django
-   sqlite
-   playwright
-   ruff

## Instalar dependencias

`pip install -r requirements.txt`

## Iniciar la Base de Datos

`python manage.py migrate`

### Crear usuario admin

`python manage.py createsuperuser`

### Llenar la base de datos

`python manage.py loaddata fixtures/events.json`

## Iniciar app

`python manage.py runserver`

## Integrantes.

`Hiriart, Irineo. Legajo 32599 `
`Vicente, Juan. Legajo 24770 `
`Leiva, Emanuel. Legajo 31483`
`Battistella, Tomás. Legajo 31520`
`Sarria, Ivan. Legajo 31144`

## Configuracion de variables de entorno.
-Copiar el archivo env-example a un archivo llamado .env
-Editar el archivo .env reemplazando valores de ejemplo, con valores reales
-Ejecutar el contenedor Docker pasando el archivo .env usando la opcion --env-file
    'docker run -d -p 8000:8000 -name myapp --env-file .env nombreimagen'
