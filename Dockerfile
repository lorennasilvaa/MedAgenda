# Usa uma imagem leve e oficial do Python
FROM python:3.13-slim

# Evita que o Python gere arquivos .pyc e garante que os logs apareçam em tempo real no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define a pasta de trabalho dentro do contêiner
WORKDIR /app

# Copia e instala as dependências primeiro (aproveita o cache do Docker)
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante do código do projeto
COPY . /app/