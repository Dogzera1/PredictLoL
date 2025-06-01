from __future__ import annotations

import os
import asyncio
import time
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass
from enum import Enum
import re
import logging
import json
from datetime import datetime, timedelta

try:
    from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    from telegram.constants import ParseMode
    from telegram.error import TelegramError, Forbidden, BadRequest
    TELEGRAM_AVAILABLE = True
except ImportError:
    # Fallback para quando Telegram não está disponível
    TELEGRAM_AVAILABLE = False
    Bot = Update = InlineKeyboardButton = InlineKeyboardMarkup = None
    Application = CommandHandler = CallbackQueryHandler = ContextTypes = None
    ParseMode = TelegramError = Forbidden = BadRequest = None

from ..data_models.tip_data import ProfessionalTip
from ..core_logic.game_analyzer import GameAnalysis
from ..utils.constants import TELEGRAM_CONFIG, TIP_TEMPLATE
from ..utils.helpers import get_current_timestamp
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class SubscriptionType(Enum):
    """Tipos de subscrição disponíveis"""
    ALL_TIPS = "all_tips"           # Todas as tips
    HIGH_VALUE = "high_value"       # Apenas tips de alto valor (EV > 10%)
    HIGH_CONFIDENCE = "high_conf"   # Apenas tips de alta confiança (> 80%)
    PREMIUM = "premium"             # Tips premium (EV > 15% e confiança > 85%)
    CUSTOM = "custom"               # Filtros customizados


class NotificationType(Enum):
    """Tipos de notificação"""
    TIP_ALERT = "tip"               # Alerta de tip
    MATCH_UPDATE = "match_update"   # Atualização de partida
    SYSTEM_STATUS = "system"        # Status do sistema
    ERROR_ALERT = "error"           # Alerta de erro


@dataclass
class TelegramUser:
    """Usuário do Telegram"""
    user_id: int
    username: str
    first_name: str
    subscription_type: SubscriptionType
    is_active: bool = True
    joined_at: float = 0.0
    last_active: float = 0.0
    tips_received: int = 0
    custom_filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.joined_at == 0.0:
            self.joined_at = time.time()
        if self.last_active == 0.0:
            self.last_active = time.time()
        if self.custom_filters is None:
            self.custom_filters = {}


@dataclass
class TelegramGroup:
    """Grupo do Telegram"""
    group_id: int
    title: str
    subscription_type: SubscriptionType
    is_active: bool = True
    activated_by: int = 0  # ID do usuário que ativou
    activated_at: float = 0.0
    tips_received: int = 0
    custom_filters: Dict[str, Any] = None
    admin_ids: List[int] = None
    
    def __post_init__(self):
        if self.activated_at == 0.0:
            self.activated_at = time.time()
        if self.custom_filters is None:
            self.custom_filters = {}
        if self.admin_ids is None:
            self.admin_ids = []


