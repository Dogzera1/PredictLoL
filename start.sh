#!/bin/bash
echo "🚂 Iniciando Bot LoL no Railway..."
echo "🔧 Verificando dependências..."
pip list | grep -E "(telegram|flask|requests)"
echo "🤖 Iniciando aplicação..."
python main.py 