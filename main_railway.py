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
    
    def debug(self, msg):
        print(f"[DEBUG] {msg}")

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
                
                # CRÍTICO: Inicia o polling para receber comandos
                await self.alerts_system.start_bot()
                logger.info("✅ Telegram inicializado com polling ativo")
            except Exception as e:
                logger.error(f"❌ Erro Telegram: {e}")
                raise
            
            # 2. Inicialização básica sem ScheduleManager complexo
            # (Sistema funcionará apenas com Telegram para Railway)
            logger.info("✅ Sistema básico inicializado para Railway!")
            logger.info("🤖 Bot Telegram operacional")
            
        except Exception as e:
            logger.error(f"❌ Falha na inicialização: {e}")
            raise

    async def cleanup(self):
        """Limpeza de recursos"""
        try:
            logger.info("🧹 Iniciando limpeza...")
            
            if hasattr(self, 'alerts_system') and self.alerts_system:
                # Usar o método correto de limpeza
                if hasattr(self.alerts_system, 'cleanup_old_cache'):
                    self.alerts_system.cleanup_old_cache()
                    
                # Tentar parar o bot de forma segura
                if hasattr(self.alerts_system, 'application') and self.alerts_system.application:
                    try:
                        if self.alerts_system.application.updater and self.alerts_system.application.updater.running:
                            await self.alerts_system.application.updater.stop()
                        if self.alerts_system.application.running:
                            await self.alerts_system.application.stop()
                        await self.alerts_system.application.shutdown()
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ Erro na limpeza do Telegram: {cleanup_error}")
                    
            logger.info("✅ Limpeza concluída")
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")

    async def run(self):
        """Execução principal simplificada"""
        try:
            await self.initialize()
            
            logger.info("🚀 Bot LoL V3 Railway executando!")
            logger.info("💡 Sistema básico ativo - Telegram Bot funcionando")
            logger.info("🔄 Bot aguardando comandos via polling...")
            
            # Loop principal para manter o processo ativo
            # O polling do Telegram roda em background
            while True:
                await asyncio.sleep(30)  # Health check a cada 30s
                
                # Verifica se o bot ainda está rodando
                if hasattr(self, 'alerts_system') and self.alerts_system:
                    if (hasattr(self.alerts_system, 'application') and 
                        self.alerts_system.application and 
                        hasattr(self.alerts_system.application, 'updater') and
                        self.alerts_system.application.updater and
                        self.alerts_system.application.updater.running):
                        logger.debug("🔄 Sistema ativo - Telegram polling OK")
                    else:
                        logger.warning("⚠️ Polling do Telegram não está ativo")
                        break
                else:
                    logger.warning("⚠️ Sistema não inicializado corretamente")
                    break
                    
        except KeyboardInterrupt:
            logger.info("🛑 Interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro durante execução: {e}")
            raise
        finally:
            # Cleanup
            await self.cleanup()

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
        await bot.run()
        
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