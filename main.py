import os
import json
import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request, Response
import traceback

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Criar a aplicação Flask
app = Flask(__name__)

# Token do Telegram (da variável de ambiente)
TOKEN = os.environ.get("TELEGRAM_TOKEN")

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

🔧 Status: Funcionando no Railway
🌐 Hospedagem: 24/7 online
    """
    await update.message.reply_text(mensagem, parse_mode="Markdown")

async def unknown_command_handler(update, context):
    await update.message.reply_text("❌ Comando não reconhecido. Use /ajuda para ver os comandos disponíveis.")

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
        
        logger.info("✅ Bot inicializado com sucesso no Railway!")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar bot: {str(e)}")
        logger.error(traceback.format_exc())
else:
    logger.error("❌ TOKEN não encontrado - configure a variável TELEGRAM_TOKEN")

# Função para processar updates
async def process_update_async(update_data):
    try:
        if not application:
            logger.error("❌ Application não inicializada")
            return
        
        update = Update.de_json(data=update_data, bot=application.bot)
        if update:
            await application.process_update(update)
            logger.info("✅ Update processado com sucesso")
        else:
            logger.warning("⚠️ Update inválido recebido")
    except Exception as e:
        logger.error(f"❌ Erro ao processar update: {str(e)}")
        logger.error(traceback.format_exc())

# Rotas da aplicação
@app.route('/', methods=['GET'])
def home():
    status = "🟢 ATIVO" if application else "🔴 INATIVO"
    token_status = "✅ Configurado" if TOKEN else "❌ Não configurado"
    
    return f"""
    <h1>🤖 Bot LoL - Railway</h1>
    <p><strong>Status:</strong> {status}</p>
    <p><strong>Token:</strong> {token_status}</p>
    <p><strong>Webhook:</strong> /webhook</p>
    <p><strong>Bot:</strong> @BETLOLGPT_bot</p>
    <hr>
    <p>✅ Funcionando no Railway!</p>
    """

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de saúde"""
    if application and TOKEN:
        return {
            "status": "healthy", 
            "bot": "active", 
            "platform": "railway",
            "token": "configured"
        }, 200
    else:
        return {
            "status": "unhealthy", 
            "bot": "inactive", 
            "platform": "railway",
            "reason": "Token não configurado"
        }, 500

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == "GET":
        status = "🟢 ATIVO" if application else "🔴 INATIVO"
        return f"🤖 Webhook do Bot LoL está {status}!"
    
    elif request.method == "POST":
        try:
            if not application:
                logger.error("❌ Bot não inicializado - verificar TOKEN")
                return Response("❌ Bot não inicializado", status=500)
            
            payload = request.get_json()
            if not payload:
                logger.warning("⚠️ Payload vazio recebido")
                return Response("❌ Payload inválido", status=400)
            
            logger.info(f"📨 Recebido update do Telegram")
            
            # Processar update de forma assíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update_async(payload))
            loop.close()
            
            return Response('✅ OK', status=200)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar webhook: {str(e)}")
            logger.error(traceback.format_exc())
            return Response('✅ OK', status=200)  # Sempre retorna OK para evitar reenvios

if __name__ == "__main__":
    # Para Railway, usar a porta do ambiente ou 8080 como padrão
    port = int(os.environ.get("PORT", 8080))
    
    print("🚂 Iniciando Bot LoL no Railway...")
    print(f"🔧 Porta: {port}")
    print(f"🤖 Token configurado: {'✅' if TOKEN else '❌'}")
    print(f"📡 Bot inicializado: {'✅' if application else '❌'}")
    
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        exit(1) 