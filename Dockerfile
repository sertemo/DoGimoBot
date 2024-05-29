# Usar una imagen base de Python
FROM python:3.10-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar curl para descargar poetry y otras herramientas útiles
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.8.3


# Actualizar pip e instalar Poetry utilizando pip
RUN pip install --upgrade pip && \
    pip install "poetry==$POETRY_VERSION"


# Asegurarse de que el binario de Poetry esté en el PATH
ENV PATH="/root/.poetry/bin:${PATH}"

# Configurar Poetry: no crear un entorno virtual y no preguntar en la instalación
RUN poetry config virtualenvs.create false && \
    poetry config installer.parallel false

# Copiar solo archivos necesarios para la instalación de dependencias
COPY pyproject.toml poetry.lock* /app/

# Instalar dependencias de proyecto utilizando Poetry
RUN poetry install --no-dev --no-interaction --no-ansi

# Copiar el resto del código fuente al contenedor (excepto lo del .dockerignore)
COPY . /app

# Establecer variables de entorno necesarias para el bot
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Comando para ejecutar el bot
CMD ["python", "src/dogimobot/main.py"]
