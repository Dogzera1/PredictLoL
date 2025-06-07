
# Cliente para APIs alternativas - PRONTO PARA USO
import asyncio
import aiohttp

class AlternativeAPIClient:
    """Cliente para obter dados de composições de APIs gratuitas"""
    
    async def get_compositions(self):
        """Método principal para obter composições"""
        
        async with aiohttp.ClientSession() as session:
            
            # 1. Live Client Data API
            try:
                url = 'https://127.0.0.1:2999/liveclientdata/allgamedata'
                async with session.get(url, ssl=False, timeout=2) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        players = data.get('allPlayers', [])
                        team1 = [p.get('championName') for p in players if p.get('team') == 'ORDER']
                        team2 = [p.get('championName') for p in players if p.get('team') == 'CHAOS']
                        
                        if len(team1) == 5 and len(team2) == 5:
                            return team1, team2
            except:
                pass
            
            # 2. Outros métodos podem ser adicionados aqui
            
        return None, None

# TESTE RÁPIDO
async def test():
    client = AlternativeAPIClient()
    team1, team2 = await client.get_compositions()
    
    if team1 and team2:
        print(f"Team 1: {team1}")
        print(f"Team 2: {team2}")
    else:
        print("Nenhuma composição encontrada")

if __name__ == "__main__":
    asyncio.run(test())
        