@dataclass
class AlertStats:
    """Estatísticas de alertas"""
    total_alerts_sent: int = 0
    tips_sent: int = 0
    match_updates_sent: int = 0
    system_alerts_sent: int = 0
    failed_deliveries: int = 0
    blocked_users: int = 0
    last_alert_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso de entrega"""
        total_attempts = self.total_alerts_sent + self.failed_deliveries
        if total_attempts == 0:
            return 100.0
        return (self.total_alerts_sent / total_attempts) * 100


class TelegramAlertsSystem:
    """
    Sistema de Alertas Telegram para Bot LoL V3 Ultra Avançado
    
    Responsável por:
    - Envio de tips profissionais formatadas
    - Gerenciamento de usuários e subscrições
    - Formatação de mensagens para Telegram
    - Integração com ProfessionalTipsSystem
    - Rate limiting e tratamento de erros
    - Comandos do bot (/start, /subscribe, /status)
    
    Características:
    - Formatação MarkdownV2 para Telegram
    - Subscrições personalizáveis
    - Filtros avançados
    - Estatísticas detalhadas
    - Sistema anti-spam
    - Tratamento de usuários bloqueados
    """

    def __init__(self, bot_token: str):
        """
        Inicializa o sistema de alertas
        
        Args:
            bot_token: Token do bot do Telegram
        """
        self.bot_token = bot_token
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
        # Usuários e subscrições
        self.users: Dict[int, TelegramUser] = {}
        self.groups: Dict[int, TelegramGroup] = {}  # Grupos registrados
        self.blocked_users: Set[int] = set()
        self.blocked_groups: Set[int] = set()  # Grupos bloqueados
        
        # Estatísticas
        self.stats = AlertStats()
        
        # Rate limiting (por usuário)
        self.user_message_times: Dict[int, List[float]] = {}
        self.max_messages_per_hour = 10
        
        # Cache de mensagens para evitar spam
        self.recent_tips_cache: Dict[str, float] = {}  # tip_id -> timestamp
        self.cache_duration = 300  # 5 minutos
        
        # Estatísticas expandidas
        self.tips_sent_count = 0
        self.users_notified_count = 0
        self.groups_notified_count = 0
        
        # Cache para otimização
        self._subscription_cache = {}
        self._last_cache_update = 0
        
        self.logger = logging.getLogger(__name__)
        
        logger.info("TelegramAlertsSystem inicializado")

    async def initialize(self) -> None:
        """Inicializa o bot do Telegram"""
        try:
            self.bot = Bot(token=self.bot_token)
            self.application = Application.builder().token(self.bot_token).build()
            
            # Configura handlers
            self._setup_handlers()
            
            # Testa conexão
            bot_info = await self.bot.get_me()
            logger.info(f"Bot conectado: @{bot_info.username} ({bot_info.first_name})")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar bot do Telegram: {e}")
            raise

    def _setup_handlers(self) -> None:
        """Configura handlers de comandos"""
        
        # Comandos básicos
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("subscribe", self._handle_subscribe))
        self.application.add_handler(CommandHandler("unsubscribe", self._handle_unsubscribe))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(CommandHandler("mystats", self._handle_my_stats))
        
        # Comandos para grupos
        self.application.add_handler(CommandHandler("activate_group", self._handle_activate_group))
        self.application.add_handler(CommandHandler("group_status", self._handle_group_status))
        self.application.add_handler(CommandHandler("deactivate_group", self._handle_deactivate_group))
        
        # Callback handlers para botões inline
        self.application.add_handler(CallbackQueryHandler(self._handle_subscription_callback))
        
        logger.debug("Handlers configurados")

    async def start_bot(self) -> None:
        """Inicia o bot do Telegram"""
        if not self.application:
            await self.initialize()
        
        logger.info("🤖 Iniciando bot do Telegram...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def stop_bot(self) -> None:
        """Para o bot do Telegram"""
        if self.application and self.application.updater:
            logger.info("🛑 Parando bot do Telegram...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

    async def send_professional_tip(self, tip: ProfessionalTip) -> bool:
        """
        Envia tip profissional para todos os usuários e grupos subscritos
        
        Args:
            tip: Tip profissional a enviar
            
        Returns:
            True se enviada com sucesso para pelo menos um destinatário
        """
        if not self.bot:
            logger.error("Bot não inicializado para envio de tip")
            return False
        
        # Verifica cache para evitar spam
        tip_id = f"{tip.match_id}_{tip.team_name}_{tip.prediction_type}"
        if tip_id in self.recent_tips_cache:
            logger.debug(f"Tip {tip_id} já enviada recentemente (cache)")
            return False
        
        # Adiciona ao cache
        self.recent_tips_cache[tip_id] = time.time()
        
        # Formata mensagem
        message = self._format_tip_message(tip)
        
        # Envia para usuários individuais
        eligible_users = self._get_eligible_users_for_tip(tip)
        user_success_count = 0
        
        for user_id in eligible_users:
            if await self._send_message_to_user(user_id, message, NotificationType.TIP_ALERT):
                user_success_count += 1
                if user_id in self.users:
                    self.users[user_id].tips_received += 1
        
        # Envia para grupos
        eligible_groups = self._get_eligible_groups_for_tip(tip)
        group_success_count = 0
        
        for group_id in eligible_groups:
            if await self._send_message_to_group(group_id, message, NotificationType.TIP_ALERT):
                group_success_count += 1
                if group_id in self.groups:
                    self.groups[group_id].tips_received += 1
        
        total_success = user_success_count + group_success_count
        
        if total_success > 0:
            self.stats.tips_sent += 1
            self.stats.total_alerts_sent += total_success
            self.stats.last_alert_time = time.time()
            
            logger.info(f"Tip enviada para {user_success_count} usuários e {group_success_count} grupos")
            return True
        else:
            logger.warning("Tip não foi enviada para nenhum destinatário")
            return False

    async def send_match_update(self, analysis: GameAnalysis, match_id: str) -> None:
        """Envia atualização de partida"""
        try:
            message = self._format_match_update(analysis, match_id)
            
            # Envia apenas para usuários com subscrição ALL_TIPS ou PREMIUM
            eligible_users = [
                user_id for user_id, user in self.users.items()
                if user.is_active and user.subscription_type in [
                    SubscriptionType.ALL_TIPS, 
                    SubscriptionType.PREMIUM
                ]
            ]
            
            for user_id in eligible_users:
                if self._can_send_to_user(user_id):
                    await self._send_message_to_user(
                        user_id, 
                        message, 
                        NotificationType.MATCH_UPDATE
                    )
            
            self.stats.match_updates_sent += len(eligible_users)
            logger.debug(f"Atualização de partida enviada para {len(eligible_users)} usuários")
            
        except Exception as e:
            logger.error(f"Erro ao enviar atualização de partida: {e}")

    async def send_system_alert(self, message: str, alert_type: str = "info") -> None:
        """Envia alerta do sistema para admins"""
        try:
            # Envia apenas para usuários premium (admins)
            admin_users = [
                user_id for user_id, user in self.users.items()
                if user.subscription_type == SubscriptionType.PREMIUM
            ]
            
            emoji_map = {
                "info": "ℹ️",
                "warning": "⚠️", 
                "error": "❌",
                "success": "✅"
            }
            
            formatted_message = f"{emoji_map.get(alert_type, 'ℹ️')} **SISTEMA**\n\n{message}"
            
            for user_id in admin_users:
                await self._send_message_to_user(
                    user_id, 
                    formatted_message, 
                    NotificationType.SYSTEM_STATUS
                )
            
            self.stats.system_alerts_sent += len(admin_users)
            logger.info(f"Alerta do sistema enviado para {len(admin_users)} admins")
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta do sistema: {e}")

    def _format_tip_message(self, tip: ProfessionalTip) -> str:
        """Formata tip para Telegram com MarkdownV2"""
        try:
            # Escapa caracteres especiais do MarkdownV2
            def escape_md(text: str) -> str:
                chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
                for char in chars_to_escape:
                    text = text.replace(char, f'\\{char}')
                return text
            
            # Determina emoji do risco
            risk_emojis = {
                "Risco Muito Alto": "🔥🔥🔥",
                "Risco Alto": "🔥🔥",
                "Risco Médio-Alto": "🔥",
                "Risco Médio": "📊",
                "Risco Baixo": "🎯",
                "Risco Mínimo": "💡"
            }
            
            risk_emoji = risk_emojis.get(tip.risk_level, "📊")
            
            # Formata EV com cor
            ev_icon = "📈" if tip.ev_percentage > 15 else "📊" if tip.ev_percentage > 5 else "📉"
            
            message = f"""🚀 **TIP PROFISSIONAL LoL** 🚀

