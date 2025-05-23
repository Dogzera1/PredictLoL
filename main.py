#!/usr/bin/env python3
"""
Bot LoL v2 - Arquitetura robusta sem problemas de event loop
"""

import os
import json
import logging
import asyncio
import threading
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request, Response
import traceback
from contextlib import asynccontextmanager

print("🚀 BOT LOL V2 - ARQUITETURA ROBUSTA INICIANDO")

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token do Telegram
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN não configurado!")

# Variáveis globais
application = None
bot_initialized = False

class TelegramBotManager:
    """Gerenciador robusto do bot Telegram"""
    
    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.bot = None
        self._lock = threading.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Inicializa o bot de forma segura"""
        with self._lock:
            if self._initialized:
                return True
            
            try:
                logger.info("🤖 Inicializando Bot Telegram...")
                
                # Criar aplicação com configurações robustas
                self.application = (
                    Application.builder()
                    .token(self.token)
                    .concurrent_updates(True)
                    .build()
                )
                
                # Obter referência do bot
                self.bot = self.application.bot
                
                # Testar conexão
                bot_info = await self.bot.get_me()
                logger.info(f"✅ Bot conectado: @{bot_info.username}")
                
                # Configurar handlers
                self._setup_handlers()
                
                # Inicializar aplicação
                await self.application.initialize()
                
                self._initialized = True
                logger.info("🎯 Bot inicializado com sucesso!")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Erro na inicialização: {e}")
                self._initialized = False
                return False
    
    def _setup_handlers(self):
        """Configura os handlers do bot"""
        
        # Handler para /start
        async def start_handler(update: Update, context):
            try:
                await update.message.reply_text(
                    "✅ Bot LoL V2 ativo!\n"
                    "🎮 Use /ajuda para ver comandos\n"
                    "🔧 Arquitetura robusta implementada"
                )
            except Exception as e:
                logger.error(f"Erro no start_handler: {e}")
        
        # Handler para /ajuda
        async def help_handler(update: Update, context):
            try:
                mensagem = """
📋 *Comandos disponíveis:*
/start - Iniciar o bot
/ajuda - Mostrar esta ajuda
/status - Status do sistema
/ping - Testar conexão

🎮 *Bot de apostas LoL*
📊 Modelo preditivo em desenvolvimento
🔧 Versão 2.0 - Arquitetura robusta
                """
                await update.message.reply_text(mensagem, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Erro no help_handler: {e}")
        
        # Handler para /status
        async def status_handler(update: Update, context):
            try:
                status = {
                    "Bot": "✅ Ativo",
                    "Versão": "2.0 - Robusta", 
                    "Platform": "Railway",
                    "Event Loop": "✅ Estável"
                }
                
                message = "\n".join([f"{k}: {v}" for k, v in status.items()])
                await update.message.reply_text(f"🔧 **STATUS DO SISTEMA**\n\n{message}")
            except Exception as e:
                logger.error(f"Erro no status_handler: {e}")
        
        # Handler para /ping
        async def ping_handler(update: Update, context):
            try:
                await update.message.reply_text("🏓 Pong! Bot respondendo normalmente.")
            except Exception as e:
                logger.error(f"Erro no ping_handler: {e}")
        
        # Handler para mensagens de texto
        async def text_handler(update: Update, context):
            try:
                text = update.message.text.lower()
                
                if "oi" in text or "olá" in text:
                    await update.message.reply_text("👋 Olá! Use /ajuda para ver comandos.")
                elif "aposta" in text:
                    await update.message.reply_text("🎮 Sistema de apostas em desenvolvimento!")
                else:
                    await update.message.reply_text("🤖 Não entendi. Use /ajuda para ver comandos.")
            except Exception as e:
                logger.error(f"Erro no text_handler: {e}")
        
        # Adicionar handlers
        self.application.add_handler(CommandHandler("start", start_handler))
        self.application.add_handler(CommandHandler("ajuda", help_handler))
        self.application.add_handler(CommandHandler("status", status_handler))
        self.application.add_handler(CommandHandler("ping", ping_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    async def process_update(self, update_data: dict) -> bool:
        """Processa um update de forma segura"""
        
        if not self._initialized:
            logger.warning("⚠️ Bot não inicializado para processar update")
            return False
        
        try:
            # Criar objeto Update
            update = Update.de_json(update_data, self.bot)
            
            if update:
                # Processar update
                await self.application.process_update(update)
                return True
            else:
                logger.warning("⚠️ Update inválido recebido")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar update: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Verifica se o bot está pronto"""
        return self._initialized and self.application is not None

