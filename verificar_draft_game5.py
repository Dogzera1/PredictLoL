"""
Verificação específica do draft do Game 5
Analisa se o sistema está detectando e processando o match
"""

import asyncio
import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.systems.alternative_api_client import AlternativeAPIClient, get_match_compositions
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.data_models.match_data import MatchData

async def verificar_game5_urgente():
    """Verificação urgente do Game 5"""
    
    print('🔍 VERIFICAÇÃO URGENTE - DRAFT GAME 5')
    print(f'Horário: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    # 1. Testa APIs alternativas diretamente
    print('1️⃣ TESTANDO APIS ALTERNATIVAS PARA GAME 5')
    
    try:
        async with AlternativeAPIClient() as client:
            
            # Testa Live Client Data API
            print('   🎮 Testando Live Client Data API...')
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    url = 'https://127.0.0.1:2999/liveclientdata/allgamedata'
                    async with session.get(url, ssl=False, timeout=3) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            players = data.get('allPlayers', [])
                            if len(players) == 10:
                                print(f'   ✅ JOGO DETECTADO! {len(players)} players')
                                
                                team1_comp = []
                                team2_comp = []
                                
                                for player in players:
                                    champion = player.get('championName')
                                    team = player.get('team')
                                    summoner = player.get('summonerName', 'Unknown')
                                    
                                    if champion:
                                        if team == 'ORDER':
                                            team1_comp.append(f'{champion} ({summoner})')
                                        elif team == 'CHAOS':
                                            team2_comp.append(f'{champion} ({summoner})')
                                
                                print(f'   📊 COMPOSIÇÕES DETECTADAS:')
                                print(f'      🔵 Team ORDER: {", ".join(team1_comp)}')
                                print(f'      🔴 Team CHAOS: {", ".join(team2_comp)}')
                                
                                # Dados do jogo
                                game_data = data.get('gameData', {})
                                game_time = game_data.get('gameTime', 0)
                                game_mode = game_data.get('gameMode', 'UNKNOWN')
                                
                                print(f'   ⏱️ Tempo de jogo: {game_time:.1f}s')
                                print(f'   🎮 Modo: {game_mode}')
                                
                                return True
                        else:
                            print(f'   ❌ Live Client: Status {response.status}')
            except Exception as e:
                print(f'   ❌ Live Client não disponível: {e}')
            
            # Testa Riot Esports API
            print('   🏆 Testando Riot Esports API...')
            try:
                async with aiohttp.ClientSession() as session:
                    # IDs conhecidos para FlyQuest vs Cloud9
                    game_ids = [
                        '1174344',  # ID mencionado anteriormente
                        '98767975604431411',  # ID genérico de teste
                    ]
                    
                    for game_id in game_ids:
                        url = f'https://feed.lolesports.com/livestats/v1/details/{game_id}'
                        
                        try:
                            async with session.get(url, timeout=5) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    print(f'   ✅ Dados encontrados para ID {game_id}!')
                                    
                                    # Analisa dados
                                    participants = data.get('participants', {})
                                    if participants:
                                        print(f'      👥 {len(participants)} participantes detectados')
                                        
                                        # Mostra alguns participantes
                                        for i, (player_id, player_data) in enumerate(list(participants.items())[:3]):
                                            champion_id = player_data.get('championId', 'Unknown')
                                            team_id = player_data.get('teamId', 'Unknown')
                                            print(f'         Player {i+1}: Champion {champion_id}, Team {team_id}')
                                    
                                    return True
                                else:
                                    print(f'   ⚠️ ID {game_id}: Status {response.status}')
                        except Exception as e:
                            print(f'   ⚠️ ID {game_id}: {e}')
                            
            except Exception as e:
                print(f'   ❌ Riot Esports API: {e}')
    
    except Exception as e:
        print(f'❌ Erro geral nas APIs: {e}')
    
    return False

async def verificar_pandascore_game5():
    """Verifica se PandaScore tem dados do Game 5"""
    
    print('\n2️⃣ VERIFICANDO PANDASCORE PARA GAME 5')
    print('=' * 40)
    
    try:
        # Inicializa cliente PandaScore
        pandascore_client = PandaScoreAPIClient()
        
        print('   📡 Buscando matches ao vivo...')
        
        # Busca matches ao vivo
        live_matches = await pandascore_client.get_live_matches()
        
        if live_matches:
            print(f'   ✅ {len(live_matches)} matches ao vivo encontrados')
            
            # Procura por FlyQuest vs Cloud9
            target_teams = ['flyquest', 'cloud9', 'fly', 'c9']
            
            for match in live_matches:
                team1 = getattr(match, 'team1_name', '').lower()
                team2 = getattr(match, 'team2_name', '').lower()
                match_id = getattr(match, 'match_id', 'unknown')
                
                # Verifica se é FlyQuest vs Cloud9
                is_target_match = any(team in team1 for team in target_teams) and any(team in team2 for team in target_teams)
                
                if is_target_match:
                    print(f'   🎯 MATCH ENCONTRADO: {match.team1_name} vs {match.team2_name}')
                    print(f'      ID: {match_id}')
                    print(f'      Status: {getattr(match, "status", "unknown")}')
                    print(f'      Liga: {getattr(match, "league", "unknown")}')
                    
                    # Verifica composições
                    team1_comp = getattr(match, 'team1_composition', [])
                    team2_comp = getattr(match, 'team2_composition', [])
                    
                    print(f'      Team 1 composition: {len(team1_comp)} champions')
                    print(f'      Team 2 composition: {len(team2_comp)} champions')
                    
                    if team1_comp and team2_comp:
                        if len(team1_comp) == 5 and len(team2_comp) == 5:
                            print(f'   ✅ DRAFT COMPLETO via PandaScore!')
                        else:
                            print(f'   ⏳ Draft incompleto: {len(team1_comp)}/5 vs {len(team2_comp)}/5')
                    else:
                        print(f'   ❌ Sem dados de composição no PandaScore')
                    
                    return match
                else:
                    print(f'   📋 Outro match: {team1} vs {team2}')
        else:
            print('   ❌ Nenhum match ao vivo encontrado no PandaScore')
    
    except Exception as e:
        print(f'   ❌ Erro no PandaScore: {e}')
    
    return None

async def testar_sistema_completo():
    """Testa o sistema completo de detecção"""
    
    print('\n3️⃣ TESTE DO SISTEMA COMPLETO')
    print('=' * 40)
    
    try:
        # Simula match do Game 5
        test_match = MatchData(
            match_id="1174344",
            team1_name="FlyQuest",
            team2_name="Cloud9", 
            league="LTA North",
            status="running"
        )
        
        print(f'   🎮 Testando com: {test_match.team1_name} vs {test_match.team2_name}')
        
        # Testa sistema de APIs alternativas
        composition_data = await get_match_compositions(test_match)
        
        if composition_data:
            print(f'   ✅ Sistema funcionando! Fonte: {composition_data.source.upper()}')
            print(f'      Team 1: {", ".join(composition_data.team1_composition)}')
            print(f'      Team 2: {", ".join(composition_data.team2_composition)}')
            print(f'      Draft completo: {composition_data.draft_complete}')
            return True
        else:
            print(f'   ❌ Sistema não conseguiu obter composições')
            
    except Exception as e:
        print(f'   ❌ Erro no teste: {e}')
    
    return False

async def main():
    """Verificação principal"""
    
    print('🚨 VERIFICAÇÃO URGENTE - GAME 5 DRAFT')
    
    # Executa todas as verificações
    api_success = await verificar_game5_urgente()
    pandascore_match = await verificar_pandascore_game5()
    system_success = await testar_sistema_completo()
    
    # Resultado final
    print(f'\n' + '=' * 60)
    print(f'📊 RESULTADO DA VERIFICAÇÃO:')
    print('=' * 60)
    
    if api_success:
        print(f'✅ JOGO DETECTADO via APIs alternativas')
        print(f'🎮 Sistema consegue ver o jogo rodando localmente')
    else:
        print(f'❌ Nenhum jogo detectado via APIs alternativas')
    
    if pandascore_match:
        print(f'✅ Match encontrado no PandaScore')
        print(f'📊 Dados: {pandascore_match.team1_name} vs {pandascore_match.team2_name}')
    else:
        print(f'❌ Match não encontrado no PandaScore')
    
    if system_success:
        print(f'✅ Sistema de backup funcionando')
    else:
        print(f'❌ Sistema de backup precisa de ajustes')
    
    # Diagnóstico
    print(f'\n🔧 DIAGNÓSTICO:')
    
    if api_success and not pandascore_match:
        print(f'⚠️ PROBLEMA: Jogo rodando mas PandaScore não detecta')
        print(f'✅ SOLUÇÃO: APIs alternativas podem resolver')
    elif pandascore_match and not api_success:
        print(f'✅ SITUAÇÃO: PandaScore tem dados, APIs locais indisponíveis')
        print(f'✅ NORMAL: Sistema principal funcionando')
    elif not api_success and not pandascore_match:
        print(f'❌ PROBLEMA: Nenhuma fonte detecta o jogo')
        print(f'🔍 AÇÃO: Verificar se há jogo realmente ativo')
    else:
        print(f'✅ IDEAL: Múltiplas fontes detectam o jogo')

if __name__ == '__main__':
    asyncio.run(main()) 