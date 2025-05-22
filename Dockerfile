FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 8080

# Comando de inicialização explícito
CMD ["python", "main.py"] 