#!/usr/bin/env python3
"""
Teste para o Analisador de Composições

Testa as funcionalidades básicas do sistema de análise de composições:
- Análise de força individual
- Cálculo de sinergias
- Análise de matchups
- Flexibilidade estratégica
"""

import asyncio
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.analyzers.composition_analyzer import CompositionAnalyzer
from bot.utils.logger_config import setup_logging

# Configuração de logging
logger = setup_logging(log_level="INFO", log_file=None)

async def test_composition_analyzer():
    """Teste principal do analisador de composições"""
    
    print("🎮 TESTE DO ANALISADOR DE COMPOSIÇÕES")
    print("=" * 50)
    
    # Inicializa o analisador
    analyzer = CompositionAnalyzer()
    
    # Aguarda inicialização das databases
    await asyncio.sleep(2)
    
    # Dados de teste - Composição T1 vs Gen.G
    team_t1_picks = [
        {"champion": "Gnar", "position": "top", "pick_order": 1},
        {"champion": "Graves", "position": "jungle", "pick_order": 2},
        {"champion": "Azir", "position": "mid", "pick_order": 3},
        {"champion": "Jinx", "position": "adc", "pick_order": 4},
        {"champion": "Thresh", "position": "support", "pick_order": 5}
    ]
    
    team_geng_picks = [
        {"champion": "Jayce", "position": "top", "pick_order": 1},
        {"champion": "Kindred", "position": "jungle", "pick_order": 2},
        {"champion": "Viktor", "position": "mid", "pick_order": 3},
        {"champion": "Aphelios", "position": "adc", "pick_order": 4},
        {"champion": "Leona", "position": "support", "pick_order": 5}
    ]
    
    print("🔵 T1 COMPOSIÇÃO:")
    for pick in team_t1_picks:
        print(f"  • {pick['position'].upper()}: {pick['champion']}")
    
    print("\n🔴 GEN.G COMPOSIÇÃO:")
    for pick in team_geng_picks:
        print(f"  • {pick['position'].upper()}: {pick['champion']}")
    
    print("\n📊 ANALISANDO COMPOSIÇÕES...")
    
    # Testa análise da composição T1
    t1_analysis = await analyzer.analyze_team_composition(
        team_picks=team_t1_picks,
        enemy_picks=team_geng_picks,
        patch_version="14.10"
    )
    
    # Testa análise da composição Gen.G
    geng_analysis = await analyzer.analyze_team_composition(
        team_picks=team_geng_picks,
        enemy_picks=team_t1_picks,
        patch_version="14.10"
    )
    
    # Exibe resultados
    print("\n" + "="*50)
    print("📊 RESULTADOS DA ANÁLISE:")
    print("="*50)
    
    print(f"\n🔵 T1 ANÁLISE:")
    print(f"  📈 Score Geral: {t1_analysis['overall_score']}/10")
    print(f"  ⚡ Força Individual: {t1_analysis['individual_strength']}/10")
    print(f"  🤝 Sinergias: {t1_analysis['team_synergies']}/10")
    print(f"  ⚔️ Matchups: {t1_analysis['matchup_advantages']}/10")
    print(f"  🎯 Flexibilidade: {t1_analysis['strategic_flexibility']}/10")
    print(f"  📋 Resumo: {t1_analysis['composition_summary']}")
    
    print(f"\n🔴 GEN.G ANÁLISE:")
    print(f"  📈 Score Geral: {geng_analysis['overall_score']}/10")
    print(f"  ⚡ Força Individual: {geng_analysis['individual_strength']}/10")
    print(f"  🤝 Sinergias: {geng_analysis['team_synergies']}/10")
    print(f"  ⚔️ Matchups: {geng_analysis['matchup_advantages']}/10")
    print(f"  🎯 Flexibilidade: {geng_analysis['strategic_flexibility']}/10")
    print(f"  📋 Resumo: {geng_analysis['composition_summary']}")
    
    # Comparação
    t1_score = t1_analysis['overall_score']
    geng_score = geng_analysis['overall_score']
    
    print(f"\n🏆 VANTAGEM DE COMPOSIÇÃO:")
    if t1_score > geng_score:
        advantage = t1_score - geng_score
        print(f"  ✅ T1 tem vantagem: +{advantage:.2f} pontos")
        print(f"  📊 Porcentagem: {((t1_score/geng_score - 1) * 100):.1f}% superior")
    elif geng_score > t1_score:
        advantage = geng_score - t1_score
        print(f"  ✅ Gen.G tem vantagem: +{advantage:.2f} pontos")
        print(f"  📊 Porcentagem: {((geng_score/t1_score - 1) * 100):.1f}% superior")
    else:
        print(f"  ⚖️ Composições equilibradas")
    
    # Testa detalhes da análise
    print(f"\n🔍 ANÁLISE DETALHADA T1:")
    detailed = t1_analysis.get('detailed_analysis', {})
    print(f"  🎮 Tipo: {detailed.get('composition_type', 'N/A')}")
    print(f"  💪 Pontos Fortes: {', '.join(detailed.get('strengths', []))}")
    print(f"  ⚠️ Fraquezas: {', '.join(detailed.get('weaknesses', []))}")
    
    # Força por fase do jogo
    phases = t1_analysis.get('game_phase_strength', {})
    print(f"\n📈 FORÇA POR FASE - T1:")
    print(f"  🌅 Early Game: {phases.get('early', 0)}/10")
    print(f"  🏙️ Mid Game: {phases.get('mid', 0)}/10") 
    print(f"  🌃 Late Game: {phases.get('late', 0)}/10")
    
    phases_geng = geng_analysis.get('game_phase_strength', {})
    print(f"\n📈 FORÇA POR FASE - GEN.G:")
    print(f"  🌅 Early Game: {phases_geng.get('early', 0)}/10")
    print(f"  🏙️ Mid Game: {phases_geng.get('mid', 0)}/10")
    print(f"  🌃 Late Game: {phases_geng.get('late', 0)}/10")
    
    print("\n" + "="*50)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("="*50)
    
    return t1_analysis, geng_analysis

