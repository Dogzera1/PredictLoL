import asyncio
import aiohttp
import json
from datetime import datetime

async def investigate_flyquest_match():
    """Investiga detalhadamente o match FlyQuest vs Cloud9"""
    
    api_key = '90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ'
    
    print(f'🔍 INVESTIGAÇÃO DETALHADA: FlyQuest vs Cloud9')
    print(f'Horário: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    # 1. Busca o match específico
    url = 'https://api.pandascore.co/lol/matches/running'
    params = {'token': api_key, 'per_page': 20}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    matches = await response.json()
                    
                    flyquest_match = None
                    for match in matches:
                        opponents = match.get('opponents', [])
                        if len(opponents) >= 2:
                            team1 = opponents[0].get('opponent', {}).get('name', '')
                            team2 = opponents[1].get('opponent', {}).get('name', '')
                            
                            if 'flyquest' in team1.lower() or 'cloud9' in team2.lower() or \
                               'flyquest' in team2.lower() or 'cloud9' in team1.lower():
                                flyquest_match = match
                                break
                    
                    if flyquest_match:
                        print('🎮 MATCH ENCONTRADO!')
                        print(f'ID: {flyquest_match.get("id")}')
                        print(f'Status: {flyquest_match.get("status")}')
                        print(f'Nome: {flyquest_match.get("name", "N/A")}')
                        
                        print('\n📊 DADOS COMPLETOS DO MATCH:')
                        print(json.dumps(flyquest_match, indent=2)[:1000] + '...')
                        
                        # 2. Busca a série específica se houver
                        serie_id = flyquest_match.get('serie_id')
                        if serie_id:
                            print(f'\n🏆 INVESTIGANDO SÉRIE (ID: {serie_id})')
                            
                            serie_url = f'https://api.pandascore.co/lol/series/{serie_id}'
                            serie_params = {'token': api_key}
                            
                            async with session.get(serie_url, params=serie_params) as serie_response:
                                if serie_response.status == 200:
                                    serie_data = await serie_response.json()
                                    
                                    print('📈 DADOS DA SÉRIE:')
                                    print(f'Nome: {serie_data.get("name", "N/A")}')
                                    print(f'Status: {serie_data.get("status", "N/A")}')
                                    
                                    # Analisa opponents da série
                                    serie_opponents = serie_data.get('opponents', [])
                                    if serie_opponents:
                                        print('\n🏃 PLACAR DA SÉRIE:')
                                        for i, opp in enumerate(serie_opponents):
                                            team_name = opp.get('opponent', {}).get('name', f'Team{i+1}')
                                            wins = opp.get('wins', 0)
                                            print(f'   {team_name}: {wins} wins')
                                        
                                        total_wins = sum(opp.get('wins', 0) for opp in serie_opponents)
                                        print(f'   Total games jogados: {total_wins}')
                                        
                                        if total_wins == 4:
                                            print('   🎯 SÉRIE 2-2 CONFIRMADA - É GAME 5!')
                                        else:
                                            print(f'   🗺️ Game {total_wins + 1} da série')
                                    
                                    # Analisa games da série
                                    games = serie_data.get('games', [])
                                    if games:
                                        print(f'\n🎮 GAMES DA SÉRIE ({len(games)} total):')
                                        for i, game in enumerate(games):
                                            game_status = game.get('status', 'unknown')
                                            game_id = game.get('id', 'N/A')
                                            winner = game.get('winner', {}).get('name', 'TBD') if game.get('winner') else 'TBD'
                                            print(f'   Game {i+1}: Status={game_status}, Winner={winner}, ID={game_id}')
                                        
                                        # Verifica se o match atual é o último game
                                        if len(games) >= 5:
                                            current_game = games[-1]
                                            if current_game.get('id') == flyquest_match.get('id'):
                                                print('   ✅ Match atual É o Game 5!')
                                else:
                                    print(f'❌ Erro ao buscar série: {serie_response.status}')
                        else:
                            print('\n⚠️ Match não tem serie_id - verificando dados embedded')
                            
                            # Verifica se há dados de série embedded no match
                            serie_embedded = flyquest_match.get('serie')
                            if serie_embedded:
                                print('📈 DADOS DE SÉRIE EMBEDDED:')
                                print(json.dumps(serie_embedded, indent=2))
                        
                        # 3. Verifica composições/draft
                        print('\n📝 VERIFICANDO DRAFT:')
                        games = flyquest_match.get('games', [])
                        if games:
                            current_game = games[-1]
                            teams_data = current_game.get('teams', [])
                            
                            if teams_data:
                                for i, team in enumerate(teams_data):
                                    players = team.get('players', [])
                                    team_name = f'Team {i+1}'
                                    champ_count = len([p for p in players if p.get('champion')])
                                    
                                    print(f'   {team_name}: {champ_count}/5 champions')
                                    
                                    if champ_count > 0:
                                        champions = [p.get('champion', {}).get('name', 'Unknown') 
                                                   for p in players if p.get('champion')]
                                        print(f'      Champions: {", ".join(champions)}')
                            else:
                                print('   ⚠️ Sem dados de teams/composições')
                        else:
                            print('   ⚠️ Sem dados de games')
                    
                    else:
                        print('❌ Match FlyQuest vs Cloud9 não encontrado nos matches ativos')
                
                else:
                    print(f'❌ Erro na API: {response.status}')
                    
        except Exception as e:
            print(f'❌ Erro: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(investigate_flyquest_match()) 