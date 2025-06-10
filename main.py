#!/usr/bin/env python3
"""
PredictLoL - Sistema Integrado de Apostas e Previsões
Desenvolvido para auxílio em apostas pessoais + previsões pós-draft
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Configurações básicas
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PredictLoLBot:
    """Sistema integrado PredictLoL"""
    
    def __init__(self):
        self.personal_betting = None
        self.telegram_bot = None
        self.is_running = False
        
        logger.info("🚀 PredictLoL System - Inicializando...")
        
    async def initialize(self):
        """Inicializa componentes do sistema"""
        try:
            # 1. Sistema de Apostas Pessoais
            from bot.personal_betting import PersonalBettingSystem
            self.personal_betting = PersonalBettingSystem()
            logger.info("✅ Sistema de Apostas Pessoais inicializado")
            
            # 2. Bot Telegram
            from bot.telegram_bot.predictlol_bot import PredictLoLTelegramBot
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN não encontrado nas variáveis de ambiente")
            
            self.telegram_bot = PredictLoLTelegramBot(
                token=bot_token,
                personal_betting=self.personal_betting
            )
            await self.telegram_bot.initialize()
            logger.info("✅ Bot Telegram inicializado")
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            raise
    
    async def start(self):
        """Inicia o sistema"""
        if self.is_running:
            return
        
        try:
            await self.initialize()
            
            # Inicia bot Telegram
            if self.telegram_bot:
                await self.telegram_bot.start()
                logger.info("🤖 Bot Telegram iniciado e funcionando")
            
            self.is_running = True
            logger.info("🎯 PredictLoL System ATIVO e funcionando!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sistema: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Para o sistema"""
        if not self.is_running:
            return
        
        logger.info("🛑 Parando PredictLoL System...")
        
        if self.telegram_bot:
            await self.telegram_bot.stop()
        
        self.is_running = False
        logger.info("✅ Sistema parado")

async def main():
    """Função principal"""
    bot = PredictLoLBot()
    
    try:
        await bot.start()
        
        # Mantém o bot rodando
        while bot.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🔴 Interrupção pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Para Railway/produção
    if "PORT" in os.environ:
        # Health check simples para Railway
        from threading import Thread
        import http.server
        import socketserver
        
        PORT = int(os.environ.get("PORT", 8000))
        
        class HealthHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "ok", "service": "PredictLoL"}')
                else:
                    self.send_response(404)
                    self.end_headers()
        
        def start_health_server():
            with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
                logger.info(f"🏥 Health server rodando na porta {PORT}")
                httpd.serve_forever()
        
        # Inicia health server em thread separada
        health_thread = Thread(target=start_health_server, daemon=True)
        health_thread.start()
    
    # Inicia o bot
    asyncio.run(main()) 