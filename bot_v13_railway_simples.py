#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT LOL V3 SIMPLIFICADO - Sem ML e Threading para Railway
Versão para identificar problemas específicos
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import pytz

# VERIFICAÇÃO CRÍTICA DE CONFLITOS NO INÍCIO
def early_conflict_check():
    """Verificação precoce de conflitos antes de importar bibliotecas pesadas"""
    # Verificar se é Railway
    is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))

    if not is_railway:
        print("⚠️ EXECUTANDO EM MODO LOCAL - VERIFICANDO CONFLITOS...")
        # Verificar arquivo de lock existente
        import tempfile
        lock_file = os.path.join(tempfile.gettempdir(), 'bot_lol_v3_simples.lock')

        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                # Verificar se processo ainda existe
                try:
                    if os.name == 'nt':  # Windows
                        import subprocess
                        result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'],
                                              capture_output=True, text=True)
                        if str(old_pid) in result.stdout:
                            print(f"🚨 OUTRA INSTÂNCIA DETECTADA! PID: {old_pid}")
                            print("🛑 ABORTANDO PARA EVITAR CONFLITOS!")
                            sys.exit(1)
                    else:  # Unix/Linux
                        os.kill(old_pid, 0)  # Não mata, só verifica
                        print(f"🚨 OUTRA INSTÂNCIA DETECTADA! PID: {old_pid}")
                        print("🛑 ABORTANDO PARA EVITAR CONFLITOS!")
                        sys.exit(1)
                except OSError:
                    # Processo não existe mais, remover lock
                    os.remove(lock_file)
                    print("🧹 Lock antigo removido (processo morto)")
            except:
                # Arquivo corrompido, remover
                try:
                    os.remove(lock_file)
                except:
                    pass
        print("✅ Verificação precoce de conflitos OK")

# Executar verificação precoce
early_conflict_check()

# Flask para health check
from flask import Flask, jsonify, request
import requests

# Telegram imports v13
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.error import TelegramError

import numpy as np
import aiohttp

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')
OWNER_ID = int(os.getenv('OWNER_ID', '6404423764'))
PORT = int(os.getenv('PORT', 5800))

