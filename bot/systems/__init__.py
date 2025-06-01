"""
Sistemas principais do Bot LoL V3 Ultra Avançado

Este módulo contém os sistemas centrais de processamento:
- Sistema de Tips Profissionais: Geração e validação de tips
- Gerenciador de Cronograma: Orquestração e automação
"""

from .tips_system import ProfessionalTipsSystem, TipStatus
from .schedule_manager import (
    ScheduleManager,
    TaskStatus,
    TaskType,
    ScheduledTask,
    SystemHealth
)

__all__ = [
    'ProfessionalTipsSystem',
    'TipStatus',
    'ScheduleManager',
    'TaskStatus',
    'TaskType',
    'ScheduledTask',
    'SystemHealth'
] 