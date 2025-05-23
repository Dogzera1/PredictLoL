import os
import json
import logging
import asyncio
import threading
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request, Response
import traceback

# RAILWAY REDEPLOY FORCE - 2025.05.23 - FIX EVENT LOOP
print("🚀 INICIANDO BOT COM CORREÇÃO DE EVENT LOOP - v2025.05.23")

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
application_initialized = False
background_loop = None
loop_thread = None

def run_background_loop(loop):
    """Executa o loop assíncrono em thread separada"""
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def initialize_application():
    """Inicializa a Application uma única vez"""
    global application, application_initialized
    
    if application_initialized:
        return True
    
    if not TOKEN:
        logger.error("❌ TOKEN não encontrado - configure a variável TELEGRAM_TOKEN")
        return False
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Registrar os handlers
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("ajuda", help_handler))
        application.add_handler(CommandHandler("help", help_handler))
        application.add_handler(CommandHandler("sobre", about_handler))
        application.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))
        
        # IMPORTANTE: Inicializar a Application
        await application.initialize()
        application_initialized = True
        
        logger.info("✅ Bot inicializado com sucesso no Railway!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar bot: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Função para processar updates
async def process_update_async(update_data):
    try:
        if not application or not application_initialized:
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

def process_webhook_sync(payload):
    """Processa webhook de forma síncrona usando o background loop"""
    global background_loop
    
    if background_loop and not background_loop.is_closed():
        future = asyncio.run_coroutine_threadsafe(
            process_update_async(payload), 
            background_loop
        )
        try:
            # Aguardar no máximo 10 segundos
            future.result(timeout=10)
        except Exception as e:
            logger.error(f"❌ Erro no processamento assíncrono: {e}")
    else:
        logger.error("❌ Background loop não disponível")

# Rotas da aplicação
@app.route('/', methods=['GET'])
def home():
    status = "🟢 ATIVO" if application_initialized else "🔴 INATIVO"
    token_status = "✅ Configurado" if TOKEN else "❌ Não configurado"
    loop_status = "✅ Ativo" if background_loop and not background_loop.is_closed() else "❌ Inativo"
    
    return f"""
    <h1>🤖 Bot LoL - Railway</h1>
    <p><strong>Status:</strong> {status}</p>
    <p><strong>Token:</strong> {token_status}</p>
    <p><strong>Loop:</strong> {loop_status}</p>
    <p><strong>Webhook:</strong> /webhook</p>
    <p><strong>Bot:</strong> @BETLOLGPT_bot</p>
    <hr>
    <p>✅ Funcionando no Railway!</p>
    """

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de saúde"""
    loop_healthy = background_loop and not background_loop.is_closed()
    
    if application_initialized and TOKEN and loop_healthy:
        return {
            "status": "healthy", 
            "bot": "active", 
            "platform": "railway",
            "token": "configured",
            "initialized": application_initialized,
            "loop": "active",
            "version": "2025.05.23-event-loop-fix",
            "background_thread": loop_thread.is_alive() if loop_thread else False
        }, 200
    else:
        reason = "Token não configurado"
        if not application_initialized:
            reason = "Application não inicializada"
        elif not loop_healthy:
            reason = "Background loop não ativo"
            
        return {
            "status": "unhealthy", 
            "bot": "inactive", 
            "platform": "railway",
            "reason": reason,
            "initialized": application_initialized,
            "loop": "active" if loop_healthy else "inactive",
            "version": "2025.05.23-event-loop-fix",
            "background_thread": loop_thread.is_alive() if loop_thread else False
        }, 500

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == "GET":
        status = "🟢 ATIVO" if application_initialized else "🔴 INATIVO"
        return f"🤖 Webhook do Bot LoL está {status}!"
    
    elif request.method == "POST":
        try:
            if not application or not application_initialized:
                logger.error("❌ Bot não inicializado - verificar TOKEN")
                return Response("❌ Bot não inicializado", status=500)
            
            payload = request.get_json()
            if not payload:
                logger.warning("⚠️ Payload vazio recebido")
                return Response("❌ Payload inválido", status=400)
            
            logger.info(f"📨 Recebido update do Telegram")
            
            # Processar usando background loop
            process_webhook_sync(payload)
            
            return Response('✅ OK', status=200)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar webhook: {str(e)}")
            logger.error(traceback.format_exc())
            return Response('✅ OK', status=200)  # Sempre retorna OK para evitar reenvios

# Inicialização da aplicação no startup
def initialize_bot_sync():
    """Função para inicializar o bot e background loop"""
    global background_loop, loop_thread
    
    try:
        # Criar loop para thread separada
        background_loop = asyncio.new_event_loop()
        
        # Iniciar thread com o loop
        loop_thread = threading.Thread(
            target=run_background_loop, 
            args=(background_loop,),
            daemon=True
        )
        loop_thread.start()
        
        # Inicializar o bot no background loop
        future = asyncio.run_coroutine_threadsafe(
            initialize_application(), 
            background_loop
        )
        
        # Aguardar inicialização
        success = future.result(timeout=30)
        
        if success:
            logger.info("✅ Background loop e bot inicializados")
        else:
            logger.error("❌ Falha na inicialização do bot")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        return False

if __name__ == "__main__":
    # Para Railway, usar a porta do ambiente ou 8080 como padrão
    port = int(os.environ.get("PORT", 8080))
    
    print("🚂 Iniciando Bot LoL no Railway...")
    print(f"🔧 Porta: {port}")
    print(f"🤖 Token configurado: {'✅' if TOKEN else '❌'}")
    
    # Inicializar o bot antes de iniciar o Flask
    bot_success = initialize_bot_sync()
    print(f"📡 Bot inicializado: {'✅' if bot_success else '❌'}")
    
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        exit(1)
    finally:
        # Cleanup do loop ao encerrar
        if background_loop and not background_loop.is_closed():
            background_loop.call_soon_threadsafe(background_loop.stop) 