#!/usr/bin/env python3
"""
Bot LoL V3 Ultra Avançado - Sistema Principal
Versão com prevenção de conflitos de instância
"""

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
    """Classe principal do Bot LoL V3 Ultra Avançado"""
    
    def __init__(self):
        # Adquire lock de instância única
        instance_manager.acquire_lock()
        
        self.schedule_manager = None
        self.bot_interface = None
        self.alerts_system = None
        self.is_running = False
        
        main_logger.info("🤖 Bot LoL V3 Ultra Avançado - Inicializando...")
        
    async def initialize_components(self):
        """Inicializa todos os componentes do sistema"""
        try:
            main_logger.info("🔧 Inicializando componentes...")
            
            # Import dinâmico para evitar erros de import circular
            from bot.telegram_bot.alerts_system import TelegramAlertsSystem
            from bot.systems.schedule_manager import ScheduleManager
            
            # 1. Sistema de alertas Telegram
            main_logger.info("📱 Inicializando sistema de alertas...")
            
            # Pega o token das variáveis de ambiente
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            if not bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN não configurado")
            
            self.alerts_system = TelegramAlertsSystem(bot_token=bot_token)
            await self.alerts_system.initialize()
            
            # 2. Schedule Manager (orquestrador principal)
            main_logger.info("⏰ Inicializando gerenciador de cronograma...")
            self.schedule_manager = ScheduleManager(
                alerts_system=self.alerts_system
            )
            
            # 3. Interface do Bot simplificada (apenas o que é necessário)
            main_logger.info("🎮 Bot interface integrada no ScheduleManager...")
            self.bot_interface = self.alerts_system  # Usar o próprio alerts_system
            
            main_logger.info("✅ Todos os componentes inicializados com sucesso!")
            
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
            main_logger.info("🚀 Iniciando sistemas...")
            
            # 1. Inicia tarefas agendadas
            await self.schedule_manager.start_scheduled_tasks()
            
            # 2. O alerts_system já gerencia o bot Telegram
            main_logger.info("📱 Sistema Telegram ativo via AlertsSystem")
            
            main_logger.info("🎉 Bot LoL V3 Ultra Avançado iniciado com sucesso!")
            main_logger.info("📊 Sistema de tips automático ativo")
            main_logger.info("📱 Bot Telegram operacional")
            
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
                
            if self.alerts_system:
                await self.alerts_system.cleanup()
            
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
        is_production = os.getenv("ENVIRONMENT") == "production"
        
        main_logger.info("🔍 Detectando ambiente...")
        main_logger.info(f"   Railway: {'✅' if is_railway else '❌'}")
        main_logger.info(f"   Produção: {'✅' if is_production else '❌'}")
        
        # Validações usando variáveis de ambiente diretamente
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        admin_ids = os.getenv("TELEGRAM_ADMIN_USER_IDS", "")
        
        if not telegram_token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN não configurado!")
            
        if not admin_ids:
            main_logger.warning("⚠️ TELEGRAM_ADMIN_USER_IDS não encontrado, usando padrão")
        
        main_logger.info("✅ Configurações validadas")
        main_logger.info(f"🤖 Token: {telegram_token[:10]}...")
        main_logger.info(f"👑 Admin IDs: {admin_ids}")
        
        # Cria e inicia bot
        bot = BotLoLV3()
        await bot.start()
        
    except KeyboardInterrupt:
        main_logger.info("⌨️  Interrompido pelo usuário")
    except Exception as e:
        main_logger.error(f"💥 Erro fatal: {e}")
        sys.exit(1)

def run_bot():
    """Executa o bot com prevenção de conflitos"""
    try:
        # Inicia health check server em thread separada
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        
        # Configura política de eventos para Windows
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Executa bot
        asyncio.run(main())
        
    except Exception as e:
        main_logger.error(f"💥 Erro na execução: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Verifica se é execução direta
    main_logger.info("🎯 Bot LoL V3 Ultra Avançado - Iniciando...")
    main_logger.info(f"   PID: {os.getpid()}")
    main_logger.info(f"   Ambiente: {os.getenv('ENVIRONMENT', 'development')}")
    
    run_bot() 
