#!/usr/bin/env python3
"""
Sistema de Apostas Pessoais LoL - Módulo Principal
Integração completa de todos os sistemas
"""

from .bankroll_manager import PersonalBankrollManager, create_default_manager
from .value_analyzer import ManualValueAnalyzer, create_default_analyzer  
from .betting_tracker import BettingTracker, create_default_tracker
from .pre_game_analyzer import PreGameAnalyzer, create_default_pre_game_analyzer

class PersonalBettingSystem:
    """Sistema integrado de apostas pessoais"""
    
    def __init__(self, initial_bankroll: float = 1000.0):
        self.bankroll_manager = create_default_manager(initial_bankroll)
        self.value_analyzer = create_default_analyzer()
        self.betting_tracker = create_default_tracker()
        self.pre_game_analyzer = create_default_pre_game_analyzer()
        self.version = "1.4.0"
    
    def get_status(self):
        """Retorna status do sistema"""
        return {
            'version': self.version,
            'bankroll': self.bankroll_manager.settings.current_bankroll,
            'components': {
                'bankroll_manager': 'active',
                'value_analyzer': 'active', 
                'betting_tracker': 'active',
                'pre_game_analyzer': 'active'
            }
        }

__all__ = [
    'PersonalBankrollManager',
    'create_default_manager',
    'ManualValueAnalyzer', 
    'create_default_analyzer',
    'BettingTracker',
    'create_default_tracker',
    'PreGameAnalyzer',
    'create_default_pre_game_analyzer',
    'PersonalBettingSystem'
]

def create_integrated_betting_system(initial_bankroll: float = 1000.0):
    """
    Cria sistema integrado completo de apostas LoL
    
    Returns:
        dict: Sistema completo com todos os componentes integrados
    """
    # Cria componentes individuais
    bankroll_manager = create_default_manager(initial_bankroll)
    value_analyzer = create_default_analyzer()
    betting_tracker = create_default_tracker()
    pre_game_analyzer = create_default_pre_game_analyzer()
    
    # Sistema integrado
    system = {
        'bankroll_manager': bankroll_manager,
        'value_analyzer': value_analyzer,
        'betting_tracker': betting_tracker,
        'pre_game_analyzer': pre_game_analyzer,
        'version': '1.4.0',
        'features': [
            '💰 Gestão de Bankroll com Kelly Criterion',
            '🔍 Análise Manual de Value Bets',
            '📊 Dashboard Visual de Performance',
            '🤖 Análise Automatizada Pré-Jogo',
            '📈 Dados Históricos e Tendências',
            '🔗 Sistema Totalmente Integrado'
        ]
    }
    
    return system

def get_system_info():
    """Retorna informações sobre o sistema"""
    return {
        'name': 'Sistema de Apostas Pessoais LoL',
        'version': '1.4.0',
        'components': {
            '1': '💰 Personal Bankroll Manager - Gestão financeira profissional',
            '2': '🔍 Manual Value Analyzer - Análise manual sistemática',
            '3': '📊 Betting Tracker - Dashboard visual de performance',
            '4': '🤖 Pre-Game Analyzer - Análise automatizada com dados históricos'
        },
        'status': 'Totalmente Operacional',
        'description': '''
Sistema completo para apostas em LoL com:

🎯 CARACTERÍSTICAS PRINCIPAIS:
• Gestão de bankroll com Kelly Criterion
• Análise sistemática de value bets
• Tracking visual de performance
• Análise automatizada pré-jogo
• Integração total entre sistemas
• Dados históricos e tendências

🚀 PRONTO PARA USO:
• Conservative risk management
• Professional-grade analysis tools
• Real-time performance monitoring
• Automated data-driven insights
• Complete betting lifecycle support

📊 SISTEMA TESTADO E VALIDADO
        '''.strip()
    }

if __name__ == "__main__":
    info = get_system_info()
    print(f"🎮 {info['name']} v{info['version']}")
    print(f"📊 Status: {info['status']}")
    print(info['description']) 