import os
import json
import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request, Response
import traceback

# Configuração de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar a aplicação Flask
app = Flask(__name__)

# Token do Telegram (da variável de ambiente ou fallback)
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo")

# Handlers simples para comandos básicos
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

async def unknown_command_handler(update, context):
    await update.message.reply_text("Comando não reconhecido. Use /ajuda para ver os comandos disponíveis.")

# Inicializar o bot
application = None
if TOKEN:
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Registrar os handlers
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("ajuda", help_handler))
        application.add_handler(CommandHandler("help", help_handler))
        application.add_handler(CommandHandler("sobre", about_handler))
        application.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))
        
        logger.info("Bot inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar bot: {str(e)}")
        logger.error(traceback.format_exc())
else:
    logger.error("TOKEN não encontrado")

# Função para processar update de forma assíncrona
async def process_update_async(update_data):
    try:
        if not application:
            logger.error("Application não inicializada")
            return
        
        update = Update.de_json(data=update_data, bot=application.bot)
        if update:
            await application.process_update(update)
            logger.info("Update processado com sucesso")
        else:
            logger.warning("Update inválido recebido")
    except Exception as e:
        logger.error(f"Erro ao processar update: {str(e)}")
        logger.error(traceback.format_exc())

# Rotas da aplicação
@app.route('/', methods=['GET'])
def home():
    status = "ativo" if application else "inativo (verificar TOKEN)"
    token_status = "configurado" if TOKEN else "não configurado"
    return Response(f"Bot de LoL {status}! Token: {token_status}. Use /api/webhook para o endpoint do Telegram.", status=200)

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de saúde para verificar status do bot"""
    if application and TOKEN:
        return {"status": "healthy", "bot": "active", "token": "configured"}, 200
    else:
        return {"status": "unhealthy", "bot": "inactive", "token": "missing" if not TOKEN else "configured"}, 500

@app.route('/api/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == "GET":
        status = "ativo" if application else "inativo"
        return Response(f'Bot de apostas LoL está {status}! Endpoint de webhook configurado.', status=200)
    
    elif request.method == "POST":
        try:
            # Verificar se o bot foi inicializado corretamente
            if not application:
                logger.error("Bot não inicializado - verificar TOKEN")
                return Response("Configuração do bot incompleta", status=500)
            
            # Obter dados do update
            payload = request.get_json()
            if not payload:
                logger.warning("Payload vazio recebido")
                return Response("Payload inválido", status=400)
            
            logger.info(f"Recebido update: {json.dumps(payload, ensure_ascii=False)[:200]}...")
            
            # Processar update de forma assíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update_async(payload))
            loop.close()
            
            return Response('ok', status=200)
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {str(e)}")
            logger.error(traceback.format_exc())
            return Response('ok', status=200)  # Retorna 200 mesmo com erro para evitar reenvios

# Para debugging local
if __name__ == "__main__":
    app.run(debug=True, port=5000) 