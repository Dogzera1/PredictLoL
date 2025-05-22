"""
Script para testar o webhook localmente.

Este script inicia um servidor local Flask para simular o ambiente Vercel,
permitindo testar o bot do Telegram sem precisar implantar na nuvem.
"""

import logging
import os
import sys
from flask import Flask, request, jsonify

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar o webhook da API
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.webhook import app as webhook_app

# Criar app Flask
app = Flask(__name__)

# Rota para testar se o servidor está funcionando
@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "OK", "message": "Servidor de teste do webhook está funcionando!"})

# Redirecionar todas as outras rotas para o app do webhook
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    logger.info(f"Recebida requisição para /{path}")
    with webhook_app.request_context(request.environ):
        return webhook_app.full_dispatch_request()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Iniciando servidor de teste na porta {port}...")
    logger.info("Use ngrok ou uma ferramenta similar para expor este servidor à internet")
    logger.info("e configurar o webhook do Telegram.")
    app.run(host="0.0.0.0", port=port, debug=True) 