#!/usr/bin/env python3
"""
Bot LoL V3 Ultra Avançado - Sistema Principal
Versão com TODAS as APIs integradas
"""

# FORÇA REDEPLOY - CORREÇÕES APLICADAS - TIMESTAMP: 2025-06-07 18:43
# Sistema corrigido: LTA Norte + in_game status + tips pós-draft

import os
import sys
import asyncio
import signal
import atexit
import time
import threading
from pathlib import Path

# Configurações de ambiente
os.environ.setdefault('TZ', 'America/Sao_Paulo')

# Adiciona o diretório do bot ao path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

# Health check em thread separada
def start_health_server():
    """Inicia servidor de health check em thread separada"""
    try:
        from simple_health_check import run_server
        print("🏥 Iniciando health check server...")
        run_server()
    except Exception as e:
        print(f"⚠️ Erro no health check: {e}")

# Imports do sistema
from bot.utils.logger_config import setup_logging, get_logger

# Logger global
logger = setup_logging(log_level="INFO")
main_logger = get_logger("main")

# Arquivo de lock para prevenir múltiplas instâncias
LOCK_FILE = BOT_DIR / "bot.lock"

class BotInstanceManager:
    """Gerenciador para prevenir múltiplas instâncias do bot"""
    
    def __init__(self):
        self.lock_acquired = False
        
    def acquire_lock(self):
        """Adquire lock de instância única"""
        try:
            if LOCK_FILE.exists():
                # Verifica se o processo ainda existe
                try:
                    with open(LOCK_FILE, 'r') as f:
                        old_pid = int(f.read().strip())
                    
                    # Tenta verificar se processo existe (Windows/Linux)
                    if os.name == 'nt':  # Windows
                        import subprocess
                        result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'], 
                                              capture_output=True, text=True)
                        if str(old_pid) not in result.stdout:
                            # Processo morto, remove lock antigo
                            LOCK_FILE.unlink()
                        else:
                            raise RuntimeError(f"Bot já rodando com PID {old_pid}")
                    else:  # Linux/Unix
                        os.kill(old_pid, 0)  # Verifica se processo existe
                        raise RuntimeError(f"Bot já rodando com PID {old_pid}")
                        
                except (OSError, ValueError):
                    # Processo não existe, remove lock antigo
                    LOCK_FILE.unlink()
            
            # Cria novo lock
            with open(LOCK_FILE, 'w') as f:
                f.write(str(os.getpid()))
            
            self.lock_acquired = True
            main_logger.info(f"🔒 Lock de instância adquirido: PID {os.getpid()}")
            
        except Exception as e:
            main_logger.error(f"❌ Erro ao adquirir lock: {e}")
            raise
    
    def release_lock(self):
        """Libera lock de instância"""
        if self.lock_acquired and LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
                main_logger.info("🔓 Lock de instância liberado")
            except Exception as e:
                main_logger.error(f"❌ Erro ao liberar lock: {e}")

# Instância global do gerenciador
instance_manager = BotInstanceManager()

def cleanup_on_exit():
    """Cleanup ao sair"""
    instance_manager.release_lock()

def signal_handler(signum, frame):
    """Handler para sinais de término"""
    main_logger.info(f"📡 Recebido sinal {signum}, terminando...")
    cleanup_on_exit()
    sys.exit(0)

# Registra handlers de cleanup
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

