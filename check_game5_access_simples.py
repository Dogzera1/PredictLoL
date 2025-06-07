# VERIFICAÇÃO RÁPIDA: ACESSO AO GAME 5
# Verifica se sistema consegue acessar o draft que acabou de terminar

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importações corretas
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.data_models.match_data import MatchData

async def quick_check_game5():
    """Verificação rápida do Game 5"""
    
    print("🔍 VERIFICANDO ACESSO AO GAME 5")
    print("Draft acabou de terminar - sistema detectando?")
    print("=" * 50)
    
    try:
        # Inicializa cliente
        client = PandaScoreAPIClient()
        print("✅ Cliente PandaScore inicializado")
        
        # Busca matches LoL ao vivo
        print("\n📡 BUSCANDO MATCHES ATIVOS...")
        
        url = "https://api.pandascore.co/lol/matches/running"
        params = {
            'token': client.api_key,
            'per_page': 20,
            'sort': '-begin_at'
        }
        
        async with client.session.get(url, params=params) as response:
            if response.status == 200:
                matches = await response.json()
                print(f"   📊 {len(matches)} matches ativos encontrados")
                
                game5_matches = []
                
                for match in matches:
                    match_name = match.get('name', 'Unknown')
                    teams = f"{match.get('opponents', [{}])[0].get('opponent', {}).get('name', 'Team1')} vs {match.get('opponents', [{}])[1].get('opponent', {}).get('name', 'Team2') if len(match.get('opponents', [])) > 1 else 'TeamX'}"
                    status = match.get('status', 'unknown')
                    
                    print(f"\n🎮 MATCH: {teams}")
                    print(f"   Status: {status}")
                    print(f"   Nome: {match_name}")
                    
                    # Verifica se é Game 5
                    serie_info = match.get('serie', {})
                    if serie_info:
                        # Analisa wins
                        opponents = serie_info.get('opponents', [])
                        if len(opponents) >= 2:
                            wins1 = opponents[0].get('wins', 0)
                            wins2 = opponents[1].get('wins', 0)
                            total_wins = wins1 + wins2
                            
                            print(f"   📊 Série: {wins1}-{wins2} (total: {total_wins})")
                            
                            if total_wins == 4:  # Série 2-2 = Game 5
                                print(f"   🎯 GAME 5 DETECTADO!")
                                game5_matches.append({
                                    'match': match,
                                    'teams': teams,
                                    'wins': f"{wins1}-{wins2}"
                                })
                                
                                # Verifica draft/composições
                                games = match.get('games', [])
                                if games:
                                    latest_game = games[-1] if games else {}
                                    teams_data = latest_game.get('teams', [])
                                    
                                    if teams_data and len(teams_data) >= 2:
                                        team1_players = teams_data[0].get('players', [])
                                        team2_players = teams_data[1].get('players', [])
                                        
                                        team1_champs = len([p for p in team1_players if p.get('champion')])
                                        team2_champs = len([p for p in team2_players if p.get('champion')])
                                        
                                        print(f"   🔵 Team1: {team1_champs}/5 champions")
                                        print(f"   🔴 Team2: {team2_champs}/5 champions")
                                        
                                        if team1_champs == 5 and team2_champs == 5:
                                            print(f"   ✅ DRAFT COMPLETO!")
                                            
                                            # Mostra alguns champions
                                            champs1 = [p.get('champion', {}).get('name', 'Unknown') for p in team1_players[:3] if p.get('champion')]
                                            champs2 = [p.get('champion', {}).get('name', 'Unknown') for p in team2_players[:3] if p.get('champion')]
                                            
                                            print(f"      Team1: {', '.join(champs1)}...")
                                            print(f"      Team2: {', '.join(champs2)}...")
                                            
                                        else:
                                            print(f"   ⏳ Draft em andamento")
                                    else:
                                        print(f"   ⚠️ Sem dados de composição")
                
                # Resumo Game 5
                print(f"\n" + "=" * 50)
                print(f"📊 RESUMO GAME 5:")
                if game5_matches:
                    print(f"   ✅ {len(game5_matches)} Game(s) 5 encontrado(s)!")
                    for g5 in game5_matches:
                        print(f"      • {g5['teams']} (série {g5['wins']})")
                else:
                    print(f"   ⚠️ Nenhum Game 5 encontrado")
                    print(f"   Possíveis motivos:")
                    print(f"      • Não há séries 2-2 ativas")
                    print(f"      • Game 5 ainda não começou")
                    print(f"      • APIs com delay")
                
            else:
                print(f"❌ Erro na API: {response.status}")
                text = await response.text()
                print(f"   Resposta: {text[:200]}...")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

async def check_live_status():
    """Verifica status geral"""
    
    print(f"\n🔄 STATUS DO SISTEMA:")
    print(f"   • Horário: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")
    print(f"   • Sistema online: ✅")
    print(f"   • Aguardando Game 5...")

if __name__ == "__main__":
    asyncio.run(quick_check_game5())
    asyncio.run(check_live_status()) 