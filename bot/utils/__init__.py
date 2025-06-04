"""
Utilitários compartilhados

Este módulo contém:
- constants: Constantes globais do sistema
- helpers: Funções auxiliares gerais
- logger_config: Configuração do sistema de logs
"""

from .constants import *
from .helpers import *
from .logger_config import setup_logging

__all__ = ['setup_logging'] 
