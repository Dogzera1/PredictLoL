from __future__ import annotations

import os
import asyncio
import time
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass
from enum import Enum
import re

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
        self.blocked_users: Set[int] = set()
        
        # Estatísticas
        self.stats = AlertStats()
        
        # Rate limiting (por usuário)
        self.user_message_times: Dict[int, List[float]] = {}
        self.max_messages_per_hour = 10
        
        # Cache de mensagens para evitar spam
        self.recent_tips_cache: Dict[str, float] = {}  # tip_id -> timestamp
        self.cache_duration = 300  # 5 minutos
        
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
        Envia tip profissional para todos os usuários subscritos
        
        Args:
            tip: Tip profissional a enviar
            
        Returns:
            True se enviada com sucesso para pelo menos um usuário
        """
        try:
            # Verifica cache para evitar duplicatas
            tip_cache_key = f"{tip.match_id}_{tip.tip_on_team}_{tip.odds}"
            current_time = time.time()
            
            if tip_cache_key in self.recent_tips_cache:
                last_sent = self.recent_tips_cache[tip_cache_key]
                if current_time - last_sent < self.cache_duration:
                    logger.debug(f"Tip já enviada recentemente: {tip_cache_key}")
                    return False
            
            # Formata mensagem
            formatted_message = self._format_tip_message(tip)
            
            # Filtra usuários elegíveis
            eligible_users = self._get_eligible_users_for_tip(tip)
            
            if not eligible_users:
                logger.warning("Nenhum usuário elegível para receber a tip")
                return False
            
            # Envia para todos os usuários elegíveis
            successful_sends = 0
            
            for user_id in eligible_users:
                try:
                    if self._can_send_to_user(user_id):
                        await self._send_message_to_user(
                            user_id, 
                            formatted_message, 
                            NotificationType.TIP_ALERT
                        )
                        successful_sends += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar tip para usuário {user_id}: {e}")
            
            # Atualiza cache e estatísticas
            if successful_sends > 0:
                self.recent_tips_cache[tip_cache_key] = current_time
                self.stats.tips_sent += successful_sends
                logger.info(f"✅ Tip enviada para {successful_sends} usuários")
                return True
            else:
                logger.warning("Falha ao enviar tip para qualquer usuário")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar tip profissional: {e}")
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
        """Verifica se pode enviar mensagem para usuário (rate limiting)"""
        if user_id in self.blocked_users:
            return False
        
        current_time = time.time()
        one_hour_ago = current_time - 3600
        
        # Limpa mensagens antigas
        if user_id in self.user_message_times:
            self.user_message_times[user_id] = [
                msg_time for msg_time in self.user_message_times[user_id]
                if msg_time > one_hour_ago
            ]
        else:
            self.user_message_times[user_id] = []
        
        # Verifica limite
        return len(self.user_message_times[user_id]) < self.max_messages_per_hour

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
        
        welcome_message = f"""🚀 **Bem\\-vindo ao Bot LoL V3 Ultra Avançado\\!**

Olá, {user.first_name}\\! 

Este bot envia **tips profissionais** para apostas em League of Legends baseadas em:
• 🧠 Machine Learning \\+ Algoritmos Heurísticos
• 📊 Análise em tempo real de partidas
• 💰 Expected Value calculado
• 🎯 Gestão profissional de risco

**Comandos disponíveis:**
/subscribe \\- Configurar notificações
/status \\- Ver status do sistema
/mystats \\- Suas estatísticas
/help \\- Ajuda completa

🔥 **Subscreva\\-se para receber tips profissionais\\!**"""
        
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
            welcome_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_subscription_keyboard()
        )

    async def _handle_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /subscribe"""
        await update.message.reply_text(
            "📋 **Escolha seu tipo de subscrição:**",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=self._get_subscription_keyboard()
        )

    async def _handle_unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /unsubscribe"""
        user_id = update.effective_user.id
        
        if user_id in self.users:
            self.users[user_id].is_active = False
            message = "❌ **Subscrição cancelada**\n\nVocê não receberá mais notificações\\.\nUse /subscribe para reativar\\."
        else:
            message = "ℹ️ Você não está subscrito\\."
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /status"""
        status_message = f"""📊 **STATUS DO SISTEMA**

👥 **Usuários:** {len(self.users)} registrados
✅ **Ativos:** {sum(1 for u in self.users.values() if u.is_active)}
📨 **Tips enviadas:** {self.stats.tips_sent}
📈 **Taxa de sucesso:** {self.stats.success_rate:.1f}%
🚫 **Bloqueados:** {self.stats.blocked_users}

⏰ **Última tip:** {self._format_time_ago(self.stats.last_alert_time)}

🔥 **Sistema operacional\\!**"""
        
        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_my_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /mystats"""
        user_id = update.effective_user.id
        
        if user_id not in self.users:
            await update.message.reply_text("ℹ️ Você não está registrado\\. Use /start primeiro\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        
        user = self.users[user_id]
        
        stats_message = f"""📊 **SUAS ESTATÍSTICAS**

