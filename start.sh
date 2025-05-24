#!/bin/bash
echo "🚀 Iniciando Bot LoL V3 Ultra Avançado no Railway..."
echo "📁 Verificando arquivos..."
ls -la /app/

echo "🐍 Versão Python:"
python --version

echo "📦 Dependências instaladas:"
pip list | grep -E "(telegram|flask|requests|numpy)"

echo "▶️ Iniciando bot_v13_railway.py..."
exec python bot_v13_railway.py 