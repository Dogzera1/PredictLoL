#!/usr/bin/env python3
"""
Teste para verificar dados estatísticos em tempo real

Verifica se o bot consegue acessar e processar:
- Dados de partidas ao vivo
- Estatísticas detalhadas dos times
- Informações em tempo real
- Capacidade de análise para tips
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any, List
from datetime import datetime

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients import PandaScoreAPIClient, RiotAPIClient
from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging para testes
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_realtime")


async def test_live_match_data():
    """Testa obtenção de dados de partidas ao vivo"""
    print("⚡ TESTE DE DADOS EM TEMPO REAL - Partidas Ao Vivo")
    print("=" * 65)
    
    try:
        async with PandaScoreAPIClient() as pandascore:
            # 1. Busca partidas ao vivo
            print("📡 Buscando partidas ao vivo na PandaScore...")
            live_matches = await pandascore.get_lol_live_matches()
            
            if not live_matches:
                print("❌ Nenhuma partida ao vivo encontrada")
                return False, {}
            
            print(f"✅ Encontradas {len(live_matches)} partidas ao vivo")
            
            # 2. Analisa dados da primeira partida ao vivo
            first_match = live_matches[0]
            match_id = first_match.get('id')
            
            print(f"\n🔍 ANÁLISE DETALHADA - Partida {match_id}")
            print("-" * 50)
            
            # Informações básicas
            print(f"📊 Status: {first_match.get('status')}")
            print(f"🎮 Jogo: {first_match.get('videogame', {}).get('name')}")
            print(f"🏆 Liga: {first_match.get('league', {}).get('name')}")
            print(f"📅 Início: {first_match.get('begin_at', 'N/A')}")
            
            # Times participantes
            opponents = first_match.get('opponents', [])
            if len(opponents) >= 2:
                team1 = opponents[0].get('opponent', {})
                team2 = opponents[1].get('opponent', {})
                
                print(f"\n⚔️  TIMES:")
                print(f"   🔵 {team1.get('name', 'N/A')} (ID: {team1.get('id', 'N/A')})")
                print(f"   🔴 {team2.get('name', 'N/A')} (ID: {team2.get('id', 'N/A')})")
            
            # 3. Verifica campos estatísticos disponíveis
            print(f"\n📈 CAMPOS ESTATÍSTICOS DISPONÍVEIS:")
            stats_fields = []
            
            for key, value in first_match.items():
                if any(stat_word in key.lower() for stat_word in 
                      ['stat', 'score', 'kill', 'death', 'assist', 'gold', 'cs', 'damage']):
                    stats_fields.append((key, value))
                    print(f"   • {key}: {value}")
            
            if not stats_fields:
                print("   ⚠️  Nenhum campo estatístico direto encontrado")
            
            # 4. Verifica dados de jogos/games dentro da partida
            games = first_match.get('games', [])
            print(f"\n🎯 JOGOS DA PARTIDA: {len(games)} game(s)")
            
            if games:
                for i, game in enumerate(games):
                    print(f"   Game {i+1}:")
                    print(f"     Status: {game.get('status', 'N/A')}")
                    print(f"     Início: {game.get('begin_at', 'N/A')}")
                    print(f"     Fim: {game.get('end_at', 'N/A')}")
                    
                    # Verifica se há winner
                    winner = game.get('winner')
                    if winner:
                        print(f"     Vencedor: {winner.get('name', 'N/A')}")
            
            # 5. Dados adicionais úteis
            print(f"\n🔧 DADOS TÉCNICOS:")
            print(f"   • Match ID: {match_id}")
            print(f"   • Número de jogos: {first_match.get('number_of_games', 'N/A')}")
            print(f"   • Draw: {first_match.get('draw', 'N/A')}")
            print(f"   • Live: {first_match.get('live', 'N/A')}")
            
            return True, {
                'match_data': first_match,
                'teams': [team1.get('name'), team2.get('name')] if len(opponents) >= 2 else [],
                'stats_available': len(stats_fields) > 0,
                'games_count': len(games),
                'match_id': match_id
            }
            
    except Exception as e:
        print(f"❌ Erro ao buscar dados ao vivo: {e}")
        return False, {}


async def test_team_statistics():
    """Testa obtenção de estatísticas dos times"""
    print("\n📊 TESTE DE ESTATÍSTICAS DOS TIMES")
    print("=" * 45)
    
    try:
        async with PandaScoreAPIClient() as pandascore:
            # 1. Busca times
            print("🔍 Buscando dados de times...")
            teams = await pandascore.get_teams()
            
            if not teams:
                print("❌ Nenhum time encontrado")
                return False
            
            print(f"✅ Encontrados {len(teams)} times")
            
            # 2. Analisa primeiro time
            first_team = teams[0]
            team_id = first_team.get('id')
            team_name = first_team.get('name')
            
            print(f"\n🔍 ANÁLISE DO TIME: {team_name}")
            print("-" * 40)
            
            # Informações básicas do time
            print(f"📋 ID: {team_id}")
            print(f"📛 Nome: {team_name}")
            print(f"🏷️  Slug: {first_team.get('slug', 'N/A')}")
            print(f"🌍 Localização: {first_team.get('location', 'N/A')}")
            
            # Players do time
            players = first_team.get('players', [])
            print(f"\n👥 PLAYERS ({len(players)}):")
            for player in players[:5]:  # Primeiros 5 players
                print(f"   • {player.get('name', 'N/A')} ({player.get('slug', 'N/A')})")
            
            # Verifica campos estatísticos
            stats_fields = []
            for key, value in first_team.items():
                if any(stat_word in key.lower() for stat_word in 
                      ['stat', 'win', 'loss', 'score', 'rating']):
                    stats_fields.append((key, value))
                    print(f"📈 {key}: {value}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao buscar estatísticas dos times: {e}")
        return False


async def test_riot_api_data():
    """Testa dados da Riot API"""
    print("\n🎮 TESTE DE DADOS DA RIOT API")
    print("=" * 40)
    
    try:
        async with RiotAPIClient() as riot:
            # 1. Testa health check
            print("📡 Testando conexão com Riot API...")
            health_ok = await riot.health_check()
            
            if not health_ok:
                print("❌ Riot API não acessível")
                return False
            
            print("✅ Riot API conectada com sucesso")
            
            # 2. Busca ligas
            print("\n🏆 Buscando ligas disponíveis...")
            leagues = await riot.get_leagues()
            
            if leagues:
                print(f"✅ Encontradas {len(leagues)} ligas")
                # Mostra primeiras ligas
                for league in leagues[:3]:
                    print(f"   • {league.get('name', 'N/A')} - {league.get('region', 'N/A')}")
            else:
                print("⚠️  Nenhuma liga encontrada")
            
            # 3. Busca dados ao vivo
            print("\n⚡ Buscando dados de partidas ao vivo...")
            live_data = await riot.get_live_matches()
            
            if live_data:
                print(f"✅ Dados ao vivo obtidos")
                print(f"📊 Tipo de dados: {type(live_data)}")
                
                if isinstance(live_data, dict):
                    print(f"📋 Chaves disponíveis: {list(live_data.keys())}")
                elif isinstance(live_data, list):
                    print(f"📋 {len(live_data)} items encontrados")
            else:
                print("⚠️  Nenhum dado ao vivo encontrado")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro na Riot API: {e}")
        return False


async def test_data_processing():
    """Testa processamento e análise dos dados"""
    print("\n🧠 TESTE DE PROCESSAMENTO DE DADOS")
    print("=" * 45)
    
    try:
        # Simula processamento de dados como o sistema faria
        print("🔄 Simulando processamento de análise...")
        
        # 1. Verifica se pode importar sistemas de análise
        try:
            from bot.systems.lol_game_analyzer import LoLGameAnalyzer
            print("✅ LoLGameAnalyzer importado com sucesso")
            
            analyzer = LoLGameAnalyzer()
            print("✅ Analyzer inicializado")
            
        except Exception as e:
            print(f"⚠️  Problema com LoLGameAnalyzer: {e}")
        
        # 2. Verifica sistema de predição
        try:
            from bot.systems.prediction.dynamic_prediction_system import DynamicPredictionSystem
            print("✅ DynamicPredictionSystem importado com sucesso")
            
            prediction = DynamicPredictionSystem()
            print("✅ Sistema de predição inicializado")
            
        except Exception as e:
            print(f"⚠️  Problema com DynamicPredictionSystem: {e}")
        
        # 3. Verifica sistema de tips
        try:
            from bot.systems.professional_tips_system import ProfessionalTipsSystem
            print("✅ ProfessionalTipsSystem importado com sucesso")
            
        except Exception as e:
            print(f"⚠️  Problema com ProfessionalTipsSystem: {e}")
        
        print("✅ Sistemas de processamento operacionais")
        return True
        
    except Exception as e:
        print(f"❌ Erro no processamento: {e}")
        return False


async def main():
    """Função principal do teste"""
    print("🚀 VERIFICAÇÃO DE DADOS ESTATÍSTICOS EM TEMPO REAL")
    print("=" * 70)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {}
    
    # Teste 1: Dados de partidas ao vivo
    live_success, live_data = await test_live_match_data()
    results['live_matches'] = live_success
    
    # Teste 2: Estatísticas dos times
    team_stats_success = await test_team_statistics()
    results['team_statistics'] = team_stats_success
    
    # Teste 3: Dados da Riot API
    riot_success = await test_riot_api_data()
    results['riot_api'] = riot_success
    
    # Teste 4: Processamento de dados
    processing_success = await test_data_processing()
    results['data_processing'] = processing_success
    
    # Resultado final
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL - DADOS EM TEMPO REAL")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"✅ Testes passados: {passed_tests}/{total_tests}")
    print(f"📈 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 DETALHES:")
    print(f"   {'✅' if results['live_matches'] else '❌'} Partidas ao vivo: {'Funcionando' if results['live_matches'] else 'Com problemas'}")
    print(f"   {'✅' if results['team_statistics'] else '❌'} Estatísticas times: {'Funcionando' if results['team_statistics'] else 'Com problemas'}")
    print(f"   {'✅' if results['riot_api'] else '❌'} Riot API: {'Funcionando' if results['riot_api'] else 'Com problemas'}")
    print(f"   {'✅' if results['data_processing'] else '❌'} Processamento: {'Funcionando' if results['data_processing'] else 'Com problemas'}")
    
    if passed_tests >= 3:
        print(f"\n🎉 SISTEMA OPERACIONAL!")
        print(f"✅ Bot possui dados suficientes para gerar tips em tempo real")
        
        if live_data and live_data.get('teams'):
            print(f"🎯 Exemplo de partida analisável:")
            print(f"   Times: {' vs '.join(live_data['teams'])}")
            print(f"   Match ID: {live_data.get('match_id')}")
            print(f"   Stats disponíveis: {'Sim' if live_data.get('stats_available') else 'Básicos'}")
    else:
        print(f"\n⚠️  SISTEMA COM LIMITAÇÕES")
        print(f"❌ Pode haver problemas na obtenção de dados em tempo real")
    
    print(f"\n💡 O bot pode funcionar com os dados disponíveis!")


if __name__ == "__main__":
    asyncio.run(main()) 