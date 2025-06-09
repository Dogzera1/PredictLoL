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
    """Bot completo para Railway"""
    
    def __init__(self):
        self.is_running = False
        self.alerts_system = None
        self.schedule_manager = None
        self.professional_tips_system = None
        self.multi_api_client = None
        self.pandascore_client = None
        self.riot_client = None
        self.prediction_system = None
        self.game_analyzer = None
        self.units_system = None
        
    async def initialize(self):
        """Inicialização completa do sistema"""
        try:
            logger.info("🔧 Inicializando componentes completos...")
            
            # 1. Sistema de alertas Telegram
            try:
                from bot.telegram_bot.alerts_system import TelegramAlertsSystem
                logger.info("📱 Inicializando Telegram...")
                
                # Pega o token das variáveis de ambiente do Railway
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI")
                if not bot_token:
                    raise ValueError("TELEGRAM_BOT_TOKEN não configurado")
                
                logger.info(f"📱 Token configurado: {bot_token[:20]}...{bot_token[-10:]}")
                
                self.alerts_system = TelegramAlertsSystem(bot_token=bot_token)
                await self.alerts_system.initialize()
                
                # CRÍTICO: Inicia o polling para receber comandos
                await self.alerts_system.start_bot()
                logger.info("✅ Telegram inicializado com polling ativo")
            except Exception as e:
                logger.error(f"❌ Erro Telegram: {e}")
                raise
            
            # 2. Sistema Multi-API
            try:
                from bot.api_clients.multi_api_client import MultiAPIClient
                logger.info("🌐 Inicializando Multi-API Client...")
                
                self.multi_api_client = MultiAPIClient()
                logger.info("✅ Multi-API Client inicializado")
            except Exception as e:
                logger.error(f"❌ Erro Multi-API: {e}")
                raise
            
            # 3. Inicialização de clientes APIs e sistemas de análise
            try:
                from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
                from bot.api_clients.riot_api_client import RiotAPIClient
                from bot.core_logic.prediction_system import DynamicPredictionSystem
                from bot.core_logic.game_analyzer import LoLGameAnalyzer
                from bot.core_logic.units_system import ProfessionalUnitsSystem
                
                logger.info("🔧 Inicializando clientes APIs e sistemas...")
                
                self.pandascore_client = PandaScoreAPIClient()
                self.riot_client = RiotAPIClient()
                
                # Sistemas de análise necessários para DynamicPredictionSystem
                self.game_analyzer = LoLGameAnalyzer()
                self.units_system = ProfessionalUnitsSystem()
                self.prediction_system = DynamicPredictionSystem(
                    game_analyzer=self.game_analyzer,
                    units_system=self.units_system
                )
                
                logger.info("✅ Clientes APIs e sistemas de análise inicializados")
            except Exception as e:
                logger.error(f"❌ Erro clientes APIs: {e}")
                raise
            
            # 4. Sistema de Tips Profissionais
            try:
                from bot.systems.tips_system import ProfessionalTipsSystem
                logger.info("💎 Inicializando Sistema de Tips Profissionais...")
                
                self.professional_tips_system = ProfessionalTipsSystem(
                    pandascore_client=self.pandascore_client,
                    riot_client=self.riot_client,
                    prediction_system=self.prediction_system,
                    telegram_alerts=self.alerts_system
                )
                logger.info("✅ Sistema de Tips Profissionais inicializado")
            except Exception as e:
                logger.error(f"❌ Erro Sistema de Tips: {e}")
                raise
            
            # 5. Schedule Manager (orquestrador principal)
            try:
                from bot.systems.schedule_manager import ScheduleManager
                logger.info("⏰ Inicializando Schedule Manager...")
                
                self.schedule_manager = ScheduleManager(
                    tips_system=self.professional_tips_system,
                    telegram_alerts=self.alerts_system,
                    pandascore_client=self.pandascore_client,
                    riot_client=self.riot_client
                )
                
                # Inicia tarefas agendadas
                await self.schedule_manager.start_scheduled_tasks()
                logger.info("✅ Schedule Manager inicializado e tarefas iniciadas")
            except Exception as e:
                logger.error(f"❌ Erro Schedule Manager: {e}")
                raise
            
            logger.info("✅ Todos os componentes inicializados com sucesso!")
            logger.info("🤖 Bot Telegram operacional")
            logger.info("💎 Sistema de Tips automático ativo")
            logger.info("🌐 APIs múltiplas funcionando")
            logger.info("⏰ Cronograma de automação ativo")
            
        except Exception as e:
            logger.error(f"❌ Falha na inicialização: {e}")
            raise

    async def cleanup(self):
        """Limpeza de recursos"""
        try:
            logger.info("🧹 Iniciando limpeza...")
            self.is_running = False
            
            # Para sistemas na ordem inversa
            if hasattr(self, 'schedule_manager') and self.schedule_manager:
                try:
                    logger.info("⏰ Parando Schedule Manager...")
                    await self.schedule_manager.stop_scheduled_tasks()
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao parar Schedule Manager: {e}")
            
            if hasattr(self, 'professional_tips_system') and self.professional_tips_system:
                try:
                    logger.info("💎 Parando Sistema de Tips...")
                    # Sistema de tips não tem stop específico, apenas cleanup
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao parar Sistema de Tips: {e}")
            
            if hasattr(self, 'alerts_system') and self.alerts_system:
                try:
                    logger.info("📱 Parando Telegram...")
                    # Usar o método correto de limpeza
                    if hasattr(self.alerts_system, 'cleanup_old_cache'):
                        self.alerts_system.cleanup_old_cache()
                        
                    # Tentar parar o bot de forma segura
                    if hasattr(self.alerts_system, 'application') and self.alerts_system.application:
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
            logger.info("💡 Sistema completo ativo - Todas as funcionalidades disponíveis")
            logger.info("🔄 Bot aguardando comandos via polling...")
            
            # Loop principal para manter o processo ativo
            # O polling do Telegram roda em background
            while self.is_running:
                await asyncio.sleep(30)  # Health check a cada 30s
                
                # Verifica se todos os sistemas ainda estão rodando
                systems_ok = True
                
                # Verifica Telegram
                if hasattr(self, 'alerts_system') and self.alerts_system:
                    if (hasattr(self.alerts_system, 'application') and 
                        self.alerts_system.application and 
                        hasattr(self.alerts_system.application, 'updater') and
                        self.alerts_system.application.updater and
                        self.alerts_system.application.updater.running):
                        logger.debug("🔄 Telegram polling OK")
                    else:
                        logger.warning("⚠️ Polling do Telegram não está ativo")
                        systems_ok = False
                else:
                    logger.warning("⚠️ Sistema de alertas não inicializado")
                    systems_ok = False
                
                # Verifica Schedule Manager
                if hasattr(self, 'schedule_manager') and self.schedule_manager:
                    logger.debug("🔄 Schedule Manager OK")
                else:
                    logger.warning("⚠️ Schedule Manager não disponível")
                
                # Verifica Sistema de Tips
                if hasattr(self, 'professional_tips_system') and self.professional_tips_system:
                    logger.debug("🔄 Sistema de Tips OK")
                else:
                    logger.warning("⚠️ Sistema de Tips não disponível")
                
                if not systems_ok:
                    logger.error("❌ Sistemas críticos falharam, parando...")
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
        
        # Validações adicionais
        if not admin_ids:
            logger.warning("⚠️ TELEGRAM_ADMIN_USER_IDS não configurado, usando padrão")
        
        logger.info("✅ Configurações validadas")
        
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