🎮 **{escape_md(tip.team_a)} vs {escape_md(tip.team_b)}**
🏆 **Liga:** {escape_md(tip.league)}
⚡ **Tip:** {escape_md(tip.tip_on_team)}
💰 **Odds:** {tip.odds}
{risk_emoji} **Unidades:** {tip.units} \\({escape_md(tip.risk_level)}\\)
⏰ **Tempo:** {escape_md(tip.game_time_at_tip)}

📊 **Análise:**
{ev_icon} **EV:** \\+{tip.ev_percentage:.1f}%
🎯 **Confiança:** {tip.confidence_percentage:.0f}%
🤖 **Fonte:** {escape_md(tip.prediction_source)}

⭐ **Qualidade:** {tip.data_quality_score:.0%}

🔥 **Bot LoL V3 Ultra Avançado**"""

            return message
            
        except Exception as e:
            logger.error(f"Erro ao formatar tip: {e}")
            return f"🚀 **TIP PROFISSIONAL**\n\n{tip.team_a} vs {tip.team_b}\nTip: {tip.tip_on_team} @ {tip.odds}"

    def _format_match_update(self, analysis: GameAnalysis, match_id: str) -> str:
        """Formata atualização de partida"""
        try:
            def escape_md(text: str) -> str:
                chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
                for char in chars_to_escape:
                    text = text.replace(char, f'\\{char}')
                return text
            
            message = f"""📺 **ATUALIZAÇÃO DA PARTIDA**

