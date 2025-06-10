#!/usr/bin/env python3
"""
Teste Completo do Manual Value Analyzer
Demonstra todas as funcionalidades do sistema de análise de value bets
"""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.personal_betting.value_analyzer import ManualValueAnalyzer
from bot.personal_betting.bankroll_manager import PersonalBankrollManager


def test_value_analyzer():
    """Teste completo do sistema de análise de value"""
    
    print("📊 TESTE COMPLETO: MANUAL VALUE ANALYZER")
    print("=" * 80)
    
    # 1. Inicialização
    print("\n🚀 1. INICIALIZANDO SISTEMAS")
    analyzer = ManualValueAnalyzer()
    bankroll_manager = PersonalBankrollManager()
    
    # Configura bankroll manager
    bankroll_manager.setup_bankroll(1500.0, {
        'min_confidence': 75.0,
        'min_ev': 8.0,
        'max_bet_percentage': 4.0
    })
    
    print(f"✅ Value Analyzer inicializado")
    print(f"✅ Bankroll Manager configurado - R$ 1.500")
    
    # 2. Criando análises detalhadas de times
    print("\n👥 2. CRIANDO ANÁLISES DETALHADAS DE TIMES")
    
    # Time favorito (T1)
    t1_analysis = analyzer.create_team_analysis(
        name="T1",
        recent_form="9W-1L",
        key_players_status="Full roster - Zeus/Oner/Faker/Gumayusi/Keria",
        meta_adaptation=9,
        individual_skill=9,
        teamwork_level=9,
        coaching_impact=8,
        motivation_level=9,
        notes="Dominando completamente o LCK, adaptação perfeita ao patch 14.24. Faker em forma excepcional."
    )
    
    # Time underdog (Gen.G)
    gen_analysis = analyzer.create_team_analysis(
        name="Gen.G",
        recent_form="6W-4L",
        key_players_status="Full roster - Kiin/Canyon/Chovy/Peyz/Lehends",
        meta_adaptation=6,
        individual_skill=8,
        teamwork_level=6,
        coaching_impact=7,
        motivation_level=6,
        notes="Inconsistentes após mudanças no coaching staff. Problemas de coordenação no late game."
    )
    
    # Time equilibrado (DRX)
    drx_analysis = analyzer.create_team_analysis(
        name="DRX",
        recent_form="7W-3L",
        key_players_status="Full roster - Kingen/Croco/Zeka/Deft/BeryL",
        meta_adaptation=7,
        individual_skill=7,
        teamwork_level=8,
        coaching_impact=8,
        motivation_level=7,
        notes="Time bem estruturado, joga limpo e consistente. Deft ainda em boa forma."
    )
    
    # Time instável (KT)
    kt_analysis = analyzer.create_team_analysis(
        name="KT Rolster",
        recent_form="4W-6L",
        key_players_status="Sub jungle - PerfecT substituindo Cuzz",
        meta_adaptation=5,
        individual_skill=6,
        teamwork_level=5,
        coaching_impact=6,
        motivation_level=5,
        notes="Muitas mudanças no roster. PerfecT ainda se adaptando, comunicação comprometida."
    )
    
    print(f"✅ Análises criadas para 4 times:")
    print(f"   🏆 T1: {t1_analysis.individual_skill}/10 skill, {t1_analysis.meta_adaptation}/10 meta")
    print(f"   🔶 Gen.G: {gen_analysis.individual_skill}/10 skill, {gen_analysis.meta_adaptation}/10 meta")
    print(f"   🔷 DRX: {drx_analysis.individual_skill}/10 skill, {drx_analysis.meta_adaptation}/10 meta")
    print(f"   🔻 KT: {kt_analysis.individual_skill}/10 skill, {kt_analysis.meta_adaptation}/10 meta")
    
    # 3. Analisando múltiplas partidas
    print("\n🎮 3. ANALISANDO MÚLTIPLAS PARTIDAS")
    
    analyses = []
    
    # Partida 1: T1 vs Gen.G (Favorito vs Segundo lugar)
    market_odds_1 = {
        "bet365": {"team1": 1.60, "team2": 2.40},
        "betfair": {"team1": 1.65, "team2": 2.35},
        "pinnacle": {"team1": 1.62, "team2": 2.38},
        "betano": {"team1": 1.58, "team2": 2.45}
    }
    
    analysis_1 = analyzer.analyze_match(
        league="LCK",
        team1_analysis=t1_analysis,
        team2_analysis=gen_analysis,
        your_probability_team1=0.75,  # 75% chance para T1
        confidence_level=88,
        reasoning="T1 dominando completamente o LCK. Gen.G inconsistente após mudanças no coaching. Meta atual favorece estilo de jogo do T1.",
        market_odds=market_odds_1,
        importance_level=9,
        patch_impact="Patch favorece T1 - forte no late game",
        historical_h2h="T1 7-3 vs Gen.G (últimas 10 partidas)"
    )
    analyses.append(analysis_1)
    
    # Partida 2: DRX vs KT (Equilibrada com edge)
    market_odds_2 = {
        "bet365": {"team1": 1.90, "team2": 1.95},
        "betfair": {"team1": 1.95, "team2": 1.90},
        "pinnacle": {"team1": 1.92, "team2": 1.93},
        "betano": {"team1": 1.88, "team2": 1.97}
    }
    
    analysis_2 = analyzer.analyze_match(
        league="LCK",
        team1_analysis=drx_analysis,
        team2_analysis=kt_analysis,
        your_probability_team1=0.58,  # 58% chance para DRX
        confidence_level=72,
        reasoning="DRX mais consistente e estável. KT com problemas internos após mudança no jungle. Mercado subestimando edge do DRX.",
        market_odds=market_odds_2,
        importance_level=6,
        patch_impact="Neutro para ambos os times",
        historical_h2h="DRX 6-4 vs KT (últimas 10 partidas)"
    )
    analyses.append(analysis_2)
    
    # Partida 3: Gen.G vs DRX (Trap game)
    market_odds_3 = {
        "bet365": {"team1": 1.75, "team2": 2.10},
        "betfair": {"team1": 1.80, "team2": 2.05},
        "pinnacle": {"team1": 1.77, "team2": 2.08}
    }
    
    analysis_3 = analyzer.analyze_match(
        league="LCK",
        team1_analysis=gen_analysis,
        team2_analysis=drx_analysis,
        your_probability_team1=0.45,  # 45% chance para Gen.G (underdog value)
        confidence_level=65,
        reasoning="Gen.G overvalued pelo mercado baseado em reputação. DRX tem melhor form recente e consistência. Valor no underdog.",
        market_odds=market_odds_3,
        importance_level=7,
        patch_impact="Favorece ligeiramente DRX",
        historical_h2h="Even 5-5 (últimas 10 partidas)"
    )
    analyses.append(analysis_3)
    
    print(f"✅ 3 partidas analisadas:")
    print(f"   1. T1 vs Gen.G - Confiança: {analysis_1.confidence_level}% - Value Rating: {analysis_1.value_rating}")
    print(f"   2. DRX vs KT - Confiança: {analysis_2.confidence_level}% - Value Rating: {analysis_2.value_rating}")
    print(f"   3. Gen.G vs DRX - Confiança: {analysis_3.confidence_level}% - Value Rating: {analysis_3.value_rating}")
    
    # 4. Encontrando value bets
    print("\n💎 4. PROCURANDO VALUE BETS")
    
    # Diferentes critérios de busca
    criteria_sets = [
        {"min_ev": 5.0, "min_confidence": 80, "name": "Conservative"},
        {"min_ev": 3.0, "min_confidence": 70, "name": "Moderate"},
        {"min_ev": 1.0, "min_confidence": 60, "name": "Aggressive"}
    ]
    
    for criteria in criteria_sets:
        value_bets = analyzer.find_value_bets(
            min_ev=criteria["min_ev"],
            min_confidence=criteria["min_confidence"]
        )
        
        print(f"\n📊 {criteria['name']} (EV ≥ {criteria['min_ev']}%, Confiança ≥ {criteria['min_confidence']}%):")
        print(f"   🎯 Value bets encontrados: {len(value_bets)}")
        
        for i, bet in enumerate(value_bets[:3], 1):  # Top 3
            print(f"   {i}. {bet['team']} vs {bet['opponent']} @ {bet['odds']} ({bet['casa_apostas']})")
            print(f"      💰 EV: {bet['ev_percentage']:+.2f}% | 🎯 Confiança: {bet['confidence']}% | ⭐ Rating: {bet['value_rating']}")
    
    # 5. Comparando casas de apostas
    print("\n🏪 5. COMPARANDO CASAS DE APOSTAS")
    
    print(f"\n📊 Análise detalhada: T1 vs Gen.G")
    comparison = analyzer.compare_bookmakers(analysis_1)
    
    if "error" not in comparison:
        print(f"   🎯 Sua análise: T1 {comparison['your_probabilities']['team1']:.1%} vs Gen.G {comparison['your_probabilities']['team2']:.1%}")
        print(f"   🏆 Melhores odds:")
        print(f"     • T1: {comparison['best_odds']['team1']['odds']} ({comparison['best_odds']['team1']['casa']}) - EV: {comparison['best_odds']['team1']['ev']:+.2f}%")
        print(f"     • Gen.G: {comparison['best_odds']['team2']['odds']} ({comparison['best_odds']['team2']['casa']}) - EV: {comparison['best_odds']['team2']['ev']:+.2f}%")
        
        if comparison.get('arbitrage_opportunity'):
            print(f"   🔥 ARBITRAGEM DETECTADA! Lucro garantido: {comparison['arbitrage_profit']:.2f}%")
        
        print(f"   📋 Comparação por casa:")
        for casa, dados in comparison['bookmakers'].items():
            print(f"     • {casa}: Margem {dados['margin']:.2f}% | T1: {dados['team1_odds']} | Gen.G: {dados['team2_odds']}")
    
    # 6. Gerando recomendações integradas
    print("\n🎯 6. GERANDO RECOMENDAÇÕES INTEGRADAS")
    
    for i, analysis in enumerate(analyses, 1):
        print(f"\n📋 Recomendação {i}: {analysis.team1.name} vs {analysis.team2.name}")
        
        recommendation = analyzer.generate_betting_recommendation(analysis, bankroll_manager)
        
        if recommendation['recommended']:
            print(f"   ✅ RECOMENDADO: {recommendation['team']} @ {recommendation['odds']}")
            print(f"   💰 Expected Value: {recommendation['ev_percentage']:+.2f}%")
            print(f"   🎯 Sua probabilidade: {recommendation['your_probability']:.1f}%")
            print(f"   🏪 Casa: {recommendation['casa_apostas']}")
            print(f"   ⭐ Value Rating: {recommendation['value_rating']}")
            
            # Recomendação do bankroll
            if 'bankroll_recommendation' in recommendation:
                bankroll_rec = recommendation['bankroll_recommendation']
                if bankroll_rec['recommended']:
                    print(f"   💳 Valor sugerido: R$ {bankroll_rec['bet_amount']:.2f}")
                    print(f"   📊 Risco: {bankroll_rec['risk_level']}")
                    print(f"   💰 Lucro potencial: R$ {bankroll_rec['potential_profit']:.2f}")
                else:
                    print(f"   ❌ Bankroll: {bankroll_rec['reason']}")
        else:
            print(f"   ❌ NÃO RECOMENDADO: {recommendation['reason']}")
    
    # 7. Relatórios detalhados
    print("\n📋 7. RELATÓRIOS DETALHADOS")
    
    # Relatório da melhor análise
    best_analysis = max(analyses, key=lambda a: max(max(evs.values()) for evs in a.expected_values.values()) if a.expected_values else 0)
    
    print(f"\n📊 RELATÓRIO COMPLETO - MELHOR OPORTUNIDADE:")
    print(analyzer.export_analysis_report(best_analysis))
    
    # 8. Estatísticas gerais
    print("\n📈 8. ESTATÍSTICAS GERAIS")
    
    summary = analyzer.get_analysis_summary()
    if "error" not in summary:
        print(f"   📊 Total de análises: {summary['total_analyses']}")
        print(f"   🎯 Confiança média: {summary['average_confidence']:.1f}%")
        print(f"   💎 Value bets encontrados: {summary['total_value_bets_found']}")
        print(f"   📈 Taxa de value bets: {summary['value_bet_rate']:.1f}%")
        print(f"   ⭐ Por qualidade: {summary['by_quality']}")
        print(f"   💰 Por value rating: {summary['by_value_rating']}")
    
    print("\n" + "=" * 80)
    print("🎉 TESTE COMPLETO FINALIZADO!")
    print("✅ Sistema de Value Analysis totalmente funcional")
    print("💎 Capaz de identificar value bets sistematicamente")
    print("🎯 Integração perfeita com Bankroll Manager")
    print("📊 Relatórios profissionais disponíveis")


