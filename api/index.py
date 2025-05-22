import os
import json
import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request
import traceback

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token do Telegram
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo")

# Criar aplicação Flask
app = Flask(__name__)

# Handlers do bot
async def start_handler(update, context):
    await update.message.reply_text("✅ Bot ativo! Use /ajuda para ver os comandos disponíveis.")

async def help_handler(update, context):
    mensagem = """
📋 *Comandos disponíveis:*
/start - Iniciar o bot
/ajuda - Mostrar esta ajuda
/sobre - Informações sobre o bot

_Bot em manutenção, mais funcionalidades em breve!_
    """
    await update.message.reply_text(mensagem, parse_mode="Markdown")

async def about_handler(update, context):
    mensagem = """
*LoL-GPT Betting Assistant* 🎮

Um bot para ajudar em apostas de League of Legends, usando modelos preditivos.
    """
    await update.message.reply_text(mensagem, parse_mode="Markdown")

# Inicializar bot
application = None
if TOKEN:
    try:
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("ajuda", help_handler))
        application.add_handler(CommandHandler("help", help_handler))
        application.add_handler(CommandHandler("sobre", about_handler))
        logger.info("Bot inicializado")
    except Exception as e:
        logger.error(f"Erro ao inicializar bot: {e}")

# Função para processar updates
async def process_update_async(update_data):
    try:
        if not application:
            return
        update = Update.de_json(data=update_data, bot=application.bot)
        if update:
            await application.process_update(update)
    except Exception as e:
        logger.error(f"Erro ao processar update: {e}")

@app.route('/')
def home():
    return f"Bot LoL ativo! Token: {'configurado' if TOKEN else 'não configurado'}"

@app.route('/api/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == "GET":
        return "Webhook ativo!"
    
    try:
        if not application:
            return "Bot não inicializado", 500
        
        payload = request.get_json()
        if not payload:
            return "Payload inválido", 400
        
        # Processar update
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_update_async(payload))
        loop.close()
        
        return "OK"
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return "OK"  # Sempre retorna OK para evitar reenvios

# Handler para Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None) 