🎮 **Match ID:** {escape_md(match_id)}
⏰ **Tempo:** {analysis.game_time_seconds // 60}min
🎯 **Fase:** {escape_md(analysis.current_phase.value)}

📊 **Situação:**
• **Vencedor Provável:** {escape_md(analysis.predicted_winner or "Indefinido")}
• **Probabilidade:** {analysis.win_probability:.1%}
• **Confiança:** {analysis.confidence_score:.1%}

🔥 **Vantagens:**
• **Gold:** {analysis.team1_advantage.gold_advantage:+.0f}
• **Torres:** {analysis.team1_advantage.tower_advantage:+d}
• **Dragões:** {analysis.team1_advantage.dragon_advantage:+d}

📈 **Bot LoL V3**"""

            return message
            
        except Exception as e:
            logger.error(f"Erro ao formatar atualização: {e}")
            return f"📺 **ATUALIZAÇÃO DA PARTIDA**\n\nMatch: {match_id}"

    def _get_eligible_users_for_tip(self, tip: ProfessionalTip) -> List[int]:
        """Determina usuários elegíveis para receber a tip"""
        eligible = []
        
        for user_id, user in self.users.items():
            if not user.is_active or user_id in self.blocked_users:
                continue
            
            # Verifica tipo de subscrição
            if user.subscription_type == SubscriptionType.ALL_TIPS:
                eligible.append(user_id)
            elif user.subscription_type == SubscriptionType.HIGH_VALUE and tip.ev_percentage > 10:
                eligible.append(user_id)
            elif user.subscription_type == SubscriptionType.HIGH_CONFIDENCE and tip.confidence_percentage > 80:
                eligible.append(user_id)
            elif user.subscription_type == SubscriptionType.PREMIUM and tip.ev_percentage > 15 and tip.confidence_percentage > 85:
                eligible.append(user_id)
            elif user.subscription_type == SubscriptionType.CUSTOM:
                # Aplica filtros customizados
                if self._meets_custom_filters(tip, user.custom_filters):
                    eligible.append(user_id)
        
        return eligible

    def _meets_custom_filters(self, tip: ProfessionalTip, filters: Dict[str, Any]) -> bool:
        """Verifica se tip atende filtros customizados"""
        try:
            # EV mínimo
            if "min_ev" in filters and tip.ev_percentage < filters["min_ev"]:
                return False
            
            # Confiança mínima
            if "min_confidence" in filters and tip.confidence_percentage < filters["min_confidence"]:
                return False
            
            # Odds mínima/máxima
            if "min_odds" in filters and tip.odds < filters["min_odds"]:
                return False
            if "max_odds" in filters and tip.odds > filters["max_odds"]:
                return False
            
            # Ligas específicas
            if "leagues" in filters and tip.league not in filters["leagues"]:
                return False
            
            # Unidades mínimas/máximas
            if "min_units" in filters and tip.units < filters["min_units"]:
                return False
            if "max_units" in filters and tip.units > filters["max_units"]:
                return False
            
            return True
            
        except Exception:
            return True  # Em caso de erro, permite a tip

    def _can_send_to_user(self, user_id: int) -> bool:
        """Verifica se pode enviar mensagem para o usuário (rate limiting)"""
        if user_id in self.blocked_users:
            return False
        
        current_time = time.time()
        user_times = self.user_message_times.get(user_id, [])
        
        # Remove mensagens antigas (últimas hora)
        user_times = [t for t in user_times if current_time - t < 3600]
        
        # Verifica rate limit
        if len(user_times) >= self.max_messages_per_hour:
            logger.debug(f"Rate limit atingido para usuário {user_id}")
            return False
        
        # Atualiza lista de tempos
        user_times.append(current_time)
        self.user_message_times[user_id] = user_times
        return True

    async def _send_message_to_user(
        self, 
        user_id: int, 
        message: str, 
        notification_type: NotificationType
    ) -> bool:
        """Envia mensagem para um usuário específico"""
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True
            )
            
            # Atualiza rate limiting
            self.user_message_times.setdefault(user_id, []).append(time.time())
            
            # Atualiza estatísticas do usuário
            if user_id in self.users:
                self.users[user_id].last_active = time.time()
                if notification_type == NotificationType.TIP_ALERT:
                    self.users[user_id].tips_received += 1
            
            # Atualiza estatísticas globais
            self.stats.total_alerts_sent += 1
            self.stats.last_alert_time = time.time()
            
            return True
            
        except Forbidden:
            # Usuário bloqueou o bot
            logger.warning(f"Usuário {user_id} bloqueou o bot")
            self.blocked_users.add(user_id)
            if user_id in self.users:
                self.users[user_id].is_active = False
            self.stats.blocked_users += 1
            return False
            
        except BadRequest as e:
            logger.error(f"Erro de formato na mensagem para {user_id}: {e}")
            self.stats.failed_deliveries += 1
            return False
            
        except TelegramError as e:
            logger.error(f"Erro do Telegram ao enviar para {user_id}: {e}")
            self.stats.failed_deliveries += 1
            return False

    # Command Handlers
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /start"""
        user = update.effective_user
        
        welcome_message = f"""🚀 **Bem-vindo ao Bot LoL V3 Ultra Avançado!**

Olá, {user.first_name}! 

Este bot envia **tips profissionais** para apostas em League of Legends baseadas em:
• 🧠 Machine Learning + Algoritmos Heurísticos
• 📊 Análise em tempo real de partidas
• 💰 Expected Value calculado
• 🎯 Gestão profissional de risco

**Comandos disponíveis:**
/subscribe - Configurar notificações
/status - Ver status do sistema
/mystats - Suas estatísticas
/help - Ajuda completa

🔥 **Subscreva-se para receber tips profissionais!**"""
        
        # Registra usuário se novo
        if user.id not in self.users:
            self.users[user.id] = TelegramUser(
                user_id=user.id,
                username=user.username or "",
                first_name=user.first_name,
                subscription_type=SubscriptionType.ALL_TIPS
            )
            logger.info(f"Novo usuário registrado: {user.first_name} ({user.id})")
        
        await update.message.reply_text(
            self._escape_markdown_v2(welcome_message),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_subscription_keyboard()
        )

    async def _handle_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /subscribe"""
        await update.message.reply_text(
            self._escape_markdown_v2("📋 **Escolha seu tipo de subscrição:**"),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_subscription_keyboard()
        )

    async def _handle_unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /unsubscribe"""
        user_id = update.effective_user.id
        
        if user_id in self.users:
            self.users[user_id].is_active = False
            message = "❌ **Subscrição cancelada**\n\nVocê não receberá mais notificações.\nUse /subscribe para reativar."
        else:
            message = "ℹ️ Você não está subscrito."
        
        await update.message.reply_text(
            self._escape_markdown_v2(message), 
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /status"""
        status_message = f"""📊 **STATUS DO SISTEMA**

👥 **Usuários:** {len(self.users)} registrados
✅ **Ativos:** {sum(1 for u in self.users.values() if u.is_active)}
📨 **Tips enviadas:** {self.stats.tips_sent}
📈 **Taxa de sucesso:** {self.stats.success_rate:.1f}%
🚫 **Bloqueados:** {self.stats.blocked_users}

⏰ **Última tip:** {self._format_time_ago(self.stats.last_alert_time)}

🔥 **Sistema operacional!**"""
        
        await update.message.reply_text(
            self._escape_markdown_v2(status_message), 
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _handle_my_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /mystats"""
        user_id = update.effective_user.id
        
        if user_id not in self.users:
            await update.message.reply_text(
                self._escape_markdown_v2("ℹ️ Você não está registrado. Use /start primeiro."), 
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        user = self.users[user_id]
        
        stats_message = f"""📊 **SUAS ESTATÍSTICAS**

👤 **Usuário:** {user.first_name}
📅 **Membro desde:** {self._format_time_ago(user.joined_at)}
📨 **Tips recebidas:** {user.tips_received}
🔔 **Tipo:** {user.subscription_type.value}
✅ **Status:** {"Ativo" if user.is_active else "Inativo"}

⏰ **Última atividade:** {self._format_time_ago(user.last_active)}"""
        
        await update.message.reply_text(
            self._escape_markdown_v2(stats_message), 
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /help"""
        help_text = """🆘 **Ajuda - Bot LoL V3**

**👤 Comandos Pessoais:**
• `/start` - Iniciar bot
• `/subscribe` - Configurar alertas
• `/unsubscribe` - Cancelar alertas
• `/status` - Status do sistema
• `/mystats` - Suas estatísticas

**👥 Comandos para Grupos:**
• `/activate_group` - Ativar alertas no grupo
• `/group_status` - Status do grupo
• `/deactivate_group` - Desativar alertas

**📊 Tipos de Subscrição:**
• 🔔 Todas as Tips
• 💎 Alto Valor (EV > 10%)
• 🎯 Alta Confiança (> 80%)
• 👑 Premium (EV > 15% + Conf > 85%)

🤖 **Bot LoL V3 Ultra Avançado**
⚡ Sistema profissional de tips eSports"""
        
        await update.message.reply_text(
            self._escape_markdown_v2(help_text),
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _handle_subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para callbacks de subscrição"""
        query = update.callback_query
        await query.answer()
        
        chat = query.message.chat
        user = query.from_user
        
        try:
            subscription_type = SubscriptionType(query.data)
        except ValueError:
            await query.edit_message_text(
                self._escape_markdown_v2("❌ **Tipo de subscrição inválido.**"), 
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return

        # Determina se é grupo ou usuário individual
        if chat.type in ['group', 'supergroup']:
            await self._handle_group_subscription(query, chat, user, subscription_type)
        else:
            await self._handle_user_subscription(query, user, subscription_type)

    async def _handle_group_subscription(self, query, chat, user, subscription_type: SubscriptionType) -> None:
        """Manipula subscrição em grupos"""
        # Verifica se usuário é admin do grupo
        try:
            chat_member = await self.bot.get_chat_member(chat.id, user.id)
            is_admin = chat_member.status in ['administrator', 'creator']
        except Exception:
            is_admin = False
        
        if not is_admin:
            await query.edit_message_text(
                self._escape_markdown_v2("❌ **Apenas administradores podem configurar alertas do grupo.**"),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Registra ou atualiza grupo
        self.groups[chat.id] = TelegramGroup(
            group_id=chat.id,
            title=chat.title or "Grupo",
            subscription_type=subscription_type,
            activated_by=user.id,
            admin_ids=[user.id]
        )
        
        confirmation_message = f"""✅ **Alertas de grupo configurados!**

📋 **Grupo:** {chat.title}
🔔 **Tipo:** {subscription_type.value}
👤 **Configurado por:** {user.first_name}

🎯 O grupo receberá tips conforme a subscrição selecionada."""
        
        await query.edit_message_text(
            self._escape_markdown_v2(confirmation_message),
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _handle_user_subscription(self, query, user, subscription_type: SubscriptionType) -> None:
        """Manipula subscrição individual"""
        # Registra ou atualiza usuário
        if user.id in self.users:
            self.users[user.id].subscription_type = subscription_type
            self.users[user.id].is_active = True
        else:
            self.users[user.id] = TelegramUser(
                user_id=user.id,
                username=user.username or "",
                first_name=user.first_name,
                subscription_type=subscription_type
            )
        
        confirmation_message = f"""✅ **Subscrição configurada!**

🔔 **Tipo:** {subscription_type.value}
👤 **Usuário:** {user.first_name}

🎯 Você receberá tips conforme sua subscrição."""
        
        await query.edit_message_text(
            self._escape_markdown_v2(confirmation_message),
            parse_mode=ParseMode.MARKDOWN_V2
        )

    def _get_subscription_keyboard(self) -> InlineKeyboardMarkup:
        """Cria teclado inline para subscrições"""
        keyboard = [
            [InlineKeyboardButton("🔔 Todas as Tips", callback_data=SubscriptionType.ALL_TIPS.value)],
            [InlineKeyboardButton("💎 Alto Valor (EV > 10%)", callback_data=SubscriptionType.HIGH_VALUE.value)],
            [InlineKeyboardButton("🎯 Alta Confiança (> 80%)", callback_data=SubscriptionType.HIGH_CONFIDENCE.value)],
            [InlineKeyboardButton("👑 Premium (EV > 15% + Conf > 85%)", callback_data=SubscriptionType.PREMIUM.value)],
        ]
        return InlineKeyboardMarkup(keyboard)

    def _format_time_ago(self, timestamp: float) -> str:
        """Formata timestamp como tempo relativo"""
        if timestamp == 0:
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

    def get_system_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de alertas"""
        active_users = sum(1 for user in self.users.values() if user.is_active)
        blocked_users = len(self.blocked_users)
        
        active_groups = sum(1 for group in self.groups.values() if group.is_active)
        blocked_groups = len(self.blocked_groups)
        
        subscriptions_by_type = {}
        for subscription_type in SubscriptionType:
            user_count = sum(1 for user in self.users.values() 
                           if user.subscription_type == subscription_type and user.is_active)
            group_count = sum(1 for group in self.groups.values() 
                            if group.subscription_type == subscription_type and group.is_active)
            subscriptions_by_type[subscription_type.value] = {
                "users": user_count,
                "groups": group_count,
                "total": user_count + group_count
            }
        
        return {
            "users": {
                "total": len(self.users),
                "active": active_users,
                "blocked": blocked_users,
                "subscriptions_by_type": {k: v["users"] for k, v in subscriptions_by_type.items()}
            },
            "groups": {
                "total": len(self.groups),
                "active": active_groups,
                "blocked": blocked_groups,
                "subscriptions_by_type": {k: v["groups"] for k, v in subscriptions_by_type.items()}
            },
            "combined_subscriptions": subscriptions_by_type,
            "alerts": {
                "total_sent": self.stats.total_alerts_sent,
                "tips_sent": self.stats.tips_sent,
                "match_updates_sent": self.stats.match_updates_sent,
                "system_alerts_sent": self.stats.system_alerts_sent,
                "failed_deliveries": self.stats.failed_deliveries,
                "success_rate": self.stats.success_rate
            },
            "rate_limiting": {
                "max_messages_per_hour": self.max_messages_per_hour,
                "cache_duration_minutes": self.cache_duration // 60,
                "recent_tips_cached": len(self.recent_tips_cache)
            }
        }

    def cleanup_old_cache(self) -> None:
        """Limpa cache antigo"""
        current_time = time.time()
        
        # Limpa cache de tips
        old_tips = [
            tip_id for tip_id, timestamp in self.recent_tips_cache.items()
            if current_time - timestamp > self.cache_duration
        ]
        
        for tip_id in old_tips:
            del self.recent_tips_cache[tip_id]
        
        if old_tips:
            logger.debug(f"Cache limpo: {len(old_tips)} tips antigas removidas")

    # ===== HANDLERS PARA GRUPOS =====

    async def _handle_activate_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para ativar alertas em um grupo"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Verifica se é um grupo
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "❌ **Este comando só funciona em grupos!**\n\n"
                "Use `/subscribe` para alertas pessoais.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Verifica se o usuário é admin do grupo
        try:
            member = await self.bot.get_chat_member(chat.id, user.id)
            if member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ **Apenas administradores podem ativar alertas no grupo!**",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                return
        except Exception as e:
            logger.error(f"Erro ao verificar admin: {e}")
            await update.message.reply_text(
                "❌ **Erro ao verificar permissões.**",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Verifica se o grupo já está ativo
        if chat.id in self.groups and self.groups[chat.id].is_active:
            group = self.groups[chat.id]
            await update.message.reply_text(
                f"✅ **Grupo já está ativo!**\n\n"
                f"📊 **Tipo:** {group.subscription_type.value}\n"
                f"🎯 **Tips recebidas:** {group.tips_received}\n"
                f"👤 **Ativado por:** {group.activated_by}\n\n"
                f"Use `/group_status` para mais detalhes.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Mostra opções de subscrição para o grupo
        keyboard = self._get_group_subscription_keyboard()
        
        await update.message.reply_text(
            f"🔔 **Ativar Alertas de Tips no Grupo**\n\n"
            f"📋 **Grupo:** {chat.title}\n"
            f"👤 **Admin:** {user.first_name}\n\n"
            f"Escolha o tipo de alerta que o grupo receberá:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboard
        )

    async def _handle_group_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para status do grupo"""
        chat = update.effective_chat
        
        # Verifica se é um grupo
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "❌ **Este comando só funciona em grupos!**",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Verifica se o grupo está registrado
        if chat.id not in self.groups:
            await update.message.reply_text(
                "ℹ️ **Grupo não está registrado.**\n\n"
                "Use `/activate_group` para ativar alertas.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        group = self.groups[chat.id]
        
        # Calcula uptime
        uptime_hours = (time.time() - group.activated_at) / 3600
        
        status_text = f"""📊 **STATUS DO GRUPO**

📋 **Informações:**
• Nome: {chat.title}
• ID: `{chat.id}`
• Status: {'✅ Ativo' if group.is_active else '❌ Inativo'}

🔔 **Alertas:**
• Tipo: {group.subscription_type.value}
• Tips recebidas: {group.tips_received}
• Ativo há: {uptime_hours:.1f}h

👤 **Configuração:**
• Ativado por: {group.activated_by}
• Data: {time.strftime('%d/%m/%Y %H:%M', time.localtime(group.activated_at))}

⚙️ **Comandos:**
• `/activate_group` - Reconfigurar alertas
• `/deactivate_group` - Desativar alertas"""
        
        await update.message.reply_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _handle_deactivate_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para desativar alertas do grupo"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Verifica se é um grupo
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "❌ **Este comando só funciona em grupos!**",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Verifica se o usuário é admin do grupo
        try:
            member = await self.bot.get_chat_member(chat.id, user.id)
            if member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ **Apenas administradores podem desativar alertas!**",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                return
        except Exception as e:
            logger.error(f"Erro ao verificar admin: {e}")
            return
        
        # Verifica se o grupo está ativo
        if chat.id not in self.groups or not self.groups[chat.id].is_active:
            await update.message.reply_text(
                "ℹ️ **Alertas já estão desativados neste grupo.**",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Desativa o grupo
        self.groups[chat.id].is_active = False
        
        await update.message.reply_text(
            f"❌ **Alertas desativados!**\n\n"
            f"O grupo não receberá mais tips automáticas.\n"
            f"Use `/activate_group` para reativar.",
            parse_mode=ParseMode.MARKDOWN_V2
        )

    def _get_group_subscription_keyboard(self) -> InlineKeyboardMarkup:
        """Cria teclado inline para subscrições de grupo"""
        keyboard = [
            [InlineKeyboardButton("🔔 Todas as Tips", callback_data=SubscriptionType.ALL_TIPS.value)],
            [InlineKeyboardButton("💎 Alto Valor (EV > 10%)", callback_data=SubscriptionType.HIGH_VALUE.value)],
            [InlineKeyboardButton("🎯 Alta Confiança (> 80%)", callback_data=SubscriptionType.HIGH_CONFIDENCE.value)],
            [InlineKeyboardButton("👑 Premium (EV > 15% + Conf > 85%)", callback_data=SubscriptionType.PREMIUM.value)],
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_eligible_groups_for_tip(self, tip: ProfessionalTip) -> List[int]:
        """Filtra grupos elegíveis para receber a tip"""
        eligible_groups = []
        
        for group_id, group in self.groups.items():
            if not group.is_active or group_id in self.blocked_groups:
                continue
            
            # Filtra por tipo de subscrição
            if group.subscription_type == SubscriptionType.ALL_TIPS:
                eligible_groups.append(group_id)
            elif group.subscription_type == SubscriptionType.HIGH_VALUE and tip.expected_value > 0.10:
                eligible_groups.append(group_id)
            elif group.subscription_type == SubscriptionType.HIGH_CONFIDENCE and tip.confidence > 0.80:
                eligible_groups.append(group_id)
            elif group.subscription_type == SubscriptionType.PREMIUM and tip.expected_value > 0.15 and tip.confidence > 0.85:
                eligible_groups.append(group_id)
            elif group.subscription_type == SubscriptionType.CUSTOM and self._meets_custom_filters(tip, group.custom_filters):
                eligible_groups.append(group_id)
        
        return eligible_groups

    async def _send_message_to_group(self, group_id: int, message: str, notification_type: NotificationType) -> bool:
        """Envia mensagem para um grupo específico"""
        try:
            if group_id in self.blocked_groups:
                return False
            
            await self.bot.send_message(
                chat_id=group_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True
            )
            
            return True
            
        except Forbidden:
            logger.warning(f"Bot foi removido do grupo {group_id}")
            self.blocked_groups.add(group_id)
            if group_id in self.groups:
                self.groups[group_id].is_active = False
            return False
            
        except BadRequest as e:
            logger.error(f"Erro de requisição para grupo {group_id}: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para grupo {group_id}: {e}")
            self.stats.failed_deliveries += 1
            return False

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