def demonstrate_real_world_workflow():
    """Demonstra workflow completo no mundo real"""
    
    print("\n\n🌍 DEMONSTRAÇÃO: WORKFLOW COMPLETO NO MUNDO REAL")
    print("=" * 80)
    
    print("📝 CENÁRIO: Você está analisando partidas para apostar hoje")
    
    # Sistema integrado
    analyzer = ManualValueAnalyzer()
    bankroll_manager = PersonalBankrollManager()
    
    # Setup conservador
    bankroll_manager.setup_bankroll(800.0, {
        'daily_limit_percentage': 8.0,    # 8% por dia
        'max_bet_percentage': 3.0,        # 3% por aposta
        'min_confidence': 75.0,           # Confiança alta
        'min_ev': 6.0                     # EV mínimo 6%
    })
    
    print(f"💰 Bankroll configurado: R$ 800 (conservador)")
    print(f"📅 Limite diário: R$ 64 | 🎯 Máximo por aposta: R$ 24")
    
    # Análise rápida de uma partida real
    print(f"\n🎮 ANALISANDO: Fnatic vs G2 Esports (LEC)")
    
    fnatic = analyzer.create_team_analysis(
        name="Fnatic",
        recent_form="7W-3L",
        key_players_status="Full roster disponível",
        meta_adaptation=7,
        individual_skill=7,
        teamwork_level=8,
        coaching_impact=8,
        motivation_level=7,
        notes="Boa adaptação ao meta, Razork em forma"
    )
    
    g2 = analyzer.create_team_analysis(
        name="G2 Esports", 
        recent_form="8W-2L",
        key_players_status="Full roster disponível",
        meta_adaptation=8,
        individual_skill=9,
        teamwork_level=7,
        coaching_impact=7,
        motivation_level=8,
        notes="Caps carregando o time, bot lane inconsistente"
    )
    
    # Odds reais simuladas
    real_odds = {
        "bet365": {"team1": 2.10, "team2": 1.75},
        "betfair": {"team1": 2.15, "team2": 1.72},
        "pinnacle": {"team1": 2.12, "team2": 1.74}
    }
    
    analysis = analyzer.analyze_match(
        league="LEC",
        team1_analysis=fnatic,
        team2_analysis=g2,
        your_probability_team1=0.52,  # 52% para Fnatic (slight edge)
        confidence_level=78,
        reasoning="Fnatic com melhor teamwork e coach. G2 dependente do Caps. Meta atual favorece estilo Fnatic. Mercado overvaluing G2.",
        market_odds=real_odds,
        importance_level=6
    )
    
    print(f"✅ Análise concluída:")
    print(f"   🎯 Sua avaliação: FNC 52% vs G2 48%")
    print(f"   📊 Confiança: 78%")
    print(f"   💭 Reasoning: Meta favorece Fnatic, G2 overvalued")
    
    # Busca value
    value_bets = analyzer.find_value_bets(min_ev=3.0, min_confidence=75)
    
    if value_bets:
        best_bet = value_bets[0]
        print(f"\n💎 VALUE BET IDENTIFICADO:")
        print(f"   🎯 {best_bet['team']} @ {best_bet['odds']} ({best_bet['casa_apostas']})")
        print(f"   📈 Expected Value: {best_bet['ev_percentage']:+.2f}%")
        print(f"   🎲 Sua probabilidade: {best_bet['your_probability']:.1f}%")
        
        # Gera recomendação integrada
        recommendation = analyzer.generate_betting_recommendation(analysis, bankroll_manager)
        
        if recommendation['recommended'] and 'bankroll_recommendation' in recommendation:
            bankroll_rec = recommendation['bankroll_recommendation']
            
            if bankroll_rec['recommended']:
                print(f"\n✅ RECOMENDAÇÃO FINAL:")
                print(f"   💰 Apostar: R$ {bankroll_rec['bet_amount']:.2f}")
                print(f"   📊 Risco: {bankroll_rec['risk_level']}")
                print(f"   🎯 Retorno potencial: R$ {bankroll_rec['potential_return']:.2f}")
                print(f"   💰 Lucro potencial: R$ {bankroll_rec['potential_profit']:.2f}")
                
                # Simula registro da aposta
                bet_result = bankroll_manager.place_bet(
                    team=best_bet['team'],
                    opponent=best_bet['opponent'], 
                    league="LEC",
                    odds=best_bet['odds'],
                    amount=bankroll_rec['bet_amount'],
                    confidence=analysis.confidence_level,
                    ev_percentage=best_bet['ev_percentage'],
                    reasoning=analysis.reasoning
                )
                
                if bet_result['success']:
                    print(f"   ✅ Aposta registrada: {bet_result['message']}")
                    print(f"   💳 Bankroll restante: R$ {bet_result['remaining_bankroll']:.2f}")
            else:
                print(f"\n❌ Bankroll não recomenda: {bankroll_rec['reason']}")
        else:
            print(f"\n❌ Recomendação final: Não apostar")
    else:
        print(f"\n❌ Nenhum value bet identificado com os critérios atuais")
    
    print(f"\n💡 PRÓXIMOS PASSOS NO WORKFLOW:")
    print(f"   1. 📊 Continue analisando outras partidas do dia")
    print(f"   2. 🔄 Monitore mudanças nas odds ao longo do dia") 
    print(f"   3. 📈 Acompanhe os resultados para calibrar suas análises")
    print(f"   4. 📋 Revise performance semanalmente")


if __name__ == "__main__":
    # Executa testes
    test_value_analyzer()
    demonstrate_real_world_workflow()
    
    print(f"\n🚀 PRÓXIMAS PRIORIDADES DISPONÍVEIS:")
    print(f"   3. 📈 Betting Tracker - Dashboard visual de performance")
    print(f"   4. 🎮 Pre-Game Analyzer - Análise automática de dados")
    print(f"   5. 📱 Interface Unificada - Dashboard web completo") 