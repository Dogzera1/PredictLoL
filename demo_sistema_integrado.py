#!/usr/bin/env python3
"""
Demonstração do Sistema Integrado
Bankroll Manager + Value Analyzer
"""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.personal_betting import PersonalBankrollManager, ManualValueAnalyzer


def main_demo():
    """Demonstração completa do sistema integrado"""
    
    print("🚀 SISTEMA INTEGRADO DE APOSTAS PESSOAIS")
    print("=" * 60)
    print("💰 Bankroll Manager + 📊 Value Analyzer")
    
    # Inicializa sistemas
    print("\n🔧 INICIALIZANDO SISTEMAS...")
    bankroll_manager = PersonalBankrollManager()
    value_analyzer = ManualValueAnalyzer()
    
    # Configuração inicial
    bankroll_manager.setup_bankroll(1000.0, {
        'daily_limit_percentage': 10.0,
        'max_bet_percentage': 4.0,
        'min_confidence': 75.0,
        'min_ev': 6.0,
        'kelly_multiplier': 0.30
    })
    
    print("✅ Sistemas inicializados e configurados")
    print(f"   💰 Bankroll: R$ 1.000")
    print(f"   📊 Limite diário: R$ 100")
    print(f"   🎯 Máximo por aposta: R$ 40")
    
    # Análise de uma partida
    print("\n🎮 ANALISANDO PARTIDA: T1 vs DAMWON")
    
    # Cria análises dos times
    t1 = value_analyzer.create_team_analysis(
        name="T1",
        recent_form="8W-1L",
        key_players_status="Full roster",
        meta_adaptation=9,
        individual_skill=9,
        teamwork_level=8,
        coaching_impact=8,
        motivation_level=9,
        notes="Em excelente forma, dominando o LCK"
    )
    
    damwon = value_analyzer.create_team_analysis(
        name="DAMWON KIA",
        recent_form="6W-3L", 
        key_players_status="Full roster",
        meta_adaptation=7,
        individual_skill=8,
        teamwork_level=7,
        coaching_impact=7,
        motivation_level=7,
        notes="Inconsistente após roster changes"
    )
    
    # Odds simuladas
    market_odds = {
        "bet365": {"team1": 1.70, "team2": 2.20},
        "betfair": {"team1": 1.75, "team2": 2.15},
        "pinnacle": {"team1": 1.72, "team2": 2.18}
    }
    
    # Realiza análise
    analysis = value_analyzer.analyze_match(
        league="LCK",
        team1_analysis=t1,
        team2_analysis=damwon,
        your_probability_team1=0.68,  # 68% para T1
        confidence_level=82,
        reasoning="T1 superior em todos os aspectos. Meta atual favorece seu estilo. DAMWON instável.",
        market_odds=market_odds,
        importance_level=8
    )
    
    print(f"✅ Análise concluída:")
    print(f"   🎯 T1: 68% | DAMWON: 32%")
    print(f"   📊 Confiança: 82%")
    print(f"   ⭐ Value Rating: {analysis.value_rating}")
    
    # Busca value bets
    value_bets = value_analyzer.find_value_bets(min_ev=5.0, min_confidence=80)
    
    if value_bets:
        best_bet = value_bets[0]
        print(f"\n💎 VALUE BET IDENTIFICADO:")
        print(f"   🏆 {best_bet['team']} @ {best_bet['odds']} ({best_bet['casa_apostas']})")
        print(f"   📈 EV: {best_bet['ev_percentage']:+.2f}%")
        
        # Gera recomendação integrada
        recommendation = value_analyzer.generate_betting_recommendation(analysis, bankroll_manager)
        
        if recommendation.get('recommended') and 'bankroll_recommendation' in recommendation:
            bankroll_rec = recommendation['bankroll_recommendation']
            
            if bankroll_rec['recommended']:
                print(f"\n🎯 RECOMENDAÇÃO FINAL:")
                print(f"   💰 Valor sugerido: R$ {bankroll_rec['bet_amount']:.2f}")
                print(f"   📊 % do bankroll: {bankroll_rec['percentage_bankroll']:.1f}%")
                print(f"   🎲 Risco: {bankroll_rec['risk_level']}")
                print(f"   💰 Lucro potencial: R$ {bankroll_rec['potential_profit']:.2f}")
                
                # Confirma aposta
                response = input("\n❓ Registrar esta aposta? (s/n): ").lower().strip()
                
                if response == 's':
                    bet_result = bankroll_manager.place_bet(
                        team=best_bet['team'],
                        opponent=best_bet['opponent'],
                        league="LCK", 
                        odds=best_bet['odds'],
                        amount=bankroll_rec['bet_amount'],
                        confidence=analysis.confidence_level,
                        ev_percentage=best_bet['ev_percentage'],
                        reasoning=analysis.reasoning
                    )
                    
                    if bet_result['success']:
                        print(f"✅ APOSTA REGISTRADA!")
                        print(f"   🎫 ID: {bet_result['bet_id']}")
                        print(f"   💳 Bankroll restante: R$ {bet_result['remaining_bankroll']:.2f}")
                        
                        # Simula resultado (para demonstração)
                        print(f"\n⏳ Aguardando resultado da partida...")
                        sim_result = input("🎮 Resultado (w/l): ").lower().strip()
                        
                        if sim_result in ['w', 'l']:
                            won = sim_result == 'w'
                            resolve_result = bankroll_manager.resolve_bet(
                                bet_result['bet_id'], 
                                won=won,
                                notes="Resultado simulado para demo"
                            )
                            
                            if resolve_result['success']:
                                result_emoji = "🏆" if won else "💔"
                                print(f"{result_emoji} RESULTADO: {resolve_result['result']}")
                                print(f"   💰 Lucro/Prejuízo: R$ {resolve_result['profit']:.2f}")
                                print(f"   💳 Novo bankroll: R$ {resolve_result['new_bankroll']:.2f}")
                    else:
                        print(f"❌ Erro: {bet_result['error']}")
                else:
                    print("❌ Aposta não registrada")
            else:
                print(f"\n❌ Bankroll Manager não recomenda:")
                print(f"   📋 Motivo: {bankroll_rec['reason']}")
        else:
            print(f"\n❌ Value Analyzer não recomenda apostar")
    else:
        print(f"\n❌ Nenhum value bet identificado")
    
    # Estatísticas finais
    print(f"\n📊 ESTATÍSTICAS ATUAIS:")
    stats = bankroll_manager.get_performance_stats()
    
    if stats.get('total_bets', 0) > 0:
        print(f"   📈 Total de apostas: {stats['total_bets']}")
        print(f"   🏆 Win rate: {stats['win_rate']:.1f}%")
        print(f"   💰 ROI: {stats['roi']:.2f}%")
        print(f"   📊 Lucro total: R$ {stats['total_profit']:.2f}")
    
    print(f"   💳 Bankroll atual: R$ {bankroll_manager.settings.current_bankroll:.2f}")
    print(f"   📅 Limite restante hoje: R$ {bankroll_manager.get_daily_remaining_limit():.2f}")
    
    # Relatório de value analysis
    print(f"\n📋 RESUMO DE ANÁLISES:")
    analysis_summary = value_analyzer.get_analysis_summary()
    
    if "error" not in analysis_summary:
        print(f"   📊 Total de análises: {analysis_summary['total_analyses']}")
        print(f"   🎯 Confiança média: {analysis_summary['average_confidence']:.1f}%")
        print(f"   💎 Value bets encontrados: {analysis_summary['total_value_bets_found']}")
    
    print(f"\n🎉 DEMONSTRAÇÃO CONCLUÍDA!")
    print(f"✅ Sistema totalmente integrado e funcional")


if __name__ == "__main__":
    main_demo() 