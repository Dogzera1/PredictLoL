#!/usr/bin/env python3
"""
Teste Completo: Pre-Game Analyzer
Sistema de análise automatizada com dados históricos
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.personal_betting.pre_game_analyzer import PreGameAnalyzer, MatchResult
from datetime import datetime, timedelta

def main():
    print("=" * 70)
    print("🤖 TESTE: PRE-GAME ANALYZER")
    print("Sistema de Análise Automatizada com Dados Históricos")
    print("=" * 70)
    
    # 1. Inicializa o analyzer
    print("\n📊 INICIALIZANDO PRE-GAME ANALYZER...")
    analyzer = PreGameAnalyzer()
    
    print(f"✅ Analyzer inicializado com {len(analyzer.team_stats)} times")
    print(f"📈 {len(analyzer.historical_results)} partidas históricas carregadas")
    
    # 2. Demonstra análise de uma partida
    print(f"\n{'='*50}")
    print("🎮 ANALISANDO PARTIDA: T1 vs Gen.G")
    print(f"{'='*50}")
    
    analysis = analyzer.analyze_upcoming_match(
        team1="T1",
        team2="Gen.G",
        league="LCK",
        match_importance="final",
        patch="14.2"
    )
    
    # 3. Gera e exibe relatório completo
    print("\n📋 RELATÓRIO DA ANÁLISE:")
    print("-" * 50)
    report = analyzer.generate_pre_game_report(analysis)
    print(report)
    
    # 4. Testa análise de diferentes cenários
    print(f"\n{'='*50}")
    print("🔄 TESTANDO DIFERENTES CENÁRIOS")
    print(f"{'='*50}")
    
    # Cenário 2: Times equilibrados
    print("\n🎮 Cenário 2: Times Equilibrados (G2 vs FNC)")
    analysis2 = analyzer.analyze_upcoming_match(
        team1="G2",
        team2="FNC",
        league="LEC",
        match_importance="playoffs"
    )
    
    print(f"📊 Resultado: {analysis2.team1} {analysis2.team1_win_probability:.1%} vs {analysis2.team2} {analysis2.team2_win_probability:.1%}")
    print(f"🎯 Confiança: {analysis2.confidence_level:.1%}")
    print(f"⭐ Qualidade: {analysis2.prediction_quality}")
    if analysis2.recommended_bet:
        print(f"✅ Recomendação: {analysis2.recommended_bet}")
    else:
        print("❌ Nenhuma aposta recomendada")
    
    # Cenário 3: Times com histórico
    print("\n🎮 Cenário 3: Times com Head-to-Head (100T vs TL)")
    analysis3 = analyzer.analyze_upcoming_match(
        team1="100T",
        team2="TL",
        league="LCS",
        match_importance="regular"
    )
    
    print(f"📊 Resultado: {analysis3.team1} {analysis3.team1_win_probability:.1%} vs {analysis3.team2} {analysis3.team2_win_probability:.1%}")
    print(f"🎯 Confiança: {analysis3.confidence_level:.1%}")
    print(f"⚔️ H2H: {analysis3.head_to_head.team1_wins}-{analysis3.head_to_head.team2_wins}")
    
    # 5. Adiciona resultado e verifica atualização
    print(f"\n{'='*50}")
    print("📝 ADICIONANDO RESULTADO DE PARTIDA")
    print(f"{'='*50}")
    
    # Adiciona resultado da partida T1 vs Gen.G
    new_result = MatchResult(
        date=datetime.now().isoformat(),
        team1="T1",
        team2="Gen.G",
        winner="T1",
        duration_minutes=28,
        patch="14.2",
        league="LCK",
        importance="final",
        team1_kills=18,
        team2_kills=11,
        team1_towers=11,
        team2_towers=2
    )
    
    analyzer.add_match_result(new_result)
    print(f"✅ Resultado adicionado: T1 venceu Gen.G")
    
    # 6. Testa resumo de análise de time
    print(f"\n{'='*50}")
    print("📈 RESUMO DE ANÁLISE DE TIME")
    print(f"{'='*50}")
    
    team_summary = analyzer.get_team_analysis_summary("T1", days=30)
    
    print(f"\n🏆 RESUMO: {team_summary['team']}")
    print(f"📊 Record geral: {team_summary['overall_stats']['record']}")
    print(f"📈 Win rate: {team_summary['overall_stats']['win_rate']:.1%}")
    print(f"🔥 Form recente: {' '.join(team_summary['overall_stats']['recent_form'])}")
    print(f"📋 Tendência: {team_summary['overall_stats']['form_trend'].title()}")
    
    print(f"\n💪 PONTOS FORTES:")
    for strength in team_summary['strengths']:
        print(f"   ✅ {strength}")
    
    if team_summary['weaknesses']:
        print(f"\n⚠️ PONTOS FRACOS:")
        for weakness in team_summary['weaknesses']:
            print(f"   ❌ {weakness}")
    
    print(f"\n🎮 ESTILO DE JOGO:")
    style = team_summary['game_style']
    print(f"   Early Game: {style['early_game']:.1%}")
    print(f"   Late Game: {style['late_game']:.1%}")
    print(f"   Teamfight: {style['teamfight']:.1%}")
    print(f"   Macro: {style['macro']:.1%}")
    
    # 7. Demonstra integração com outros sistemas
    print(f"\n{'='*50}")
    print("🔗 INTEGRAÇÃO COM OUTROS SISTEMAS")
    print(f"{'='*50}")
    
    # Simula integração com bankroll manager
    try:
        from bot.personal_betting.bankroll_manager import create_default_bankroll_manager
        
        bankroll_manager = create_default_bankroll_manager()
        analyzer_integrated = PreGameAnalyzer(bankroll_manager=bankroll_manager)
        
        print("✅ Integração com Bankroll Manager: OK")
        
        # Testa análise com recomendação de aposta
        analysis_integrated = analyzer_integrated.analyze_upcoming_match(
            team1="JDG",
            team2="BLG",
            league="LPL",
            match_importance="playoffs"
        )
        
        if analysis_integrated.recommended_bet:
            print(f"🎯 Análise integrada recomenda: {analysis_integrated.recommended_bet}")
            print(f"💰 Probabilidade: {analysis_integrated.team1_win_probability:.1%} vs {analysis_integrated.team2_win_probability:.1%}")
            
            # Simula cálculo de aposta recomendada
            if analysis_integrated.recommended_bet == "JDG":
                prob = analysis_integrated.team1_win_probability
            else:
                prob = analysis_integrated.team2_win_probability
            
            # Odds simuladas para demonstração
            odds = 1.85
            kelly_fraction = bankroll_manager._calculate_kelly_criterion(prob, odds)
            recommended_amount = bankroll_manager.bankroll * kelly_fraction
            
            print(f"💵 Valor sugerido (Kelly): R$ {recommended_amount:.2f}")
            
    except ImportError:
        print("⚠️ Bankroll Manager não disponível para integração")
    
    # 8. Estatísticas finais
    print(f"\n{'='*50}")
    print("📊 ESTATÍSTICAS FINAIS")
    print(f"{'='*50}")
    
    print(f"📈 Total de análises realizadas: {len(analyzer.analyses)}")
    print(f"🏆 Times na base de dados: {len(analyzer.team_stats)}")
    print(f"📋 Partidas históricas: {len(analyzer.historical_results)}")
    
    # Análises por qualidade
    quality_counts = {}
    for analysis in analyzer.analyses:
        quality = analysis.prediction_quality
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
    
    print(f"\n🎯 QUALIDADE DAS ANÁLISES:")
    for quality, count in quality_counts.items():
        print(f"   {quality.title()}: {count}")
    
    # Recomendações
    recommended_count = sum(1 for a in analyzer.analyses if a.recommended_bet)
    print(f"\n✅ Apostas recomendadas: {recommended_count}/{len(analyzer.analyses)}")
    
    print(f"\n{'='*70}")
    print("✅ TESTE DO PRE-GAME ANALYZER CONCLUÍDO COM SUCESSO!")
    print("🚀 Sistema pronto para análises automatizadas de LoL")
    print("=" * 70)

if __name__ == "__main__":
    main() 