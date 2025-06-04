"""
Lógica central do sistema Bot LoL V3 Ultra Avançado

Este módulo contém os componentes principais de análise e predição:
- Sistema de Unidades Profissionais: Cálculo de apostas baseado em confiança e EV
- Analisador de Jogos LoL: Análise de eventos cruciais e estados de jogo
- Sistema de Predição Dinâmico: Machine Learning + algoritmos heurísticos
"""

from .units_system import ProfessionalUnitsSystem, TipRecommendation
from .game_analyzer import (
    LoLGameAnalyzer, 
    GameAnalysis, 
    TeamAdvantage, 
    GamePhase, 
    EventImportance
)
from .prediction_system import (
    DynamicPredictionSystem,
    PredictionResult,
    TipGenerationResult,
    PredictionMethod,
    PredictionConfidence
)

__all__ = [
    'ProfessionalUnitsSystem',
    'TipRecommendation',
    'LoLGameAnalyzer',
    'GameAnalysis',
    'TeamAdvantage', 
    'GamePhase',
    'EventImportance',
    'DynamicPredictionSystem',
    'PredictionResult',
    'TipGenerationResult',
    'PredictionMethod',
    'PredictionConfidence'
] 
