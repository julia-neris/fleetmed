# Use uma imagem base do Python com as dependências do sistema
FROM python:3.10-slim

# Instale as dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libatlas-base-dev \
    gfortran \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos do projeto para o contêiner
COPY . .

# Atualize o pip e instale as dependências do projeto
RUN pip install --upgrade pip && pip install -r requirements.txt

# Comando para iniciar o aplicativo
CMD ["python", "app.py"]