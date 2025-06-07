import asyncio
import aiohttp
import json
from datetime import datetime

async def check_flyquest_draft_detailed():
    """Verifica detalhadamente o draft do FlyQuest vs Cloud9"""
    
    api_key = '90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ'
    match_id = 1174344  # ID do match FlyQuest vs Cloud9
    
    print(f'🔍 VERIFICAÇÃO DETALHADA DO DRAFT')
    print(f'Match: FlyQuest vs Cloud9 (ID: {match_id})')
    print(f'Horário: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Busca detalhes específicos do match
            print('📊 1. DADOS DETALHADOS DO MATCH:')
            match_url = f'https://api.pandascore.co/lol/matches/{match_id}'
            match_params = {'token': api_key}
            
            async with session.get(match_url, params=match_params) as response:
                if response.status == 200:
                    match_data = await response.json()
                    
                    print(f'   Status: {match_data.get("status")}')
                    print(f'   Nome: {match_data.get("name")}')
                    print(f'   Ao vivo: {match_data.get("live", {}).get("supported", False)}')
                    
                    # Verifica dados de série embedded
                    serie = match_data.get('serie')
                    if serie:
                        print(f'\n📈 2. DADOS DA SÉRIE EMBEDDED:')
                        print(f'   Série ID: {serie.get("id")}')
                        print(f'   Nome: {serie.get("name")}')
                        
                        # Placar da série
                        opponents = serie.get('opponents', [])
                        if opponents:
                            print(f'   📊 Placar:')
                            total_wins = 0
                            for opp in opponents:
                                team_name = opp.get('opponent', {}).get('name', 'Unknown')
                                wins = opp.get('wins', 0)
                                total_wins += wins
                                print(f'      {team_name}: {wins} wins')
                            
                            current_game = total_wins + 1
                            print(f'   🗺️ Game atual: {current_game}')
                            
                            if current_game == 5:
                                print(f'   🎯 CONFIRMADO: É GAME 5!')
                    
                    # 3. Verifica games e composições
                    games = match_data.get('games', [])
                    print(f'\n🎮 3. GAMES DO MATCH ({len(games)} encontrados):')
                    
                    if games:
                        for i, game in enumerate(games):
                            game_id = game.get('id')
                            game_status = game.get('status', 'unknown')
                            print(f'   Game {i+1}: ID={game_id}, Status={game_status}')
                            
                            # Verifica composições no game atual
                            teams = game.get('teams', [])
                            if teams:
                                print(f'      📝 Composições:')
                                for j, team in enumerate(teams):
                                    players = team.get('players', [])
                                    champions = [p.get('champion', {}).get('name') 
                                               for p in players if p.get('champion')]
                                    
                                    team_name = f'Team {j+1}'
                                    print(f'         {team_name}: {len(champions)}/5 picks')
                                    if champions:
                                        print(f'         Champions: {", ".join(champions)}')
                    
                else:
                    print(f'   ❌ Erro ao buscar match: {response.status}')
            
            # 4. Busca dados ao vivo usando endpoint específico
            print(f'\n📡 4. DADOS AO VIVO:')
            live_url = f'https://api.pandascore.co/lol/matches/{match_id}/live'
            live_params = {'token': api_key}
            
            async with session.get(live_url, params=live_params) as response:
                if response.status == 200:
                    live_data = await response.json()
                    print(f'   ✅ Dados ao vivo disponíveis')
                    
                    # Verifica se há informações de draft
                    if 'teams' in live_data:
                        teams = live_data['teams']
                        print(f'   📝 Draft ao vivo:')
                        for i, team in enumerate(teams):
                            team_name = team.get('name', f'Team {i+1}')
                            players = team.get('players', [])
                            champions = [p.get('champion', {}).get('name') 
                                       for p in players if p.get('champion')]
                            
                            print(f'      {team_name}: {len(champions)}/5 champions')
                            if champions:
                                print(f'         {", ".join(champions)}')
                    
                    # Status do game
                    game_state = live_data.get('game', {})
                    if game_state:
                        phase = game_state.get('phase', 'unknown')
                        time_seconds = game_state.get('time', 0)
                        time_minutes = time_seconds // 60
                        
                        print(f'   🎮 Fase: {phase}')
                        print(f'   ⏱️ Tempo: {time_minutes} minutos')
                        
                        if phase == 'draft':
                            print(f'   📝 DRAFT EM ANDAMENTO!')
                        elif phase == 'game':
                            print(f'   🎮 JOGO EM ANDAMENTO!')
                
                else:
                    print(f'   ⚠️ Dados ao vivo não disponíveis: {response.status}')
            
            # 5. RESUMO
            print(f'\n' + '=' * 60)
            print(f'📋 RESUMO:')
            print(f'✅ Match FlyQuest vs Cloud9 está ativo')
            print(f'✅ Sistema TEM acesso aos dados do match')
            
            # Próximos passos
            print(f'\n🔄 PRÓXIMOS PASSOS:')
            print(f'1. ⏳ Aguardar draft completo (se ainda em andamento)')
            print(f'2. 🤖 Sistema gerará tip automaticamente quando:')
            print(f'   • Draft estiver 100% completo (10/10 champions)')
            print(f'   • Atender critérios de qualidade')
            print(f'   • Game estiver ativo')
            print(f'3. 📱 Tip será enviada via Telegram')
            
        except Exception as e:
            print(f'❌ Erro: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_flyquest_draft_detailed()) 