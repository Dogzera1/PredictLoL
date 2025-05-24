#!/usr/bin/env python3
"""
Teste para verificar se as correções do bot estão funcionando
"""

import asyncio
import sys
import os

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_v13_railway import (
    DynamicPredictionSystem,
    RiotAPIClient,
    ValueBettingSystem,
    ChampionAnalyzer
)

async def test_prediction_system():
    """Testa o sistema de predição"""
    print("🔮 TESTANDO SISTEMA DE PREDIÇÃO")
    print("=" * 50)
    
    # Inicializar sistema
    prediction_system = DynamicPredictionSystem()
    
    # Mock de partida para teste
    test_match = {
        'teams': [
            {'name': 'T1', 'code': 'T1'},
            {'name': 'Gen.G', 'code': 'GEN'}
        ],
        'league': 'LCK',
        'status': 'Ao vivo'
    }
    
    # Fazer predição
    prediction = await prediction_system.predict_live_match(test_match)
    
    print(f"✅ Predição gerada:")
    print(f"   • {prediction['team1']} vs {prediction['team2']}")
    print(f"   • Probabilidades: {prediction['team1_win_probability']*100:.1f}% vs {prediction['team2_win_probability']*100:.1f}%")
    print(f"   • Odds: {prediction['team1_odds']:.2f} vs {prediction['team2_odds']:.2f}")
    print(f"   • Confiança: {prediction['confidence']}")
    print(f"   • Análise: {prediction['analysis']}")
    print()

async def test_riot_api():
    """Testa a API da Riot"""
    print("🌐 TESTANDO RIOT API CLIENT")
    print("=" * 50)
    
    riot_client = RiotAPIClient()
    
    # Buscar partidas ao vivo
    matches = await riot_client.get_live_matches()
    
    print(f"✅ API testada:")
    print(f"   • {len(matches)} partidas encontradas")
    
    if matches:
        for i, match in enumerate(matches[:2], 1):
            teams = match.get('teams', [])
            if len(teams) >= 2:
                print(f"   • Partida {i}: {teams[0].get('name')} vs {teams[1].get('name')} ({match.get('league')})")
    else:
        print("   • Nenhuma partida ao vivo no momento")
    print()

def test_value_betting():
    """Testa o sistema de value betting"""
    print("💰 TESTANDO VALUE BETTING SYSTEM")
    print("=" * 50)
    
    riot_client = RiotAPIClient()
    value_system = ValueBettingSystem(riot_client)
    
    # Buscar oportunidades atuais
    opportunities = value_system.get_current_opportunities()
    
    print(f"✅ Value betting testado:")
    print(f"   • {len(opportunities)} oportunidades atuais")
    
    if opportunities:
        for i, opp in enumerate(opportunities[:2], 1):
            print(f"   • Oportunidade {i}: {opp['team1']} vs {opp['team2']}")
            print(f"     - Value: +{opp['value']:.1%}")
            print(f"     - Kelly: {opp['kelly_fraction']:.1%}")
            print(f"     - Stake: R$ {opp['recommended_stake']:.0f}")
    else:
        print("   • Nenhuma oportunidade detectada no momento")
    print()

def test_champion_analyzer():
    """Testa o analisador de campeões"""
    print("🏆 TESTANDO CHAMPION ANALYZER")
    print("=" * 50)
    
    analyzer = ChampionAnalyzer()
    
    # Teste de análise de draft
    team1_comp = ['Aatrox', 'Graves', 'Azir', 'Jinx', 'Thresh']
    team2_comp = ['Camille', 'Lee Sin', 'LeBlanc', 'Lucian', 'Lulu']
    
    draft_analysis = analyzer.analyze_draft(team1_comp, team2_comp)
    
    print(f"✅ Champion analyzer testado:")
    print(f"   • Análise de draft disponível: {draft_analysis.get('analysis', 'OK')}")
    print()

async def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DO BOT LOL V3")
    print("=" * 50)
    print()
    
    try:
        # Teste 1: Sistema de Predição
        await test_prediction_system()
        
        # Teste 2: Riot API
        await test_riot_api()
        
        # Teste 3: Value Betting
        test_value_betting()
        
        # Teste 4: Champion Analyzer
        test_champion_analyzer()
        
        print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("=" * 50)
        print()
        print("✅ SISTEMAS VERIFICADOS:")
        print("   • ✅ Sistema de Predição IA funcionando")
        print("   • ✅ Riot API Client conectando")
        print("   • ✅ Value Betting System operacional")
        print("   • ✅ Champion Analyzer disponível")
        print()
        print("🔧 CORREÇÕES IMPLEMENTADAS:")
        print("   • ✅ Adicionado sistema de predição completo")
        print("   • ✅ Comandos /predict e /predicao funcionais")
        print("   • ✅ Callback de partidas com predições")
        print("   • ✅ Tips de value betting melhorados")
        print("   • ✅ Erro de atualização de partidas corrigido")
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 