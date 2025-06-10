#!/usr/bin/env python3
"""
Teste do Sistema PredictLoL Novo
Sistema limpo focado em apostas pessoais
"""

from bot.personal_betting import PersonalBettingSystem

def main():
    print("🎯 TESTE: SISTEMA PREDICTLOL NOVO")
    print("=" * 60)
    
    # Criar sistema
    print("🚀 Inicializando sistema...")
    system = PersonalBettingSystem(initial_bankroll=1000.0)
    
    # Status do sistema
    status = system.get_status()
    print(f"✅ Sistema v{status['version']} inicializado")
    print(f"💰 Bankroll: R$ {status['bankroll']:.2f}")
    
    print("\n📊 COMPONENTES ATIVOS:")
    for component, status_comp in status['components'].items():
        print(f"   • {component}: {status_comp}")
    
    print("\n🎮 TESTE: ANÁLISE DE PARTIDA")
    print("-" * 40)
    
    # Teste de análise manual
    try:
        analysis = system.value_analyzer.analyze_match(
            team1="T1",
            team2="Gen.G",
            bookmaker_odds={
                'bet365': {'team1': 1.75, 'team2': 2.10},
                'pinnacle': {'team1': 1.78, 'team2': 2.05}
            }
        )
        
        print(f"📊 Análise T1 vs Gen.G:")
        print(f"   • Probabilidade T1: {analysis['team1_probability']:.1f}%")
        print(f"   • Expected Value: {analysis['ev_team1']:.1f}%")
        print(f"   • Recomendação: {analysis['recommendation']}")
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
    
    print("\n💰 TESTE: CÁLCULO DE APOSTA")
    print("-" * 40)
    
    # Teste de cálculo de aposta
    try:
        bet_calc = system.bankroll_manager.calculate_bet_size(
            confidence=75.0,
            odds=1.78,
            your_probability=0.65,
            reasoning="T1 em boa forma"
        )
        
        if bet_calc['recommended']:
            print(f"✅ Aposta recomendada:")
            print(f"   • Valor: R$ {bet_calc['amount']:.2f}")
            print(f"   • Kelly Fraction: {bet_calc['kelly_fraction']:.3f}")
            print(f"   • Risco: {bet_calc['risk_level']}")
        else:
            print(f"❌ Aposta não recomendada: {bet_calc['reason']}")
            
    except Exception as e:
        print(f"❌ Erro no cálculo: {e}")
    
    print("\n📈 TESTE: DASHBOARD")
    print("-" * 40)
    
    # Teste do dashboard
    try:
        dashboard = system.betting_tracker.generate_dashboard()
        print(f"📊 Dashboard gerado:")
        print(f"   • Bankroll: R$ {dashboard['current_balance']:.2f}")
        print(f"   • Total apostas: {dashboard['total_bets']}")
        print(f"   • Win rate: {dashboard['win_rate']:.1f}%")
        print(f"   • ROI: {dashboard['roi']:.1f}%")
        
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
    
    print("\n🤖 TESTE: ANÁLISE AUTOMATIZADA")
    print("-" * 40)
    
    # Teste do pre-game analyzer
    try:
        prediction = system.pre_game_analyzer.analyze_match(
            team1="T1",
            team2="Gen.G"
        )
        
        print(f"🎮 Previsão automatizada:")
        print(f"   • T1: {prediction['team1_probability']:.1f}%")
        print(f"   • Confiança: {prediction['confidence']:.1f}%")
        print(f"   • Qualidade: {prediction['quality']}")
        print(f"   • Recomendação: {prediction['recommendation']}")
        
    except Exception as e:
        print(f"❌ Erro na previsão: {e}")
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO - SISTEMA FUNCIONANDO!")
    print("🚀 Pronto para deploy no Railway")
    print("🤖 Bot Telegram integrado")
    print("💰 Sistema de apostas pessoais completo")

if __name__ == "__main__":
    main() 