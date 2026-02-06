# Imagen base oficial de NVIDIA con CUDA 11.8 y Ubuntu 22.04
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

WORKDIR /app

# Instalar Python y dependencias de sistema necesarias
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Asegurar que 'python' y 'pip' apunten a la versión 3
RUN ln -s /usr/bin/python3 /usr/bin/python

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p uploads files_temp

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]