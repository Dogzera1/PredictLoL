import os, logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request, Response

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criação da aplicação Flask - ponto de entrada para Vercel
app = Flask(__name__)

# Handlers simples
async def start_handler(update, context):
    await update.message.reply_text("✅ Bot ativo! Use /ajuda para ver os comandos disponíveis.")

async def help_handler(update, context):
    await update.message.reply_text("📋 Comandos: /start, /ajuda, /sobre")

async def about_handler(update, context):
    await update.message.reply_text("LoL-GPT Betting Assistant - Bot para apostas em LoL")

# Token do Telegram
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    try:
        from config import BOT_TOKEN
        TOKEN = BOT_TOKEN
    except:
        pass

# Inicialização do bot
application = None
if TOKEN:
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Registrar os handlers básicos
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("ajuda", help_handler))
        application.add_handler(CommandHandler("help", help_handler))
        application.add_handler(CommandHandler("sobre", about_handler))
    except Exception as e:
        logger.error(f"Erro: {str(e)}")

# Rotas da aplicação
@app.route('/', methods=['GET'])
def home():
    return "Bot ativo!"

@app.route('/api/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == "GET":
        return Response('OK', status=200)
    
    elif request.method == "POST":
        try:
            if not application:
                return Response("Configuração incompleta", status=500)
            
            payload = request.get_json()
            if not payload:
                return Response("Payload inválido", status=400)
            
            update = Update.de_json(data=payload, bot=application.bot)
            if update:
                application.process_update(update)
                return Response('ok', status=200)
            else:
                return Response("Update inválido", status=400)
        except Exception as e:
            logger.error(f"Erro: {str(e)}")
            return Response('ok', status=200)

# Handler para Vercel
handler = app 