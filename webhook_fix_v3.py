#!/usr/bin/env python3
"""
Webhook Fix V3 - Script alternativo para testar webhook
"""

import os
import asyncio
import logging
from flask import Flask, request, jsonify

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports condicionais
try:
    from telegram import Update
    from telegram.ext import Application
    TELEGRAM_AVAILABLE = True
    logger.info("✅ Telegram libraries encontradas")
except ImportError:
    logger.error("❌ Telegram libraries não encontradas")
    TELEGRAM_AVAILABLE = False

# Token
TOKEN = os.environ.get("TELEGRAM_TOKEN")
logger.info(f"Token status: {'✅ Configurado' if TOKEN else '❌ Não configurado'}")

# Variável global para o bot
telegram_app = None

def initialize_bot():
    """Inicializa o bot Telegram"""
    global telegram_app
    
    if not TELEGRAM_AVAILABLE or not TOKEN:
        logger.warning("⚠️ Bot não pode ser inicializado")
        return None
    
    try:
        telegram_app = Application.builder().token(TOKEN).build()
        logger.info("✅ Bot Telegram inicializado com sucesso")
        return telegram_app
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar bot: {e}")
        return None

# Inicializar bot antes de tudo
bot_app = initialize_bot()

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "version": "webhook-fix-v3",
        "telegram_available": TELEGRAM_AVAILABLE,
        "token_configured": TOKEN is not None,
        "bot_initialized": bot_app is not None
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "components": {
            "flask": True,
            "telegram": TELEGRAM_AVAILABLE,
            "bot_app": bot_app is not None,
            "token": TOKEN is not None
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook robusto com debug"""
    try:
        # Verificar se temos dados
        json_data = request.get_json()
        if not json_data:
            logger.error("❌ Webhook: Dados JSON vazios")
            return "NO DATA", 400
        
        # Verificar se o bot está disponível
        if not bot_app:
            logger.error("❌ Webhook: Bot não inicializado")
            return "BOT NOT INITIALIZED", 500
        
        if not bot_app.bot:
            logger.error("❌ Webhook: Bot.bot não disponível")
            return "BOT.BOT NOT AVAILABLE", 500
        
        # Processar update
        logger.info(f"📨 Webhook: Processando update {json_data.get('update_id', 'unknown')}")
        
        update = Update.de_json(json_data, bot_app.bot)
        
        # Processar update de forma síncrona para teste
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(bot_app.process_update(update))
            logger.info("✅ Webhook: Update processado com sucesso")
        finally:
            loop.close()
        
        return "OK"
        
    except Exception as e:
        logger.error(f"❌ Webhook erro: {type(e).__name__}: {str(e)}")
        return f"ERROR: {str(e)}", 500

@app.route('/test')
def test():
    """Endpoint de teste"""
    return jsonify({
        "message": "Webhook Fix V3 funcionando",
        "bot_status": "initialized" if bot_app else "not_initialized",
        "telegram_lib": "available" if TELEGRAM_AVAILABLE else "not_available"
    })

if __name__ == "__main__":
    print("🔧 Webhook Fix V3 - Teste alternativo")
    print(f"🤖 Bot: {'✅ OK' if bot_app else '❌ Falha'}")
    print(f"📡 Telegram Lib: {'✅ OK' if TELEGRAM_AVAILABLE else '❌ Falha'}")
    print(f"🔑 Token: {'✅ OK' if TOKEN else '❌ Falha'}")
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True) 