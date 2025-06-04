#!/usr/bin/env python3
"""
Teste para verificar dados ao vivo via WebSocket

Verificar se conseguimos acessar o feed de dados em tempo real
da PandaScore via WebSocket para obter estatísticas detalhadas
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients import PandaScoreAPIClient
from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging para testes
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_websocket")


async def test_live_feed_access():
    """Testa acesso ao feed de dados ao vivo"""
    print("📡 TESTE DE FEED DE DADOS AO VIVO")
    print("=" * 50)
    
    try:
        async with PandaScoreAPIClient() as client:
            # 1. Busca partidas ao vivo
            print("🔍 Buscando partidas ao vivo...")
            live_matches = await client.get_lol_live_matches()
            
            if not live_matches:
                print("❌ Nenhuma partida ao vivo encontrada")
                return False
            
            print(f"✅ Encontradas {len(live_matches)} partidas ao vivo")
            
            # 2. Verifica dados de feed ao vivo
            for i, match in enumerate(live_matches[:2]):  # Analisa primeiras 2 partidas
                match_id = match.get('id')
                live_info = match.get('live', {})
                
                print(f"\n🎯 PARTIDA {i+1} - ID: {match_id}")
                print("-" * 40)
                
                # Informações da partida
                opponents = match.get('opponents', [])
                if len(opponents) >= 2:
                    team1 = opponents[0].get('opponent', {}).get('name', 'N/A')
                    team2 = opponents[1].get('opponent', {}).get('name', 'N/A')
                    print(f"⚔️  Times: {team1} vs {team2}")
                
                print(f"📊 Status: {match.get('status', 'N/A')}")
                print(f"🏆 Liga: {match.get('league', {}).get('name', 'N/A')}")
                
                # Análise do feed ao vivo
                if live_info:
                    print(f"\n📡 FEED AO VIVO:")
                    print(f"   Suportado: {live_info.get('supported', False)}")
                    
                    if live_info.get('url'):
                        print(f"   URL WebSocket: {live_info.get('url')}")
                        print(f"   Abre em: {live_info.get('opens_at', 'N/A')}")
                    
                    if live_info.get('supported'):
                        print(f"   ✅ Feed em tempo real disponível!")
                    else:
                        print(f"   ❌ Feed em tempo real não suportado")
                else:
                    print(f"\n❌ Nenhuma informação de feed ao vivo")
                
                # Verifica games em andamento
                games = match.get('games', [])
                print(f"\n🎮 GAMES DA PARTIDA: {len(games)}")
                
                for j, game in enumerate(games):
                    status = game.get('status', 'N/A')
                    if status == 'running':
                        print(f"   Game {j+1}: ⚡ {status} (EM ANDAMENTO)")
                        
                        # Verifica se há dados detalhados do game
                        if game.get('detailed_stats'):
                            print(f"      📊 Estatísticas detalhadas: SIM")
                        
                        # Procura por dados específicos do game
                        for key, value in game.items():
                            if key in ['length', 'position', 'teams']:
                                print(f"      📈 {key}: {value}")
                    else:
                        print(f"   Game {j+1}: {status}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao acessar feed ao vivo: {e}")
        return False


async def test_detailed_match_data():
    """Testa dados detalhados de uma partida específica"""
    print("\n📊 TESTE DE DADOS DETALHADOS DA PARTIDA")
    print("=" * 55)
    
    try:
        async with PandaScoreAPIClient() as client:
            # Busca partidas ao vivo
            live_matches = await client.get_lol_live_matches()
            
            if not live_matches:
                print("❌ Nenhuma partida ao vivo para analisar")
                return False
            
            # Pega a primeira partida
            match = live_matches[0]
            match_id = match.get('id')
            
            print(f"🔍 Analisando dados detalhados da partida {match_id}")
            
            # Verifica todos os campos disponíveis
            print(f"\n📋 TODOS OS CAMPOS DISPONÍVEIS:")
            for key, value in match.items():
                if isinstance(value, (dict, list)) and value:
                    if isinstance(value, dict):
                        print(f"   📁 {key}: dict com {len(value)} campos")
                        # Mostra sub-campos se for pequeno
                        if len(value) <= 5:
                            for sub_key in value.keys():
                                print(f"      - {sub_key}")
                    elif isinstance(value, list):
                        print(f"   📋 {key}: lista com {len(value)} items")
                        if len(value) > 0:
                            print(f"      Tipo do primeiro item: {type(value[0])}")
                else:
                    print(f"   📄 {key}: {value}")
            
            # Foca em dados que podem conter estatísticas
            important_fields = ['detailed_stats', 'live', 'games', 'results', 'streams']
            
            print(f"\n🎯 CAMPOS IMPORTANTES PARA ESTATÍSTICAS:")
            for field in important_fields:
                if field in match:
                    value = match[field]
                    print(f"   ✅ {field}: {value}")
                else:
                    print(f"   ❌ {field}: não encontrado")
            
            # Analisa games em detalhes
            games = match.get('games', [])
            if games:
                print(f"\n🎮 ANÁLISE DETALHADA DOS GAMES:")
                for i, game in enumerate(games):
                    print(f"\n   Game {i+1} - ID: {game.get('id', 'N/A')}")
                    print(f"   Status: {game.get('status', 'N/A')}")
                    print(f"   Duração: {game.get('length', 'N/A')} segundos")
                    
                    # Busca dados estatísticos no game
                    stats_found = []
                    for key, value in game.items():
                        if any(stat_word in key.lower() for stat_word in 
                              ['stat', 'score', 'kill', 'gold', 'damage', 'team']):
                            stats_found.append((key, value))
                    
                    if stats_found:
                        print(f"   📊 Estatísticas encontradas:")
                        for stat_key, stat_value in stats_found[:5]:  # Primeiras 5
                            print(f"      - {stat_key}: {stat_value}")
                    else:
                        print(f"   ⚠️  Nenhuma estatística específica encontrada")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao analisar dados detalhados: {e}")
        return False


async def test_data_sufficiency():
    """Avalia se os dados são suficientes para análise"""
    print("\n✅ AVALIAÇÃO DE SUFICIÊNCIA DOS DADOS")
    print("=" * 50)
    
    data_score = 0
    max_score = 10
    
    try:
        async with PandaScoreAPIClient() as client:
            # 1. Teste de acesso às partidas (2 pontos)
            live_matches = await client.get_lol_live_matches()
            if live_matches:
                data_score += 2
                print("✅ [+2] Acesso a partidas ao vivo")
            else:
                print("❌ [+0] Sem acesso a partidas ao vivo")
            
            # 2. Teste de dados dos times (2 pontos)
            teams = await client.get_teams()
            if teams and len(teams) > 50:
                data_score += 2
                print("✅ [+2] Base de dados de times robusta")
            elif teams:
                data_score += 1
                print("⚠️  [+1] Base de dados de times limitada")
            else:
                print("❌ [+0] Sem dados de times")
            
            # 3. Teste de ligas (1 ponto)
            leagues = await client.get_leagues()
            if leagues and len(leagues) > 20:
                data_score += 1
                print("✅ [+1] Informações de ligas disponíveis")
            else:
                print("❌ [+0] Dados de ligas insuficientes")
            
            # 4. Teste de partidas futuras (2 pontos)
            upcoming = await client.get_lol_upcoming_matches()
            if upcoming and len(upcoming) > 10:
                data_score += 2
                print("✅ [+2] Agenda de partidas futuras robusta")
            elif upcoming:
                data_score += 1
                print("⚠️  [+1] Agenda de partidas limitada")
            else:
                print("❌ [+0] Sem agenda de partidas")
            
            # 5. Teste de dados estruturados (2 pontos)
            if live_matches:
                match = live_matches[0]
                if match.get('games') and match.get('opponents'):
                    data_score += 2
                    print("✅ [+2] Dados estruturados adequadamente")
                else:
                    data_score += 1
                    print("⚠️  [+1] Estrutura de dados básica")
            
            # 6. Teste de feed ao vivo (1 ponto)
            if live_matches:
                live_info = live_matches[0].get('live', {})
                if live_info.get('supported'):
                    data_score += 1
                    print("✅ [+1] Feed ao vivo suportado")
                else:
                    print("❌ [+0] Feed ao vivo não disponível")
        
        # Resultado final
        percentage = (data_score / max_score) * 100
        
        print(f"\n📊 PONTUAÇÃO FINAL: {data_score}/{max_score} ({percentage:.1f}%)")
        
        if percentage >= 80:
            print("🎉 EXCELENTE! Dados suficientes para análise profissional")
            return "excellent"
        elif percentage >= 60:
            print("✅ BOM! Dados adequados para análise")
            return "good"
        elif percentage >= 40:
            print("⚠️  BÁSICO! Dados limitados mas utilizáveis")
            return "basic"
        else:
            print("❌ INSUFICIENTE! Dados inadequados para análise")
            return "insufficient"
            
    except Exception as e:
        print(f"❌ Erro na avaliação: {e}")
        return "error"


async def main():
    """Função principal"""
    print("🚀 VERIFICAÇÃO COMPLETA DE DADOS EM TEMPO REAL")
    print("=" * 65)
    
    # Teste 1: Feed de dados ao vivo
    live_feed_ok = await test_live_feed_access()
    
    # Teste 2: Dados detalhados
    detailed_ok = await test_detailed_match_data()
    
    # Teste 3: Suficiência dos dados
    data_quality = await test_data_sufficiency()
    
    # Resultado consolidado
    print("\n" + "=" * 65)
    print("🏆 RESULTADO CONSOLIDADO")
    print("=" * 65)
    
    print(f"📡 Feed ao vivo: {'✅ Funcionando' if live_feed_ok else '❌ Com problemas'}")
    print(f"📊 Dados detalhados: {'✅ Disponíveis' if detailed_ok else '❌ Limitados'}")
    print(f"🎯 Qualidade dos dados: {data_quality.upper()}")
    
    if live_feed_ok and detailed_ok and data_quality in ['excellent', 'good']:
        print(f"\n🎉 SISTEMA TOTALMENTE OPERACIONAL!")
        print(f"✅ Bot pode gerar tips em tempo real com alta qualidade")
        print(f"✅ Dados suficientes para análise profissional")
    elif live_feed_ok or detailed_ok:
        print(f"\n⚡ SISTEMA PARCIALMENTE OPERACIONAL!")
        print(f"✅ Bot pode gerar tips básicos")
        print(f"⚠️  Algumas limitações na qualidade dos dados")
    else:
        print(f"\n⚠️  SISTEMA COM LIMITAÇÕES!")
        print(f"❌ Capacidade de análise em tempo real reduzida")
    
    print(f"\n💡 Recomendação: Bot pode funcionar mesmo com limitações!")


if __name__ == "__main__":
    asyncio.run(main()) 