async def test_composition_api_integration():
    """Testa integração com PandaScore API para coleta de composições"""
    
    print("\n🔍 TESTE DE INTEGRAÇÃO API - COMPOSIÇÕES")
    print("=" * 50)
    
    try:
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        
        async with PandaScoreAPIClient() as api:
            print("📡 Buscando partidas ao vivo...")
            
            live_matches = await api.get_lol_live_matches()
            print(f"✅ {len(live_matches)} partidas ao vivo encontradas")
            
            if live_matches:
                # Testa coleta de composição da primeira partida
                match = live_matches[0]
                match_id = match.get("id")
                
                if match_id:
                    print(f"\n🎮 Testando coleta de composição para match {match_id}...")
                    
                    composition_data = await api.get_match_composition_data(match_id)
                    
                    if composition_data:
                        print("✅ Composição coletada com sucesso!")
                        print(f"  📊 Teams: {composition_data['teams']['team_a']['name']} vs {composition_data['teams']['team_b']['name']}")
                        print(f"  🏆 Liga: {composition_data.get('league', 'N/A')}")
                        print(f"  📋 Patch: {composition_data.get('patch', 'N/A')}")
                        
                        # Mostra picks se disponíveis
                        team_a_picks = composition_data['teams']['team_a']['picks']
                        if team_a_picks:
                            print(f"\n🔵 {composition_data['teams']['team_a']['name']} PICKS:")
                            for pick in team_a_picks:
                                print(f"  • {pick.get('position', 'N/A')}: {pick.get('champion', 'N/A')}")
                    else:
                        print("⚠️ Dados de composição não disponíveis para esta partida")
                else:
                    print("⚠️ Match ID não encontrado")
            else:
                print("⚠️ Nenhuma partida ao vivo encontrada")
                
    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")

async def main():
    """Função principal de teste"""
    
    # Teste 1: Analisador de composições
    t1_analysis, geng_analysis = await test_composition_analyzer()
    
    # Teste 2: Integração com API (opcional)
    try:
        await test_composition_api_integration()
    except Exception as e:
        print(f"\n⚠️ Teste de API pulado (normal em desenvolvimento): {e}")
    
    print(f"\n🎉 TODOS OS TESTES CONCLUÍDOS!")
    
    return {
        "t1_score": t1_analysis['overall_score'],
        "geng_score": geng_analysis['overall_score'],
        "winner": "T1" if t1_analysis['overall_score'] > geng_analysis['overall_score'] else "Gen.G"
    }

if __name__ == "__main__":
    results = asyncio.run(main()) 
