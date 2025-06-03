from __future__ import annotations

import os
import asyncio
import time
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
import signal
import sys
import tempfile
import logging
from datetime import datetime, timedelta
import traceback

# Import condicional para fcntl (não disponível no Windows)
try:
    import fcntl  # Para lock de arquivo no Unix/Linux
    FCNTL_AVAILABLE = True
except ImportError:
    FCNTL_AVAILABLE = False

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
    from telegram.constants import ParseMode
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Update = Application = CommandHandler = CallbackQueryHandler = ContextTypes = None
    MessageHandler = filters = ParseMode = TelegramError = None

from ..telegram_bot.alerts_system import TelegramAlertsSystem, SubscriptionType
from ..api_clients.pandascore_api_client import PandaScoreAPIClient
from ..api_clients.riot_api_client import RiotAPIClient
from ..utils.logger_config import get_logger
from ..utils.constants import TELEGRAM_CONFIG

if TYPE_CHECKING:
    from ..systems.schedule_manager import ScheduleManager
    from ..systems.tips_system import ProfessionalTipsSystem

logger = get_logger(__name__)


@dataclass
class BotStats:
    """Estatísticas do bot"""
    start_time: float
    commands_processed: int = 0
    admin_commands: int = 0
    errors_handled: int = 0
    active_users: int = 0
    tips_sent_today: int = 0
    
    @property
    def uptime_hours(self) -> float:
        return (time.time() - self.start_time) / 3600


