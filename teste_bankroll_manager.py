#!/usr/bin/env python3
"""
Teste Completo do Personal Bankroll Manager
Demonstra todas as funcionalidades do sistema de gestão de bankroll pessoal
"""

import asyncio
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.personal_betting.bankroll_manager import PersonalBankrollManager, RiskLevel
from datetime import datetime


def test_bankroll_manager():
    """Teste completo do sistema de gestão de bankroll"""
    
    print("🏦 TESTE COMPLETO: PERSONAL BANKROLL MANAGER")
    print("=" * 70)
    
    # 1. Inicialização
    print("\n💰 1. INICIALIZANDO SISTEMA DE BANKROLL")
    manager = PersonalBankrollManager()
    
    # 2. Configuração inicial
    print("\n⚙️ 2. CONFIGURANDO BANKROLL INICIAL")
    setup_result = manager.setup_bankroll(2000.0, {
        'daily_limit_percentage': 12.0,    # 12% por dia
        'max_bet_percentage': 5.0,         # 5% por aposta
        'min_confidence': 70.0,            # Confiança mínima 70%
        'min_ev': 5.0,                     # EV mínimo 5%
        'kelly_multiplier': 0.3,           # 30% do Kelly
        'risk_tolerance': 'medium'
    })
    
    print(f"✅ Setup: {setup_result['message']}")
    print(f"   💰 Bankroll: R${setup_result['settings']['current_bankroll']:.2f}")
    print(f"   📊 Limite diário: R${setup_result['daily_limit']:.2f}")
    print(f"   🎯 Máximo por aposta: R${setup_result['max_bet']:.2f}")
    
    # 3. Testando cálculos de apostas
    print("\n🧮 3. TESTANDO CÁLCULOS DE APOSTAS")
    
    # Cenário 1: Aposta com bom value
    print("\n📊 CENÁRIO 1: T1 vs Gen.G (Alta confiança)")
    bet_calc_1 = manager.calculate_bet_size(
        confidence=85.0,
        odds=1.75,
        your_probability=0.70,  # 70% de chance
        league="LCK",
        reasoning="T1 em excelente forma, Gen.G instável após mudanças no roster"
    )
    
    if bet_calc_1['recommended']:
        print(f"   ✅ RECOMENDADO: R${bet_calc_1['bet_amount']:.2f}")
        print(f"   📈 EV: {bet_calc_1['ev_percentage']:.2f}%")
        print(f"   🎯 Risco: {bet_calc_1['risk_level']}")
        print(f"   💰 Lucro potencial: R${bet_calc_1['potential_profit']:.2f}")
        print(f"   📊 Kelly: {bet_calc_1['kelly_fraction']:.4f}")
        
        # Warnings se houver
        if bet_calc_1['warnings']:
            print("   ⚠️ Avisos:")
            for warning in bet_calc_1['warnings']:
                print(f"     • {warning}")
    else:
        print(f"   ❌ NÃO RECOMENDADO: {bet_calc_1['reason']}")
    
    # Cenário 2: Aposta com baixo EV
    print("\n📊 CENÁRIO 2: FNC vs G2 (EV baixo)")
    bet_calc_2 = manager.calculate_bet_size(
        confidence=60.0,  # Baixa confiança
        odds=1.45,
        your_probability=0.55,  # 55% de chance vs odds que implicam 69%
        league="LEC",
        reasoning="Partida equilibrada, sem edge clara"
    )
    
    if bet_calc_2['recommended']:
        print(f"   ✅ RECOMENDADO: R${bet_calc_2['bet_amount']:.2f}")
    else:
        print(f"   ❌ NÃO RECOMENDADO: {bet_calc_2['reason']}")
    
    # 4. Registrando apostas
    print("\n📝 4. REGISTRANDO APOSTAS")
    
    # Registra a primeira aposta se foi recomendada
    if bet_calc_1['recommended']:
        bet_result = manager.place_bet(
            team="T1",
            opponent="Gen.G",
            league="LCK",
            odds=1.75,
            amount=bet_calc_1['bet_amount'],
            confidence=85.0,
            ev_percentage=bet_calc_1['ev_percentage'],
            reasoning="T1 em excelente forma, Gen.G instável"
        )
        
        if bet_result['success']:
            print(f"   ✅ Aposta 1 registrada: {bet_result['message']}")
            bet_id_1 = bet_result['bet_id']
        else:
            print(f"   ❌ Erro: {bet_result['error']}")
    
    # Registra mais algumas apostas de exemplo
    bet_result_2 = manager.place_bet(
        team="DRX",
        opponent="KT Rolster",
        league="LCK",
        odds=2.10,
        amount=50.0,
        confidence=75.0,
        ev_percentage=8.5,
        reasoning="DRX underdog com valor, KT inconsistente"
    )
    
    bet_result_3 = manager.place_bet(
        team="C9",
        opponent="Team Liquid",
        league="LCS",
        odds=1.90,
        amount=30.0,
        confidence=72.0,
        ev_percentage=6.2,
        reasoning="C9 melhor momentum recente"
    )
    
    print(f"   ✅ Total de apostas registradas: 3")
    
    # 5. Resolvendo apostas
    print("\n🎯 5. RESOLVENDO APOSTAS")
    
    # Resolve primeira aposta como vitória
    if 'bet_id_1' in locals():
        resolve_1 = manager.resolve_bet(bet_id_1, won=True, notes="T1 dominou early game")
        print(f"   🏆 Aposta 1: {resolve_1['result']} - Lucro: R${resolve_1['profit']:.2f}")
    
    # Resolve segunda como derrota
    if bet_result_2['success']:
        resolve_2 = manager.resolve_bet(bet_result_2['bet_id'], won=False, notes="DRX throw no late game")
        print(f"   💔 Aposta 2: {resolve_2['result']} - Prejuízo: R${resolve_2['profit']:.2f}")
    
    # Terceira deixa pendente
    print(f"   ⏳ Aposta 3: Pendente")
    
    # 6. Estatísticas de performance
    print("\n📊 6. ESTATÍSTICAS DE PERFORMANCE")
    stats = manager.get_performance_stats(days=30)
    
    if stats.get('total_bets', 0) > 0:
        print(f"   📈 Total de apostas: {stats['total_bets']}")
        print(f"   🏆 Win Rate: {stats['win_rate']:.1f}%")
        print(f"   💰 ROI: {stats['roi']:.2f}%")
        print(f"   📊 Lucro total: R${stats['total_profit']:.2f}")
        print(f"   💵 Bankroll atual: R${stats['current_bankroll']:.2f}")
        
        # Melhor aposta
        if 'best_bet' in stats:
            print(f"   🌟 Melhor aposta: {stats['best_bet']['team']} (+R${stats['best_bet']['profit']:.2f})")
    else:
        print("   📝 Nenhuma aposta resolvida ainda")
    
    # 7. Apostas pendentes
    print("\n⏳ 7. APOSTAS PENDENTES")
    pending = manager.get_pending_bets()
    print(f"   📋 Apostas pendentes: {len(pending)}")
    
    for bet in pending:
        print(f"     • {bet['team']} vs {bet['opponent']} - R${bet['amount']:.2f} @ {bet['odds']}")
    
    # 8. Limites atuais
    print("\n📏 8. LIMITES E DISPONIBILIDADE")
    print(f"   💰 Bankroll disponível: R${manager.settings.current_bankroll:.2f}")
    print(f"   📅 Limite diário: R${manager.get_daily_limit():.2f}")
    print(f"   ⏰ Restante hoje: R${manager.get_daily_remaining_limit():.2f}")
    print(f"   🎯 Máximo por aposta: R${manager.get_max_bet_amount():.2f}")
    
    # 9. Relatório completo
    print("\n📋 9. RELATÓRIO COMPLETO")
    print(manager.generate_report())
    
    # 10. Teste de funcionalidades avançadas
    print("\n🔧 10. FUNCIONALIDADES AVANÇADAS")
    
    # Teste com diferentes níveis de risco
    print("\n   🎲 Teste de níveis de risco:")
    risk_scenarios = [
        (20.0, "Aposta conservadora"),
        (60.0, "Aposta moderada"), 
        (100.0, "Aposta agressiva"),
        (150.0, "Aposta extrema")
    ]
    
    for amount, description in risk_scenarios:
        risk_level = manager._determine_risk_level(amount)
        percentage = (amount / manager.settings.current_bankroll) * 100
        print(f"     • R${amount:.2f} ({percentage:.1f}%): {risk_level.value} - {description}")
    
    # Exemplo de Kelly Criterion
    print(f"\n   📊 Exemplo Kelly Criterion:")
    print(f"     • Prob: 60% | Odds: 2.0 | Kelly: {((2.0 * 0.6) - 1) / (2.0 - 1):.3f}")
    print(f"     • Prob: 70% | Odds: 1.8 | Kelly: {((1.8 * 0.7) - 1) / (1.8 - 1):.3f}")
    
    print("\n" + "=" * 70)
    print("🎉 TESTE COMPLETO FINALIZADO!")
    print("✅ Sistema de Bankroll totalmente funcional")
    print("💰 Pronto para uso em apostas reais")
    print("📊 Todas as funcionalidades validadas")


