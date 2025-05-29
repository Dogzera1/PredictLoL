#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT DIAGNÓSTICO RAILWAY - Versão mínima para testar /start
Identifica onde está o problema real
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações básicas
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')
PORT = int(os.getenv('PORT', 5800))

logger.info("🔍 DIAGNÓSTICO: Configurações carregadas")

# Flask para health check
app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check simplificado"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'bot_diagnostico',
        'test': 'railway_debug'
    }), 200

@app.route('/')
def root():
    return jsonify({'message': 'Bot Diagnóstico Railway', 'status': 'online'}), 200

logger.info("🔍 DIAGNÓSTICO: Flask configurado")

# Testar imports do Telegram
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
    logger.info("✅ DIAGNÓSTICO: Imports telegram OK")
except Exception as e:
    logger.error(f"❌ DIAGNÓSTICO: Erro nos imports telegram: {e}")

# Classe de bot mínima
class BotDiagnostico:
    def __init__(self):
        logger.info("🔍 DIAGNÓSTICO: Inicializando bot...")

    def start_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /start de teste"""
        logger.info("🔍 DIAGNÓSTICO: Comando /start executado")
        try:
            user = update.effective_user
            message = f"""
🔍 **BOT DIAGNÓSTICO RAILWAY** 🔍

Olá {user.first_name}! 👋

✅ **TESTES REALIZADOS:**
• Telegram API: Funcionando
• Webhook: Ativo
• Railway: Conectado
• /start: Sucesso

🎯 **PRÓXIMOS PASSOS:**
Se você está vendo esta mensagem, o problema não é nos imports básicos.

Timestamp: {datetime.now().strftime('%H:%M:%S')}
            """
            
            update.message.reply_text(message, parse_mode="Markdown")
            logger.info("✅ DIAGNÓSTICO: Resposta enviada com sucesso")
            
        except Exception as e:
            logger.error(f"❌ DIAGNÓSTICO: Erro no /start: {e}")
            try:
                update.message.reply_text(f"❌ Erro de diagnóstico: {str(e)}")
            except:
                pass

def main():
    """Função principal de diagnóstico"""
    try:
        logger.info("🔍 DIAGNÓSTICO: Iniciando main()")
        
        # Verificar ambiente
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME'))
        logger.info(f"🔍 DIAGNÓSTICO: Ambiente Railway: {is_railway}")
        
        # Inicializar bot
        bot_diag = BotDiagnostico()
        
        # Configurar updater
        logger.info("🔍 DIAGNÓSTICO: Configurando updater...")
        updater = Updater(TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Handler básico
        dispatcher.add_handler(CommandHandler("start", bot_diag.start_command))
        logger.info("✅ DIAGNÓSTICO: Handler /start adicionado")
        
        if is_railway:
            # Modo Railway - Webhook
            logger.info("🔍 DIAGNÓSTICO: Configurando webhook Railway...")
            
            webhook_path = "/webhook"
            
            @app.route(webhook_path, methods=['POST'])
            def webhook_debug():
                try:
                    from flask import request
                    from telegram import Update
                    
                    update_data = request.get_json(force=True)
                    logger.info(f"🔍 DIAGNÓSTICO: Webhook recebeu dados: {bool(update_data)}")
                    
                    if update_data:
                        update_obj = Update.de_json(update_data, updater.bot)
                        dispatcher.process_update(update_obj)
                        logger.info("✅ DIAGNÓSTICO: Update processado")
                    
                    return "OK", 200
                except Exception as e:
                    logger.error(f"❌ DIAGNÓSTICO: Erro no webhook: {e}")
                    return "ERROR", 500
            
            # Configurar webhook
            railway_url = os.getenv('RAILWAY_STATIC_URL', f"https://{os.getenv('RAILWAY_SERVICE_NAME', 'bot')}.railway.app")
            if not railway_url.startswith('http'):
                railway_url = f"https://{railway_url}"
            webhook_url = f"{railway_url}{webhook_path}"
            
            logger.info(f"🔍 DIAGNÓSTICO: URL do webhook: {webhook_url}")
            
            try:
                updater.bot.delete_webhook(drop_pending_updates=True)
                updater.bot.set_webhook(webhook_url)
                logger.info("✅ DIAGNÓSTICO: Webhook configurado")
            except Exception as e:
                logger.error(f"❌ DIAGNÓSTICO: Erro ao configurar webhook: {e}")
            
            # Iniciar Flask
            logger.info("🔍 DIAGNÓSTICO: Iniciando Flask...")
            app.run(host='0.0.0.0', port=PORT, debug=False)
            
        else:
            # Modo Local - Polling
            logger.info("🔍 DIAGNÓSTICO: Modo local - polling")
            updater.start_polling()
            updater.idle()
            
    except Exception as e:
        logger.error(f"❌ DIAGNÓSTICO: Erro crítico: {e}")
        import traceback
        logger.error(f"❌ DIAGNÓSTICO: Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 