# Flask app para healthcheck
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/health')
def health_check():
    """Health check para Railway"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'bot_lol_v3_simples',
            'version': 'v13_webhook_simples',
            'port': PORT,
            'environment': 'railway' if os.getenv('RAILWAY_ENVIRONMENT_NAME') else 'local'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/')
def root():
    """Rota raiz"""
    try:
        return jsonify({
            'message': 'BOT LOL V3 SIMPLES - Sem ML/Threading',
            'status': 'online',
            'health_check': '/health',
            'webhook': '/webhook'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/ping')
def ping():
    """Ping simples"""
    return "pong", 200

class LoLBotV3Simples:
    """Bot LoL V3 Versão Simplificada - Sem ML e Threading"""

    def __init__(self):
        logger.info("🤖 Bot LoL V3 Simples inicializado")

    def start_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /start"""
        user = update.effective_user
        welcome_message = f"""
🎮 **BOT LOL V3 SIMPLES** 🎮

Olá {user.first_name}! 👋

✅ **VERSÃO SIMPLIFICADA FUNCIONANDO:**
• Telegram API: OK
• Webhook: Ativo  
• Railway: Conectado
• /start: Sucesso

🔧 **TESTES REALIZADOS:**
• Sem Machine Learning
• Sem Threading
• Apenas funcionalidades básicas

⏰ Timestamp: {datetime.now().strftime('%H:%M:%S')}

Se este bot funciona, o problema está no ML ou Threading.
        """

        keyboard = [
            [InlineKeyboardButton("✅ Teste OK", callback_data="test_ok")],
            [InlineKeyboardButton("🔧 Diagnóstico", callback_data="diagnostico")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")

    def callback_handler(self, update: Update, context: CallbackContext) -> None:
        """Handler para callbacks dos botões"""
        query = update.callback_query
        query.answer()

        if query.data == "test_ok":
            query.edit_message_text("✅ **TESTE CONFIRMADO!**\n\nO bot básico funciona. O problema está no ML ou Threading do bot principal.")
        elif query.data == "diagnostico":
            query.edit_message_text("🔧 **DIAGNÓSTICO:**\n\n• Bot básico: ✅ OK\n• Telegram: ✅ OK\n• Webhook: ✅ OK\n\n❌ Problema: ML ou Threading")

def main():
    """Função principal"""
    try:
        logger.info("🎮 INICIANDO BOT LOL V3 SIMPLES")
        logger.info("=" * 50)
        logger.info("🔧 VERSÃO DE TESTE - SEM ML/THREADING")
        logger.info("=" * 50)

        # Inicializar bot
        bot_instance = LoLBotV3Simples()

        # Verificar modo de execução
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))

        logger.info(f"🔍 Modo detectado: {'🚀 RAILWAY (webhook)' if is_railway else '🏠 LOCAL (polling)'}")

        # Versão v13
        updater = Updater(TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        # Limpar webhook existente
        try:
            logger.info("🧹 Limpando webhook existente...")
            updater.bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Webhook anterior removido")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao limpar webhook: {e}")

        # Handlers
        dispatcher.add_handler(CommandHandler("start", bot_instance.start_command))
        dispatcher.add_handler(CallbackQueryHandler(bot_instance.callback_handler))

        logger.info(f"✅ Handlers registrados no dispatcher v13")

        if is_railway:
            # Modo Railway - Webhook v13
            logger.info("🚀 Detectado ambiente Railway v13 - Configurando webhook")

            webhook_path = f"/webhook"

            @app.route(webhook_path, methods=['POST'])
            def webhook_v13():
                try:
                    update_data = request.get_json(force=True)
                    if update_data:
                        from telegram import Update
                        update_obj = Update.de_json(update_data, updater.bot)
                        dispatcher.process_update(update_obj)
                        logger.info(f"🔄 Webhook v13 processou atualização: {update_obj.update_id if update_obj else 'None'}")
                    return "OK", 200
                except Exception as e:
                    logger.error(f"❌ Erro no webhook v13: {e}")
                    return "ERROR", 500

            # Configurar webhook
            railway_url = os.getenv('RAILWAY_STATIC_URL', f"https://{os.getenv('RAILWAY_SERVICE_NAME', 'bot')}.railway.app")
            if not railway_url.startswith('http'):
                railway_url = f"https://{railway_url}"
            webhook_url = f"{railway_url}{webhook_path}"

            try:
                logger.info("🔄 Removendo webhook anterior v13...")
                updater.bot.delete_webhook(drop_pending_updates=True)
                time.sleep(2)

                logger.info(f"🔗 Configurando webhook v13: {webhook_url}")
                result = updater.bot.set_webhook(webhook_url)
                logger.info(f"✅ Webhook v13 configurado: {result}")

                webhook_info = updater.bot.get_webhook_info()
                logger.info(f"📋 Webhook v13 ativo: {webhook_info.url}")

                me = updater.bot.get_me()
                logger.info(f"🤖 Bot v13 verificado: @{me.username}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao configurar webhook v13: {e}")

            logger.info("✅ Bot configurado (Railway webhook v13) - Iniciando Flask...")

            app.config['ENV'] = 'production'
            app.config['DEBUG'] = False

            logger.info(f"🌐 Iniciando Flask v13 na porta {PORT}")
            logger.info(f"🔗 Webhook disponível em: {webhook_url}")

            app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

        else:
            # Modo Local - Polling v13
            logger.info("🏠 Ambiente local v13 detectado - Usando polling")

            logger.info("✅ Bot configurado (polling v13) - Iniciando...")

            try:
                updater.bot.delete_webhook(drop_pending_updates=True)
                logger.info("🧹 Webhook removido antes de iniciar polling v13")
            except Exception as e:
                logger.debug(f"Webhook já estava removido v13: {e}")

            logger.info("🔄 Iniciando polling v13...")
            updater.start_polling(drop_pending_updates=True)
            updater.idle()

    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        import traceback
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 