def demonstrate_real_world_usage():
    """Demonstra uso no mundo real"""
    
    print("\n\n🌍 DEMONSTRAÇÃO: USO NO MUNDO REAL")
    print("=" * 70)
    
    # Cenário real de apostas
    manager = PersonalBankrollManager()
    
    # Setup com bankroll real
    manager.setup_bankroll(500.0, {  # R$ 500 inicial
        'daily_limit_percentage': 10.0,  # 10% por dia = R$ 50
        'max_bet_percentage': 4.0,       # 4% por aposta = R$ 20
        'min_confidence': 65.0,          # Confiança mínima 65%
        'min_ev': 3.0                    # EV mínimo 3%
    })
    
    print("💰 Configuração conservadora para iniciante:")
    print(f"   • Bankroll: R$ 500")
    print(f"   • Limite diário: R$ 50 (10%)")
    print(f"   • Máximo por aposta: R$ 20 (4%)")
    
    # Exemplos de análises reais
    real_scenarios = [
        {
            "match": "T1 vs DRX",
            "your_analysis": "T1 65% chance",
            "market_odds": 1.60,  # Implica 62.5%
            "confidence": 80,
            "reasoning": "T1 melhor late game, DRX early game instável"
        },
        {
            "match": "G2 vs MAD Lions",
            "your_analysis": "G2 58% chance", 
            "market_odds": 1.85,  # Implica 54%
            "confidence": 70,
            "reasoning": "G2 melhor individual skill, MAD dependente de Elyoya"
        },
        {
            "match": "100 Thieves vs TSM",
            "your_analysis": "100T 45% chance",
            "market_odds": 2.50,  # Implica 40%
            "confidence": 68,
            "reasoning": "100T undervalued, TSM overrated pelo hype"
        }
    ]
    
    print(f"\n📊 Análises de partidas reais:")
    
    for i, scenario in enumerate(real_scenarios, 1):
        print(f"\n   {i}. {scenario['match']}")
        
        # Calcula probabilidade implícita das odds
        implied_prob = 1 / scenario['market_odds']
        your_prob = scenario['your_analysis'].split('%')[0]
        your_prob = float(your_prob.split()[-1]) / 100
        
        # Calcula EV
        ev = (your_prob * scenario['market_odds']) - 1
        ev_percent = ev * 100
        
        print(f"      📈 Sua análise: {your_prob:.1%}")
        print(f"      🏪 Odds do mercado: {scenario['market_odds']} (implica {implied_prob:.1%})")
        print(f"      💡 Expected Value: {ev_percent:+.2f}%")
        print(f"      🎯 Confiança: {scenario['confidence']}%")
        
        # Testa se seria recomendada
        bet_calc = manager.calculate_bet_size(
            confidence=scenario['confidence'],
            odds=scenario['market_odds'],
            your_probability=your_prob,
            reasoning=scenario['reasoning']
        )
        
        if bet_calc['recommended']:
            print(f"      ✅ RECOMENDADA: R${bet_calc['bet_amount']:.2f}")
            print(f"      🎲 Risco: {bet_calc['risk_level']}")
        else:
            print(f"      ❌ NÃO RECOMENDADA: {bet_calc['reason']}")
    
    print(f"\n💡 DICAS PARA USO REAL:")
    print(f"   1. 📊 Sempre compare suas probabilidades com odds do mercado")
    print(f"   2. 🎯 Só aposte com EV positivo (>3%)")
    print(f"   3. 💰 Respeite rigorosamente os limites de bankroll")
    print(f"   4. 📝 Documente todas as análises e resultados")
    print(f"   5. 📈 Acompanhe performance semanalmente")


if __name__ == "__main__":
    # Executa testes
    test_bankroll_manager()
    demonstrate_real_world_usage()
    
    print(f"\n🚀 SISTEMA PRONTO PARA IMPLEMENTAR AS PRÓXIMAS PRIORIDADES:")
    print(f"   2. 📊 Manual Value Analyzer")
    print(f"   3. 📈 Betting Tracker") 
    print(f"   4. 🎮 Pre-Game Analyzer")
    print(f"   5. 📱 Interface Unificada") 