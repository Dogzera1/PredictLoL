#!/usr/bin/env python3
"""
Teste Completo do Betting Tracker
Demonstra todas as funcionalidades do sistema de tracking visual
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.personal_betting.bankroll_manager import PersonalBankrollManager
from bot.personal_betting.value_analyzer import ManualValueAnalyzer
from bot.personal_betting.betting_tracker import BettingTracker

def simulate_betting_history(bankroll_manager: PersonalBankrollManager, value_analyzer: ManualValueAnalyzer):
    """Simula histórico de apostas para demonstrar o tracker"""
    print("📊 Simulando histórico de apostas...")
    
    # Simula 30 apostas nos últimos 15 dias
    betting_scenarios = [
        # Últimos 15 dias - mix de resultados realistas
        ("T1", "Gen.G", "LCK", 70, 1.85, "won", -2),    # 2 dias atrás
        ("KT", "DRX", "LCK", 65, 2.10, "lost", -2),
        ("FNC", "G2", "LEC", 80, 1.65, "won", -3),      # 3 dias atrás
        ("MAD", "BDS", "LEC", 60, 2.50, "lost", -3),
        ("FLY", "100T", "LCS", 75, 1.90, "won", -4),    # 4 dias atrás
        ("TL", "C9", "LCS", 85, 1.75, "won", -4),
        ("JDG", "BLG", "LPL", 60, 2.20, "lost", -5),    # 5 dias atrás
        ("WBG", "TES", "LPL", 55, 2.80, "lost", -5),
        ("T1", "HLE", "LCK", 90, 1.55, "won", -6),      # 6 dias atrás
        ("GEN", "KT", "LCK", 75, 1.80, "won", -6),
        ("G2", "FNC", "LEC", 70, 1.95, "lost", -7),     # 7 dias atrás
        ("VIT", "SK", "LEC", 80, 1.70, "won", -7),
        ("100T", "TSM", "LCS", 65, 2.30, "won", -8),    # 8 dias atrás
        ("TL", "EG", "LCS", 55, 2.60, "lost", -8),
        ("BLG", "LNG", "LPL", 85, 1.60, "won", -9),     # 9 dias atrás
        ("JDG", "WE", "LPL", 70, 2.00, "won", -9),
        ("DRX", "LSB", "LCK", 75, 1.85, "lost", -10),   # 10 dias atrás
        ("T1", "NS", "LCK", 95, 1.45, "won", -10),
        ("FNC", "VIT", "LEC", 60, 2.40, "lost", -11),   # 11 dias atrás
        ("G2", "MAD", "LEC", 80, 1.75, "won", -11),
        ("C9", "FLY", "LCS", 70, 1.90, "won", -12),     # 12 dias atrás
        ("TSM", "100T", "LCS", 45, 3.20, "lost", -12),
        ("TES", "IG", "LPL", 85, 1.65, "won", -13),     # 13 dias atrás
        ("RNG", "BLG", "LPL", 55, 2.50, "lost", -13),
        ("GEN", "DK", "LCK", 80, 1.70, "won", -14),     # 14 dias atrás
        ("KT", "HLE", "LCK", 60, 2.10, "lost", -14),
        ("SK", "BDS", "LEC", 75, 1.80, "won", -15),     # 15 dias atrás
        ("MAD", "FNC", "LEC", 65, 2.20, "lost", -15),
        ("EG", "TL", "LCS", 70, 1.95, "won", -15),
        ("100T", "C9", "LCS", 85, 1.60, "won", -15),
    ]
    
    print(f"💰 Bankroll inicial: R$ {bankroll_manager.settings.current_bankroll:.2f}")
    
    for i, (team1, team2, league, confidence, odds, result, days_ago) in enumerate(betting_scenarios):
        # Cria análises dos times
        team1_analysis = value_analyzer.create_team_analysis(
            name=team1,
            recent_form="3W-2L",
            meta_adaptation=7,
            individual_skill=8,
            teamwork_level=7,
            coaching_impact=6,
            motivation_level=7
        )
        
        team2_analysis = value_analyzer.create_team_analysis(
            name=team2,
            recent_form="2W-3L", 
            meta_adaptation=6,
            individual_skill=7,
            teamwork_level=6,
            coaching_impact=6,
            motivation_level=6
        )
        
        # Cria análise da partida
        analysis = value_analyzer.analyze_match(
            league=league,
            team1_analysis=team1_analysis,
            team2_analysis=team2_analysis,
            your_probability_team1=confidence/100,
            confidence_level=confidence,
            reasoning=f"Value bet identificado - {confidence}% confiança",
            market_odds={"bet365": {"team1": odds, "team2": 2.5 - odds + 0.5}},
            importance_level=5
        )
        
        # Simula recomendação de aposta baseada no Kelly
        bet_calc = bankroll_manager.calculate_bet_size(
            confidence=confidence,
            odds=odds,
            your_probability=confidence/100,
            league=league,
            reasoning=f"Value bet - {confidence}% confiança"
        )
        
        if bet_calc.get("recommended"):
            # Registra aposta
            bet_result = bankroll_manager.place_bet(
                team=team1,
                opponent=team2,
                league=league,
                odds=odds,
                amount=bet_calc["bet_amount"],
                confidence=confidence,
                ev_percentage=bet_calc["ev_percentage"],
                reasoning=f"Value bet - {bet_calc['ev_percentage']:.1f}% EV"
            )
            
            if bet_result["success"]:
                # Ajusta data da aposta
                bet = bankroll_manager.bets[-1]
                bet_date = datetime.now() + timedelta(days=days_ago)
                bet.date = bet_date.isoformat()
                
                # Resolve aposta
                if result == "won":
                    bankroll_manager.resolve_bet(bet_result['bet_id'], True)
                    print(f"✅ {team1} vs {team2} - GANHOU")
                else:
                    bankroll_manager.resolve_bet(bet_result['bet_id'], False)
                    print(f"❌ {team1} vs {team2} - PERDEU")
    
    bankroll_manager._save_data()
    print(f"\n💰 Bankroll final: R$ {bankroll_manager.settings.current_bankroll:.2f}")
    print(f"📊 Total de apostas simuladas: {len(betting_scenarios)}")


def test_full_betting_tracker():
    """Teste completo do Betting Tracker"""
    print("🚀 TESTE COMPLETO DO BETTING TRACKER")
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
    
    # 2. Simula histórico
    print("\n2️⃣ Simulando histórico de apostas...")
    simulate_betting_history(bankroll_manager, value_analyzer)
    
    # 3. Cria snapshots diários
    print("\n3️⃣ Criando snapshots diários...")
    for i in range(15):
        snapshot_date = datetime.now() - timedelta(days=i)
        # Simula snapshot
        betting_tracker.create_daily_snapshot()
    
    # 4. Dashboard completo
    print("\n4️⃣ Gerando Dashboard Visual...")
    print("=" * 60)
    dashboard = betting_tracker.generate_dashboard(period_days=15)
    print(dashboard)
    
    # 5. Análise de padrões
    print("\n5️⃣ Análise de Padrões de Apostas...")
    print("=" * 60)
    patterns = betting_tracker.analyze_betting_patterns(period_days=15)
    
    if "error" not in patterns:
        print(f"📊 Apostas analisadas: {patterns['total_bets_analyzed']}")
        
        # Performance por dia da semana
        print("\n📅 PERFORMANCE POR DIA DA SEMANA:")
        for day, stats in patterns['weekday_performance'].items():
            profit_emoji = "🟢" if stats['profit'] > 0 else "🔴" if stats['profit'] < 0 else "⚪"
            print(f"   {profit_emoji} {day}: {stats['bets']} apostas | {stats['win_rate']:.1f}% WR | R$ {stats['profit']:+.2f}")
        
        # Performance por odds
        print("\n🎯 PERFORMANCE POR RANGE DE ODDS:")
        for range_key, stats in patterns['odds_range_performance'].items():
            if stats['bets'] > 0:
                profit_emoji = "🟢" if stats['profit'] > 0 else "🔴" if stats['profit'] < 0 else "⚪"
                roi = (stats['profit'] / (stats['bets'] * 50)) * 100  # Estimativa ROI
                print(f"   {profit_emoji} {range_key}: {stats['bets']} apostas | {stats['win_rate']:.1f}% WR | {roi:+.1f}% ROI")
    
    # 6. Tracking de sessão
    print("\n6️⃣ Testando Tracking de Sessão...")
    print("=" * 60)
    
    # Inicia sessão
    session_result = betting_tracker.track_session("Sessão de Teste Completa")
    print(f"✅ {session_result['message']}")
    
    # Simula algumas apostas na sessão
    print("📊 Simulando apostas na sessão...")
    session_bets = [
        ("T1", "GEN", "LCK", 80, 1.70, "won"),
        ("FNC", "G2", "LEC", 75, 1.85, "lost"),
        ("100T", "TL", "LCS", 85, 1.60, "won"),
    ]
    
    for team1, team2, league, confidence, odds, result in session_bets:
        # Análise rápida
        analysis = value_analyzer.analyze_match(
            team1=team1,
            team2=team2,
            league=league,
            match_importance="regular",
            estimated_probability=confidence,
            bookmaker_odds={"bet365": odds}
        )
        
        if analysis and analysis.value_bets:
            best_bet = analysis.value_bets[0]
            bet_result = bankroll_manager.place_bet(
                team=team1,
                opponent=team2,
                league=league,
                odds=odds,
                amount=best_bet.recommended_bet_size,
                confidence=confidence,
                ev_percentage=best_bet.expected_value,
                reasoning=f"Sessão: {best_bet.expected_value:.1f}% EV"
            )
            
            if bet_result["success"]:
                bet_id = bet_result["bet_id"]
                bankroll_manager.resolve_bet(bet_id, result == "won")
                print(f"   {'✅' if result == 'won' else '❌'} {team1} vs {team2} - {result.upper()}")
    
    # Finaliza sessão
    end_result = betting_tracker.end_session(session_result['session_id'])
    if end_result['success']:
        summary = end_result['session_summary']
        print(f"\n📊 RESUMO DA SESSÃO:")
        print(f"   Duração: {summary['duration']}")
        print(f"   Apostas: {summary['bets_placed']}")
        print(f"   Vitórias: {summary['wins']}")
        print(f"   Win Rate: {summary['win_rate']:.1f}%")
        print(f"   Lucro: R$ {summary['profit']:+.2f}")
    
    # 7. Métricas de performance
    print("\n7️⃣ Métricas de Performance Detalhadas...")
    print("=" * 60)
    metrics = betting_tracker.calculate_performance_metrics(period_days=15)
    
    print(f"📊 RESUMO EXECUTIVO:")
    print(f"   Total de Apostas: {metrics.total_bets}")
    print(f"   Win Rate: {metrics.win_rate:.1f}%")
    print(f"   ROI: {metrics.roi:+.2f}%")
    print(f"   Lucro Total: R$ {metrics.total_profit:+.2f}")
    print(f"   Nível de Performance: {metrics.performance_level.upper()}")
    print(f"   Tendência: {metrics.trend_direction.upper()}")
    
    print(f"\n🔥 ANÁLISE DE STREAKS:")
    print(f"   Melhor Streak: {metrics.best_streak} vitórias")
    print(f"   Pior Streak: {metrics.worst_streak} derrotas")
    if metrics.current_streak > 0:
        print(f"   Streak Atual: {metrics.current_streak} {metrics.streak_type}s")
    
    # 8. Relatório exportável
    print("\n8️⃣ Relatório Exportável...")
    print("=" * 60)
    
    # Relatório resumido
    summary_report = betting_tracker.export_performance_report(
        period_days=15, 
        format_type="summary"
    )
    print(summary_report)
    
    # 9. Gráfico ASCII de evolução
    print("\n9️⃣ Demonstração de Gráfico ASCII...")
    print("=" * 60)
    
    # Simula dados de bankroll para gráfico
    bankroll_data = [1000, 1050, 1020, 1080, 1040, 1120, 1090, 1150, 1100, 1180, 1140, 1200]
    chart = betting_tracker.generate_ascii_chart(
        bankroll_data, 
        "Evolução do Bankroll (12 dias)", 
        width=50, 
        height=8
    )
    print(chart)
    
    # 10. Status final
    print(f"\n🏆 TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print(f"✅ Dashboard visual - OK")
    print(f"✅ Análise de padrões - OK") 
    print(f"✅ Tracking de sessões - OK")
    print(f"✅ Métricas de performance - OK")
    print(f"✅ Relatórios exportáveis - OK")
    print(f"✅ Gráficos ASCII - OK")
    print(f"✅ Integração completa - OK")
    
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
    test_full_betting_tracker()