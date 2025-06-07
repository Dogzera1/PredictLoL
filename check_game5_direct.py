import asyncio
import aiohttp
from datetime import datetime

async def check_game5_direct():
    """Verificação direta do Game 5 com chaves da config"""
    
    # Chave da API (do arquivo railway_vars.env)
    api_key = '90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ'
    
    url = 'https://api.pandascore.co/lol/matches/running'
    params = {'token': api_key, 'per_page': 20}
    
    print(f'🔍 VERIFICANDO GAME 5 - {datetime.now().strftime("%H:%M:%S")}')
    print('Draft acabou de terminar - sistema consegue acessar?')
    print('=' * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    matches = await response.json()
                    print(f'📊 Matches ativos encontrados: {len(matches)}')
                    
                    game5_found = False
                    draft_complete_found = False
                    
                    for i, match in enumerate(matches):
                        opponents = match.get('opponents', [])
                        if len(opponents) >= 2:
                            team1 = opponents[0].get('opponent', {}).get('name', 'Team1')
                            team2 = opponents[1].get('opponent', {}).get('name', 'Team2')
                            league = match.get('league', {}).get('name', 'Unknown')
                            status = match.get('status', 'unknown')
                            match_id = match.get('id', 'unknown')
                            
                            print(f'\n🎮 MATCH {i+1}: {team1} vs {team2}')
                            print(f'   Liga: {league}')
                            print(f'   Status: {status}')
                            print(f'   ID: {match_id}')
                            
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
                                        
                                        # Verifica draft/composições
                                        games = match.get('games', [])
                                        if games:
                                            current_game = games[-1]
                                            teams_data = current_game.get('teams', [])
                                            
                                            if len(teams_data) >= 2:
                                                team1_players = teams_data[0].get('players', [])
                                                team2_players = teams_data[1].get('players', [])
                                                
                                                team1_champs = len([p for p in team1_players if p.get('champion')])
                                                team2_champs = len([p for p in team2_players if p.get('champion')])
                                                total_champs = team1_champs + team2_champs
                                                
                                                print(f'   🔵 {team1}: {team1_champs}/5 champions')
                                                print(f'   🔴 {team2}: {team2_champs}/5 champions')
                                                print(f'   📝 Draft: {total_champs}/10 picks completos')
                                                
                                                if team1_champs == 5 and team2_champs == 5:
                                                    print(f'   ✅ DRAFT COMPLETO!')
                                                    print(f'   🚀 PRONTO PARA GERAR TIP!')
                                                    draft_complete_found = True
                                                    
                                                    # Mostra alguns champions
                                                    if team1_players:
                                                        champs1 = [p.get('champion', {}).get('name', 'Unknown') 
                                                                  for p in team1_players[:3] if p.get('champion')]
                                                        if champs1:
                                                            print(f'      {team1}: {", ".join(champs1)}...')
                                                    
                                                    if team2_players:
                                                        champs2 = [p.get('champion', {}).get('name', 'Unknown') 
                                                                  for p in team2_players[:3] if p.get('champion')]
                                                        if champs2:
                                                            print(f'      {team2}: {", ".join(champs2)}...')
                                                
                                                elif total_champs > 0:
                                                    print(f'   ⏳ Draft em andamento... ({total_champs}/10)')
                                                else:
                                                    print(f'   📝 Aguardando início do draft')
                                            else:
                                                print(f'   ⚠️ Sem dados detalhados de composição')
                                    
                                    elif total_wins < 4:
                                        current_game_num = total_wins + 1
                                        print(f'   🗺️ Game {current_game_num} da série')
                                else:
                                    print(f'   ⚠️ Dados de série incompletos')
                            else:
                                print(f'   ℹ️ Match sem dados de série (possivelmente Bo1)')
                    
                    print('\n' + '=' * 60)
                    print('📋 RESUMO DA VERIFICAÇÃO:')
                    
                    if game5_found:
                        print('🎉 GAME 5 ENCONTRADO!')
                        if draft_complete_found:
                            print('✅ Sistema TEM acesso ao draft completo')
                            print('📱 Condições ideais para gerar tip!')
                            print('🚀 Tip deve ser enviada em breve')
                        else:
                            print('⏳ Game 5 encontrado mas draft ainda em andamento')
                            print('🔄 Sistema aguardando draft completo')
                    else:
                        print('⚠️ Nenhum Game 5 ativo no momento')
                        print('Possíveis motivos:')
                        print('   • Não há séries 2-2 em andamento')
                        print('   • Game 5 ainda não começou')
                        print('   • Game 5 já terminou')
                        print('   • APIs com delay na atualização')
                    
                    print(f'\n⏰ Próxima verificação: Sistema monitora a cada 30 segundos')
                    
                else:
                    print(f'❌ Erro na API PandaScore: HTTP {response.status}')
                    text = await response.text()
                    print(f'Resposta: {text[:300]}...')
                    
        except Exception as e:
            print(f'❌ Erro na verificação: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_game5_direct()) 