# Instância global do gerenciador
bot_manager = TelegramBotManager(TOKEN)

# Flask App
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint do webhook"""
    try:
        # Verificar se bot está pronto
        if not bot_manager.is_ready():
            logger.error("❌ Bot não está pronto")
            return Response("Bot not ready", status=503)
        
        # Obter dados do update
        update_data = request.get_json()
        
        if not update_data:
            logger.warning("⚠️ Webhook sem dados")
            return Response("No data", status=400)
        
        # Processar update de forma assíncrona e segura
        def process_in_thread():
            """Processa update em thread separada"""
            try:
                # Criar novo event loop para esta thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Processar update
                success = loop.run_until_complete(
                    bot_manager.process_update(update_data)
                )
                
                # Fechar loop de forma limpa
                loop.close()
                
                if success:
                    logger.info("✅ Update processado com sucesso")
                else:
                    logger.error("❌ Falha ao processar update")
                    
            except Exception as e:
                logger.error(f"❌ Erro no processamento: {e}")
        
        # Executar em thread separada
        thread = threading.Thread(target=process_in_thread, daemon=True)
        thread.start()
        
        # Retornar resposta imediata
        return Response("OK", status=200)
        
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        return Response("Error", status=500)

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de saúde"""
    try:
        status = {
            "status": "healthy" if bot_manager.is_ready() else "initializing",
            "bot": "active" if bot_manager.is_ready() else "starting",
            "platform": "railway",
            "version": "2.0-robust",
            "token": "configured" if TOKEN else "missing",
            "event_loop": "stable"
        }
        
        status_code = 200 if bot_manager.is_ready() else 503
        return json.dumps(status), status_code, {'Content-Type': 'application/json'}
        
    except Exception as e:
        logger.error(f"❌ Erro no health check: {e}")
        return json.dumps({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Endpoint raiz"""
    return {
        "message": "🤖 Bot LoL V2 - Arquitetura Robusta",
        "status": "active" if bot_manager.is_ready() else "initializing",
        "version": "2.0"
    }

async def initialize_bot():
    """Inicializa o bot na startup"""
    logger.info("🚀 Inicializando Bot LoL V2...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            success = await bot_manager.initialize()
            
            if success:
                logger.info("✅ Bot inicializado com sucesso!")
                return True
            else:
                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou")
                
        except Exception as e:
            logger.error(f"❌ Erro na tentativa {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2)
    
    logger.error("❌ Falha na inicialização após todas as tentativas")
    return False

def run_initialization():
    """Executa a inicialização em thread separada"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(initialize_bot())
        logger.info(f"🎯 Inicialização concluída: {'✅' if success else '❌'}")
    finally:
        loop.close()

if __name__ == "__main__":
    print("🚂 Iniciando Bot LoL V2 no Railway...")
    print(f"🔧 Porta: {os.environ.get('PORT', '8080')}")
    print(f"🤖 Token configurado: {'✅' if TOKEN else '❌'}")
    
    # Inicializar bot em thread separada
    init_thread = threading.Thread(target=run_initialization, daemon=True)
    init_thread.start()
    
    # Aguardar um pouco para a inicialização
    import time
    time.sleep(3)
    
    # Executar Flask
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True) 