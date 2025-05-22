import os
import json
from http.server import BaseHTTPRequestHandler
import asyncio
import logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler

# Token do bot
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handlers do bot
async def start_handler(update, context):
    await update.message.reply_text("✅ Bot ativo! Use /ajuda para ver os comandos disponíveis.")

async def help_handler(update, context):
    mensagem = """
📋 *Comandos disponíveis:*
/start - Iniciar o bot
/ajuda - Mostrar esta ajuda
/sobre - Informações sobre o bot
    """
    await update.message.reply_text(mensagem, parse_mode="Markdown")

# Inicializar aplicação do bot
application = None
if TOKEN:
    try:
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("ajuda", help_handler))
        application.add_handler(CommandHandler("help", help_handler))
        logger.info("Bot inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar bot: {e}")

async def process_update(update_data):
    """Processa um update do Telegram"""
    try:
        if not application:
            logger.error("Application não inicializada")
            return
        
        update = Update.de_json(data=update_data, bot=application.bot)
        if update:
            await application.process_update(update)
            logger.info("Update processado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao processar update: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Bot LoL ativo!')
        elif self.path == '/api/webhook':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Webhook ativo!')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests (webhook)"""
        if self.path == '/api/webhook':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                update_data = json.loads(post_data.decode('utf-8'))
                
                if application:
                    # Processar update de forma assíncrona
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(process_update(update_data))
                    loop.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'OK')
            except Exception as e:
                logger.error(f"Erro no webhook: {e}")
                self.send_response(200)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers() 