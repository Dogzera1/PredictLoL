#!/usr/bin/env python3
"""
DEMO SISTEMA COMPLETO FINAL
Demonstração integrada dos 3 sistemas de apostas pessoais:
1. Personal Bankroll Manager
2. Manual Value Analyzer  
3. Betting Tracker

Sistema completo para apostas LoL independentes
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.personal_betting import PersonalBankrollManager, ManualValueAnalyzer, BettingTracker

def demo_sistema_completo():
    """Demonstração completa do sistema integrado"""
    print("🚀 DEMO SISTEMA COMPLETO DE APOSTAS LOL")
    print("=" * 80)
    print("Sistema integrado para apostadores independentes")
    print("Bankroll Manager + Value Analyzer + Betting Tracker")
    print("=" * 80)
    
    # ========================================
    # 1. INICIALIZAÇÃO DOS SISTEMAS
    # ========================================
    print("\n🔧 1. INICIALIZANDO SISTEMAS INTEGRADOS")
    print("-" * 50)
    
    # Bankroll Manager
    print("💰 Inicializando Personal Bankroll Manager...")
    bankroll_manager = PersonalBankrollManager()
    setup_result = bankroll_manager.setup_bankroll(
        initial_amount=2000.0,
        settings={
            'daily_limit_percentage': 15.0,  # 15% do bankroll por dia
            'max_bet_percentage': 8.0,       # 8% máximo por aposta
            'kelly_multiplier': 0.3,         # Kelly conservador
            'min_confidence': 70.0,          # Mínimo 70% confiança
            'min_ev': 5.0                    # Mínimo 5% EV
        }
    )
    print(f"✅ {setup_result['message']}")
    print(f"   Limite diário: R$ {setup_result['daily_limit']:.2f}")
    print(f"   Máximo por aposta: R$ {setup_result['max_bet']:.2f}")
    
    # Value Analyzer
    print("\n🔍 Inicializando Manual Value Analyzer...")
    value_analyzer = ManualValueAnalyzer()
    print("✅ Value Analyzer pronto para análises manuais")
    
    # Betting Tracker
    print("\n📊 Inicializando Betting Tracker...")
    betting_tracker = BettingTracker(
        bankroll_manager=bankroll_manager,
        value_analyzer=value_analyzer
    )
    print("✅ Betting Tracker pronto para monitoramento")
    
    # ========================================
    # 2. ANÁLISE DE VALUE BET COMPLETA
    # ========================================
    print("\n🎯 2. ANÁLISE COMPLETA DE VALUE BET")
    print("-" * 50)
    print("Cenário: T1 vs Gen.G - Final LCK Spring")
    
    # Análise detalhada dos times
    print("\n📋 Criando análises dos times...")
    
    t1_analysis = value_analyzer.create_team_analysis(
        name="T1",
        recent_form="8W-2L",
        key_players_status="Full roster - Faker em ótima forma",
        meta_adaptation=9,      # Excelente adaptação ao meta
        individual_skill=10,    # Skill individual excepcional
        teamwork_level=9,       # Teamwork de elite
        coaching_impact=8,      # Coaching sólido
        motivation_level=10,    # Motivação máxima para final
        notes="T1 dominante na split, Faker jogando em alto nível"
    )
    
    geng_analysis = value_analyzer.create_team_analysis(
        name="Gen.G",
        recent_form="6W-4L",
        key_players_status="Chovy com problema no punho",
        meta_adaptation=7,      # Boa adaptação
        individual_skill=8,     # Skill alto mas abaixo do T1
        teamwork_level=7,       # Teamwork bom
        coaching_impact=7,      # Coaching competente
        motivation_level=8,     # Motivação alta
        notes="Gen.G inconsistente, dependente do Chovy"
    )
    
    print(f"✅ Análise T1: {t1_analysis.individual_skill}/10 skill, {t1_analysis.motivation_level}/10 motivação")
    print(f"✅ Análise Gen.G: {geng_analysis.individual_skill}/10 skill, {geng_analysis.motivation_level}/10 motivação")
    
    # Análise da partida
    print("\n🔍 Realizando análise da partida...")
    
    match_analysis = value_analyzer.analyze_match(
        league="LCK",
        team1_analysis=t1_analysis,
        team2_analysis=geng_analysis,
        your_probability_team1=0.75,  # 75% chance para T1
        confidence_level=85,           # 85% confiança na análise
        reasoning="""
        T1 claramente superior:
        - Faker em forma excepcional
        - Teamwork superior demonstrado na split
        - Histórico positivo contra Gen.G
        - Gen.G dependente demais do Chovy
        - Pressão da final favorece experiência do T1
        """,
        market_odds={
            "bet365": {"team1": 1.75, "team2": 2.15},
            "pinnacle": {"team1": 1.78, "team2": 2.08},
            "betfair": {"team1": 1.80, "team2": 2.05}
        },
        importance_level=10,  # Final - máxima importância
        patch_impact="Favorece T1 - meta de teamfight",
        historical_h2h="T1 6-2 nos últimos confrontos"
    )
    
    print(f"✅ Análise criada - Qualidade: {match_analysis.analysis_quality}")
    print(f"   Sua probabilidade T1: {match_analysis.your_probability_team1*100:.1f}%")
    print(f"   Confiança: {match_analysis.confidence_level}%")
    
    # Comparação de casas de apostas
    print("\n💰 Comparando odds entre casas...")
    comparison = value_analyzer.compare_bookmakers(match_analysis)
    
    if "error" not in comparison:
        print("📊 COMPARAÇÃO DE ODDS:")
        for casa, odds in comparison['bookmakers'].items():
            ev_t1 = odds.get('team1_ev', 0)
            ev_t2 = odds.get('team2_ev', 0)
            print(f"   {casa}: T1 @ {odds['team1_odds']:.2f} (EV: {ev_t1:+.1f}%) | Gen.G @ {odds['team2_odds']:.2f} (EV: {ev_t2:+.1f}%)")
        
        if comparison['best_odds']:
            best_t1 = comparison['best_odds']['team1']
            best_t2 = comparison['best_odds']['team2']
            print(f"\n🎯 MELHORES ODDS:")
            print(f"   T1: {best_t1['casa']} @ {best_t1['odds']:.2f} (EV: {best_t1['ev']:+.1f}%)")
            print(f"   Gen.G: {best_t2['casa']} @ {best_t2['odds']:.2f} (EV: {best_t2['ev']:+.1f}%)")
    
    # ========================================
    # 3. CÁLCULO DE APOSTA OTIMIZADA
    # ========================================
    print("\n💡 3. CÁLCULO DE APOSTA OTIMIZADA")
    print("-" * 50)
    
    # Usa a melhor odd encontrada
    best_odds = 1.80  # Betfair
    
    bet_calculation = bankroll_manager.calculate_bet_size(
        confidence=85,
        odds=best_odds,
        your_probability=0.75,
        league="LCK",
        reasoning="Final LCK - T1 favorito com value significativo"
    )
    
    if bet_calculation["recommended"]:
        print("✅ APOSTA RECOMENDADA:")
        print(f"   Time: T1")
        print(f"   Odds: {best_odds}")
        print(f"   Valor: R$ {bet_calculation['bet_amount']:.2f}")
        print(f"   % do Bankroll: {bet_calculation['percentage_bankroll']:.1f}%")
        print(f"   Expected Value: {bet_calculation['ev_percentage']:+.2f}%")
        print(f"   Retorno Potencial: R$ {bet_calculation['potential_return']:.2f}")
        print(f"   Lucro Potencial: R$ {bet_calculation['potential_profit']:.2f}")
        print(f"   Nível de Risco: {bet_calculation['risk_level'].upper()}")
        
        if bet_calculation.get('warnings'):
            print(f"⚠️  Avisos: {', '.join(bet_calculation['warnings'])}")
    else:
        print(f"❌ Aposta NÃO recomendada: {bet_calculation.get('reason', 'Critérios não atendidos')}")
        return
    
    # ========================================
    # 4. REGISTRO E TRACKING DA APOSTA
    # ========================================
    print("\n📝 4. REGISTRANDO APOSTA NO SISTEMA")
    print("-" * 50)
    
    # Inicia sessão de tracking
    session = betting_tracker.track_session("Final LCK Spring - T1 vs Gen.G")
    print(f"🎮 {session['message']}")
    
    # Registra a aposta
    bet_result = bankroll_manager.place_bet(
        team="T1",
        opponent="Gen.G", 
        league="LCK",
        odds=best_odds,
        amount=bet_calculation["bet_amount"],
        confidence=85,
        ev_percentage=bet_calculation["ev_percentage"],
        reasoning="Final LCK - T1 superior em todos os aspectos, value excelente @ 1.80"
    )
    
    if bet_result["success"]:
        print(f"✅ {bet_result['message']}")
        print(f"   Bankroll restante: R$ {bet_result['remaining_bankroll']:.2f}")
        
        # Simula resultado da partida (T1 vence 3-1)
        print(f"\n🎮 SIMULANDO RESULTADO DA PARTIDA...")
        print(f"   T1 3 x 1 Gen.G")
        print(f"   Faker MVP com performance dominante!")
        
        # Resolve aposta como vitória
        resolution = bankroll_manager.resolve_bet(bet_result["bet_id"], True)
        if resolution["success"]:
            print(f"🎉 {resolution['result']}!")
            print(f"   Lucro: R$ {resolution['profit']:+.2f}")
            print(f"   Novo bankroll: R$ {resolution['new_bankroll']:.2f}")
    
    # Finaliza sessão
    session_end = betting_tracker.end_session(session['session_id'])
    if session_end['success']:
        summary = session_end['session_summary']
        print(f"\n📊 RESUMO DA SESSÃO:")
        print(f"   Duração: {summary['duration']}")
        print(f"   Resultado: {summary['win_rate']:.0f}% win rate")
        print(f"   Lucro da sessão: R$ {summary['profit']:+.2f}")
    
    # ========================================
    # 5. DASHBOARD E ANÁLISE FINAL
    # ========================================
    print("\n📈 5. DASHBOARD DE PERFORMANCE")
    print("-" * 50)
    
    # Cria snapshot
    betting_tracker.create_daily_snapshot()
    
    # Dashboard visual
    dashboard = betting_tracker.generate_dashboard(period_days=1)
    print(dashboard)
    
    # ========================================
    # 6. RELATÓRIO FINAL INTEGRADO
    # ========================================
    print("\n📋 6. RELATÓRIO FINAL INTEGRADO")
    print("=" * 80)
    
    # Performance do bankroll
    bankroll_stats = bankroll_manager.get_performance_stats(days=1)
    
    print("💰 PERFORMANCE FINANCEIRA:")
    print(f"   Bankroll inicial: R$ 2000.00")
    print(f"   Bankroll atual: R$ {bankroll_stats['current_bankroll']:.2f}")
    print(f"   Mudança: R$ {bankroll_stats['bankroll_change']:+.2f}")
    print(f"   ROI: {bankroll_stats['roi']:+.2f}%")
    print(f"   Win Rate: {bankroll_stats['win_rate']:.1f}%")
    
    # Análises realizadas
    analysis_summary = value_analyzer.get_analysis_summary(days=1)
    print(f"\n🔍 ANÁLISES REALIZADAS:")
    print(f"   Total de análises: {analysis_summary.get('total_analyses', 0)}")
    print(f"   Confiança média: {analysis_summary.get('average_confidence', 0):.1f}%")
    print(f"   Value bets encontrados: {analysis_summary.get('total_value_bets_found', 0)}")
    
    # Métricas de tracking
    tracking_metrics = betting_tracker.calculate_performance_metrics(period_days=1)
    print(f"\n📊 MÉTRICAS DE TRACKING:")
    print(f"   Apostas monitoradas: {tracking_metrics.total_bets}")
    print(f"   Streak atual: {tracking_metrics.current_streak} {tracking_metrics.streak_type}s")
    print(f"   Nível de performance: {tracking_metrics.performance_level.upper()}")
    print(f"   Tendência: {tracking_metrics.trend_direction.upper()}")
    
    # ========================================
    # 7. PRÓXIMOS PASSOS E RECOMENDAÇÕES
    # ========================================
    print(f"\n🎯 7. PRÓXIMOS PASSOS")
    print("=" * 80)
    
    print("✅ SISTEMA COMPLETAMENTE OPERACIONAL:")
    print("   • Bankroll Manager: Gestão financeira profissional")
    print("   • Value Analyzer: Identificação sistemática de value bets")
    print("   • Betting Tracker: Monitoramento visual de performance")
    
    print(f"\n📈 CAPACIDADES DO SISTEMA:")
    print("   • Kelly Criterion para sizing otimizado")
    print("   • Análise detalhada de times e contexto")
    print("   • Comparação automática entre casas de apostas")
    print("   • Dashboard visual em tempo real")
    print("   • Tracking de streaks e padrões")
    print("   • Relatórios exportáveis")
    print("   • Controle de risco avançado")
    
    print(f"\n🚀 PRONTO PARA USO REAL:")
    print("   • Configure seu bankroll inicial")
    print("   • Defina seus critérios de risco")
    print("   • Analise partidas com o Value Analyzer")
    print("   • Registre apostas no Bankroll Manager")
    print("   • Monitore performance no Betting Tracker")
    
    print(f"\n💡 DICAS PARA SUCESSO:")
    print("   • Seja disciplinado com os critérios")
    print("   • Nunca aposte sem análise prévia")
    print("   • Respeite os limites do sistema")
    print("   • Monitore performance regularmente")
    print("   • Ajuste estratégia baseado nos dados")
    
    final_bankroll = bankroll_manager.settings.current_bankroll
    initial_bankroll = 2000.0
    total_profit = final_bankroll - initial_bankroll
    total_roi = (total_profit / initial_bankroll) * 100
    
    print(f"\n🏆 RESULTADO DA DEMONSTRAÇÃO:")
    print("=" * 80)
    print(f"💰 Bankroll: R$ {initial_bankroll:.2f} → R$ {final_bankroll:.2f}")
    print(f"📈 Lucro: R$ {total_profit:+.2f}")
    print(f"📊 ROI: {total_roi:+.2f}%")
    print(f"🎯 Sistema: 100% OPERACIONAL")
    
    print(f"\n🎉 SISTEMA COMPLETO DE APOSTAS LOL PRONTO!")
    print("=" * 80)


if __name__ == "__main__":
    demo_sistema_completo()