class BotLoLV3:
    """Classe principal do Bot LoL V3 Ultra Avançado com TODAS as APIs"""
    
    def __init__(self):
        # Adquire lock de instância única
        instance_manager.acquire_lock()
        
        # Inicialização de componentes
        self.schedule_manager = None
        self.alerts_system = None
        self.professional_tips_system = None
        self.multi_api_client = None
        self.pandascore_client = None
        self.riot_client = None
        self.lolesports_client = None
        self.prediction_system = None
        self.game_analyzer = None
        self.units_system = None
        self.is_running = False
        
        main_logger.info("🤖 Bot LoL V3 Ultra Avançado - Inicializando SISTEMA COMPLETO...")
        
    async def initialize_components(self):
        """Inicializa TODOS os componentes do sistema com APIs completas"""
        try:
            main_logger.info("🔧 Inicializando TODOS os componentes...")
            
            # 1. Sistema de alertas Telegram
            try:
                from bot.telegram_bot.alerts_system import TelegramAlertsSystem
                main_logger.info("📱 Inicializando sistema de alertas...")
                
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
                if not bot_token:
                    raise ValueError("TELEGRAM_BOT_TOKEN não configurado")
                
                self.alerts_system = TelegramAlertsSystem(bot_token=bot_token)
                await self.alerts_system.initialize()
                
                # CRÍTICO: Inicia o polling para receber comandos
                await self.alerts_system.start_bot()
                main_logger.info("✅ Telegram inicializado com polling ativo")
            except Exception as e:
                main_logger.error(f"❌ Erro Telegram: {e}")
                raise
            
            # 2. Sistema Multi-API (15+ APIs gratuitas)
            try:
                from bot.api_clients.multi_api_client import MultiAPIClient
                main_logger.info("🌐 Inicializando Multi-API Client...")
                
                self.multi_api_client = MultiAPIClient()
                main_logger.info("✅ Multi-API Client inicializado (15+ APIs gratuitas)")
            except Exception as e:
                main_logger.error(f"❌ Erro Multi-API: {e}")
                raise
            
            # 3. Clientes APIs principais e sistemas de análise
            try:
                from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
                from bot.api_clients.riot_api_client import RiotAPIClient
                from bot.api_clients.lolesports_api_client import LolesportsAPIClient
                from bot.core_logic.prediction_system import DynamicPredictionSystem
                from bot.core_logic.game_analyzer import LoLGameAnalyzer
                from bot.core_logic.units_system import ProfessionalUnitsSystem
                
                main_logger.info("🔧 Inicializando clientes APIs e sistemas ML...")
                
                self.pandascore_client = PandaScoreAPIClient()
                self.riot_client = RiotAPIClient()
                self.lolesports_client = LolesportsAPIClient()
                
                # Sistemas de análise necessários para DynamicPredictionSystem
                self.game_analyzer = LoLGameAnalyzer()
                self.units_system = ProfessionalUnitsSystem()
                self.prediction_system = DynamicPredictionSystem(
                    game_analyzer=self.game_analyzer,
                    units_system=self.units_system
                )
                
                main_logger.info("✅ PandaScore + Riot + Lolesports APIs + ML Systems inicializados")
            except Exception as e:
                main_logger.error(f"❌ Erro clientes APIs: {e}")
                raise
            
            # 4. Sistema de Tips Profissionais
            try:
                from bot.systems.tips_system import ProfessionalTipsSystem
                main_logger.info("💎 Inicializando Sistema de Tips Profissionais...")
                
                self.professional_tips_system = ProfessionalTipsSystem(
                    pandascore_client=self.pandascore_client,
                    riot_client=self.riot_client,
                    prediction_system=self.prediction_system,
                    telegram_alerts=self.alerts_system
                )
                main_logger.info("✅ Sistema de Tips Profissionais inicializado")
            except Exception as e:
                main_logger.error(f"❌ Erro Sistema de Tips: {e}")
                raise
            
            # 5. Schedule Manager (orquestrador principal)
            try:
                from bot.systems.schedule_manager import ScheduleManager
                main_logger.info("⏰ Inicializando Schedule Manager...")
                
                self.schedule_manager = ScheduleManager(
                    tips_system=self.professional_tips_system,
                    telegram_alerts=self.alerts_system,
                    pandascore_client=self.pandascore_client,
                    riot_client=self.riot_client,
                    lolesports_client=self.lolesports_client
                )
                main_logger.info("✅ Schedule Manager inicializado")
            except Exception as e:
                main_logger.error(f"❌ Erro Schedule Manager: {e}")
                raise
            
            main_logger.info("✅ TODOS OS COMPONENTES INICIALIZADOS COM SUCESSO!")
            main_logger.info("🤖 Bot Telegram operacional")
            main_logger.info("💎 Sistema de Tips automático ativo")
            main_logger.info("🌐 Multi-API (15+ APIs gratuitas) funcionando")
            main_logger.info("💰 PandaScore API (Money Line) ativo")
            main_logger.info("🎮 Riot API oficial ativo")
            main_logger.info("⚡ Lolesports API (dados em tempo real) ativo")
            main_logger.info("🧠 Sistemas ML/Algoritmos ativos")
            main_logger.info("⏰ Automação completa ativa")
            
        except Exception as e:
            main_logger.error(f"❌ Erro na inicialização: {e}")
            raise
    
    async def start(self):
        """Inicia o bot e todos os sistemas"""
        try:
            self.is_running = True
            
            # Inicializa componentes
            await self.initialize_components()
            
            # Inicia sistemas
            main_logger.info("🚀 Iniciando TODOS os sistemas...")
            
            # 1. Inicia tarefas agendadas
            await self.schedule_manager.start_scheduled_tasks()
            
            main_logger.info("🎉 Bot LoL V3 Ultra Avançado COMPLETO iniciado com sucesso!")
            main_logger.info("📊 Sistema de tips automático com TODAS as APIs ativo")
            main_logger.info("📱 Bot Telegram com comandos operacional")
            main_logger.info("💰 Money Line + ML ready para LTA Norte")
            main_logger.info("⚡ Dados em tempo real do Lolesports disponíveis")
            
            # Aguarda até receber sinal de parada
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            main_logger.error(f"❌ Erro durante execução: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Para o bot e limpa recursos"""
        if not self.is_running:
            return
            
        main_logger.info("🛑 Parando Bot LoL V3...")
        self.is_running = False
        
        try:
            # Para sistemas na ordem inversa
            if self.schedule_manager:
                await self.schedule_manager.stop_scheduled_tasks()
                
            if self.professional_tips_system:
                # Tips system não tem stop específico
                pass
            
            if self.lolesports_client:
                await self.lolesports_client.close()
            
            if self.alerts_system:
                # Limpeza do Telegram
                if hasattr(self.alerts_system, 'cleanup_old_cache'):
                    self.alerts_system.cleanup_old_cache()
                    
                # Para bot de forma segura
                if hasattr(self.alerts_system, 'application') and self.alerts_system.application:
                    if self.alerts_system.application.updater and self.alerts_system.application.updater.running:
                        await self.alerts_system.application.updater.stop()
                    if self.alerts_system.application.running:
                        await self.alerts_system.application.stop()
                    await self.alerts_system.application.shutdown()
                    
            if self.multi_api_client:
                # Multi-API client cleanup
                pass
            
            main_logger.info("✅ Bot parado com sucesso")
            
        except Exception as e:
            main_logger.error(f"❌ Erro ao parar: {e}")
        finally:
            # Libera lock
            instance_manager.release_lock()

async def main():
    """Função principal assíncrona"""
    try:
        # Detecta ambiente
        is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT_ID"))
        main_logger.info(f"🌍 Ambiente: {'Railway' if is_railway else 'Local'}")
        
        # Health check em thread separada
        if is_railway:
            health_thread = threading.Thread(target=start_health_server, daemon=True)
            health_thread.start()
            main_logger.info("🏥 Health check server iniciado em thread separada")
        
        # Cria e inicia bot
        bot = BotLoLV3()
        await bot.start()
        
    except KeyboardInterrupt:
        main_logger.info("⌨️ Interrupção por teclado")
    except Exception as e:
        main_logger.error(f"❌ Erro na função main: {e}")
        raise
    finally:
        main_logger.info("🛑 Finalizando main()")

def run_bot():
    """Função de entrada - executa bot com tratamento de erros robusto"""
    try:
        # Configura event loop para Windows se necessário
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Executa função principal
        asyncio.run(main())
        
    except KeyboardInterrupt:
        main_logger.info("⌨️ Bot interrompido pelo usuário")
    except Exception as e:
        main_logger.error(f"❌ Erro fatal: {e}")
        raise

if __name__ == "__main__":
    run_bot()
