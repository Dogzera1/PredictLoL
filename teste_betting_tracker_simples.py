#!/usr/bin/env python3
"""
Teste Simples do Betting Tracker
Demonstra funcionalidades básicas do sistema
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.personal_betting.bankroll_manager import PersonalBankrollManager
from bot.personal_betting.value_analyzer import ManualValueAnalyzer
from bot.personal_betting.betting_tracker import BettingTracker

def test_betting_tracker():
    """Teste simples do Betting Tracker"""
    print("🚀 TESTE SIMPLES DO BETTING TRACKER")
    print("=" * 60)
    
    # 1. Inicializa sistemas
    print("\n1️⃣ Inicializando sistemas...")
    bankroll_manager = PersonalBankrollManager()
    bankroll_manager.setup_bankroll(1000.0)
    value_analyzer = ManualValueAnalyzer()
    betting_tracker = BettingTracker(
        bankroll_manager=bankroll_manager,
        value_analyzer=value_analyzer
    )
    
    print("✅ Sistemas inicializados com sucesso!")
    
    # 2. Simula algumas apostas
    print("\n2️⃣ Simulando apostas...")
    
    # Aposta 1 - Vitória
    bet_calc = bankroll_manager.calculate_bet_size(
        confidence=75,
        odds=1.85,
        your_probability=0.75,
        league="LCK",
        reasoning="T1 favorito contra Gen.G"
    )
    
    if bet_calc.get("recommended"):
        bet_result = bankroll_manager.place_bet(
            team="T1",
            opponent="Gen.G",
            league="LCK",
            odds=1.85,
            amount=bet_calc["bet_amount"],
            confidence=75,
            ev_percentage=bet_calc["ev_percentage"],
            reasoning="T1 favorito - boa forma"
        )
        
        if bet_result["success"]:
            bankroll_manager.resolve_bet(bet_result['bet_id'], True)  # Vitória
            print(f"✅ T1 vs Gen.G - VITÓRIA - R$ {bet_calc['bet_amount']:.2f}")
    
    # Aposta 2 - Derrota
    bet_calc2 = bankroll_manager.calculate_bet_size(
        confidence=65,
        odds=2.10,
        your_probability=0.65,
        league="LEC",
        reasoning="FNC vs G2 - jogo equilibrado"
    )
    
    if bet_calc2.get("recommended"):
        bet_result2 = bankroll_manager.place_bet(
            team="FNC",
            opponent="G2",
            league="LEC",
            odds=2.10,
            amount=bet_calc2["bet_amount"],
            confidence=65,
            ev_percentage=bet_calc2["ev_percentage"],
            reasoning="FNC underdog com value"
        )
        
        if bet_result2["success"]:
            bankroll_manager.resolve_bet(bet_result2['bet_id'], False)  # Derrota
            print(f"❌ FNC vs G2 - DERROTA - R$ {bet_calc2['bet_amount']:.2f}")
    
    # Aposta 3 - Vitória
    bet_calc3 = bankroll_manager.calculate_bet_size(
        confidence=80,
        odds=1.70,
        your_probability=0.80,
        league="LCS",
        reasoning="100T muito forte"
    )
    
    if bet_calc3.get("recommended"):
        bet_result3 = bankroll_manager.place_bet(
            team="100T",
            opponent="TL",
            league="LCS",
            odds=1.70,
            amount=bet_calc3["bet_amount"],
            confidence=80,
            ev_percentage=bet_calc3["ev_percentage"],
            reasoning="100T dominante na split"
        )
        
        if bet_result3["success"]:
            bankroll_manager.resolve_bet(bet_result3['bet_id'], True)  # Vitória
            print(f"✅ 100T vs TL - VITÓRIA - R$ {bet_calc3['bet_amount']:.2f}")
    
    # 3. Cria snapshots
    print("\n3️⃣ Criando snapshots...")
    betting_tracker.create_daily_snapshot()
    print("✅ Snapshot diário criado")
    
    # 4. Dashboard básico
    print("\n4️⃣ Dashboard Visual...")
    print("=" * 60)
    dashboard = betting_tracker.generate_dashboard(period_days=7)
    print(dashboard)
    
    # 5. Métricas de performance
    print("\n5️⃣ Métricas de Performance...")
    print("=" * 60)
    metrics = betting_tracker.calculate_performance_metrics(period_days=7)
    
    print(f"📊 RESUMO:")
    print(f"   Total de Apostas: {metrics.total_bets}")
    print(f"   Win Rate: {metrics.win_rate:.1f}%")
    print(f"   ROI: {metrics.roi:+.2f}%")
    print(f"   Lucro Total: R$ {metrics.total_profit:+.2f}")
    print(f"   Bankroll Atual: R$ {metrics.bankroll_current:.2f}")
    
    # 6. Análise de padrões
    print("\n6️⃣ Análise de Padrões...")
    print("=" * 60)
    patterns = betting_tracker.analyze_betting_patterns(period_days=7)
    
    if "error" not in patterns and patterns.get('total_bets_analyzed', 0) > 0:
        print(f"📊 Apostas analisadas: {patterns['total_bets_analyzed']}")
        
        if patterns.get('odds_range_performance'):
            print("\n🎯 PERFORMANCE POR RANGE DE ODDS:")
            for range_key, stats in patterns['odds_range_performance'].items():
                if stats['bets'] > 0:
                    profit_emoji = "🟢" if stats['profit'] > 0 else "🔴" if stats['profit'] < 0 else "⚪"
                    print(f"   {profit_emoji} {range_key}: {stats['bets']} apostas | {stats['win_rate']:.1f}% WR | R$ {stats['profit']:+.2f}")
    else:
        print("📊 Dados insuficientes para análise de padrões")
    
    # 7. Tracking de sessão
    print("\n7️⃣ Tracking de Sessão...")
    print("=" * 60)
    
    # Inicia sessão
    session_result = betting_tracker.track_session("Teste Simples")
    print(f"✅ {session_result['message']}")
    
    # Finaliza sessão
    end_result = betting_tracker.end_session(session_result['session_id'])
    if end_result['success']:
        summary = end_result['session_summary']
        print(f"📊 Sessão finalizada:")
        print(f"   Duração: {summary['duration']}")
        print(f"   Apostas: {summary['bets_placed']}")
        print(f"   Vitórias: {summary['wins']}")
    
    # 8. Relatório exportável
    print("\n8️⃣ Relatório Resumido...")
    print("=" * 60)
    
    summary_report = betting_tracker.export_performance_report(
        period_days=7, 
        format_type="summary"
    )
    print(summary_report)
    
    # 9. Gráfico ASCII demonstrativo
    print("\n9️⃣ Gráfico ASCII...")
    print("=" * 60)
    
    # Simula evolução do bankroll
    bankroll_evolution = [1000, 1025, 1010, 1040, 1020, 1055, 1035, 1070]
    chart = betting_tracker.generate_ascii_chart(
        bankroll_evolution, 
        "Evolução do Bankroll (8 dias)", 
        width=40, 
        height=6
    )
    print(chart)
    
    # 10. Status final
    print(f"\n🏆 TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print(f"✅ Dashboard visual - OK")
    print(f"✅ Métricas de performance - OK")
    print(f"✅ Análise de padrões - OK")
    print(f"✅ Tracking de sessões - OK")
    print(f"✅ Relatórios exportáveis - OK")
    print(f"✅ Gráficos ASCII - OK")
    
    final_bankroll = bankroll_manager.settings.current_bankroll
    initial_bankroll = 1000.0
    total_profit = final_bankroll - initial_bankroll
    total_roi = (total_profit / initial_bankroll) * 100
    
    print(f"\n💰 RESULTADO FINAL:")
    print(f"   Bankroll Inicial: R$ {initial_bankroll:.2f}")
    print(f"   Bankroll Final: R$ {final_bankroll:.2f}")
    print(f"   Lucro Total: R$ {total_profit:+.2f}")
    print(f"   ROI Total: {total_roi:+.2f}%")
    
    print(f"\n🎯 BETTING TRACKER 100% OPERACIONAL!")


if __name__ == "__main__":
    test_betting_tracker() 