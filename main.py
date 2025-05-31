#!/usr/bin/env python3
"""
Bot LoL V3 Ultra Avançado - Aplicação Principal
Sistema profissional completo para tips de League of Legends

🚀 SISTEMA 100% OPERACIONAL:
- ScheduleManager: Automação total end-to-end
- TelegramAlertsSystem: Comunicação profissional
- LoLBotV3UltraAdvanced: Interface completa
- APIs: Riot + PandaScore integradas
- ML + Algoritmos: Predição híbrida
- Deploy: Railway ready

Características:
- Monitoramento 24/7 automático
- Tips profissionais com ML
- Interface Telegram completa
- Sistema resiliente a falhas
- Performance enterprise-grade
"""

import os
import sys
import asyncio
import signal
from typing import List

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup de logging (antes dos outros imports)
from bot.utils.logger_config import setup_logging, get_logger
logger = setup_logging(log_level="INFO", log_file="bot_lol_v3.log")

# Configuração de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("⚠️ python-dotenv não disponível, usando apenas environment variables")

# Imports do sistema
try:
    from bot.systems.schedule_manager import ScheduleManager
    from bot.systems.tips_system import ProfessionalTipsSystem
    from bot.telegram_bot import LoLBotV3UltraAdvanced, TelegramAlertsSystem
    from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
    from bot.api_clients.riot_api_client import RiotAPIClient
    from bot.utils.constants import PANDASCORE_API_KEY, TELEGRAM_CONFIG
except ImportError as e:
    logger.error(f"❌ Erro crítico ao importar módulos: {e}")
    sys.exit(1)


