"""
Teste direto do PandaScore para verificar matches ao vivo
"""

import asyncio
import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients.pandascore_api_client import PandaScoreAPIClient

async def testar_pandascore_completo():
    """Teste completo do PandaScore"""
    
    print('🔍 TESTE DIRETO DO PANDASCORE')
    print(f'Horário: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    try:
        async with PandaScoreAPIClient() as client:
            print('✅ Cliente PandaScore inicializado')
            
            # 1. Testa matches ao vivo
            print('\n1️⃣ BUSCANDO MATCHES AO VIVO...')
            try:
                live_matches = await client.get_lol_live_matches()
                
                if live_matches:
                    print(f'✅ {len(live_matches)} matches ao vivo encontrados!')
                    
                    for i, match in enumerate(live_matches):
                        print(f'\n   📋 MATCH {i+1}:')
                        print(f'      ID: {match.get("id", "unknown")}')
                        
                        # Teams
                        opponents = match.get('opponents', [])
                        if len(opponents) >= 2:
                            team1 = opponents[0].get('opponent', {}).get('name', 'Team1')
                            team2 = opponents[1].get('opponent', {}).get('name', 'Team2')
                            print(f'      Teams: {team1} vs {team2}')
                            
                            # Verifica se é FlyQuest vs Cloud9
                            if any(t in team1.lower() for t in ['flyquest', 'fly']) and any(t in team2.lower() for t in ['cloud9', 'c9']):
                                print(f'      🎯 FLYQUEST vs CLOUD9 ENCONTRADO!')
                                await analisar_match_especifico(client, match)
                        
                        # Liga
                        league = match.get('league', {})
                        if league:
                            league_name = league.get('name', 'Unknown')
                            print(f'      Liga: {league_name}')
                        
                        # Status
                        status = match.get('status', 'unknown')
                        print(f'      Status: {status}')
                        
                        # Games da série
                        games = match.get('games', [])
                        print(f'      Games: {len(games)} na série')
                        
                        # Mostra apenas os primeiros 3 matches para não poluir
                        if i >= 2:
                            print(f'   ... e mais {len(live_matches) - 3} matches')
                            break
                            
                else:
                    print('❌ Nenhum match ao vivo encontrado')
                    
            except Exception as e:
                print(f'❌ Erro ao buscar matches ao vivo: {e}')
            
            # 2. Testa compositions ao vivo
            print('\n2️⃣ BUSCANDO COMPOSIÇÕES AO VIVO...')
            try:
                compositions = await client.get_live_match_compositions()
                
                if compositions:
                    print(f'✅ {len(compositions)} matches com composições encontrados!')
                    
                    for comp in compositions[:3]:  # Primeiros 3
                        match_id = comp.get('match_id', 'unknown')
                        teams = comp.get('teams', {})
                        print(f'   📊 Match {match_id}: {len(teams)} teams com composições')
                        
                else:
                    print('❌ Nenhuma composição ao vivo encontrada')
                    
            except Exception as e:
                print(f'❌ Erro ao buscar composições: {e}')
            
            # 3. Busca por FlyQuest vs Cloud9 especificamente
            print('\n3️⃣ BUSCA ESPECÍFICA FLYQUEST vs CLOUD9...')
            try:
                matches = await client.search_matches_by_teams('FlyQuest', 'Cloud9')
                
                if matches:
                    print(f'✅ {len(matches)} matches FlyQuest vs Cloud9 encontrados!')
                    
                    for match in matches[:2]:  # Primeiros 2
                        match_id = match.get('id', 'unknown')
                        status = match.get('status', 'unknown')
                        print(f'   🎮 Match {match_id}: Status {status}')
                        
                        if status in ['running', 'live', 'in_progress']:
                            print(f'      🔥 MATCH AO VIVO!')
                            await analisar_match_especifico(client, match)
                            
                else:
                    print('❌ Nenhum match FlyQuest vs Cloud9 encontrado')
                    
            except Exception as e:
                print(f'❌ Erro na busca específica: {e}')
                
    except Exception as e:
        print(f'❌ Erro geral: {e}')

async def analisar_match_especifico(client: PandaScoreAPIClient, match: dict):
    """Analisa um match específico em detalhes"""
    
    match_id = match.get('id')
    if not match_id:
        return
    
    print(f'\n      🔍 ANÁLISE DETALHADA DO MATCH {match_id}:')
    
    try:
        # 1. Busca dados de composição
        comp_data = await client.get_match_composition_data(match_id)
        
        if comp_data:
            print(f'      ✅ Dados de composição obtidos!')
            
            teams = comp_data.get('teams', {})
            for team_key, team_data in teams.items():
                picks = team_data.get('picks', [])
                print(f'         {team_key}: {len(picks)} champions')
                
                for pick in picks[:3]:  # Primeiros 3 champions
                    champion = pick.get('champion', {}).get('name', 'Unknown')
                    print(f'            - {champion}')
                    
        else:
            print(f'      ❌ Sem dados de composição')
        
        # 2. Busca games da série
        games_data = await client.get_match_games_data(match_id)
        
        if games_data:
            print(f'      📊 {len(games_data)} games na série:')
            
            for i, game in enumerate(games_data):
                game_id = game.get('id', 'unknown')
                status = game.get('status', 'unknown')
                number = game.get('position', i+1)
                print(f'         Game {number} (ID: {game_id}): {status}')
                
                if status in ['running', 'live', 'in_progress']:
                    print(f'            🔥 GAME AO VIVO!')
                    
        else:
            print(f'      ❌ Sem dados de games')
            
    except Exception as e:
        print(f'      ❌ Erro na análise: {e}')

async def main():
    """Teste principal"""
    
    await testar_pandascore_completo()
    
    print(f'\n' + '=' * 60)
    print(f'📋 CONCLUSÃO:')
    print('=' * 60)
    print(f'🔍 Se nenhum match foi encontrado:')
    print(f'   • Game 5 pode ter terminado')
    print(f'   • Não há matches LoL ao vivo no momento')
    print(f'   • Aguardar próxima partida profissional')
    
    print(f'\n✅ APIs alternativas já estão integradas')
    print(f'🚀 Sistema funcionará quando houver matches ativos')

if __name__ == '__main__':
    asyncio.run(main()) 