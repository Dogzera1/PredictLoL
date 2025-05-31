"""
Sistema de Bot do Telegram - Bot LoL V3 Ultra Avançado

Este módulo contém toda a infraestrutura do bot Telegram:
- Sistema de Alertas: Envio de tips profissionais
- Interface Principal: Controle total via Telegram
- Gerenciamento de Usuários: Preferências e subscrições
"""

from .alerts_system import (
    TelegramAlertsSystem,
    TelegramUser,
    SubscriptionType,
    NotificationType,
    AlertStats
)

from .bot_interface import (
    LoLBotV3UltraAdvanced,
    BotStats
)

__all__ = [
    'TelegramAlertsSystem',
    'TelegramUser', 
    'SubscriptionType',
    'NotificationType',
    'AlertStats',
    'LoLBotV3UltraAdvanced',
    'BotStats'
] 