class BotApplication:
    """
    Aplicação Principal do Bot LoL V3 Ultra Avançado
    
    Orquestra todos os componentes:
    - APIs (Riot + PandaScore)
    - Sistema de Tips Profissionais
    - Sistema de Alertas Telegram
    - ScheduleManager (automação total)
    - Interface Principal do Bot
    
    Deploy-ready para Railway com:
    - Configuração via environment variables
    - Shutdown graceful
    - Error handling robusto
    - Logging completo
    """

    def __init__(self):
        """Inicializa a aplicação principal"""
        logger.info("🚀 Inicializando Bot LoL V3 Ultra Avançado...")
        
        # Configuração de ambiente
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_CONFIG["bot_token"])
        self.pandascore_api_key = os.getenv("PANDASCORE_API_KEY", PANDASCORE_API_KEY)
        self.admin_user_ids = self._parse_admin_user_ids()
        
        # Validação de configuração
        self._validate_config()
        
        # Componentes principais
        self.pandascore_client = None
        self.riot_client = None
        self.tips_system = None
        self.telegram_alerts = None
        self.schedule_manager = None
        self.bot_interface = None
        
        logger.info("✅ BotApplication inicializada")

    def _parse_admin_user_ids(self) -> List[int]:
        """Parse dos IDs de administradores"""
        # Primeiro tenta variável de ambiente
        admin_ids_str = os.getenv("TELEGRAM_ADMIN_USER_IDS", "")
        
        # Se não encontrar, usa o padrão das constantes
        if not admin_ids_str:
            default_admins = TELEGRAM_CONFIG.get("admin_user_ids", [])
            if isinstance(default_admins, list) and default_admins:
                try:
                    # Converte strings para int se necessário
                    admin_ids = [int(uid) if isinstance(uid, str) else uid for uid in default_admins]
                    logger.info(f"👑 {len(admin_ids)} administradores (padrão) configurados")
                    return admin_ids
                except (ValueError, TypeError) as e:
                    logger.error(f"❌ Erro ao parsear admin IDs padrão: {e}")
                    return []
            
            logger.warning("⚠️ Nenhum admin user ID configurado")
            return []
        
        try:
            admin_ids = [int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip()]
            logger.info(f"👑 {len(admin_ids)} administradores (env) configurados")
            return admin_ids
        except ValueError as e:
            logger.error(f"❌ Erro ao parsear admin user IDs: {e}")
            return []

    def _validate_config(self) -> None:
        """Valida configuração essencial"""
        if not self.bot_token or self.bot_token == "BOT_TOKEN_HERE":
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN não configurado via environment variable")
            logger.info("ℹ️ Usando token padrão das constantes")
        
        if not self.pandascore_api_key:
            logger.warning("⚠️ PandaScore API key não configurada")
            logger.info("ℹ️ Usando API key padrão das constantes")
        
        logger.info("✅ Configuração validada")

    async def initialize_components(self) -> None:
        """Inicializa todos os componentes do sistema"""
        logger.info("🔧 Inicializando componentes do sistema...")
        
        try:
            # 1. API Clients
            logger.info("📡 Inicializando clientes de API...")
            self.pandascore_client = PandaScoreAPIClient(self.pandascore_api_key)
            self.riot_client = RiotAPIClient()
            
            # 2. Sistema de Tips Profissionais
            logger.info("🎯 Inicializando sistema de tips...")
            self.tips_system = ProfessionalTipsSystem(
                pandascore_client=self.pandascore_client,
                riot_client=self.riot_client
            )
            
            # 3. Sistema de Alertas Telegram
            logger.info("📤 Inicializando sistema de alertas...")
            self.telegram_alerts = TelegramAlertsSystem(
                bot_token=self.bot_token,
                max_messages_per_hour=TELEGRAM_CONFIG["rate_limit_per_user"],
                cache_duration_minutes=TELEGRAM_CONFIG["cache_duration_minutes"]
            )
            
            # 4. ScheduleManager (orquestrador total)
            logger.info("⚙️ Inicializando ScheduleManager...")
            self.schedule_manager = ScheduleManager(
                tips_system=self.tips_system,
                telegram_alerts=self.telegram_alerts,
                pandascore_client=self.pandascore_client,
                riot_client=self.riot_client
            )
            
            # 5. Interface Principal do Bot
            logger.info("🤖 Inicializando interface do bot...")
            self.bot_interface = LoLBotV3UltraAdvanced(
                bot_token=self.bot_token,
                schedule_manager=self.schedule_manager,
                admin_user_ids=self.admin_user_ids
            )
            
            logger.info("✅ Todos os componentes inicializados com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro crítico na inicialização: {e}")
            raise

    async def run_bot(self) -> None:
        """Executa o bot completo"""
        logger.info("🚀 Iniciando Bot LoL V3 Ultra Avançado...")
        
        try:
            # Inicializa componentes
            await self.initialize_components()
            
            # Exibe resumo do sistema
            self._display_system_summary()
            
            # Inicia interface principal (que conecta tudo automaticamente)
            logger.info("🎉 SISTEMA TOTALMENTE OPERACIONAL!")
            logger.info("🔄 Monitoramento automático ativo")
            logger.info("📱 Interface Telegram disponível")
            logger.info("⚡ ScheduleManager executando")
            
            # A interface principal gerencia tudo automaticamente
            await self.bot_interface.start_bot()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown solicitado pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro crítico: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shutdown graceful de todos os sistemas"""
        logger.info("🛑 Iniciando shutdown graceful...")
        
        try:
            # Para interface do bot (que para tudo automaticamente)
            if self.bot_interface and self.bot_interface.is_running:
                await self.bot_interface.stop_bot()
            
            logger.info("✅ Shutdown concluído com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro durante shutdown: {e}")

    def _display_system_summary(self) -> None:
        """Exibe resumo do sistema"""
        print("\n" + "="*70)
        print("🚀 BOT LOL V3 ULTRA AVANÇADO - SISTEMA COMPLETO")
        print("="*70)
        print("📊 COMPONENTES ATIVADOS:")
        print("  ✅ APIs: Riot + PandaScore")
        print("  ✅ Sistema de Tips Profissionais")
        print("  ✅ Sistema de Alertas Telegram")
        print("  ✅ ScheduleManager (Automação Total)")
        print("  ✅ Interface Principal do Bot")
        print("\n🎯 FUNCIONALIDADES:")
        print("  • Monitoramento 24/7 automático")
        print("  • Tips ML + algoritmos heurísticos")
        print("  • Interface Telegram completa")
        print("  • Comandos administrativos")
        print("  • Sistema resiliente a falhas")
        print("  • Health monitoring contínuo")
        print("\n👑 ADMINISTRADORES:", len(self.admin_user_ids))
        for admin_id in self.admin_user_ids:
            print(f"  • ID: {admin_id}")
        print("\n🔥 DEPLOY: Railway Ready")
        print("⚡ STATUS: 100% OPERACIONAL")
        print("="*70)


def setup_signal_handlers(app: BotApplication) -> None:
    """Configura handlers de sinal para shutdown graceful"""
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} recebido, iniciando shutdown...")
        asyncio.create_task(app.shutdown())
        sys.exit(0)
    
    if sys.platform != "win32":
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main() -> None:
    """Função principal"""
    try:
        # Exibe banner inicial
        print("\n" + "="*70)
        print("🚀 BOT LOL V3 ULTRA AVANÇADO")
        print("🎯 Sistema Profissional de Tips para League of Legends")
        print("⚡ Powered by ML + Algoritmos + Railway Deploy")
        print("="*70)
        
        # Cria e executa aplicação
        app = BotApplication()
        setup_signal_handlers(app)
        
        await app.run_bot()
        
    except Exception as e:
        logger.error(f"❌ Erro fatal na aplicação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Executa aplicação
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Aplicação interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1) 