#!/usr/bin/env python3
"""
Demo Completo: Sistema de Apostas LoL Integrado
Demonstração de todos os 4 sistemas funcionando em conjunto
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.personal_betting import create_integrated_betting_system, get_system_info
from datetime import datetime

def main():
    print("=" * 80)
    print("🎮 DEMO: SISTEMA COMPLETO DE APOSTAS LOL INTEGRADO")
    print("=" * 80)
    
    # 1. Informações do Sistema
    info = get_system_info()
    print(f"\n📊 {info['name']} v{info['version']}")
    print(f"🔧 Status: {info['status']}")
    
    print(f"\n🎯 COMPONENTES DISPONÍVEIS:")
    for key, component in info['components'].items():
        print(f"   {key}. {component}")
    
    # 2. Inicializa Sistema Integrado
    print(f"\n{'='*60}")
    print("🚀 INICIALIZANDO SISTEMA INTEGRADO")
    print(f"{'='*60}")
    
    system = create_integrated_betting_system(initial_bankroll=2000.0)
    
    print(f"✅ Sistema inicializado com R$ 2.000 de bankroll")
    print(f"🔗 Versão: {system['version']}")
    
    print(f"\n💡 FUNCIONALIDADES ATIVAS:")
    for feature in system['features']:
        print(f"   ✅ {feature}")
    
    # 3. Demonstração do Fluxo Completo
    print(f"\n{'='*60}")
    print("🎯 DEMONSTRAÇÃO: FLUXO COMPLETO DE APOSTAS")
    print(f"{'='*60}")
    
    # Componentes
    bankroll_manager = system['bankroll_manager']
    value_analyzer = system['value_analyzer']
    betting_tracker = system['betting_tracker']
    pre_game_analyzer = system['pre_game_analyzer']
    
    print(f"\n📱 Componentes carregados:")
    print(f"   💰 Bankroll Manager: R$ {bankroll_manager.settings.current_bankroll:.2f}")
    print(f"   🔍 Value Analyzer: Sistema ativo")
    print(f"   📊 Betting Tracker: Dashboard ativo")
    print(f"   🤖 Pre-Game Analyzer: {len(pre_game_analyzer.team_stats)} times")
    
    # Cenário de Uso: Análise Completa de uma Partida
    print(f"\n{'='*60}")
    print("🎮 CENÁRIO: ANÁLISE COMPLETA DE PARTIDA")
    print(f"{'='*60}")
    
    # Passo 1: Análise Automatizada
    print(f"\n1️⃣ ANÁLISE AUTOMATIZADA (Pre-Game Analyzer)")
    print("-" * 40)
    
    auto_analysis = pre_game_analyzer.analyze_upcoming_match(
        team1="T1",
        team2="Gen.G",
        league="LCK",
        match_importance="playoffs"
    )
    
    print(f"🤖 Análise automatizada concluída:")
    print(f"   📊 T1: {auto_analysis.team1_win_probability:.1%}")
    print(f"   📊 Gen.G: {auto_analysis.team2_win_probability:.1%}")
    print(f"   🎯 Confiança: {auto_analysis.confidence_level:.1%}")
    if auto_analysis.recommended_bet:
        print(f"   ✅ Recomendação: {auto_analysis.recommended_bet}")
    
    # Passo 2: Análise Manual
    print(f"\n2️⃣ ANÁLISE MANUAL (Value Analyzer)")
    print("-" * 40)
    
    # Cria análises dos times
    team1_analysis = value_analyzer.create_team_analysis(
        name="T1",
        recent_form="5W-0L",
        meta_adaptation=9,
        individual_skill=9,
        teamwork_level=8,
        coaching_impact=8,
        motivation_level=9
    )
    
    team2_analysis = value_analyzer.create_team_analysis(
        name="Gen.G",
        recent_form="2W-3L",
        meta_adaptation=7,
        individual_skill=8,
        teamwork_level=7,
        coaching_impact=7,
        motivation_level=6
    )
    
    manual_analysis = value_analyzer.analyze_match(
        league="LCK",
        team1_analysis=team1_analysis,
        team2_analysis=team2_analysis,
        your_probability_team1=0.75,  # Concorda com análise automática
        confidence_level=85,
        reasoning="T1 em forma excelente, Gen.G instável",
        market_odds={
            "betfair": {"team1": 1.40, "team2": 3.20},
            "bet365": {"team1": 1.35, "team2": 3.50},
            "pinnacle": {"team1": 1.42, "team2": 3.00}
        },
        importance_level=9  # playoffs
    )
    
    print(f"🔍 Análise manual concluída:")
    print(f"   📊 Sua probabilidade T1: {manual_analysis.your_probability_team1:.1%}")
    print(f"   💎 Melhor valor: {manual_analysis.best_value_bet}")
    if manual_analysis.expected_values:
        best_ev = max([max(evs.values()) for evs in manual_analysis.expected_values.values()])
        print(f"   📈 Expected Value: {best_ev:.2f}%")
    else:
        print(f"   📈 Expected Value: Calculando...")
    
    # Passo 3: Cálculo de Aposta
    print(f"\n3️⃣ CÁLCULO DE APOSTA (Bankroll Manager)")
    print("-" * 40)
    
    # Usa a melhor oportunidade identificada
    best_odds = 1.40  # T1 na betfair
    probability = 0.75
    
    bet_calculation = bankroll_manager.calculate_bet_size(
        confidence=probability * 100,
        odds=best_odds,
        your_probability=probability,
        reasoning="Análise integrada"
    )
    
    print(f"💰 Cálculo de aposta:")
    if bet_calculation.get('recommended'):
        print(f"   📊 Kelly Criterion: {bet_calculation['kelly_fraction']:.1%}")
        print(f"   💵 Valor recomendado: R$ {bet_calculation['bet_amount']:.2f}")
        print(f"   ⚠️ Nível de risco: {bet_calculation['risk_level']}")
        print(f"   📈 Expected Value: {bet_calculation['ev_percentage']:.2f}%")
    else:
        print(f"   ❌ Aposta não recomendada: {bet_calculation.get('reason', 'Critérios não atendidos')}")
    
    # Passo 4: Registro da Aposta
    print(f"\n4️⃣ REGISTRO DA APOSTA (Sistema Integrado)")
    print("-" * 40)
    
    if bet_calculation.get('recommended'):
        # Registra no bankroll manager
        bet_amount = bet_calculation['bet_amount']
        bet_id = bankroll_manager.place_bet(
            team="T1",
            opponent="Gen.G",
            league="LCK",
            odds=best_odds,
            amount=bet_amount,
            confidence=probability * 100,
            ev_percentage=bet_calculation['ev_percentage'],
            reasoning="Análise integrada - T1 vs Gen.G"
        )['bet_id']
        
        # Registra no betting tracker
        betting_tracker.add_bet(
            bet_id=bet_id,
            amount=bet_amount,
            odds=best_odds,
            selection="T1",
            match="T1 vs Gen.G",
            league="LCK",
            bet_type="Match Winner"
        )
        
        print(f"✅ Aposta registrada:")
        print(f"   🎫 ID: {bet_id}")
        print(f"   💵 Valor: R$ {bet_amount:.2f}")
        print(f"   🎯 Seleção: T1")
        print(f"   📊 Odds: {best_odds}")
        
        # Passo 5: Simulação de Resultado
        print(f"\n5️⃣ SIMULAÇÃO DE RESULTADO")
        print("-" * 40)
        
        # Simula vitória do T1
        result_won = True
        payout = bet_amount * best_odds if result_won else 0
        
        # Resolve aposta no bankroll manager
        bankroll_manager.resolve_bet(bet_id, result_won)
        
        # Resolve no betting tracker
        betting_tracker.resolve_bet(bet_id, result_won)
        
        print(f"🎉 Resultado: {'VITÓRIA' if result_won else 'DERROTA'}")
        print(f"💰 Payout: R$ {payout:.2f}")
        print(f"📊 Lucro: R$ {payout - bet_amount:.2f}")
        
        # Passo 6: Dashboard de Performance
        print(f"\n6️⃣ DASHBOARD DE PERFORMANCE")
        print("-" * 40)
        
        dashboard = betting_tracker.generate_dashboard()
        print(dashboard)
        
    else:
        print("❌ Aposta não recomendada pelo sistema")
        print(f"   Motivo: {bet_calculation.get('reason', 'Critérios não atendidos')}")
    
    # Demonstração de Múltiplas Análises
    print(f"\n{'='*60}")
    print("📊 DEMONSTRAÇÃO: MÚLTIPLAS ANÁLISES")
    print(f"{'='*60}")
    
    # Analisa várias partidas rapidamente
    matches = [
        ("G2", "FNC", "LEC", 0.55),
        ("100T", "TL", "LCS", 0.62),
        ("JDG", "BLG", "LPL", 0.68)
    ]
    
    print(f"\n🎯 Analisando {len(matches)} partidas adicionais...")
    
    for i, (team1, team2, league, prob) in enumerate(matches, 1):
        print(f"\n{i}. {team1} vs {team2} ({league})")
        
        # Análise automática
        auto = pre_game_analyzer.analyze_upcoming_match(
            team1=team1, team2=team2, league=league
        )
        
        # Análise rápida
        odds_sim = 1.85  # Odds simuladas
        bet_calc = bankroll_manager.calculate_bet_size(
            confidence=prob * 100, odds=odds_sim, your_probability=prob, reasoning="Análise rápida"
        )
        
        print(f"   🤖 Auto: {auto.team1_win_probability:.1%} | Manual: {prob:.1%}")
        if bet_calc.get('recommended'):
            print(f"   💰 Aposta: R$ {bet_calc['bet_amount']:.2f}")
            print(f"   ✅ Recomendada")
        else:
            print(f"   💰 Aposta: R$ 0.00")
            print(f"   ❌ Não recomendada")
    
    # Estatísticas Finais
    print(f"\n{'='*60}")
    print("📈 ESTATÍSTICAS FINAIS DO SISTEMA")
    print(f"{'='*60}")
    
    # Obtém estatísticas do bankroll
    stats = bankroll_manager.get_performance_stats()
    
    print(f"\n💰 BANKROLL MANAGER:")
    print(f"   Bankroll atual: R$ {bankroll_manager.settings.current_bankroll:.2f}")
    print(f"   Total apostado: R$ {stats.get('total_staked', 0.0):.2f}")
    print(f"   Lucro total: R$ {stats.get('total_profit', 0.0):.2f}")
    print(f"   ROI: {stats.get('roi', 0.0):.2f}%")
    
    print(f"\n🔍 VALUE ANALYZER:")
    print(f"   Análises realizadas: {len(value_analyzer.analyses)}")
    print(f"   Sistema de análise manual ativo")
    
    print(f"\n📊 BETTING TRACKER:")
    print(f"   Sistema de tracking ativo")
    print(f"   Dashboard visual disponível")
    
    print(f"\n🤖 PRE-GAME ANALYZER:")
    print(f"   Análises automáticas: {len(pre_game_analyzer.analyses)}")
    print(f"   Times na base: {len(pre_game_analyzer.team_stats)}")
    print(f"   Partidas históricas: {len(pre_game_analyzer.historical_results)}")
    
    print(f"\n{'='*80}")
    print("✅ DEMO DO SISTEMA INTEGRADO CONCLUÍDA COM SUCESSO!")
    print("🚀 Sistema completo pronto para uso em apostas reais")
    print("💡 Todos os 4 componentes funcionando perfeitamente em conjunto")
    print("=" * 80)

if __name__ == "__main__":
    main() 