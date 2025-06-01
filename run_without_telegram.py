#!/usr/bin/env python3
"""
Bot LoL V3 SEM interface Telegram
Roda apenas ScheduleManager + sistema de tips para desenvolvimento/teste
"""
import asyncio
import signal
import sys
import time
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

# Imports do sistema
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.systems.schedule_manager import ScheduleManager
from bot.telegram_bot.alerts_system import TelegramAlertsSystem
from bot.utils.logger_config import get_logger

# Configurações diretas
PANDASCORE_API_KEY = "90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ"
RIOT_API_KEY = "RGAPI-7b5ce87e-4bb8-4d9d-b905-8df7d7b4f8c2"
BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"

logger = get_logger(__name__)

class LoLSystemRunner:
    """
    Executa o sistema LoL V3 sem interface Telegram
    Ideal para desenvolvimento e testes
    """
    
    def __init__(self):
        self.is_running = False
        self.schedule_manager = None
        
    async def initialize_system(self):
        """Inicializa todos os componentes do sistema"""
        try:
            logger.info("🚀 Inicializando Sistema LoL V3 (SEM Telegram)")
            logger.info("=" * 60)
            
            # 1. Inicializa clientes de API
            logger.info("📡 Inicializando clientes de API...")
            pandascore_client = PandaScoreAPIClient(
                api_key=PANDASCORE_API_KEY
            )
            
            riot_client = RiotAPIClient(
                api_key=RIOT_API_KEY
            )
            
            # 2. Inicializa sistema de tips
            logger.info("🎯 Inicializando sistema de tips...")
            tips_system = ProfessionalTipsSystem(
                pandascore_client=pandascore_client,
                riot_client=riot_client
            )
            
            # 3. Inicializa sistema de alertas (sem envio real)
            logger.info("📤 Inicializando sistema de alertas...")
            telegram_alerts = TelegramAlertsSystem(
                bot_token=BOT_TOKEN
            )
            
            # 4. Inicializa ScheduleManager
            logger.info("⚙️ Inicializando ScheduleManager...")
            self.schedule_manager = ScheduleManager(
                tips_system=tips_system,
                telegram_alerts=telegram_alerts,
                pandascore_client=pandascore_client,
                riot_client=riot_client
            )
            
            logger.info("✅ Todos os componentes inicializados!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar sistema: {e}")
            return False
    
    async def start_system(self):
        """Inicia o sistema completo"""
        if not await self.initialize_system():
            return False
        
        try:
            logger.info("🔄 Iniciando ScheduleManager...")
            await self.schedule_manager.start_scheduled_tasks()
            
            self.is_running = True
            logger.info("✅ Sistema totalmente operacional!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sistema: {e}")
            return False
    
    async def stop_system(self):
        """Para o sistema graciosamente"""
        if self.schedule_manager and self.schedule_manager.is_running:
            logger.info("🛑 Parando ScheduleManager...")
            await self.schedule_manager.stop_scheduled_tasks()
        
        self.is_running = False
        logger.info("✅ Sistema parado com sucesso")
    
    def show_status(self):
        """Mostra status do sistema"""
        if not self.is_running or not self.schedule_manager:
            print("❌ Sistema não está rodando")
            return
        
        try:
            status = self.schedule_manager.get_system_status()
            
            print("\n" + "=" * 60)
            print("📊 STATUS DO SISTEMA LoL V3")
            print("=" * 60)
            print(f"🖥️  Sistema: {'✅ RODANDO' if status['system']['is_running'] else '❌ PARADO'}")
            print(f"💓 Saúde: {'✅ SAUDÁVEL' if status['system']['is_healthy'] else '⚠️ PROBLEMAS'}")
            print(f"⏰ Uptime: {status['system']['uptime_hours']:.2f} horas")
            print(f"💾 Memória: {status['system']['memory_usage_mb']:.1f} MB")
            
            print(f"\n📋 TAREFAS:")
            print(f"   • Agendadas: {status['tasks']['scheduled_count']}")
            print(f"   • Executando: {status['tasks']['running_count']}")
            print(f"   • Concluídas: {status['statistics']['tasks_completed']}")
            print(f"   • Falhadas: {status['statistics']['tasks_failed']}")
            
            print(f"\n🎯 ESTATÍSTICAS:")
            print(f"   • Tips geradas: {status['statistics']['tips_generated']}")
            print(f"   • Tarefas criadas: {status['statistics']['tasks_created']}")
            print(f"   • Erros recuperados: {status['statistics']['errors_recovered']}")
            
            print(f"\n⏰ ÚLTIMA TIP: {self._format_time_ago(status['health']['last_tip_time'])}")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Erro ao obter status: {e}")
    
    def _format_time_ago(self, timestamp):
        """Formata timestamp como tempo relativo"""
        if not timestamp:
            return "Nunca"
        
        now = time.time()
        diff = now - timestamp
        
        if diff < 60:
            return f"{int(diff)}s atrás"
        elif diff < 3600:
            return f"{int(diff/60)}min atrás"
        elif diff < 86400:
            return f"{int(diff/3600)}h atrás"
        else:
            return f"{int(diff/86400)}d atrás"

async def main():
    """Função principal"""
    print("🚀 BOT LOL V3 - MODO SISTEMA PURO")
    print("=" * 60)
    print("💡 Executando sem interface Telegram")
    print("🔧 Ideal para desenvolvimento e testes")
    print("⚡ Todas as funcionalidades principais ativas")
    print("=" * 60)
    
    runner = LoLSystemRunner()
    
    # Configura handlers de shutdown
    def signal_handler(signum, frame):
        print(f"\n📋 Recebido sinal {signum}, parando sistema...")
        asyncio.create_task(runner.stop_system())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Inicia sistema
    if await runner.start_system():
        print("\n🎉 SISTEMA OPERACIONAL!")
        print("💡 Comandos disponíveis:")
        print("   • Ctrl+C: Parar sistema")
        print("   • Status automático a cada 10 segundos")
        print("=" * 60)
        
        # Loop principal
        try:
            while runner.is_running:
                # Aguarda e mostra status
                await asyncio.sleep(10)  # Status a cada 10 segundos
                runner.show_status()
                    
        except Exception as e:
            logger.error(f"❌ Erro no loop principal: {e}")
        
        finally:
            await runner.stop_system()
    else:
        print("❌ Falha ao inicializar sistema")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Sistema parado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}") 