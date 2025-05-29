#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT MINIMAL TEST - Para identificar problema 502 no Railway
"""

import os
import logging
from flask import Flask, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
PORT = int(os.getenv('PORT', 5000))

# Flask app MINIMAL
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/health')
def health_check():
    """Health check minimal"""
    try:
        logger.info("🔍 Health check chamado")
        return jsonify({
            'status': 'healthy',
            'message': 'Minimal test working',
            'port': PORT
        }), 200
    except Exception as e:
        logger.error(f"❌ Erro no health check: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/')
def root():
    """Rota raiz minimal"""
    try:
        logger.info("🔍 Root chamado")
        return jsonify({
            'message': 'Minimal bot test',
            'status': 'online'
        }), 200
    except Exception as e:
        logger.error(f"❌ Erro no root: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == "__main__":
    logger.info("🚀 Iniciando bot minimal test")
    logger.info(f"🌐 Porta: {PORT}")
    
    # Iniciar Flask MINIMAL
    app.run(host='0.0.0.0', port=PORT, debug=False) 