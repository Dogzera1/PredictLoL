import asyncio
import aiohttp
from datetime import datetime

async def verificar_urgente_tip():
    """Verificação urgente: Por que a tip não foi enviada?"""
    
    api_key = '90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ'
    
    print(f'🚨 VERIFICAÇÃO URGENTE - {datetime.now().strftime("%H:%M:%S")}')
    print('Por que a tip do Game 5 não foi enviada?')
    print('Draft completo há 15min + 15min de jogo = TIP DEVERIA TER SIDO ENVIADA!')
    print('=' * 70)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Verifica matches ativos
            url = 'https://api.pandascore.co/lol/matches/running'
            params = {'token': api_key, 'per_page': 20}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    matches = await response.json()
                    
                    print(f'📊 Matches ativos: {len(matches)}')
                    
                    for match in matches:
                        opponents = match.get('opponents', [])
                        if len(opponents) >= 2:
                            team1 = opponents[0].get('opponent', {}).get('name', 'Team1')
                            team2 = opponents[1].get('opponent', {}).get('name', 'Team2')
                            
                            # Foca no match FlyQuest vs Cloud9
                            if 'flyquest' in team1.lower() or 'cloud9' in team2.lower() or \
                               'flyquest' in team2.lower() or 'cloud9' in team1.lower():
                                
                                print(f'\n🎮 MATCH ENCONTRADO: {team1} vs {team2}')
                                print(f'Status: {match.get("status")}')
                                
                                # DIAGNÓSTICO 1: Verifica série
                                serie = match.get('serie', {})
                                if serie:
                                    serie_opponents = serie.get('opponents', [])
                                    if len(serie_opponents) >= 2:
                                        wins1 = serie_opponents[0].get('wins', 0)
                                        wins2 = serie_opponents[1].get('wins', 0)
                                        total_wins = wins1 + wins2
                                        
                                        print(f'📊 Série: {wins1}-{wins2} (total: {total_wins})')
                                        
                                        if total_wins == 4:
                                            print('✅ SÉRIE 2-2 CONFIRMADA - É GAME 5')
                                        else:
                                            print(f'❌ PROBLEMA: Não é Game 5? Total wins = {total_wins}')
                                else:
                                    print('❌ PROBLEMA: Sem dados de série')
                                
                                # DIAGNÓSTICO 2: Verifica draft/composições
                                games = match.get('games', [])
                                if games:
                                    current_game = games[-1]
                                    teams_data = current_game.get('teams', [])
                                    
                                    if teams_data and len(teams_data) >= 2:
                                        total_champions = 0
                                        
                                        for i, team in enumerate(teams_data):
                                            players = team.get('players', [])
                                            champions = [p for p in players if p.get('champion')]
                                            team_champs = len(champions)
                                            total_champions += team_champs
                                            
                                            print(f'📝 {team1 if i == 0 else team2}: {team_champs}/5 champions')
                                            
                                            if champions:
                                                champ_names = [p.get('champion', {}).get('name', 'Unknown')[:10] 
                                                             for p in champions[:3]]
                                                print(f'   Champions: {", ".join(champ_names)}...')
                                        
                                        print(f'📋 TOTAL: {total_champions}/10 champions')
                                        
                                        if total_champions == 10:
                                            print('✅ DRAFT 100% COMPLETO!')
                                            print('🚨 TIP DEVERIA TER SIDO ENVIADA!')
                                        elif total_champions >= 8:
                                            print(f'⏳ Draft quase completo ({total_champions}/10)')
                                        else:
                                            print(f'❌ PROBLEMA: Draft incompleto ({total_champions}/10)')
                                    else:
                                        print('❌ PROBLEMA: Sem dados de teams/players')
                                else:
                                    print('❌ PROBLEMA: Sem dados de games')
                                
                                # DIAGNÓSTICO 3: Possíveis bloqueios
                                print(f'\n🔍 POSSÍVEIS CAUSAS DA TIP NÃO TER SIDO ENVIADA:')
                                print(f'1. ❓ Critérios de qualidade muito restritivos')
                                print(f'2. ❓ Sistema não detectou draft completo')
                                print(f'3. ❓ Problema na geração de odds')
                                print(f'4. ❓ Erro no envio via Telegram')
                                print(f'5. ❓ Cache anti-repetição bloqueando')
                                print(f'6. ❓ Sistema não está rodando no Railway')
                                
                                break
                    
                    # DIAGNÓSTICO 4: Verifica se há outros matches que podem ser Game 5
                    print(f'\n🔍 VERIFICANDO OUTROS MATCHES PARA GAME 5:')
                    game5_candidates = []
                    
                    for match in matches:
                        serie = match.get('serie', {})
                        if serie:
                            serie_opponents = serie.get('opponents', [])
                            if len(serie_opponents) >= 2:
                                wins1 = serie_opponents[0].get('wins', 0)
                                wins2 = serie_opponents[1].get('wins', 0)
                                total_wins = wins1 + wins2
                                
                                if total_wins == 4:
                                    opponents = match.get('opponents', [])
                                    if len(opponents) >= 2:
                                        team1 = opponents[0].get('opponent', {}).get('name', 'Team1')
                                        team2 = opponents[1].get('opponent', {}).get('name', 'Team2')
                                        game5_candidates.append(f'{team1} vs {team2}')
                    
                    if game5_candidates:
                        print(f'🎯 Games 5 encontrados: {len(game5_candidates)}')
                        for candidate in game5_candidates:
                            print(f'   • {candidate}')
                    else:
                        print(f'⚠️ NENHUM Game 5 detectado no momento')
                    
                else:
                    print(f'❌ Erro na API: {response.status}')
        
        except Exception as e:
            print(f'❌ Erro: {e}')
            import traceback
            traceback.print_exc()
    
    # AÇÃO CORRETIVA
    print(f'\n' + '=' * 70)
    print(f'🚀 AÇÃO IMEDIATA NECESSÁRIA:')
    print(f'1. ✅ Verificar logs do Railway para erros')
    print(f'2. ✅ Confirmar se sistema está rodando')
    print(f'3. ✅ Verificar se critérios de qualidade estão muito altos')
    print(f'4. ✅ Forçar uma nova verificação manual')
    
    print(f'\n⚠️ SE A TIP NÃO FOI ENVIADA:')
    print(f'• 🔧 Pode precisar ajustar critérios de qualidade')
    print(f'• 🔄 Pode precisar reiniciar o sistema')
    print(f'• 📡 Pode ser problema de conectividade das APIs')

if __name__ == '__main__':
    asyncio.run(verificar_urgente_tip()) 