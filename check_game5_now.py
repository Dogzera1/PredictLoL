import asyncio
import aiohttp
import os
from datetime import datetime

async def check_game5_now():
    """Verifica Game 5 em tempo real"""
    
    api_key = os.getenv('PANDASCORE_API_KEY')
    if not api_key:
        print('❌ API key não encontrada')
        return
    
    url = 'https://api.pandascore.co/lol/matches/running'
    params = {'token': api_key, 'per_page': 20}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    matches = await response.json()
                    print(f'🔍 VERIFICAÇÃO GAME 5 - {datetime.now().strftime("%H:%M:%S")}')
                    print(f'📊 Matches ativos: {len(matches)}')
                    print('=' * 50)
                    
                    game5_found = False
                    
                    for i, match in enumerate(matches):
                        opponents = match.get('opponents', [])
                        if len(opponents) >= 2:
                            team1 = opponents[0].get('opponent', {}).get('name', 'Team1')
                            team2 = opponents[1].get('opponent', {}).get('name', 'Team2')
                            league = match.get('league', {}).get('name', 'Unknown')
                            status = match.get('status', 'unknown')
                            
                            print(f'\n🎮 MATCH {i+1}: {team1} vs {team2}')
                            print(f'   Liga: {league}')
                            print(f'   Status: {status}')
                            
                            # Verifica série
                            serie = match.get('serie', {})
                            if serie:
                                serie_opponents = serie.get('opponents', [])
                                if len(serie_opponents) >= 2:
                                    wins1 = serie_opponents[0].get('wins', 0)
                                    wins2 = serie_opponents[1].get('wins', 0)
                                    total_wins = wins1 + wins2
                                    
                                    print(f'   📊 Série: {wins1}-{wins2} (total: {total_wins} games)')
                                    
                                    if total_wins == 4:  # Série 2-2 = Game 5
                                        print(f'   🎯 GAME 5 DETECTADO!')
                                        game5_found = True
                                        
                                        # Verifica draft
                                        games = match.get('games', [])
                                        if games:
                                            current_game = games[-1]
                                            teams_data = current_game.get('teams', [])
                                            
                                            if len(teams_data) >= 2:
                                                team1_players = teams_data[0].get('players', [])
                                                team2_players = teams_data[1].get('players', [])
                                                
                                                team1_champs = len([p for p in team1_players if p.get('champion')])
                                                team2_champs = len([p for p in team2_players if p.get('champion')])
                                                
                                                print(f'   🔵 {team1}: {team1_champs}/5 champions')
                                                print(f'   🔴 {team2}: {team2_champs}/5 champions')
                                                
                                                if team1_champs == 5 and team2_champs == 5:
                                                    print(f'   ✅ DRAFT COMPLETO - PRONTO PARA TIP!')
                                                elif team1_champs > 0 or team2_champs > 0:
                                                    print(f'   ⏳ Draft em andamento...')
                                                else:
                                                    print(f'   📝 Aguardando início do draft')
                                    
                                    elif total_wins < 4:
                                        current_game_num = total_wins + 1
                                        print(f'   🗺️ Game {current_game_num} da série')
                    
                    print('\n' + '=' * 50)
                    if game5_found:
                        print('🎉 GAME 5 ENCONTRADO!')
                        print('✅ Sistema tem acesso ao draft')
                        print('📱 Aguardando condições para gerar tip')
                    else:
                        print('⚠️ Nenhum Game 5 ativo no momento')
                        print('   • Verifique se há séries 2-2')
                        print('   • Game 5 pode ainda não ter começado')
                else:
                    print(f'❌ API Error: {response.status}')
                    text = await response.text()
                    print(f'Resposta: {text[:200]}...')
        except Exception as e:
            print(f'❌ Erro: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_game5_now()) 