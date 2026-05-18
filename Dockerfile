# Use uma imagem base do Python com as dependências do sistema
FROM python:3.10-slim

# Instale as dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos do projeto para o contêiner
COPY requirements.txt .

# Atualize o pip e instale numpy primeiro para evitar conflitos binários
RUN pip install --upgrade pip && \
    pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir -r requirements.txt

# Copie o resto dos arquivos
COPY . .

# Exponha a porta padrão do Flask
EXPOSE 5000

# Comando para iniciar o aplicativo
CMD ["python", "app.py"]