import asyncio
import aiohttp
import json
from datetime import datetime

async def testar_apis_gratuitas():
    """Testa APIs alternativas gratuitas para obter dados de composições"""
    
    print(f'🔍 BUSCANDO APIS GRATUITAS PARA COMPOSIÇÕES')
    print(f'Horário: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    # 1. LIVE CLIENT DATA API (Riot Games - Local)
    print('📡 1. TESTANDO LIVE CLIENT DATA API (Local Riot)')
    print('URL: https://developer.riotgames.com/docs/lol#live-client-data-api')
    print('Status: Gratuita, mas requer cliente local rodando')
    
    try:
        async with aiohttp.ClientSession() as session:
            # Testa se há cliente local rodando
            local_url = 'https://127.0.0.1:2999/liveclientdata/allgamedata'
            
            try:
                async with session.get(local_url, ssl=False, timeout=3) as response:
                    if response.status == 200:
                        data = await response.json()
                        print('✅ Cliente local detectado!')
                        
                        # Verifica dados de players
                        if 'allPlayers' in data:
                            players = data['allPlayers']
                            print(f'   👥 {len(players)} players encontrados')
                            
                            for player in players[:2]:  # Primeiros 2 players
                                champion = player.get('championName', 'Unknown')
                                team = player.get('team', 'Unknown')
                                print(f'      {team}: {champion}')
                        
                        return True
                    else:
                        print(f'⚠️ Cliente local: Status {response.status}')
            except:
                print('❌ Cliente local não detectado ou não em jogo')
    except Exception as e:
        print(f'❌ Erro Live Client API: {e}')
    
    # 2. ESPORTS API (Riot Games - Gratuita)
    print(f'\n📡 2. TESTANDO RIOT ESPORTS API')
    print('URL: https://esports-api.lolesports.com/')
    print('Status: Gratuita para dados de esports')
    
    try:
        esports_url = 'https://esports-api.lolesports.com/persisted/gw/getLive'
        params = {'hl': 'en-US'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(esports_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print('✅ Riot Esports API funcionando!')
                    
                    events = data.get('data', {}).get('schedule', {}).get('events', [])
                    live_events = [e for e in events if e.get('state') == 'inProgress']
                    
                    print(f'   🎮 {len(live_events)} eventos ao vivo')
                    
                    for event in live_events[:2]:
                        teams = event.get('match', {}).get('teams', [])
                        if len(teams) >= 2:
                            team1 = teams[0].get('name', 'Team1')
                            team2 = teams[1].get('name', 'Team2')
                            print(f'      Match: {team1} vs {team2}')
                    
                    return True
                else:
                    print(f'❌ Esports API: Status {response.status}')
    except Exception as e:
        print(f'❌ Erro Esports API: {e}')
    
    # 3. DATA DRAGON (Riot Games - Gratuita)
    print(f'\n📡 3. TESTANDO DATA DRAGON API')
    print('URL: https://ddragon.leagueoflegends.com/')
    print('Status: Gratuita para dados estáticos')
    
    try:
        dragon_url = 'https://ddragon.leagueoflegends.com/api/versions.json'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(dragon_url) as response:
                if response.status == 200:
                    versions = await response.json()
                    latest_version = versions[0]
                    print(f'✅ Data Dragon funcionando! Versão: {latest_version}')
                    
                    # Testa dados de champions
                    champ_url = f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json'
                    
                    async with session.get(champ_url) as champ_response:
                        if champ_response.status == 200:
                            champ_data = await champ_response.json()
                            champions = list(champ_data.get('data', {}).keys())
                            print(f'   🏆 {len(champions)} champions disponíveis')
                            print(f'   Exemplos: {", ".join(champions[:5])}...')
                            
                            return True
                else:
                    print(f'❌ Data Dragon: Status {response.status}')
    except Exception as e:
        print(f'❌ Erro Data Dragon: {e}')
    
    # 4. LEAGUEGRAPHS API (Terceiros - Gratuita)
    print(f'\n📡 4. TESTANDO LEAGUEGRAPHS API')
    print('URL: https://www.leagueofgraphs.com/')
    print('Status: Gratuita com limitações')
    
    try:
        # API endpoint público do LeagueOfGraphs
        lg_url = 'https://www.leagueofgraphs.com/api/champions/stats'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(lg_url) as response:
                if response.status == 200:
                    print('✅ LeagueOfGraphs API acessível!')
                    return True
                else:
                    print(f'⚠️ LeagueOfGraphs: Status {response.status}')
    except Exception as e:
        print(f'❌ Erro LeagueOfGraphs: {e}')
    
    # 5. OPGG API (Terceiros)
    print(f'\n📡 5. TESTANDO OP.GG API')
    print('URL: https://op.gg/')
    print('Status: Endpoints públicos limitados')
    
    try:
        opgg_url = 'https://op.gg/api/v1.0/internal/bypass/games/lol/champions'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(opgg_url) as response:
                if response.status == 200:
                    print('✅ OP.GG API acessível!')
                    return True
                else:
                    print(f'⚠️ OP.GG: Status {response.status}')
    except Exception as e:
        print(f'❌ Erro OP.GG: {e}')
    
    return False

async def buscar_apis_alternativas():
    """Busca outras APIs disponíveis"""
    
    print(f'\n' + '=' * 60)
    print(f'🌐 APIS ALTERNATIVAS ENCONTRADAS NA WEB:')
    print('=' * 60)
    
    apis_alternativas = [
        {
            'nome': 'Riot Live Client Data API',
            'url': 'https://127.0.0.1:2999/liveclientdata/',
            'custo': 'Gratuita',
            'dados': 'Composições ao vivo (requer cliente local)',
            'vantagem': '✅ Dados em tempo real completos',
            'desvantagem': '❌ Só funciona localmente'
        },
        {
            'nome': 'Riot Esports API',
            'url': 'https://esports-api.lolesports.com/',
            'custo': 'Gratuita',
            'dados': 'Dados de partidas profissionais',
            'vantagem': '✅ Dados oficiais de esports',
            'desvantagem': '❌ Pode não ter composições detalhadas'
        },
        {
            'nome': 'LoL Esports Stats API',
            'url': 'https://lolesports.com/api-docs',
            'custo': 'Gratuita',
            'dados': 'Estatísticas de esports',
            'vantagem': '✅ Específico para competições',
            'desvantagem': '❌ Rate limits'
        },
        {
            'nome': 'OPGG Public Endpoints',
            'url': 'https://op.gg/api/',
            'custo': 'Gratuita (limitada)',
            'dados': 'Builds e composições populares',
            'vantagem': '✅ Dados de meta atual',
            'desvantagem': '❌ Não oficial, pode mudar'
        },
        {
            'nome': 'U.GG API',
            'url': 'https://u.gg/api',
            'custo': 'Gratuita (limitada)',
            'dados': 'Stats de champions e builds',
            'vantagem': '✅ Dados analíticos',
            'desvantagem': '❌ Rate limits agressivos'
        },
        {
            'nome': 'LoLalytics Scraping',
            'url': 'https://lolalytics.com/',
            'custo': 'Gratuita (scraping)',
            'dados': 'Meta analytics',
            'vantagem': '✅ Dados detalhados',
            'desvantagem': '❌ Contra ToS, instável'
        }
    ]
    
    for api in apis_alternativas:
        print(f"\n🔌 {api['nome']}")
        print(f"   URL: {api['url']}")
        print(f"   💰 Custo: {api['custo']}")
        print(f"   📊 Dados: {api['dados']}")
        print(f"   {api['vantagem']}")
        print(f"   {api['desvantagem']}")

async def implementar_solucao_live_client():
    """Implementa solução usando Live Client Data API"""
    
    print(f'\n' + '=' * 60)
    print(f'🚀 SOLUÇÃO RECOMENDADA: LIVE CLIENT DATA API')
    print('=' * 60)
    
    print(f'📋 IMPLEMENTAÇÃO:')
    print(f'1. 🎮 Detectar se há jogo LoL rodando localmente')
    print(f'2. 📡 Conectar na Live Client Data API (127.0.0.1:2999)')
    print(f'3. 📊 Obter dados completos: /liveclientdata/allgamedata')
    print(f'4. 🏆 Extrair composições de ambos os times')
    print(f'5. 🤖 Gerar tip com dados completos')
    
    codigo_exemplo = '''
# EXEMPLO DE IMPLEMENTAÇÃO:
async def get_live_compositions():
    """Obtém composições do cliente local"""
    try:
        url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    players = data.get('allPlayers', [])
                    team1_comp = []
                    team2_comp = []
                    
                    for player in players:
                        champion = player.get('championName')
                        team = player.get('team')
                        
                        if team == 'ORDER':
                            team1_comp.append(champion)
                        else:
                            team2_comp.append(champion)
                    
                    return team1_comp, team2_comp
    except:
        return None, None
    '''
    
    print(f'\n📝 CÓDIGO DE EXEMPLO:')
    print(codigo_exemplo)
    
    print(f'\n✅ VANTAGENS:')
    print(f'• 100% gratuita')
    print(f'• Dados oficiais da Riot')
    print(f'• Composições completas e atualizadas')
    print(f'• Sem rate limits')
    print(f'• Dados em tempo real')
    
    print(f'\n⚠️ LIMITAÇÕES:')
    print(f'• Funciona apenas localmente')
    print(f'• Requer jogo LoL rodando')
    print(f'• Não serve para dados remotos')

async def main():
    """Execução principal"""
    
    print('🔍 BUSCANDO APIS GRATUITAS PARA COMPOSIÇÕES DE DRAFT')
    
    # Testa APIs disponíveis
    await testar_apis_gratuitas()
    
    # Lista APIs alternativas
    await buscar_apis_alternativas()
    
    # Propõe solução
    await implementar_solucao_live_client()
    
    print(f'\n' + '=' * 60)
    print(f'📋 CONCLUSÃO:')
    print(f'✅ Live Client Data API é a melhor opção gratuita')
    print(f'✅ Riot Esports API como backup')
    print(f'✅ Data Dragon para dados estáticos')
    print(f'⚠️ APIs de terceiros têm limitações')

if __name__ == '__main__':
    asyncio.run(main()) 