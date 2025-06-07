#!/usr/bin/env python3
"""
Bot LoL V3 - Versão Railway Simplificada
Foco em estabilidade e funcionamento básico
"""

import os
import sys
import asyncio
import threading
import time
from pathlib import Path

# Configurações de ambiente
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('TZ', 'America/Sao_Paulo')

# Adiciona o diretório do bot ao path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

# Health check em thread separada
def start_health_server():
    """Inicia servidor de health check"""
    try:
        from simple_health_check import run_server
        print("🏥 Iniciando health check server...")
        run_server()
    except Exception as e:
        print(f"⚠️ Erro no health check: {e}")

# Logger básico
class SimpleLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")
    
    def warning(self, msg):
        print(f"[WARN] {msg}")

logger = SimpleLogger()

class RailwayBot:
    """Bot simplificado para Railway"""
    
    def __init__(self):
        self.is_running = False
        self.alerts_system = None
        self.schedule_manager = None
        
    async def initialize(self):
        """Inicialização simplificada"""
        try:
            logger.info("🔧 Inicializando componentes essenciais...")
            
            # 1. Sistema de alertas Telegram
            try:
                from bot.telegram_bot.alerts_system import TelegramAlertsSystem
                logger.info("📱 Inicializando Telegram...")
                
                # Pega o token das variáveis de ambiente
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
                if not bot_token:
                    raise ValueError("TELEGRAM_BOT_TOKEN não configurado")
                
                self.alerts_system = TelegramAlertsSystem(bot_token=bot_token)
                await self.alerts_system.initialize()
                logger.info("✅ Telegram inicializado")
            except Exception as e:
                logger.error(f"❌ Erro Telegram: {e}")
                raise
            
            # 2. Schedule Manager
            try:
                from bot.systems.schedule_manager import ScheduleManager
                logger.info("⏰ Inicializando Schedule Manager...")
                self.schedule_manager = ScheduleManager(
                    alerts_system=self.alerts_system
                )
                logger.info("✅ Schedule Manager inicializado")
            except Exception as e:
                logger.error(f"❌ Erro Schedule Manager: {e}")
                raise
            
            logger.info("✅ Todos os componentes inicializados!")
            
        except Exception as e:
            logger.error(f"❌ Falha na inicialização: {e}")
            raise
    
    async def start(self):
        """Inicia o bot"""
        try:
            self.is_running = True
            
            # Inicializa componentes
            await self.initialize()
            
            # Inicia sistemas
            logger.info("🚀 Iniciando sistemas...")
            
            # Inicia tarefas agendadas
            if self.schedule_manager:
                await self.schedule_manager.start_scheduled_tasks()
                logger.info("📊 Sistema de tips ativo")
            
            logger.info("🎉 Bot LoL V3 iniciado com sucesso!")
            logger.info("📱 @BETLOLGPT_bot operacional")
            
            # Loop principal
            while self.is_running:
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"❌ Erro durante execução: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Para o bot"""
        if not self.is_running:
            return
            
        logger.info("🛑 Parando Bot...")
        self.is_running = False
        
        try:
            if self.schedule_manager:
                await self.schedule_manager.stop_scheduled_tasks()
                
            if self.alerts_system:
                await self.alerts_system.cleanup()
            
            logger.info("✅ Bot parado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar: {e}")

async def main():
    """Função principal"""
    try:
        # Validações básicas
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        admin_ids = os.getenv("TELEGRAM_ADMIN_USER_IDS", "")
        
        if not token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN não configurado!")
        
        logger.info("🔍 Ambiente Railway detectado")
        logger.info(f"🤖 Token: {token[:10]}...")
        logger.info(f"👑 Admin: {admin_ids}")
        
        # Cria e inicia bot
        bot = RailwayBot()
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("⌨️ Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro fatal: {e}")
        sys.exit(1)

def run():
    """Executa o bot"""
    try:
        # Inicia health check em thread separada
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        
        # Configura event loop
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Executa bot
        logger.info("🚀 Bot LoL V3 Railway - Iniciando...")
        logger.info(f"📍 PID: {os.getpid()}")
        
        asyncio.run(main())
        
    except Exception as e:
        logger.error(f"💥 Erro na execução: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run() 