👤 **Usuário:** {user.first_name}
📅 **Membro desde:** {self._format_time_ago(user.joined_at)}
📨 **Tips recebidas:** {user.tips_received}
🔔 **Tipo:** {user.subscription_type.value}
✅ **Status:** {"Ativo" if user.is_active else "Inativo"}

⏰ **Última atividade:** {self._format_time_ago(user.last_active)}"""
        
        await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler do comando /help"""
        help_message = """🆘 **AJUDA \\- Bot LoL V3 Ultra Avançado**

**🎯 O que é este bot?**
Sistema profissional de tips para League of Legends que combina Machine Learning com análise em tempo real para gerar recomendações de apostas de alta qualidade\\.

**📋 Comandos:**
• `/start` \\- Iniciar e registrar\\-se
• `/subscribe` \\- Configurar notificações
• `/unsubscribe` \\- Cancelar subscrição
• `/status` \\- Status do sistema
• `/mystats` \\- Suas estatísticas
• `/help` \\- Esta ajuda

**🔔 Tipos de Subscrição:**
• **Todas as Tips** \\- Recebe todas as tips geradas
• **Alto Valor** \\- Apenas tips com EV \\> 10%
• **Alta Confiança** \\- Apenas tips com confiança \\> 80%
• **Premium** \\- Tips exclusivas \\(EV \\> 15% e confiança \\> 85%\\)

**💡 Como funciona:**
1\\. Sistema monitora partidas ao vivo a cada 3 minutos
2\\. Analisa dados usando ML \\+ algoritmos heurísticos
3\\. Gera predições com confiança e Expected Value
4\\. Valida critérios profissionais rigorosos
5\\. Envia apenas tips de alta qualidade

**📊 Métricas de Qualidade:**
• Confiança mínima: 65%
• EV mínimo: 3%
• Odds entre 1\\.30 e 3\\.50
• Máximo 5 tips por hora \\(anti\\-spam\\)

🔥 **Desenvolvido com tecnologia de ponta para apostas profissionais\\!**"""
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN_V2)

    async def _handle_subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler de callbacks dos botões de subscrição"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        subscription_type = SubscriptionType(query.data)
        
        # Atualiza subscrição
        if user_id in self.users:
            self.users[user_id].subscription_type = subscription_type
            self.users[user_id].is_active = True
        else:
            self.users[user_id] = TelegramUser(
                user_id=user_id,
                username=query.from_user.username or "",
                first_name=query.from_user.first_name,
                subscription_type=subscription_type
            )
        
        await query.edit_message_text(
            f"✅ **Subscrição configurada\\!**\n\nTipo: {subscription_type.value}\n\nVocê receberá notificações conforme sua subscrição\\.",
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
        """Retorna estatísticas completas do sistema"""
        active_users = sum(1 for u in self.users.values() if u.is_active)
        
        subscriptions_by_type = {}
        for sub_type in SubscriptionType:
            subscriptions_by_type[sub_type.value] = sum(
                1 for u in self.users.values() 
                if u.is_active and u.subscription_type == sub_type
            )
        
        return {
            "users": {
                "total": len(self.users),
                "active": active_users,
                "blocked": len(self.blocked_users),
                "subscriptions_by_type": subscriptions_by_type
            },
            "alerts": {
                "total_sent": self.stats.total_alerts_sent,
                "tips_sent": self.stats.tips_sent,
                "match_updates_sent": self.stats.match_updates_sent,
                "system_alerts_sent": self.stats.system_alerts_sent,
                "failed_deliveries": self.stats.failed_deliveries,
                "success_rate": self.stats.success_rate,
                "last_alert_time": self.stats.last_alert_time
            },
            "rate_limiting": {
                "max_messages_per_hour": self.max_messages_per_hour,
                "cache_duration_minutes": self.cache_duration / 60,
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