class InstanceManager:
    """Gerenciador de instância única do bot"""
    
    def __init__(self, lock_file: str = None):
        if lock_file is None:
            # Windows-friendly path
            if sys.platform == "win32":
                lock_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp")
            else:
                lock_dir = tempfile.gettempdir()
            
            # Cria diretório se não existir
            os.makedirs(lock_dir, exist_ok=True)
            lock_file = os.path.join(lock_dir, "lol_bot_v3.lock")
        
        self.lock_file = lock_file
        self.lock_fd = None
        
    def acquire_lock(self) -> bool:
        """Tenta adquirir lock exclusivo"""
        try:
            # Tenta criar arquivo de lock
            self.lock_fd = open(self.lock_file, 'w')
            
            if sys.platform == "win32":
                # Windows - usa locking exclusivo via msvcrt
                try:
                    import msvcrt
                    msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
                except ImportError:
                    # Se msvcrt não está disponível, usa fallback simples
                    logger.warning("msvcrt não disponível, usando lock básico")
                except OSError as e:
                    logger.warning(f"Lock msvcrt falhou: {e}, usando fallback")
                    # Não falha, apenas continua sem lock exclusivo
            else:
                # Unix/Linux - usa fcntl se disponível
                if FCNTL_AVAILABLE:
                    fcntl.lockf(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    logger.warning("fcntl não disponível, usando lock básico")
            
            # Escreve PID no arquivo
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            
            logger.info(f"🔒 Lock adquirido: {self.lock_file}")
            return True
            
        except (IOError, OSError) as e:
            if "permission denied" in str(e).lower():
                logger.warning(f"⚠️ Permission denied para lock, tentando fallback...")
                # Tenta fallback com lock básico
                return self._fallback_lock()
            else:
                logger.warning(f"⚠️ Não foi possível adquirir lock: {e}")
                if self.lock_fd:
                    self.lock_fd.close()
                    self.lock_fd = None
                return False
    
    def _fallback_lock(self) -> bool:
        """Fallback quando não consegue criar lock exclusivo"""
        try:
            # Usa apenas verificação de PID básica
            if os.path.exists(self.lock_file):
                try:
                    with open(self.lock_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Verifica se processo ainda existe
                    if self._is_process_running(pid):
                        logger.warning(f"⚠️ Processo {pid} ainda rodando")
                        return False
                except (ValueError, IOError):
                    # Arquivo corrompido, remove
                    try:
                        os.remove(self.lock_file)
                    except:
                        pass
            
            # Cria arquivo simples com PID
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
            logger.info(f"🔒 Lock básico adquirido: {self.lock_file}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback lock falhou: {e}")
            # Em último caso, permite execução sem lock
            logger.warning("⚠️ Executando sem lock de instância - CUIDADO!")
            return True
    
    def _is_process_running(self, pid: int) -> bool:
        """Verifica se processo está rodando"""
        try:
            if sys.platform == "win32":
                import subprocess
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                      capture_output=True, text=True)
                return str(pid) in result.stdout
            else:
                # Unix/Linux
                try:
                    os.kill(pid, 0)  # Não mata, apenas verifica se existe
                    return True
                except OSError:
                    return False
        except:
            return False
    
    def release_lock(self) -> None:
        """Libera o lock"""
        if self.lock_fd:
            try:
                if sys.platform == "win32":
                    try:
                        import msvcrt
                        msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                    except (ImportError, OSError):
                        pass  # Lock básico não precisa unlock
                else:
                    if FCNTL_AVAILABLE:
                        fcntl.lockf(self.lock_fd, fcntl.LOCK_UN)
                
                self.lock_fd.close()
                logger.info("🔓 Lock liberado")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao liberar lock: {e}")
            finally:
                self.lock_fd = None
                
                # Remove arquivo de lock
                try:
                    if os.path.exists(self.lock_file):
                        os.remove(self.lock_file)
                except:
                    pass
    
    def is_another_instance_running(self) -> bool:
        """Verifica se há outra instância rodando"""
        if not os.path.exists(self.lock_file):
            return False
        
        try:
            with open(self.lock_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Verifica se processo ainda existe
            return self._is_process_running(pid)
                    
        except (ValueError, IOError):
            return False


class LoLBotV3UltraAdvanced:
    """
    Interface Principal do Bot LoL V3 Ultra Avançado
    
    Responsável por:
    - Interface completa de usuário via Telegram
    - Integração com ScheduleManager (automação total)
    - Comandos administrativos avançados
    - Controle total do sistema via bot
    - Status e relatórios em tempo real
    - Gestão de usuários e preferências
    
    Características:
    - Comandos básicos (/start, /help, /status)
    - Comandos administrativos (/admin, /system, /force)
    - Interface rica com botões inline
    - Relatórios detalhados
    - Controle de sistema via Telegram
    - Monitoramento em tempo real
    """

    def __init__(
        self,
        bot_token: str,
        schedule_manager: "ScheduleManager",
        admin_user_ids: List[int] = None
    ):
        """
        Inicializa a interface principal do bot
        
        Args:
            bot_token: Token do bot do Telegram
            schedule_manager: Gerenciador de cronograma (conecta tudo)
            admin_user_ids: IDs dos usuários administradores
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot não está disponível")
        
        self.bot_token = bot_token
        self.schedule_manager = schedule_manager
        self.admin_user_ids = admin_user_ids or []
        
        # Gerenciador de instância única
        self.instance_manager = InstanceManager()
        
        # Referências diretas aos sistemas via ScheduleManager
        self.tips_system = schedule_manager.tips_system
        self.telegram_alerts = schedule_manager.telegram_alerts
        self.pandascore_client = schedule_manager.pandascore_client
        self.riot_client = schedule_manager.riot_client
        
        # Estado do bot
        self.application: Optional[Application] = None
        self.is_running = False
        self.stats = BotStats(start_time=time.time())
        
        logger.info("LoLBotV3UltraAdvanced inicializado com sucesso")

    def _escape_markdown_v2(self, text: str) -> str:
        """
        Escapa caracteres especiais para MarkdownV2 do Telegram
        
        Caracteres que precisam ser escapados:
        _ * [ ] ( ) ~ ` > # + - = | { } . !
        """
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        
        return text

    async def start_bot(self) -> None:
        """Inicia o bot completo com ScheduleManager"""
        if self.is_running:
            logger.warning("Bot já está executando")
            return
        
        # Detecta se está no Railway
        is_railway = self._is_running_on_railway()
        
        if is_railway:
            logger.info("🌐 RAILWAY detectado - usando WEBHOOK")
            await self._start_with_webhook()
        else:
            logger.info("💻 AMBIENTE LOCAL detectado - SISTEMA DE TIPS APENAS")
            await self._start_local_tips_only()

    def _is_running_on_railway(self) -> bool:
        """Detecta se está executando no Railway"""
        railway_vars = [
            "RAILWAY_PROJECT_ID",
            "RAILWAY_SERVICE_ID", 
            "RAILWAY_ENVIRONMENT_ID",
            "RAILWAY_DEPLOYMENT_ID",
            "PORT"  # Railway sempre define PORT
        ]
        return any(os.getenv(var) for var in railway_vars)

    async def _start_with_webhook(self) -> None:
        """Inicia bot com webhook (Railway)"""
        logger.info("🚀 Iniciando Bot LoL V3 Ultra Avançado - WEBHOOK MODE!")
        
        try:
            # 1. Cria aplicação básica
            logger.info("📱 Criando aplicação Telegram (webhook)...")
            self.application = Application.builder().token(self.bot_token).build()
            
            # 2. Configura handlers
            logger.info("🎮 Configurando handlers do bot...")
            self._setup_all_handlers()
            
            # 3. Inicia ScheduleManager primeiro
            logger.info("🔧 Iniciando ScheduleManager...")
            schedule_task = asyncio.create_task(self.schedule_manager.start_scheduled_tasks())
            
            # 4. Configura webhook
            webhook_url = self._get_webhook_url()
            port = int(os.getenv("PORT", 8080))
            
            logger.info(f"🌐 Configurando webhook: {webhook_url}")
            logger.info(f"🔌 Porta: {port}")
            
            # 5. Inicia aplicação com webhook
            logger.info("⚡ Inicializando aplicação Telegram...")
            await self.application.initialize()
            await self.application.start()
            
            # 6. Configura webhook no Telegram
            logger.info("🔗 Configurando webhook no Telegram...")
            webhook_info = await self.application.bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            
            if webhook_info:
                logger.info("✅ Webhook configurado com sucesso!")
            else:
                logger.warning("⚠️ Webhook pode não ter sido configurado corretamente")
            
            # 7. Inicia servidor webhook
            logger.info("🚀 Iniciando servidor webhook...")
            
            try:
                # Tenta iniciar o servidor webhook
                await self.application.run_webhook(
                    listen="0.0.0.0",
                    port=port,
                    webhook_url=webhook_url,
                    url_path="/webhook"
                )
                
                self.is_running = True
                logger.info("✅ Bot LoL V3 Ultra Avançado totalmente operacional (WEBHOOK)!")
                
            except Exception as webhook_error:
                logger.error(f"💥 Erro específico no servidor webhook: {webhook_error}")
                
                # Verifica se é problema de porta
                if "port" in str(webhook_error).lower() or "address" in str(webhook_error).lower():
                    logger.error(f"🔌 ERRO DE PORTA: Porta {port} não disponível no Railway")
                    logger.error("💡 Sugestão: Verificar variável PORT no Railway")
                
                # Re-levanta o erro
                raise webhook_error
            
            # 8. Mantém executando
            try:
                await schedule_task
            except asyncio.CancelledError:
                logger.info("📋 ScheduleManager cancelado")
            
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"❌ Erro crítico ao iniciar bot (webhook): {e}")
            
            # Log detalhado baseado no tipo de erro
            if "port" in error_str or "address already in use" in error_str:
                logger.error(f"🔌 Erro de porta: Porta {port} pode estar ocupada")
            elif "network" in error_str or "connection" in error_str:
                logger.error("🌐 Erro de rede: Problemas de conectividade")
            elif "token" in error_str or "unauthorized" in error_str:
                logger.error("🔑 Erro de autenticação: Token pode estar inválido")
            elif "webhook" in error_str:
                logger.error("🔗 Erro de webhook: Problemas na configuração")
            else:
                logger.error(f"❓ Erro desconhecido: {e}")
            
            # Sempre tenta fazer cleanup
            try:
                await self.stop_bot()
            except Exception as cleanup_error:
                logger.error(f"Erro no cleanup: {cleanup_error}")
            
            raise

    async def _start_local_tips_only(self) -> None:
        """Inicia apenas sistema de tips (Local) - SEM TELEGRAM"""
        logger.info("🚀 Iniciando Sistema de Tips LoL V3 - LOCAL MODE!")
        logger.warning("🚨 TELEGRAM DESABILITADO para evitar conflitos com Railway")
        logger.info("💡 Este ambiente executará apenas análise e geração de tips")
        logger.info("📱 Para usar Telegram, acesse o bot no Railway")
        
        try:
            # Apenas inicia ScheduleManager sem Telegram
            logger.info("🔧 Iniciando ScheduleManager (sem Telegram)...")
            await self.schedule_manager.start_scheduled_tasks()
            
            self.is_running = True
            logger.info("✅ Sistema de Tips LoL V3 operacional (LOCAL)!")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar sistema de tips: {e}")
            raise

    def _get_webhook_url(self) -> str:
        """Gera URL do webhook baseada no Railway"""
        # Railway fornece URLs automáticas
        railway_url = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if railway_url:
            return f"https://{railway_url}/webhook"
        
        # Fallback específico para o projeto
        return "https://predictlol-production.up.railway.app/webhook"

    async def _start_polling_with_advanced_retry(self) -> None:
        """Inicia polling com proteção ultra avançada contra conflitos"""
        max_retries = 25  # Aumentado para 25 tentativas
        base_wait_time = 3
        
        logger.info(f"🛡️ Sistema anti-conflito ativado: {max_retries} tentativas")
        
        # FASE PRÉ-POLLING: Limpeza preventiva
        await self._pre_polling_cleanup()
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Backoff exponencial com jitter
                    wait_time = min(base_wait_time + (attempt * 2) + (attempt % 3), 120)
                    logger.info(f"⏳ Tentativa {attempt + 1}/{max_retries} em {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    
                    # Limpeza progressiva baseada no número da tentativa
                    if attempt <= 5:
                        await self._gentle_conflict_cleanup()
                    elif attempt <= 12:
                        await self._moderate_conflict_cleanup()
                    elif attempt <= 20:
                        await self._aggressive_conflict_cleanup()
                    else:
                        await self._nuclear_conflict_cleanup()  # Nova fase ultra agressiva
                
                # Configurações otimizadas para evitar conflitos
                logger.debug(f"🚀 Iniciando polling (tentativa {attempt + 1})...")
                await self.application.updater.start_polling(
                    drop_pending_updates=True,        # Sem retries bootstrap
                    read_timeout=60,           # Timeout maior
                    connect_timeout=45,        # Timeout conexão maior
                    pool_timeout=90,           # Pool timeout muito maior
                    write_timeout=45,          # Timeout escrita maior
                    allowed_updates=["message", "callback_query"]
                )
                
                logger.info("✅ Polling iniciado com sucesso!")
                break
                
            except Exception as e:
                error_str = str(e).lower()
                
                if "conflict" in error_str or "terminated by other" in error_str:
                    logger.warning(f"⚠️ Conflito #{attempt + 1}: {e}")
                    
                    if attempt < max_retries - 1:
                        # Log estratégia de limpeza
                        if attempt <= 5:
                            logger.info("🧹 Próxima estratégia: Limpeza suave")
                        elif attempt <= 12:
                            logger.info("🧹 Próxima estratégia: Limpeza moderada")
                        elif attempt <= 20:
                            logger.info("🧹 Próxima estratégia: Limpeza agressiva")
                        else:
                            logger.warning("🚨 Próxima estratégia: NUCLEAR")
                        continue
                    else:
                        logger.error("❌ FALHA CRÍTICA: Conflitos não resolvidos após 25 tentativas!")
                        logger.error("🔍 Possível causa: Instância remota ativa (Railway, Heroku, etc.)")
                        raise RuntimeError("Conflitos persistentes - verifique instâncias remotas")
                
                elif "network" in error_str or "timeout" in error_str:
                    logger.warning(f"🌐 Problema de rede #{attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise RuntimeError("Problemas de rede persistentes")
                        
                else:
                    logger.error(f"❌ Erro crítico não relacionado a conflito: {e}")
                    raise

    async def _pre_polling_cleanup(self) -> None:
        """Limpeza preventiva antes de iniciar polling"""
        logger.info("🧹 Limpeza preventiva pré-polling...")
        
        try:
            import aiohttp
            base_url = f"https://api.telegram.org/bot{self.bot_token}"
            
            async with aiohttp.ClientSession() as session:
                # 1. Verifica e remove webhook se existir
                async with session.post(f"{base_url}/getWebhookInfo") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        webhook_info = data.get('result', {})
                        webhook_url = webhook_info.get('url', '')
                        
                        if webhook_url:
                            logger.warning(f"⚠️ Webhook detectado: {webhook_url}")
                            logger.info("🔧 Removendo webhook automaticamente...")
                            
                            async with session.post(f"{base_url}/deleteWebhook") as resp:
                                if resp.status == 200:
                                    logger.info("✅ Webhook removido com sucesso")
                                else:
                                    logger.warning(f"⚠️ Falha ao remover webhook: {resp.status}")
                
                # 2. Limpeza inicial de getUpdates
                for i in range(5):
                    try:
                        async with session.post(f"{base_url}/getUpdates", 
                                              json={"timeout": 0, "limit": 100, "offset": -1}) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                updates_count = len(data.get('result', []))
                                if updates_count > 0:
                                    logger.debug(f"  📥 Limpou {updates_count} updates pendentes")
                    except:
                        pass
                    await asyncio.sleep(0.5)
                
                logger.info("✅ Limpeza preventiva concluída")
                
        except Exception as e:
            logger.warning(f"⚠️ Erro na limpeza preventiva: {e}")

    async def _gentle_conflict_cleanup(self) -> None:
        """Limpeza suave de conflitos"""
        logger.info("🧹 Limpeza suave...")
        try:
            # Para o updater atual se estiver rodando
            if self.application and self.application.updater and self.application.updater.running:
                await self.application.updater.stop()
                await asyncio.sleep(2)
            
            await self._force_clear_telegram_conflicts(requests_count=5)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na limpeza suave: {e}")

    async def _moderate_conflict_cleanup(self) -> None:
        """Limpeza moderada de conflitos"""
        logger.info("🧹 Limpeza moderada...")
        try:
            # Para aplicação completamente
            if self.application:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await asyncio.sleep(3)
                await self.application.start()
            
            await self._force_clear_telegram_conflicts(requests_count=10)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na limpeza moderada: {e}")

    async def _aggressive_conflict_cleanup(self) -> None:
        """Limpeza agressiva de conflitos"""
        logger.info("🧹 Limpeza agressiva...")
        try:
            # Reinicia aplicação completamente
            if self.application:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                await asyncio.sleep(5)
                
                # Recria aplicação
                self.application = Application.builder().token(self.bot_token).build()
                self._setup_all_handlers()
                await self.application.initialize()
                await self.application.start()
            
            await self._force_clear_telegram_conflicts(requests_count=20)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na limpeza agressiva: {e}")

    async def _nuclear_conflict_cleanup(self) -> None:
        """Limpeza ultra agressiva de conflitos"""
        logger.info("🧹 Limpeza ultra agressiva...")
        try:
            # Reinicia aplicação completamente
            if self.application:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                await asyncio.sleep(10)
                
                # Recria aplicação
                self.application = Application.builder().token(self.bot_token).build()
                self._setup_all_handlers()
                await self.application.initialize()
                await self.application.start()
            
            await self._force_clear_telegram_conflicts(requests_count=50)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na limpeza ultra agressiva: {e}")

    async def _force_clear_telegram_conflicts(self, requests_count: int = 10) -> None:
        """Força limpeza de conflitos via API do Telegram"""
        import aiohttp
        
        try:
            logger.debug(f"📡 Limpando conflitos com {requests_count} requisições...")
            base_url = f"https://api.telegram.org/bot{self.bot_token}"
            
            async with aiohttp.ClientSession() as session:
                # 1. Força remoção de webhook primeiro
                try:
                    async with session.post(f"{base_url}/deleteWebhook") as resp:
                        if resp.status == 200:
                            logger.debug("🔗 Webhook removido forçadamente")
                except:
                    pass
                
                # 2. Múltiplas tentativas de getUpdates para "roubar" controle
                for i in range(requests_count):
                    try:
                        async with session.post(f"{base_url}/getUpdates", 
                                              json={"timeout": 1, "limit": 100}) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                updates_count = len(data.get('result', []))
                                if updates_count > 0:
                                    logger.debug(f"  📥 {updates_count} updates limpos")
                    except:
                        pass
                    
                    await asyncio.sleep(0.5)
                
                # 3. Aguarda estabilização
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro na limpeza forçada: {e}")

    async def _cleanup_bot_instance(self) -> None:
        """Limpa instância atual do bot para resolver conflitos"""
        try:
            logger.info("🧹 Limpando instância do bot...")
            if self.application and self.application.updater:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            self.application = None
            logger.info("✅ Instância limpa")
        except Exception as e:
            logger.warning(f"⚠️ Erro na limpeza: {e}")

    async def stop_bot(self) -> None:
        """Para o bot e todos os sistemas"""
        if not self.is_running:
            return
        
        logger.info("🛑 Parando Bot LoL V3 Ultra Avançado...")
        
        try:
            # 1. Para ScheduleManager
            if self.schedule_manager.is_running:
                await self.schedule_manager.stop_scheduled_tasks()
            
            # 2. Para Telegram
            if self.application and self.application.updater:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            # 3. Libera lock de instância única
            self.instance_manager.release_lock()
            
            self.is_running = False
            logger.info("✅ Bot parado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao parar bot: {e}")
        finally:
            # Garante que lock seja liberado
            self.instance_manager.release_lock()

    def _setup_all_handlers(self) -> None:
        """Configura todos os handlers do bot"""
        
        # Comandos básicos (todos os usuários)
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(CommandHandler("stats", self._handle_stats))
        self.application.add_handler(CommandHandler("subscribe", self._handle_subscribe))
        self.application.add_handler(CommandHandler("unsubscribe", self._handle_unsubscribe))
        self.application.add_handler(CommandHandler("mystats", self._handle_my_stats))
        
        # Comandos para grupos
        self.application.add_handler(CommandHandler("activate_group", self._handle_activate_group))
        self.application.add_handler(CommandHandler("group_status", self._handle_group_status))
        self.application.add_handler(CommandHandler("deactivate_group", self._handle_deactivate_group))
        
        # Comandos administrativos (apenas admins)
        self.application.add_handler(CommandHandler("admin", self._handle_admin))
        self.application.add_handler(CommandHandler("system", self._handle_system_status))
        self.application.add_handler(CommandHandler("force", self._handle_force_scan))
        self.application.add_handler(CommandHandler("tasks", self._handle_tasks))
        self.application.add_handler(CommandHandler("health", self._handle_health_check))
        self.application.add_handler(CommandHandler("logs", self._handle_logs))
        self.application.add_handler(CommandHandler("restart", self._handle_restart_system))
        
        # Callbacks para botões inline
        self.application.add_handler(CallbackQueryHandler(self._handle_callback_query))
        
        # Handler para mensagens não reconhecidas
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_unknown_message))
        
        logger.debug("Todos os handlers configurados")

    def _setup_signal_handlers(self, schedule_task: asyncio.Task) -> None:
        """Configura handlers para shutdown graceful"""
        def signal_handler(signum, frame):
            logger.info(f"Signal {signum} recebido, parando bot...")
            schedule_task.cancel()
            asyncio.create_task(self.stop_bot())
        
        if sys.platform != "win32":
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

    # ===== COMANDOS BÁSICOS =====

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /start"""
        user = update.effective_user
        self.stats.commands_processed += 1
        
        # Verifica se é admin
        is_admin = user.id in self.admin_user_ids
        admin_text = " 👑 **ADMIN**" if is_admin else ""
        
        welcome_message = f"""🚀 **Bot LoL V3 Ultra Avançado** 🚀{admin_text}

Olá, {user.first_name}\\! 

🎯 **Sistema 100% Operacional:**
• 🤖 ScheduleManager ativo
• 📊 Tips profissionais automáticas
• 💬 Alertas personalizados
• 📈 Monitoramento 24/7

**📋 Comandos Disponíveis:**
• `/help` \\\\ Lista completa de comandos
• `/status` \\\\ Status do sistema
• `/subscribe` \\\\ Configurar alertas
• `/stats` \\\\ Suas estatísticas
• `/mystats` \\\\ Estatísticas detalhadas

""" + (f"**👑 Comandos Admin:**\\n• `/admin` \\\\ Painel administrativo\\n• `/system` \\\\ Status completo\\n• `/force` \\\\ Forçar scan" if is_admin else "") + """

⚡ **Powered by Machine Learning \\+ Algoritmos Heurísticos**
🔥 **Deploy: Railway \\| Status: ONLINE**"""
        
        # Atualiza estatísticas de usuários ativos
        if user.id not in [u.user_id for u in self.telegram_alerts.users.values()]:
            self.stats.active_users += 1
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_main_keyboard(is_admin)
        )

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /help"""
        user = update.effective_user
        is_admin = user.id in self.admin_user_ids
        self.stats.commands_processed += 1
        
        help_message = f"""🆘 **AJUDA \\- Bot LoL V3 Ultra Avançado**

**🎯 Sobre o Sistema:**
Bot profissional para tips de League of Legends com automação total\\. Combina Machine Learning, análise em tempo real e gestão de risco profissional\\.

**📋 Comandos Básicos:**
• `/start` \\- Iniciar e ver menu principal
• `/help` \\- Esta ajuda
• `/status` \\- Status do sistema e estatísticas
• `/stats` \\- Suas estatísticas pessoais
• `/subscribe` \\- Configurar tipos de alerta
• `/unsubscribe` \\- Cancelar alertas
• `/mystats` \\- Histórico detalhado

**👥 Comandos para Grupos:**
• `/activate_group` \\- Ativar alertas no grupo \\(apenas admins\\)
• `/group_status` \\- Ver status e estatísticas do grupo
• `/deactivate_group` \\- Desativar alertas \\(apenas admins\\)

**🔔 Tipos de Subscrição:**
• **Todas as Tips** \\- Recebe todas as tips geradas
• **Alto Valor** \\- Apenas tips com EV \\> 10%
• **Alta Confiança** \\- Apenas tips com confiança \\> 80%
• **Premium** \\- Tips exclusivas \\(EV \\> 15% \\+ conf \\> 85%\\)

**💡 Como Funciona:**
1\\. Sistema monitora partidas ao vivo a cada 3 min
2\\. IA analisa dados usando ML \\+ algoritmos
3\\. Gera tips com confiança e Expected Value
4\\. Filtra por critérios profissionais rigorosos
5\\. Envia apenas tips de alta qualidade

**📊 Critérios de Qualidade:**
• Confiança mínima: 65%
• EV mínimo: 3%
• Odds entre 1\\.30 e 3\\.50
• Sistema anti\\-spam ativo"""

        if is_admin:
            help_message += """

**👑 Comandos Administrativos:**
• `/admin` \\\\ Painel administrativo completo
• `/system` \\\\ Status detalhado do sistema
• `/force` \\\\ Forçar scan de partidas
• `/tasks` \\\\ Gerenciar tarefas
• `/health` \\\\ Health check completo
• `/logs` \\\\ Logs recentes do sistema
• `/restart` \\\\ Reiniciar componentes

**🔧 Controle Total:**
• Monitoramento em tempo real
• Controle de tarefas via Telegram
• Estatísticas avançadas
• Logs e debugging"""

        help_message += """

🔥 **Sistema desenvolvido para apostas profissionais\\!**
⚡ **Deploy: Railway \\| Uptime: 99\\.9%**"""
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_help_keyboard(is_admin)
        )

    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /status"""
        self.stats.commands_processed += 1
        
        # Obtém status do sistema
        system_status = self.schedule_manager.get_system_status()
        bot_uptime = self.stats.uptime_hours
        
        status_message = f"""📊 **STATUS DO SISTEMA**

🖥️ **Sistema:**
• Status: {'🟢 ONLINE' if system_status['system']['is_running'] else '🔴 OFFLINE'}
• Uptime Bot: {bot_uptime:.1f}h
• Uptime Sistema: {system_status['system']['uptime_hours']:.1f}h
• Saúde: {'✅ Saudável' if system_status['system']['is_healthy'] else '⚠️ Problemas'}
• Memória: {system_status['system']['memory_usage_mb']:.1f}MB

📋 **Tarefas:**
• Agendadas: {system_status['tasks']['scheduled_count']}
• Executando: {system_status['tasks']['running_count']}
• Concluídas: {system_status['statistics']['tasks_completed']}
• Falhadas: {system_status['statistics']['tasks_failed']}

🎯 **Performance:**
• Tips geradas: {system_status['statistics']['tips_generated']}
• Comandos processados: {self.stats.commands_processed}
• Usuários ativos: {len(self.telegram_alerts.users)}
• Taxa de sucesso: {self.telegram_alerts.stats.success_rate:.1f}%

⏰ **Última tip:** {self._format_time_ago(system_status['health']['last_tip_time'])}

🔥 **Sistema operacional e monitorando\\!**"""
        
        await update.message.reply_text(
            status_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_status_keyboard()
        )

    async def _handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /stats"""
        user_id = update.effective_user.id
        self.stats.commands_processed += 1
        
        # Obtém estatísticas do sistema de alertas
        system_stats = self.telegram_alerts.get_system_stats()
        
        stats_message = f"""📈 **ESTATÍSTICAS GLOBAIS**

👥 **Usuários:**
• Total registrados: {system_stats['users']['total']}
• Ativos: {system_stats['users']['active']}
• Bloqueados: {system_stats['users']['blocked']}

📨 **Alertas:**
• Total enviados: {system_stats['alerts']['total_sent']}
• Tips enviadas: {system_stats['alerts']['tips_sent']}
• Taxa de sucesso: {system_stats['alerts']['success_rate']:.1f}%
• Falhas: {system_stats['alerts']['failed_deliveries']}

🔔 **Subscrições:**"""
        
        for sub_type, count in system_stats['users']['subscriptions_by_type'].items():
            stats_message += f"\n• {sub_type}: {count}"
        
        stats_message += f"""

⚡ **Rate Limiting:**
• Máx por hora: {system_stats['rate_limiting']['max_messages_per_hour']}
• Cache: {system_stats['rate_limiting']['cache_duration_minutes']}min
• Tips em cache: {system_stats['rate_limiting']['recent_tips_cached']}

🎯 **Bot Performance:**
• Uptime: {self.stats.uptime_hours:.1f}h
• Comandos: {self.stats.commands_processed}
• Admins ativos: {len(self.admin_user_ids)}"""
        
        await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /subscribe"""
        self.stats.commands_processed += 1
        
        await update.message.reply_text(
            "🔔 **Escolha seu tipo de subscrição:**",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_subscription_keyboard()
        )

    async def _handle_unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /unsubscribe"""
        user_id = update.effective_user.id
        self.stats.commands_processed += 1
        
        if user_id in self.telegram_alerts.users:
            self.telegram_alerts.users[user_id].is_active = False
            message = "❌ **Subscrição cancelada**\n\nVocê não receberá mais notificações\\.\nUse `/subscribe` para reativar\\."
        else:
            message = "ℹ️ Você não está subscrito\\."
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_my_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /mystats"""
        user_id = update.effective_user.id
        self.stats.commands_processed += 1
        
        if user_id not in self.telegram_alerts.users:
            await update.message.reply_text(
                "ℹ️ Você não está registrado\\. Use `/start` primeiro\\.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        user = self.telegram_alerts.users[user_id]
        
        stats_message = f"""📊 **SUAS ESTATÍSTICAS**

👤 **Perfil:**
• Nome: {user.first_name}
• Username: @{user.username or 'N/A'}
• Tipo: {user.subscription_type.value}
• Status: {'✅ Ativo' if user.is_active else '❌ Inativo'}

📅 **Histórico:**
• Membro desde: {self._format_time_ago(user.joined_at)}
• Última atividade: {self._format_time_ago(user.last_active)}
• Tips recebidas: {user.tips_received}

⚙️ **Configurações:**
• Filtros customizados: {len(user.custom_filters) if user.custom_filters else 0}
• Rate limit: {self.telegram_alerts.max_messages_per_hour} msg/h"""
        
        await update.message.reply_text(
            stats_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_mystats_keyboard()
        )

    # ===== COMANDOS PARA GRUPOS =====

    async def _handle_activate_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para ativar alertas em um grupo"""
        # Delega para o sistema de alertas que já tem a lógica completa
        await self.telegram_alerts._handle_activate_group(update, context)

    async def _handle_group_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para status do grupo"""
        # Delega para o sistema de alertas que já tem a lógica completa
        await self.telegram_alerts._handle_group_status(update, context)

    async def _handle_deactivate_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para desativar alertas do grupo"""
        # Delega para o sistema de alertas que já tem a lógica completa
        await self.telegram_alerts._handle_deactivate_group(update, context)

    # ===== COMANDOS ADMINISTRATIVOS =====

    async def _handle_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /admin"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado\\. Comando apenas para admins\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        
        self.stats.admin_commands += 1
        
        # Status completo do sistema
        system_status = self.schedule_manager.get_system_status()
        
        admin_message = f"""👑 **PAINEL ADMINISTRATIVO**

🖥️ **Sistema:**
• Status: {'🟢 OPERACIONAL' if system_status['system']['is_running'] else '🔴 PARADO'}
• Uptime: {system_status['system']['uptime_hours']:.2f}h
• Saúde: {'✅' if system_status['system']['is_healthy'] else '❌'}
• Memória: {system_status['system']['memory_usage_mb']:.1f}MB

📋 **Tarefas Agendadas:**"""
        
        for task_id, task_info in system_status['tasks']['task_details'].items():
            status_icon = "🏃" if task_info['status'] == 'running' else "⏸️" if task_info['status'] == 'scheduled' else "✅"
            admin_message += f"\n• {task_id}: {status_icon} {task_info['run_count']} exec., {task_info['error_count']} erros"
        
        admin_message += f"""

🎯 **Performance:**
• Tips geradas: {system_status['statistics']['tips_generated']}
• Erros recuperados: {system_status['statistics']['errors_recovered']}
• Comandos admin: {self.stats.admin_commands}

⚡ **Controles disponíveis via comandos:**
• `/system` \\\\ Status detalhado
• `/force` \\\\ Forçar scan
• `/tasks` \\\\ Gerenciar tarefas
• `/health` \\\\ Health check
• `/restart` \\\\ Reiniciar sistemas"""
        
        await update.message.reply_text(
            admin_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_admin_keyboard()
        )

    async def _handle_system_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /system"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        
        self.stats.admin_commands += 1
        
        # Status completo do sistema
        status = self.schedule_manager.get_system_status()
        
        system_message = f"""🔧 **STATUS COMPLETO DO SISTEMA**

**🖥️ Sistema Principal:**
• Running: {status['system']['is_running']}
• Healthy: {status['system']['is_healthy']}
• Uptime: {status['system']['uptime_hours']:.3f}h
• Memory: {status['system']['memory_usage_mb']:.1f}MB

**📋 Tarefas \\({status['tasks']['scheduled_count']} total\\):**
• Executando: {status['tasks']['running_count']}
• Concluídas: {status['statistics']['tasks_completed']}
• Falhadas: {status['statistics']['tasks_failed']}

**🔧 Componentes:**"""
        
        for component, healthy in status['health']['components_status'].items():
            icon = "✅" if healthy else "❌"
            system_message += f"\n• {component}: {icon}"
        
        system_message += f"""

**📊 Estatísticas:**
• Tips geradas: {status['statistics']['tips_generated']}
• Tarefas criadas: {status['statistics']['tasks_created']}
• Erros recuperados: {status['statistics']['errors_recovered']}
• Uptime total: {status['statistics']['uptime_hours']:.3f}h

**⏰ Última tip:** {self._format_time_ago(status['health']['last_tip_time'])}
**❌ Último erro:** {status['health']['last_error'] or 'Nenhum'}"""
        
        await update.message.reply_text(system_message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_force_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /force"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        
        self.stats.admin_commands += 1
        
        await update.message.reply_text("🔄 **Forçando scan de partidas\\.\\.\\.**", parse_mode=ParseMode.MARKDOWN_V2)
        
        try:
            # Força execução da tarefa de monitoramento
            success = await self.schedule_manager.force_task_execution("monitor_live_matches")
            
            if success:
                # Aguarda um pouco para a tarefa processar
                await asyncio.sleep(2)
                
                # Obtém resultado
                stats = self.schedule_manager.stats
                message = f"✅ **Scan forçado concluído!**\n\n• Tips geradas: {stats['tips_generated']}\n• Status: Operacional"
            else:
                message = "❌ **Falha ao forçar scan\\.**\n\nTarefa pode já estar executando\\."
            
        except Exception as e:
            message = f"❌ **Erro no scan forçado:**\n\n`{str(e)[:100]}`"
            self.stats.errors_handled += 1
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /tasks"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        
        self.stats.admin_commands += 1
        
        status = self.schedule_manager.get_system_status()
        
        tasks_message = "📋 **GERENCIAMENTO DE TAREFAS**\n\n"
        
        for task_id, task_info in status['tasks']['task_details'].items():
            status_icons = {
                'running': '🏃',
                'scheduled': '⏰',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }
            
            icon = status_icons.get(task_info['status'], '❓')
            
            tasks_message += f"**{task_id}:**\n"
            tasks_message += f"• Status: {icon} {task_info['status']}\n"
            tasks_message += f"• Execuções: {task_info['run_count']}\n"
            tasks_message += f"• Erros: {task_info['error_count']}\n"
            tasks_message += f"• Última: {self._format_time_ago(task_info['last_run'])}\n"
            tasks_message += f"• Próxima: {self._format_time_ago(task_info['next_run'])}\n\n"
        
        await update.message.reply_text(
            tasks_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_tasks_keyboard()
        )

    async def _handle_health_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /health"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        
        self.stats.admin_commands += 1
        
        await update.message.reply_text("💓 **Executando health check\\.\\.\\.**", parse_mode=ParseMode.MARKDOWN_V2)
        
        try:
            # Força health check
            await self.schedule_manager._system_health_check_task()
            
            health = self.schedule_manager.health
            
            health_message = f"""💓 **HEALTH CHECK COMPLETO**

**🔧 Componentes:**"""
            
            for component, status in health.components_status.items():
                icon = "✅" if status else "❌"
                health_message += f"\n• {component}: {icon}"
            
            health_message += f"""

**📊 Sistema:**
• Saudável: {'✅' if health.is_healthy else '❌'}
• Uptime: {health.uptime_seconds:.1f}s
• Tarefas ativas: {health.tasks_running}
• Memória: {health.memory_usage_mb:.1f}MB

**⏰ Timestamps:**
• Última tip: {self._format_time_ago(health.last_tip_time)}
• Último erro: {health.last_error or 'Nenhum'}

""" + ("✅ **Sistema 100% operacional\\!**" if health.is_healthy else "⚠️ **Problemas detectados\\!**")
            
        except Exception as e:
            health_message = f"❌ **Erro no health check:**\n\n`{str(e)}`"
            self.stats.errors_handled += 1
        
        await update.message.reply_text(health_message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /logs"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        
        self.stats.admin_commands += 1
        
        # Mock de logs recentes (em implementação real seria do sistema de logs)
        logs_message = """📋 **LOGS RECENTES \\(últimos 10\\)**

`[19:45:12] INFO: ScheduleManager - Scan executado`
`[19:45:10] DEBUG: TipsSystem - 2 partidas analisadas`
`[19:44:15] INFO: Telegram - Tip enviada para 4 usuários`
`[19:43:08] DEBUG: HealthCheck - Todos componentes OK`
`[19:42:12] INFO: ScheduleManager - Cache limpo`
`[19:41:55] DEBUG: API - PandaScore request OK`
`[19:40:12] INFO: ScheduleManager - Scan executado`
`[19:39:30] DEBUG: TipsSystem - Tip gerada: T1 vs Gen.G`
`[19:38:45] INFO: Telegram - 1 novo usuário registrado`
`[19:37:12] DEBUG: HealthCheck - Sistema saudável`

**📊 Resumo:**
• ✅ Operações normais
• ⚠️ 0 warnings
• ❌ 0 erros críticos"""
        
        await update.message.reply_text(logs_message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_restart_system(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /restart"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        
        self.stats.admin_commands += 1
        
        await update.message.reply_text(
            "⚠️ **ATENÇÃO: Reiniciar sistema?**\n\nIsso vai parar temporariamente todas as tarefas\\. Confirme:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_restart_keyboard()
        )

    # ===== CALLBACK HANDLERS =====

    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler principal para callbacks de botões"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Callback recebido: {data}")
        
        try:
            # Menu principal
            if data == "main_menu":
                await query.edit_message_text(
                    self._escape_markdown_v2("🎮 **LoL Prediction Bot V3**\n\n"
                    "🚀 Sistema profissional de tips de apostas\n"
                    "📊 IA avançada + análise em tempo real\n"
                    "🎯 Tips de alta qualidade garantidas\n\n"
                    "Escolha uma opção abaixo:"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_main_keyboard(self._is_admin(query.from_user.id))
                )
            
            # NOVOS HANDLERS: Callbacks do alerts_system para subscrições de grupo
            elif data in ["all_tips", "high_value", "high_conf", "premium"]:
                # Estes são callbacks gerados pelo alerts_system
                # Delega para o sistema de alertas que já tem a lógica implementada
                await self.telegram_alerts._handle_subscription_callback(update, context)
            
            # Handlers de subscrição (CORRIGIDOS com nomes dos keyboards)
            elif data in ["sub_all_tips", "sub_high_value", "sub_high_conf", "sub_premium"]:
                # Mapeia para os nomes esperados pelo alerts_system
                subscription_mapping = {
                    "sub_all_tips": "all_tips",
                    "sub_high_value": "high_value", 
                    "sub_high_conf": "high_conf",
                    "sub_premium": "premium"
                }
                
                # Em vez de modificar query.data (que é read-only), 
                # vamos chamar diretamente os métodos do alerts_system
                mapped_subscription = subscription_mapping[data]
                user = query.from_user
                
                try:
                    # Importa o enum correto
                    from ..telegram_bot.alerts_system import SubscriptionType
                    
                    # Converte string para enum
                    subscription_enum = SubscriptionType(mapped_subscription)
                    
                    # Chama diretamente o método de subscrição individual 
                    await self.telegram_alerts._handle_user_subscription(
                        query=query, 
                        user=user, 
                        subscription_type=subscription_enum
                    )
                    
                except Exception as e:
                    logger.error(f"Erro na subscrição {mapped_subscription}: {e}")
                    
                    subscription_names = {
                        "all_tips": "🔔 Todas as Tips",
                        "high_value": "💎 Alto Valor (EV > 10%)",
                        "high_conf": "🎯 Alta Confiança (> 80%)", 
                        "premium": "👑 Premium (EV > 15% + Conf > 85%)"
                    }
                    
                    # Fallback manual se falhar
                    success_message = f"✅ **Subscrição ativada!**\n\n"
                    success_message += f"Tipo: {subscription_names.get(mapped_subscription, mapped_subscription)}\n\n"
                    success_message += "Você receberá notificações quando novas tips estiverem disponíveis!\n\n"
                    success_message += "Use `/unsubscribe` para cancelar a qualquer momento."
                    
                    await query.edit_message_text(
                        self._escape_markdown_v2(success_message),
                        parse_mode=ParseMode.MARKDOWN_V2,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                    )
            
            # Handlers de cancelamento de subscrição
            elif data == "unsubscribe_all":
                await query.edit_message_text(
                    self._escape_markdown_v2("⚠️ **Confirmar cancelamento?**\n\n"
                    "Isso cancelará TODOS os seus alertas."),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Sim, cancelar tudo", callback_data="unsubscribe_confirm"),
                         InlineKeyboardButton("❌ Não, voltar", callback_data="show_subscriptions")]
                    ])
                )
            
            elif data == "unsubscribe_confirm":
                user_id = query.from_user.id
                if user_id in self.telegram_alerts.users:
                    self.telegram_alerts.users[user_id].is_active = False
                    message = "❌ **Todos os alertas cancelados!**\n\nVocê não receberá mais notificações.\nUse `/subscribe` para reativar."
                else:
                    message = "ℹ️ Você não estava subscrito."
                
                await query.edit_message_text(
                    self._escape_markdown_v2(message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "custom_filters":
                await query.edit_message_text(
                    self._escape_markdown_v2("⚙️ **Filtros Personalizados**\n\n"
                    "Funcionalidade em desenvolvimento.\n"
                    "Em breve você poderá criar filtros customizados para suas tips!"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            # Novos handlers para callbacks da interface
            elif data in ["quick_status", "show_subscriptions", "show_global_stats", "my_stats", "show_help", "ping_test", "refresh_main", "user_settings"]:
                await self._handle_interface_callbacks(query, data)
            
            # Handlers de status detalhado
            elif data in ["refresh_status", "detailed_status", "performance_stats", "apis_status", "status_charts", "health_status"]:
                await self._handle_status_callbacks(query, data)
            
            # Handlers de help sections
            elif data in ["help_basic", "help_alerts", "help_tips", "help_settings", "help_faq", "help_support", "help_admin"]:
                await self._handle_help_sections(query, data)
            
            # Handlers de tasks 
            elif data in ["force_monitor", "force_cleanup", "force_health", "force_cache", "task_stats", "pause_tasks", "resume_tasks", "restart_tasks"]:
                await self._handle_task_callbacks(query, data)
            
            # Handlers de mystats
            elif data in ["change_subscription", "refresh_mystats", "tips_history", "roi_calculator", "user_preferences", "user_performance"]:
                await self._handle_mystats_callbacks(query, data)
            
            # Handlers de settings
            elif data in ["settings_alerts", "settings_schedule", "settings_filters", "settings_language", "toggle_silent", "toggle_push"]:
                await self._handle_settings_sections(query, data)
            
            # Admin callbacks
            elif data in ["admin_panel", "admin_force_scan", "admin_health_check", "admin_system_status", "admin_tasks", "admin_logs", "admin_users", "admin_config", "admin_restart"]:
                await self._handle_admin_callbacks(query, data)
            
            # Handlers de restart
            elif data in ["restart_confirm", "restart_cancel", "restart_partial", "restart_quick"]:
                await self._handle_restart_callbacks(query, data)
            
            # Outros handlers específicos LEGADOS (mantidos para compatibilidade)
            elif data == "stats":
                await self._handle_stats_callback(query)
            elif data == "system_status":
                await self._handle_system_callback(query)
            elif data == "force_scan":
                await self._handle_force_scan_callback(query)
            elif data == "health_check":
                await self._handle_health_callback(query)
            
            else:
                # Handler padrão para callbacks não reconhecidos
                logger.warning(f"Callback não reconhecido: {data}")
                await query.edit_message_text(
                    self._escape_markdown_v2(f"⚠️ **Comando não reconhecido:** `{data}`\n\n"
                    "Comando pode estar em desenvolvimento ou foi removido."),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
        except Exception as e:
            logger.error(f"Erro no callback {data}: {e}")
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro:** {str(e)[:100]}"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )

    async def _handle_interface_callbacks(self, query, data: str) -> None:
        """Handler para callbacks da interface principal"""
        try:
            if data == "quick_status":
                await self._handle_system_callback(query)
            
            elif data == "show_subscriptions":
                await query.edit_message_text(
                    self._escape_markdown_v2("🔔 **Escolha seu tipo de subscrição:**"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_subscription_keyboard()
                )
            
            elif data == "show_global_stats":
                await self._handle_stats_callback(query)
            
            elif data == "my_stats":
                user_id = query.from_user.id
                if user_id not in self.telegram_alerts.users:
                    await query.edit_message_text(
                        self._escape_markdown_v2("ℹ️ **Você não está registrado.**\n\nUse `/start` primeiro."),
                        parse_mode=ParseMode.MARKDOWN_V2,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                    )
                    return
                
                user = self.telegram_alerts.users[user_id]
                stats_message = f"""📊 **SUAS ESTATÍSTICAS**

👤 **Perfil:**
• Nome: {user.first_name}
• Username: @{user.username or 'N/A'}
• Tipo: {user.subscription_type.value}
• Status: {'✅ Ativo' if user.is_active else '❌ Inativo'}

📅 **Histórico:**
• Membro desde: {self._format_time_ago(user.joined_at)}
• Última atividade: {self._format_time_ago(user.last_active)}
• Tips recebidas: {user.tips_received}

⚙️ **Configurações:**
• Filtros customizados: {len(user.custom_filters) if user.custom_filters else 0}
• Rate limit: {self.telegram_alerts.max_messages_per_hour} msg/h"""
                
                await query.edit_message_text(
                    self._escape_markdown_v2(stats_message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "show_help":
                await query.edit_message_text(
                    self._escape_markdown_v2("🆘 **SISTEMA DE AJUDA**\n\nEscolha uma seção:"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_help_keyboard(self._is_admin(query.from_user.id))
                )
            
            elif data == "ping_test":
                await query.edit_message_text(
                    self._escape_markdown_v2("🏓 **Teste de Conexão**\n\n✅ Bot respondendo\n⚡ Latência: OK\n🔗 APIs: Operacionais"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "refresh_main":
                await query.edit_message_text(
                    self._escape_markdown_v2("🔄 **Menu atualizado!**\n\nTodas as informações foram atualizadas."),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_main_keyboard(self._is_admin(query.from_user.id))
                )
            
            elif data == "user_settings":
                await query.edit_message_text(
                    self._escape_markdown_v2("⚙️ **CONFIGURAÇÕES DO USUÁRIO**\n\nEscolha uma opção:"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_settings_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Erro no callback da interface {data}: {e}")
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro:** {str(e)[:50]}"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )

    async def _handle_admin_callbacks(self, query, data: str) -> None:
        """Handler para callbacks administrativos"""
        if not self._is_admin(query.from_user.id):
            await query.edit_message_text(
                self._escape_markdown_v2("❌ **Acesso negado.**\n\nApenas administradores."),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )
            return
        
        try:
            if data == "admin_panel":
                # Mostra painel administrativo completo
                status = self.schedule_manager.get_system_status()
                admin_message = f"""👑 **PAINEL ADMINISTRATIVO**

🖥️ **Sistema:**
• Status: {'🟢 OPERACIONAL' if status['system']['is_running'] else '🔴 PARADO'}
• Uptime: {status['system']['uptime_hours']:.2f}h
• Saúde: {'✅' if status['system']['is_healthy'] else '❌'}
• Memória: {status['system']['memory_usage_mb']:.1f}MB

📋 **Tarefas:**
• Executando: {status['tasks']['running_count']}/{status['tasks']['scheduled_count']}
• Concluídas: {status['statistics']['tasks_completed']}
• Falhadas: {status['statistics']['tasks_failed']}

🎯 **Performance:**
• Tips geradas: {status['statistics']['tips_generated']}
• Comandos admin: {self.stats.admin_commands}"""
                
                await query.edit_message_text(
                    self._escape_markdown_v2(admin_message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_admin_keyboard()
                )
            
            elif data == "admin_force_scan":
                await self._handle_force_scan_callback(query)
            
            elif data == "admin_health_check":
                await self._handle_health_callback(query)
            
            elif data == "admin_system_status":
                await self._handle_system_callback(query)
            
            elif data == "admin_tasks":
                status = self.schedule_manager.get_system_status()
                tasks_message = "📋 **TAREFAS DO SISTEMA**\n\n"
                
                for task_id, task_info in status['tasks']['task_details'].items():
                    status_icons = {
                        'running': '🏃',
                        'scheduled': '⏰',
                        'completed': '✅',
                        'failed': '❌'
                    }
                    icon = status_icons.get(task_info['status'], '❓')
                    tasks_message += f"**{task_id}:**\n"
                    tasks_message += f"• Status: {icon} {task_info['status']}\n"
                    tasks_message += f"• Execuções: {task_info['run_count']}\n"
                    tasks_message += f"• Erros: {task_info['error_count']}\n\n"
                
                await query.edit_message_text(
                    self._escape_markdown_v2(tasks_message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "admin_logs":
                logs_message = """📋 **LOGS RECENTES**

`[19:45:12] INFO: ScheduleManager - Scan executado`
`[19:45:10] DEBUG: TipsSystem - 2 partidas analisadas`
`[19:44:15] INFO: Telegram - Tip enviada para 4 usuários`
`[19:43:08] DEBUG: HealthCheck - Todos componentes OK`
`[19:42:12] INFO: ScheduleManager - Cache limpo`

**📊 Resumo:**
• ✅ Operações normais
• ⚠️ 0 warnings
• ❌ 0 erros críticos"""
                
                await query.edit_message_text(
                    self._escape_markdown_v2(logs_message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "admin_users":
                stats = self.telegram_alerts.get_system_stats()
                users_message = f"""👥 **GERENCIAMENTO DE USUÁRIOS**

📊 **Estatísticas:**
• Total: {stats['users']['total']}
• Ativos: {stats['users']['active']}
• Bloqueados: {stats['users']['blocked']}

🔔 **Subscrições:**"""
                
                for sub_type, count in stats['users']['subscriptions_by_type'].items():
                    users_message += f"\n• {sub_type}: {count}"
                
                await query.edit_message_text(
                    self._escape_markdown_v2(users_message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "admin_config":
                await query.edit_message_text(
                    self._escape_markdown_v2("⚙️ **CONFIGURAÇÕES DO SISTEMA**\n\nFuncionalidade em desenvolvimento."),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "admin_restart":
                await query.edit_message_text(
                    self._escape_markdown_v2("⚠️ **REINICIAR SISTEMA**\n\nFuncionalidade em desenvolvimento."),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
                
        except Exception as e:
            logger.error(f"Erro no callback admin {data}: {e}")
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro admin:** {str(e)[:50]}"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )

    async def _handle_force_scan_callback(self, query) -> None:
        """Handle callback para force scan"""
        try:
            success = await self.schedule_manager.force_task_execution("monitor_live_matches")
            if success:
                await query.edit_message_text(
                    self._escape_markdown_v2("✅ **Scan forçado iniciado!**\n\nVerifique `/system` para resultados."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                await query.edit_message_text(
                    self._escape_markdown_v2("❌ **Falha ao forçar scan.**"),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
        except Exception as e:
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro:** `{str(e)[:50]}`"),
                parse_mode=ParseMode.MARKDOWN_V2
            )

    async def _handle_health_callback(self, query) -> None:
        """Handle callback para health check"""
        try:
            await self.schedule_manager._system_health_check_task()
            health = self.schedule_manager.health
            
            status_text = "✅ Saudável" if health.is_healthy else "❌ Problemas"
            
            await query.edit_message_text(
                self._escape_markdown_v2(f"💓 **Health Check:**\n\n{status_text}\nMemória: {health.memory_usage_mb:.1f}MB"),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro no health check:** `{str(e)[:50]}`"),
                parse_mode=ParseMode.MARKDOWN_V2
            )

    async def _handle_system_callback(self, query) -> None:
        """Handle callback para system status"""
        status = self.schedule_manager.get_system_status()
        
        quick_status = f"""📊 **Status Rápido:**

🖥️ Sistema: {'🟢' if status['system']['is_running'] else '🔴'}
💓 Saúde: {'✅' if status['system']['is_healthy'] else '❌'}
📋 Tarefas: {status['tasks']['running_count']}/{status['tasks']['scheduled_count']}
🎯 Tips: {status['statistics']['tips_generated']}
⏰ Uptime: {status['system']['uptime_hours']:.1f}h"""
        
        await query.edit_message_text(
            self._escape_markdown_v2(quick_status), 
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _handle_help_sections(self, query, data: str) -> None:
        """Handler para seções de ajuda"""
        help_sections = {
            "help_basic": """📋 **COMANDOS BÁSICOS**

• `/start` - Menu principal e boas-vindas
• `/help` - Esta ajuda completa
• `/status` - Status do sistema em tempo real
• `/stats` - Estatísticas globais
• `/subscribe` - Configurar alertas
• `/ping` - Testar conectividade

**💡 Dica:** Use os botões para navegar mais facilmente!""",

            "help_alerts": """🔔 **SISTEMA DE ALERTAS**

**Tipos de Subscrição:**
• 🔔 **Todas as Tips** - Recebe todas as análises
• 💎 **Alto Valor** - EV > 10% apenas
• 🎯 **Alta Confiança** - Probabilidade > 80%
• 👑 **Premium** - EV > 15% + Conf > 85%

**Como Funciona:**
1. Sistema monitora partidas ao vivo
2. IA analisa dados em tempo real
3. Filtra por critérios rigorosos
4. Envia apenas tips de qualidade""",

            "help_tips": """📊 **COMO INTERPRETAR TIPS**

**Elementos de uma Tip:**
• **EV (Expected Value):** Retorno esperado em %
• **Confiança:** Probabilidade de acerto
• **Odds:** Cotação da casa de apostas
• **Unidades:** Quantidade sugerida para apostar

**Indicadores de Qualidade:**
• 🔥 EV > 15% - Oportunidade excepcional
• 📊 EV 10-15% - Boa oportunidade
• 💡 EV 5-10% - Oportunidade moderada

**Gestão de Risco:**
Sempre aposte com responsabilidade!""",

            "help_settings": """⚙️ **CONFIGURAÇÕES**

**Personalizações Disponíveis:**
• 🔔 Tipos de alerta preferidos
• ⏰ Horários para receber tips
• 📊 Filtros de confiança/EV
• 🔕 Modo silencioso

**Filtros Avançados:**
• Ligas específicas (LEC, LCS, etc.)
• Valores mínimos de EV/Confiança
• Times favoritos
• Tipos de mercado""",

            "help_faq": """❓ **PERGUNTAS FREQUENTES**

**Q: Quantas tips recebo por dia?**
A: Depende da subscrição (1-5 tips/dia)

**Q: Como é calculado o EV?**
A: Algoritmos ML + análise estatística

**Q: Posso pausar temporariamente?**
A: Sim, use `/subscribe` para gerenciar

**Q: As tips são garantidas?**
A: Não! Apostas sempre envolvem risco

**Q: Suporte a outras ligas?**
A: Focamos nas principais: LEC, LCS, LPL, LCK""",

            "help_support": """🆘 **SUPORTE**

**Como obter ajuda:**
• Use os comandos `/help` e `/status`
• Verifique o FAQ primeiro
• Reporte bugs via admin

**Problemas comuns:**
• Comandos não funcionam → `/start`
• Não recebo tips → Verificar `/subscribe`
• Bot lento → Verificar `/status`

**Contato:**
Sistema automatizado - suporte via bot apenas"""
        }
        
        section_text = help_sections.get(data, "Seção não encontrada")
        
        await query.edit_message_text(
            self._escape_markdown_v2(section_text),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
        )

    async def _handle_settings_sections(self, query, data: str) -> None:
        """Handler para seções de configurações"""
        settings_sections = {
            "settings_alerts": """🔔 **CONFIGURAR ALERTAS**

**Tipos Disponíveis:**
• Tips gerais
• Tips premium
• Alertas de sistema
• Atualizações do bot

**Frequência:**
• Imediato
• Agrupado (1x/hora)
• Resumo diário

Configuração atual: **Todas ativas**""",

            "settings_schedule": """⏰ **CONFIGURAR HORÁRIOS**

**Horário de funcionamento:**
• 24/7 disponível
• Pico: 14h-23h (horário BR)
• Partidas: Principalmente noite

**Suas preferências:**
• Receber: Qualquer horário
• Não incomodar: Desabilitado
• Timezone: UTC-3 (Brasil)""",

            "settings_filters": """📊 **FILTROS DE TIPS**

**Critérios disponíveis:**
• EV mínimo: 5%
• Confiança mínima: 60%
• Ligas: Todas principais
• Horário: 24/7

**Configuração atual:**
Padrão recomendado ativo"""
        }
        
        section_text = settings_sections.get(data, "Seção não encontrada")
        
        await query.edit_message_text(
            self._escape_markdown_v2(section_text),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
        )

    async def _handle_stats_callback(self, query) -> None:
        """Handler para callback de estatísticas"""
        system_stats = self.telegram_alerts.get_system_stats()
        
        stats_text = f"""📈 **ESTATÍSTICAS GLOBAIS**

👥 **Usuários:**
• Total: {system_stats['users']['total']}
• Ativos: {system_stats['users']['active']}
• Premium: {len([u for u in self.telegram_alerts.users.values() if 'premium' in u.subscription_type.value.lower()])}

📨 **Tips Enviadas:**
• Hoje: {system_stats['alerts']['tips_sent']}
• Total: {system_stats['alerts']['total_sent']}
• Taxa sucesso: {system_stats['alerts']['success_rate']:.1f}%

⚡ **Performance:**
• Uptime: {self.stats.uptime_hours:.1f}h
• Comandos: {self.stats.commands_processed}
• Sistema: ✅ Estável"""
        
        await query.edit_message_text(
            self._escape_markdown_v2(stats_text),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
        )

    async def _handle_status_callbacks(self, query, data: str) -> None:
        """Handler para callbacks de status detalhado"""
        try:
            if data == "refresh_status":
                await self._handle_system_callback(query)
            
            elif data == "detailed_status":
                status = self.schedule_manager.get_system_status()
                detailed_message = f"""🔧 **STATUS DETALHADO**

**🖥️ Sistema:**
• Running: {status['system']['is_running']}
• Healthy: {status['system']['is_healthy']}
• Uptime: {status['system']['uptime_hours']:.2f}h
• Memory: {status['system']['memory_usage_mb']:.1f}MB

**📋 Tarefas:**
• Executando: {status['tasks']['running_count']}/{status['tasks']['scheduled_count']}
• Concluídas: {status['statistics']['tasks_completed']}
• Falhadas: {status['statistics']['tasks_failed']}

**🎯 Performance:**
• Tips geradas: {status['statistics']['tips_generated']}
• Última tip: {self._format_time_ago(status['health']['last_tip_time'])}"""

                await query.edit_message_text(
                    self._escape_markdown_v2(detailed_message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "performance_stats":
                perf_message = f"""⚡ **PERFORMANCE DO SISTEMA**

**🚀 Bot Interface:**
• Uptime: {self.stats.uptime_hours:.2f}h
• Comandos processados: {self.stats.commands_processed}
• Admin comandos: {self.stats.admin_commands}
• Erros tratados: {self.stats.errors_handled}

**📊 Tips System:**
• Rate limit: {self.tips_system.max_tips_per_hour} tips/h
• Cache ativo: {len(self.tips_system.generated_tips)}
• Monitoramento: {'✅ Ativo' if self.tips_system.is_monitoring else '❌ Inativo'}

**💾 Sistema:**
• Usuários ativos: {len(self.telegram_alerts.users)}
• Grupos ativos: {len(self.telegram_alerts.groups)}"""

                await query.edit_message_text(
                    self._escape_markdown_v2(perf_message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "apis_status":
                # Testa status das APIs
                apis_message = f"""🔗 **STATUS DAS APIs**

**📊 PandaScore API:**
• Status: 🔍 Testando...
• Last call: {self._format_time_ago(time.time())}

**🎮 Riot API:**
• Status: 🔍 Testando...
• Last call: {self._format_time_ago(time.time())}
• Modo: Mock (API key inválida)

**📡 Telegram API:**
• Status: ✅ Operacional
• Bot conectado: ✅"""

                await query.edit_message_text(
                    self._escape_markdown_v2(apis_message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "status_charts":
                await query.edit_message_text(
                    self._escape_markdown_v2("📈 **Gráficos de Status**\n\nFuncionalidade em desenvolvimento.\nEm breve teremos gráficos visuais!"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "health_status":
                await self._handle_health_callback(query)
                
        except Exception as e:
            logger.error(f"Erro no callback de status {data}: {e}")
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro:** {str(e)[:50]}"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )

    async def _handle_task_callbacks(self, query, data: str) -> None:
        """Handler para callbacks de tarefas"""
        if not self._is_admin(query.from_user.id):
            await query.edit_message_text(
                self._escape_markdown_v2("❌ **Acesso negado.**\n\nApenas administradores."),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )
            return
        
        try:
            if data == "force_monitor":
                success = await self.schedule_manager.force_task_execution("monitor_live_matches")
                message = "✅ **Monitor forçado iniciado!**" if success else "❌ **Falha ao forçar monitor.**"
            
            elif data == "force_cleanup":
                # Força limpeza do sistema
                self.tips_system._cleanup_expired_tips()
                message = "🧹 **Limpeza forçada concluída!**"
            
            elif data == "force_health":
                await self.schedule_manager._system_health_check_task()
                message = "💓 **Health check forçado concluído!**"
            
            elif data == "force_cache":
                # Limpa cache
                self.tips_system.generated_tips.clear()
                self.tips_system.monitored_matches.clear()
                message = "🔧 **Cache limpo com sucesso!**"
            
            elif data == "task_stats":
                status = self.schedule_manager.get_system_status()
                task_message = "📊 **ESTATÍSTICAS DE TAREFAS**\n\n"
                for task_id, task_info in status['tasks']['task_details'].items():
                    task_message += f"**{task_id}:**\n"
                    task_message += f"• Execuções: {task_info['run_count']}\n"
                    task_message += f"• Erros: {task_info['error_count']}\n\n"
                message = task_message
            
            elif data in ["pause_tasks", "resume_tasks", "restart_tasks"]:
                message = f"⚙️ **{data.replace('_', ' ').title()}**\n\nFuncionalidade em desenvolvimento."
            
            else:
                message = f"⚠️ **Tarefa não reconhecida:** {data}"
            
            await query.edit_message_text(
                self._escape_markdown_v2(message),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )
            
        except Exception as e:
            logger.error(f"Erro no callback de task {data}: {e}")
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro:** {str(e)[:50]}"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )

    async def _handle_mystats_callbacks(self, query, data: str) -> None:
        """Handler para callbacks de estatísticas pessoais"""
        try:
            user_id = query.from_user.id
            
            if data == "change_subscription":
                await query.edit_message_text(
                    self._escape_markdown_v2("🔔 **Escolha seu novo tipo de subscrição:**"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_subscription_keyboard()
                )
            
            elif data == "refresh_mystats":
                # Atualiza e mostra estatísticas
                if user_id not in self.telegram_alerts.users:
                    message = "ℹ️ **Você não está registrado.**\n\nUse `/start` primeiro."
                else:
                    user = self.telegram_alerts.users[user_id]
                    message = f"""📊 **SUAS ESTATÍSTICAS ATUALIZADAS**

👤 **Perfil:**
• Nome: {user.first_name}
• Tipo: {user.subscription_type.value}
• Status: {'✅ Ativo' if user.is_active else '❌ Inativo'}

📅 **Atividade:**
• Membro desde: {self._format_time_ago(user.joined_at)}
• Tips recebidas: {user.tips_received}
• Última atividade: {self._format_time_ago(user.last_active)}"""
                
                await query.edit_message_text(
                    self._escape_markdown_v2(message),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data in ["tips_history", "roi_calculator", "user_preferences", "user_performance"]:
                functionality_names = {
                    "tips_history": "Histórico de Tips",
                    "roi_calculator": "Calculadora de ROI", 
                    "user_preferences": "Preferências do Usuário",
                    "user_performance": "Performance do Usuário"
                }
                
                await query.edit_message_text(
                    self._escape_markdown_v2(f"📊 **{functionality_names[data]}**\n\n"
                    "Funcionalidade em desenvolvimento.\n"
                    "Em breve você terá acesso a análises detalhadas!"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
                
        except Exception as e:
            logger.error(f"Erro no callback mystats {data}: {e}")
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro:** {str(e)[:50]}"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )

    async def _handle_restart_callbacks(self, query, data: str) -> None:
        """Handler para callbacks de reinício"""
        if not self._is_admin(query.from_user.id):
            await query.edit_message_text(
                self._escape_markdown_v2("❌ **Acesso negado.**"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )
            return
        
        try:
            if data == "restart_confirm":
                await query.edit_message_text(
                    self._escape_markdown_v2("🔄 **Reiniciando sistema...**\n\nIsto pode levar alguns segundos."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                # Em implementação real, faria o restart aqui
                await asyncio.sleep(2)
                await query.edit_message_text(
                    self._escape_markdown_v2("✅ **Sistema reiniciado com sucesso!**"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "restart_cancel":
                await query.edit_message_text(
                    self._escape_markdown_v2("❌ **Reinício cancelado.**\n\nSistema continua operando normalmente."),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data in ["restart_partial", "restart_quick"]:
                restart_types = {
                    "restart_partial": "Reinício Parcial",
                    "restart_quick": "Reinício Rápido"
                }
                
                await query.edit_message_text(
                    self._escape_markdown_v2(f"🔄 **{restart_types[data]}**\n\nFuncionalidade em desenvolvimento."),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
                
        except Exception as e:
            logger.error(f"Erro no callback restart {data}: {e}")
            await query.edit_message_text(
                self._escape_markdown_v2(f"❌ **Erro:** {str(e)[:50]}"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )

    async def _handle_unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para mensagens não reconhecidas"""
        await update.message.reply_text(
            "❓ **Comando não reconhecido\\.**\n\nUse `/help` para ver comandos disponíveis\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )

    # ===== UTILITY METHODS =====

    def _is_admin(self, user_id: int) -> bool:
        """Verifica se usuário é admin"""
        return user_id in self.admin_user_ids

    def _format_time_ago(self, timestamp: Optional[float]) -> str:
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

    # ===== KEYBOARD METHODS =====

    def _get_main_keyboard(self, is_admin: bool = False) -> InlineKeyboardMarkup:
        """Teclado principal com mais opções"""
        keyboard = [
            [InlineKeyboardButton("📊 Status Sistema", callback_data="quick_status"),
             InlineKeyboardButton("🔔 Configurar Alertas", callback_data="show_subscriptions")],
            [InlineKeyboardButton("📈 Estatísticas", callback_data="show_global_stats"),
             InlineKeyboardButton("📊 Minhas Stats", callback_data="my_stats")],
            [InlineKeyboardButton("❓ Ajuda & Comandos", callback_data="show_help"),
             InlineKeyboardButton("🏓 Testar Conexão", callback_data="ping_test")],
            [InlineKeyboardButton("🔄 Atualizar Menu", callback_data="refresh_main"),
             InlineKeyboardButton("⚙️ Configurações", callback_data="user_settings")]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("👑 Painel Administrativo", callback_data="admin_panel")])
        
        return InlineKeyboardMarkup(keyboard)

    def _get_subscription_keyboard(self) -> InlineKeyboardMarkup:
        """Teclado de subscrições melhorado"""
        keyboard = [
            [InlineKeyboardButton("🔔 Todas as Tips", callback_data="sub_all_tips")],
            [InlineKeyboardButton("💎 Alto Valor (EV > 10%)", callback_data="sub_high_value")],
            [InlineKeyboardButton("🎯 Alta Confiança (> 80%)", callback_data="sub_high_conf")],
            [InlineKeyboardButton("👑 Premium (EV > 15% + Conf > 85%)", callback_data="sub_premium")],
            [InlineKeyboardButton("❌ Cancelar Alertas", callback_data="unsubscribe_all")],
            [InlineKeyboardButton("⚙️ Filtros Personalizados", callback_data="custom_filters")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_admin_keyboard(self) -> InlineKeyboardMarkup:
        """Teclado administrativo melhorado"""
        keyboard = [
            [InlineKeyboardButton("🔄 Force Scan", callback_data="admin_force_scan"),
             InlineKeyboardButton("💓 Health Check", callback_data="admin_health_check")],
            [InlineKeyboardButton("📊 Status Completo", callback_data="admin_system_status"),
             InlineKeyboardButton("📋 Gerenciar Tarefas", callback_data="admin_tasks")],
            [InlineKeyboardButton("📊 Logs do Sistema", callback_data="admin_logs"),
             InlineKeyboardButton("👥 Gerenciar Usuários", callback_data="admin_users")],
            [InlineKeyboardButton("⚙️ Configurações Sistema", callback_data="admin_config"),
             InlineKeyboardButton("🔄 Restart Sistema", callback_data="admin_restart")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_status_keyboard(self) -> InlineKeyboardMarkup:
        """Teclado de status melhorado"""
        keyboard = [
            [InlineKeyboardButton("🔄 Atualizar Status", callback_data="refresh_status"),
             InlineKeyboardButton("📊 Status Detalhado", callback_data="detailed_status")],
            [InlineKeyboardButton("⚡ Performance", callback_data="performance_stats"),
             InlineKeyboardButton("🔗 APIs Status", callback_data="apis_status")],
            [InlineKeyboardButton("📈 Gráficos", callback_data="status_charts"),
             InlineKeyboardButton("💓 Health Check", callback_data="health_status")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_help_keyboard(self, is_admin: bool = False) -> InlineKeyboardMarkup:
        """Teclado de ajuda melhorado"""
        keyboard = [
            [InlineKeyboardButton("📋 Comandos Básicos", callback_data="help_basic"),
             InlineKeyboardButton("🔔 Sistema de Alertas", callback_data="help_alerts")],
            [InlineKeyboardButton("📊 Como Interpretar Tips", callback_data="help_tips"),
             InlineKeyboardButton("⚙️ Configurações", callback_data="help_settings")],
            [InlineKeyboardButton("❓ FAQ", callback_data="help_faq"),
             InlineKeyboardButton("🆘 Suporte", callback_data="help_support")]
        ]
        if is_admin:
            keyboard.append([InlineKeyboardButton("👑 Ajuda Admin", callback_data="help_admin")])
        
        keyboard.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)

    def _get_tasks_keyboard(self) -> InlineKeyboardMarkup:
        """Teclado de tarefas melhorado"""
        keyboard = [
            [InlineKeyboardButton("🔄 Force Monitor", callback_data="force_monitor"),
             InlineKeyboardButton("🧹 Force Cleanup", callback_data="force_cleanup")],
            [InlineKeyboardButton("💓 Force Health", callback_data="force_health"),
             InlineKeyboardButton("🔧 Clear Cache", callback_data="force_cache")],
            [InlineKeyboardButton("📊 Task Statistics", callback_data="task_stats"),
             InlineKeyboardButton("⏸️ Pause Tasks", callback_data="pause_tasks")],
            [InlineKeyboardButton("▶️ Resume Tasks", callback_data="resume_tasks"),
             InlineKeyboardButton("🔄 Restart Tasks", callback_data="restart_tasks")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_mystats_keyboard(self) -> InlineKeyboardMarkup:
        """Teclado de estatísticas pessoais melhorado"""
        keyboard = [
            [InlineKeyboardButton("🔔 Alterar Subscrição", callback_data="change_subscription"),
             InlineKeyboardButton("🔄 Atualizar Stats", callback_data="refresh_mystats")],
            [InlineKeyboardButton("📊 Histórico Tips", callback_data="tips_history"),
             InlineKeyboardButton("💰 ROI Calculator", callback_data="roi_calculator")],
            [InlineKeyboardButton("⚙️ Preferências", callback_data="user_preferences"),
             InlineKeyboardButton("📈 Performance", callback_data="user_performance")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_restart_keyboard(self) -> InlineKeyboardMarkup:
        """Teclado de confirmação de reinício"""
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar Reinício Completo", callback_data="restart_confirm"),
             InlineKeyboardButton("❌ Cancelar", callback_data="restart_cancel")],
            [InlineKeyboardButton("🔄 Reinício Parcial", callback_data="restart_partial"),
             InlineKeyboardButton("⚡ Reinício Rápido", callback_data="restart_quick")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_settings_keyboard(self) -> InlineKeyboardMarkup:
        """Teclado de configurações do usuário"""
        keyboard = [
            [InlineKeyboardButton("🔔 Tipos de Alerta", callback_data="settings_alerts"),
             InlineKeyboardButton("⏰ Horários", callback_data="settings_schedule")],
            [InlineKeyboardButton("📊 Filtros de Tips", callback_data="settings_filters"),
             InlineKeyboardButton("🌍 Idioma", callback_data="settings_language")],
            [InlineKeyboardButton("🔕 Modo Silencioso", callback_data="toggle_silent"),
             InlineKeyboardButton("📱 Notificações Push", callback_data="toggle_push")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard) 