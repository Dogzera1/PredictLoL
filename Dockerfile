# 🐳 DOCKERFILE PARA BOT LOL V3 ULTRA AVANÇADO
FROM python:3.11-slim

# Metadata
LABEL maintainer="Bot LoL V3 Team"
LABEL description="Bot LoL Predictor V3 Ultra Avançado com IA"
LABEL version="3.1.0"

# Configurar timezone
ENV TZ=America/Sao_Paulo
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root para segurança
RUN groupadd -r botuser && useradd -r -g botuser -d /app -s /bin/bash botuser

# Configurar diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements específico para Railway
COPY requirements_railway.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements_railway.txt

# Copiar código da aplicação
COPY bot_v13_railway.py .

# Criar diretórios necessários
RUN mkdir -p /app/logs /app/data /app/backups

# Configurar permissões
RUN chown -R botuser:botuser /app
USER botuser

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:5000/health || exit 1

# Expor porta para webhook (opcional)
EXPOSE 5000

# Comando principal
CMD ["python", "bot_v13_railway.py"] 