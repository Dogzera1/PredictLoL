FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE $PORT

# Comando de inicialização para Railway
CMD ["python", "-u", "main_v3_riot_integrated.py"] 