#!/usr/bin/env python3
"""
Bot LoL V3 em Modo Webhook Local
Solução alternativa para contornar conflitos de polling
"""
import asyncio
import logging
from quart import Quart, request, Response
import json
import signal
import sys
import os

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import da aplicação principal
try:
    from main import BotApplication
except ImportError:
    logger.error("Erro ao importar BotApplication. Verifique se main.py existe.")
    sys.exit(1)

# Configurações
WEBHOOK_HOST = "127.0.0.1"
WEBHOOK_PORT = 8443
WEBHOOK_PATH = f"/bot_webhook"
WEBHOOK_URL = f"http://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_PATH}"
BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"

# Aplicação web para webhook
app = Quart(__name__)

# Instância global do bot
bot_app = None

class WebhookBotRunner:
    def __init__(self):
        self.bot_app = None
        self.is_running = False
        
    async def initialize_bot(self):
        """Inicializa a aplicação do bot"""
        try:
            logger.info("🚀 Inicializando Bot LoL V3 em modo webhook...")
            
            # Cria aplicação principal
            self.bot_app = BotApplication()
            
            # Inicializa todos os componentes EXCETO a interface Telegram
            logger.info("🔧 Inicializando componentes do sistema...")
            await self.bot_app._initialize_components()
            
            # Inicializa apenas o ScheduleManager
            logger.info("⚙️ Iniciando ScheduleManager...")
            await self.bot_app.schedule_manager.start_scheduled_tasks()
            
            # Configura webhook
            await self._setup_webhook()
            
            self.is_running = True
            logger.info("✅ Bot inicializado em modo webhook!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar bot: {e}")
            return False
    
    async def _setup_webhook(self):
        """Configura webhook do Telegram"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                # Remove webhook existente
                async with session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook") as resp:
                    logger.info("🔗 Webhook anterior removido")
                
                # Configura novo webhook
                webhook_data = {
                    "url": WEBHOOK_URL,
                    "allowed_updates": ["message", "callback_query"]
                }
                
                async with session.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
                    json=webhook_data
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Webhook configurado: {WEBHOOK_URL}")
                    else:
                        logger.error(f"❌ Erro ao configurar webhook: {resp.status}")
                        
        except Exception as e:
            logger.error(f"❌ Erro ao configurar webhook: {e}")
    
    async def process_update(self, update_data):
        """Processa update do Telegram"""
        try:
            if not self.bot_app or not self.bot_app.bot_interface:
                logger.warning("⚠️ Bot não inicializado")
                return
            
            # Simula processamento de update
            # Em implementação completa, seria integrado com a interface do bot
            logger.info(f"📨 Update recebido: {update_data.get('update_id', 'unknown')}")
            
            # Aqui você integraria com os handlers do bot
            # self.bot_app.bot_interface._process_update(update_data)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar update: {e}")
    
    async def stop(self):
        """Para o bot"""
        if self.bot_app:
            await self.bot_app.stop()
        self.is_running = False
        logger.info("🛑 Bot parado")

# Instância global
webhook_runner = WebhookBotRunner()

@app.route(WEBHOOK_PATH, methods=['POST'])
async def webhook_handler():
    """Handler do webhook"""
    try:
        update_data = await request.get_json()
        
        if update_data:
            await webhook_runner.process_update(update_data)
            return Response("OK", status=200)
        else:
            return Response("No data", status=400)
            
    except Exception as e:
        logger.error(f"❌ Erro no webhook handler: {e}")
        return Response("Error", status=500)

@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "running" if webhook_runner.is_running else "stopped",
        "webhook_url": WEBHOOK_URL,
        "bot_initialized": webhook_runner.bot_app is not None
    }
    return Response(json.dumps(status), content_type='application/json')

@app.route('/status', methods=['GET'])
async def status_endpoint():
    """Status detalhado do sistema"""
    try:
        if webhook_runner.bot_app:
            system_status = webhook_runner.bot_app.schedule_manager.get_system_status()
            return Response(json.dumps(system_status, default=str), content_type='application/json')
        else:
            return Response(json.dumps({"error": "Bot not initialized"}), status=503)
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500)

async def start_webhook_bot():
    """Inicia o bot em modo webhook"""
    print("🚀 BOT LOL V3 - MODO WEBHOOK LOCAL")
    print("=" * 50)
    print(f"🌐 Webhook URL: {WEBHOOK_URL}")
    print(f"🏥 Health Check: http://{WEBHOOK_HOST}:{WEBHOOK_PORT}/health")
    print(f"📊 Status: http://{WEBHOOK_HOST}:{WEBHOOK_PORT}/status")
    print("=" * 50)
    
    # Inicializa o bot
    success = await webhook_runner.initialize_bot()
    
    if success:
        print("✅ Bot inicializado com sucesso!")
        print("📱 Testando no Telegram...")
        print("💡 Use Ctrl+C para parar")
        
        # Configura handler de shutdown
        def signal_handler(signum, frame):
            logger.info("📋 Recebido sinal de shutdown...")
            asyncio.create_task(webhook_runner.stop())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Inicia servidor web
        await app.run_task(host=WEBHOOK_HOST, port=WEBHOOK_PORT)
    else:
        print("❌ Falha ao inicializar bot")
        return False

def main():
    """Função principal"""
    try:
        asyncio.run(start_webhook_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot parado pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")

if __name__ == "__main__":
    main() 