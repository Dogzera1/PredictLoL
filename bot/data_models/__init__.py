"""
Modelos de dados estruturados

Este módulo contém:
- MatchData: Modelo para dados de partidas
- ProfessionalTip: Modelo para tips profissionais
- TeamStats: Modelo para estatísticas de times
"""

from .match_data import MatchData, TeamStats
from .tip_data import ProfessionalTip

__all__ = ['MatchData', 'TeamStats', 'ProfessionalTip'] 