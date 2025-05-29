#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE FLASK PURO - Para identificar se o problema é no Railway ou no código
"""

import os
import logging
from flask import Flask, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
PORT = int(os.getenv('PORT', 5000))

# Flask app PURO
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/health')
def health_check():
    """Health check puro"""
    try:
        logger.info("🔍 Health check PURO chamado")
        return jsonify({
            'status': 'healthy',
            'message': 'Flask PURO funcionando',
            'port': PORT,
            'test': 'SUCESSO'
        }), 200
    except Exception as e:
        logger.error(f"❌ Erro no health check puro: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/')
def root():
    """Rota raiz pura"""
    logger.info("🔍 Root PURO chamado")
    return jsonify({
        'message': 'FLASK PURO FUNCIONANDO',
        'status': 'online',
        'test': 'SUCESSO TOTAL'
    }), 200

@app.route('/webhook', methods=['POST'])
def webhook_test():
    """Webhook de teste puro"""
    logger.info("🔍 Webhook PURO chamado")
    return "WEBHOOK_PURO_OK", 200

@app.route('/ping')
def ping():
    """Ping puro"""
    logger.info("🔍 Ping PURO chamado")
    return "PONG_PURO", 200

if __name__ == "__main__":
    logger.info("🚀 INICIANDO FLASK COMPLETAMENTE PURO")
    logger.info(f"🌐 Porta: {PORT}")
    logger.info("🔍 Se isso funcionar, o problema está no bot complexo")
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        logger.error(f"❌ ERRO NO FLASK PURO: {e}")
        raise 