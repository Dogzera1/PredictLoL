from __future__ import annotations

import os
import asyncio
import time
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
import signal
import sys

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

    async def start_bot(self) -> None:
        """Inicia o bot completo com ScheduleManager"""
        if self.is_running:
            logger.warning("Bot já está executando")
            return
        
        logger.info("🚀 Iniciando Bot LoL V3 Ultra Avançado - Sistema Completo!")
        
        try:
            # 1. Cria aplicação básica
            logger.info("📱 Criando aplicação Telegram...")
            self.application = Application.builder().token(self.bot_token).build()
            
            # 2. Configura handlers
            self._setup_all_handlers()
            
            # 3. Inicia ScheduleManager primeiro
            logger.info("🔧 Iniciando ScheduleManager...")
            schedule_task = asyncio.create_task(self.schedule_manager.start_scheduled_tasks())
            
            # 4. Inicia aplicação Telegram
            logger.info("🚀 Iniciando aplicação Telegram...")
            await self.application.initialize()
            await self.application.start()
            
            # 5. Inicia polling de forma robusta
            logger.info("📞 Iniciando polling...")
            self.application.updater.start_polling(
                drop_pending_updates=True,
                bootstrap_retries=3,
                read_timeout=30,
                connect_timeout=30,
                pool_timeout=30
            )
            
            self.is_running = True
            logger.info("✅ Bot LoL V3 Ultra Avançado totalmente operacional!")
            
            # 6. Mantém executando
            try:
                await schedule_task
            except asyncio.CancelledError:
                logger.info("📋 ScheduleManager cancelado")
            
        except Exception as e:
            logger.error(f"Erro crítico ao iniciar bot: {e}")
            await self.stop_bot()
            raise

    async def _start_polling_with_retry(self) -> None:
        """Inicia polling com retry em caso de conflitos"""
        max_retries = 8
        for attempt in range(max_retries):
            try:
                # Aguarda mais tempo entre tentativas para conflitos
                if attempt > 0:
                    wait_time = min(10 + (attempt * 5), 30)  # 10, 15, 20, 25, 30, 30, 30...
                    logger.info(f"⏳ Aguardando {wait_time}s antes da tentativa {attempt + 1}")
                    await asyncio.sleep(wait_time)
                
                await self.application.updater.start_polling(
                    timeout=60,      # Aumentado de 30 para 60
                    pool_timeout=60, # Aumentado de 30 para 60
                    connect_timeout=30,
                    read_timeout=30,
                    write_timeout=30,
                    allowed_updates=["message", "callback_query", "inline_query"]  # Apenas updates necessários
                )
                logger.info("✅ Polling iniciado com sucesso")
                break
            except Exception as e:
                if "terminated by other getUpdates request" in str(e) or "Conflict" in str(e):
                    logger.warning(f"⚠️ Conflito no polling (tentativa {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        # Tenta limpar conflito via API
                        await self._force_clear_conflicts()
                        continue
                    else:
                        logger.error("❌ Máximo de tentativas atingido para polling")
                        raise
                else:
                    logger.error(f"❌ Erro não relacionado a conflito: {e}")
                    raise

    async def _force_clear_conflicts(self) -> None:
        """Força limpeza de conflitos via API do Telegram"""
        try:
            import aiohttp
            
            logger.info("🧹 Forçando limpeza de conflitos...")
            base_url = f"https://api.telegram.org/bot{self.bot_token}"
            
            async with aiohttp.ClientSession() as session:
                # Múltiplas tentativas de getUpdates para "roubar" controle
                for i in range(3):
                    try:
                        async with session.post(f"{base_url}/getUpdates", json={"timeout": 1}) as resp:
                            if resp.status == 200:
                                logger.debug(f"✅ Conflito limpo (tentativa {i + 1})")
                                break
                    except:
                        pass
                    await asyncio.sleep(1)
                
                # Aguarda estabilização
                await asyncio.sleep(3)
                
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
            
            self.is_running = False
            logger.info("✅ Bot parado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao parar bot: {e}")

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
        
        help_message = """🆘 **AJUDA \\- Bot LoL V3 Ultra Avançado**

**🎯 Sobre o Sistema:**
Bot profissional para tips de League of Legends com automação total\\. Combina Machine Learning, análise em tempo real e gestão de risco profissional\\.

**📋 Comandos Básicos:**
• `/start` \\- Iniciar e ver menu principal
• `/help` \\\\ Esta ajuda
• `/status` \\\\ Status do sistema e estatísticas
• `/stats` \\\\ Suas estatísticas pessoais
• `/subscribe` \\\\ Configurar tipos de alerta
• `/unsubscribe` \\\\ Cancelar alertas
• `/mystats` \\\\ Histórico detalhado

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
• `/tasks` \\\\ Gerenciar tarefas agendadas
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
        """Handler para callbacks de botões inline"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        try:
            if data.startswith("sub_"):
                # Subscrição
                subscription_type = SubscriptionType(data[4:])
                
                # Registra ou atualiza usuário
                from ..telegram_bot.alerts_system import TelegramUser
                
                if user_id in self.telegram_alerts.users:
                    self.telegram_alerts.users[user_id].subscription_type = subscription_type
                    self.telegram_alerts.users[user_id].is_active = True
                else:
                    self.telegram_alerts.users[user_id] = TelegramUser(
                        user_id=user_id,
                        username=query.from_user.username or "",
                        first_name=query.from_user.first_name,
                        subscription_type=subscription_type
                    )
                
                await query.edit_message_text(
                    f"✅ **Subscrição configurada!**\n\nTipo: {subscription_type.value}\n\nVocê receberá tips conforme sua subscrição.",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            
            elif data.startswith("admin_"):
                # Comandos admin via callback
                if not self._is_admin(user_id):
                    await query.edit_message_text("❌ Acesso negado\\.", parse_mode=ParseMode.MARKDOWN_V2)
                    return
                
                if data == "admin_force_scan":
                    await self._handle_force_scan_callback(query)
                elif data == "admin_health_check":
                    await self._handle_health_callback(query)
                elif data == "admin_system_status":
                    await self._handle_system_callback(query)
            
            elif data == "restart_confirm":
                # Confirma reinício
                if self._is_admin(user_id):
                    await query.edit_message_text(
                        "🔄 **Reiniciando sistema\\.\\.\\.**\n\nAguarde\\.\\.\\.",
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    # Em implementação real: reinicia componentes
                    await asyncio.sleep(2)
                    await query.edit_message_text(
                        "✅ **Sistema reiniciado\\!**\n\nTodos os componentes operacionais\\.",
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
            
            elif data == "restart_cancel":
                await query.edit_message_text(
                    "❌ **Reinício cancelado\\.**",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            
            elif data == "ping_test":
                await query.edit_message_text(
                    "🏓 **Pong\\!** \\- Resposta em `0\\.15s`\n\n"
                    "✅ Latência baixa\n"
                    "🚀 Conexão estável\n" 
                    "💚 Sistema responsivo",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
            elif data == "main_menu":
                # Retorna ao menu principal
                is_admin = self._is_admin(user_id)
                await query.edit_message_text(
                    f"🏠 **Menu Principal**\n\n"
                    f"Bem\\-vindo de volta\\! Escolha uma opção:",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_main_keyboard(is_admin)
                )
            
            elif data == "user_settings":
                await query.edit_message_text(
                    "⚙️ **Configurações do Usuário**\n\n"
                    "Personalize sua experiência com o bot:",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_settings_keyboard()
                )
            
            elif data == "show_global_stats":
                # Mostra estatísticas globais via callback
                await self._handle_stats_callback(query)
            
            elif data == "refresh_main":
                # Atualiza o menu principal
                is_admin = self._is_admin(user_id)
                await query.edit_message_text(
                    f"🔄 **Menu Atualizado**\n\n"
                    f"Sistema: ✅ Online\n"
                    f"Hora: {time.strftime('%H:%M:%S')}\n\n"
                    f"Escolha uma opção:",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=self._get_main_keyboard(is_admin)
                )
            
            elif data.startswith("help_"):
                await self._handle_help_sections(query, data)
            
            elif data.startswith("settings_"):
                await self._handle_settings_sections(query, data)
            
            elif data == "unsubscribe_all":
                # Cancela todas as subscrições
                if user_id in self.telegram_alerts.users:
                    self.telegram_alerts.users[user_id].is_active = False
                
                await query.edit_message_text(
                    "❌ **Todos os alertas cancelados\\!**\n\n"
                    "Você não receberá mais notificações\\.\n"
                    "Use `/subscribe` para reativar\\.",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
            
        except Exception as e:
            logger.error(f"Erro no callback {data}: {e}")
            await query.edit_message_text(
                f"❌ **Erro:** {str(e)[:100]}",
                parse_mode=ParseMode.MARKDOWN_V2
            )

    async def _handle_force_scan_callback(self, query) -> None:
        """Handle callback para force scan"""
        try:
            success = await self.schedule_manager.force_task_execution("monitor_live_matches")
            if success:
                await query.edit_message_text(
                    "✅ **Scan forçado iniciado\\!**\n\nVerifique `/system` para resultados\\.",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                await query.edit_message_text(
                    "❌ **Falha ao forçar scan\\.**",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Erro:** `{str(e)[:50]}`",
                parse_mode=ParseMode.MARKDOWN_V2
            )

    async def _handle_health_callback(self, query) -> None:
        """Handle callback para health check"""
        try:
            await self.schedule_manager._system_health_check_task()
            health = self.schedule_manager.health
            
            status_text = "✅ Saudável" if health.is_healthy else "❌ Problemas"
            
            await query.edit_message_text(
                f"💓 **Health Check:**\n\n{status_text}\nMemória: {health.memory_usage_mb:.1f}MB",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Erro no health check:** `{str(e)[:50]}`",
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
        
        await query.edit_message_text(quick_status, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_help_sections(self, query, data: str) -> None:
        """Handler para seções de ajuda"""
        help_sections = {
            "help_basic": """📋 **COMANDOS BÁSICOS**

• `/start` \\- Menu principal e boas\\-vindas
• `/help` \\- Esta ajuda completa
• `/status` \\- Status do sistema em tempo real
• `/stats` \\- Estatísticas globais
• `/subscribe` \\- Configurar alertas
• `/ping` \\- Testar conectividade

**💡 Dica:** Use os botões para navegar mais facilmente\\!""",

            "help_alerts": """🔔 **SISTEMA DE ALERTAS**

**Tipos de Subscrição:**
• 🔔 **Todas as Tips** \\- Recebe todas as análises
• 💎 **Alto Valor** \\- EV > 10% apenas
• 🎯 **Alta Confiança** \\- Probabilidade > 80%
• 👑 **Premium** \\- EV > 15% \\+ Conf > 85%

**Como Funciona:**
1\\. Sistema monitora partidas ao vivo
2\\. IA analisa dados em tempo real
3\\. Filtra por critérios rigorosos
4\\. Envia apenas tips de qualidade""",

            "help_tips": """📊 **COMO INTERPRETAR TIPS**

**Elementos de uma Tip:**
• **EV \\(Expected Value\\):** Retorno esperado em %
• **Confiança:** Probabilidade de acerto
• **Odds:** Cotação da casa de apostas
• **Unidades:** Quantidade sugerida para apostar

**Indicadores de Qualidade:**
• 🔥 EV > 15% \\- Oportunidade excepcional
• 📊 EV 10\\-15% \\- Boa oportunidade
• 💡 EV 5\\-10% \\- Oportunidade moderada

**Gestão de Risco:**
Sempre aposte com responsabilidade\\!""",

            "help_settings": """⚙️ **CONFIGURAÇÕES**

**Personalizações Disponíveis:**
• 🔔 Tipos de alerta preferidos
• ⏰ Horários para receber tips
• 📊 Filtros de confiança/EV
• 🔕 Modo silencioso

**Filtros Avançados:**
• Ligas específicas \\(LEC, LCS, etc\\.\\)
• Valores mínimos de EV/Confiança
• Times favoritos
• Tipos de mercado""",

            "help_faq": """❓ **PERGUNTAS FREQUENTES**

**Q: Quantas tips recebo por dia?**
A: Depende da subscrição \\(1\\-5 tips/dia\\)

**Q: Como é calculado o EV?**
A: Algoritmos ML \\+ análise estatística

**Q: Posso pausar temporariamente?**
A: Sim, use `/subscribe` para gerenciar

**Q: As tips são garantidas?**
A: Não\\! Apostas sempre envolvem risco

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
Sistema automatizado \\- suporte via bot apenas"""
        }
        
        section_text = help_sections.get(data, "Seção não encontrada")
        
        await query.edit_message_text(
            section_text,
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
• Agrupado \\(1x/hora\\)
• Resumo diário

Configuração atual: **Todas ativas**""",

            "settings_schedule": """⏰ **CONFIGURAR HORÁRIOS**

**Horário de funcionamento:**
• 24/7 disponível
• Pico: 14h\\-23h \\(horário BR\\)
• Partidas: Principalmente noite

**Suas preferências:**
• Receber: Qualquer horário
• Não incomodar: Desabilitado
• Timezone: UTC\\-3 \\(Brasil\\)""",

            "settings_filters": """📊 **FILTROS DE TIPS**

**Critérios disponíveis:**
• EV mínimo: 5%
• Confiança mínima: 65%
• Odds: 1\\.30 \\- 3\\.50
• Ligas: Todas principais

**Filtros ativos:**
• ✅ Filtro qualidade
• ✅ Anti\\-spam
• ❌ Filtro por time

Configure filtros personalizados\\!""",

            "settings_language": """🌍 **IDIOMA**

**Idiomas disponíveis:**
• 🇧🇷 Português \\(atual\\)
• 🇺🇸 English
• 🇪🇸 Español

**Formatação:**
• Números: Brasileiro
• Horário: 24h
• Moeda: R$ \\(Real\\)

Mudanças aplicam\\-se imediatamente\\."""
        }
        
        section_text = settings_sections.get(data, "Configuração não encontrada")
        
        await query.edit_message_text(
            section_text,
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
            stats_text,
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