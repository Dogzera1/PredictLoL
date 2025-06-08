"""
Cliente para APIs alternativas gratuitas de composições
Resolve problema quando PandaScore não retorna dados de draft
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CompositionData:
    """Dados de composição obtidos de APIs alternativas"""
    team1_composition: List[str]
    team2_composition: List[str]
    source: str
    draft_complete: bool
    game_time: float = 0.0
    game_mode: str = "UNKNOWN"
    confidence: float = 1.0

class AlternativeAPIClient:
    """Cliente para obter dados de composições de APIs gratuitas"""
    
    def __init__(self):
        self.session = None
        self._champion_id_map = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_compositions_for_match(self, match_data) -> Optional[CompositionData]:
        """
        Método principal para obter composições usando APIs alternativas
        Tenta múltiplas APIs em ordem de prioridade
        """
        methods = [
            ("Riot Esports GraphQL", self._get_lol_esports_data),  # PRIORIDADE 1: Melhor API
            ("Riot Esports API", self._get_esports_data),
            ("Live Client Data API", self._get_live_client_data),
            ("Game Stats Scraping", self._scrape_game_stats)
        ]
        
        for api_name, method in methods:
            try:
                logger.debug(f"🔍 Tentando {api_name}...")
                
                result = await method(match_data)
                
                if result and result.draft_complete:
                    logger.info(f"✅ Composições obtidas via {api_name}")
                    return result
                elif result:
                    logger.debug(f"⏳ Dados parciais de {api_name}")
                else:
                    logger.debug(f"❌ {api_name} não disponível")
                    
            except Exception as e:
                logger.debug(f"⚠️ Erro em {api_name}: {e}")
                continue
        
        logger.warning("❌ Nenhuma API alternativa forneceu composições completas")
        return None
    
    async def _get_live_client_data(self, match_data) -> Optional[CompositionData]:
        """Tenta obter dados do Live Client Data API (127.0.0.1:2999)"""
        try:
            url = 'https://127.0.0.1:2999/liveclientdata/allgamedata'
            
            async with self.session.get(url, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extrai dados dos players
                    players = data.get('allPlayers', [])
                    team1_comp = []
                    team2_comp = []
                    
                    for player in players:
                        champion = player.get('championName')
                        team = player.get('team')
                        
                        if champion:
                            if team == 'ORDER':
                                team1_comp.append(champion)
                            elif team == 'CHAOS':
                                team2_comp.append(champion)
                    
                    # Dados do jogo
                    game_data = data.get('gameData', {})
                    game_time = game_data.get('gameTime', 0)
                    game_mode = game_data.get('gameMode', 'CLASSIC')
                    
                    if len(team1_comp) == 5 and len(team2_comp) == 5:
                        return CompositionData(
                            team1_composition=team1_comp,
                            team2_composition=team2_comp,
                            source='live_client',
                            draft_complete=True,
                            game_time=game_time,
                            game_mode=game_mode,
                            confidence=1.0
                        )
                    
        except Exception as e:
            logger.debug(f"Live Client API error: {e}")
        
        return None
    
    async def _get_esports_data(self, match_data) -> Optional[CompositionData]:
        """Tenta obter dados da Riot Esports API"""
        try:
            # Endpoint público da Riot Esports
            match_id = getattr(match_data, 'match_id', None)
            if not match_id:
                return None
            
            url = f'https://feed.lolesports.com/livestats/v1/details/{match_id}'
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extrai participantes
                    participants = data.get('participants', {})
                    
                    team1_comp = []
                    team2_comp = []
                    
                    for player_id, player_data in participants.items():
                        champion_id = player_data.get('championId')
                        team_id = player_data.get('teamId')
                        
                        if champion_id and team_id:
                            # Converte champion ID para nome
                            champion_name = await self._get_champion_name(champion_id)
                            if champion_name:
                                if team_id == '100':
                                    team1_comp.append(champion_name)
                                else:
                                    team2_comp.append(champion_name)
                    
                    if len(team1_comp) == 5 and len(team2_comp) == 5:
                        return CompositionData(
                            team1_composition=team1_comp,
                            team2_composition=team2_comp,
                            source='esports_api',
                            draft_complete=True,
                            confidence=0.9
                        )
                    
        except Exception as e:
            logger.debug(f"Esports API error: {e}")
        
        return None
    
    async def _get_lol_esports_data(self, match_data) -> Optional[CompositionData]:
        """MELHORADO: Riot Esports GraphQL API - Dados precisos de draft em tempo real"""
        try:
            # API endpoint oficial com X-API-Key do site lolesports.com
            url = 'https://esports-api.lolesports.com/persisted/gw/getLive'
            params = {'hl': 'pt-BR'}
            
            # Headers com X-API-Key extraída do site oficial
            headers = {
                "x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    events = data.get('data', {}).get('schedule', {}).get('events', [])
                    
                    for event in events:
                        if event.get('state') in ['inProgress', 'completed']:
                            # Verifica se é o match correto
                            teams = event.get('match', {}).get('teams', [])
                            
                            if len(teams) >= 2:
                                team1_name = teams[0].get('name', '')
                                team2_name = teams[1].get('name', '')
                                
                                # Compara com match_data (melhor matching)
                                if (hasattr(match_data, 'team1_name') and 
                                    hasattr(match_data, 'team2_name')):
                                    
                                    team1_target = match_data.team1_name.lower().strip()
                                    team2_target = match_data.team2_name.lower().strip()
                                    team1_api = team1_name.lower().strip()
                                    team2_api = team2_name.lower().strip()
                                    
                                    # Verifica correspondência (ordem pode variar)
                                    if ((team1_target in team1_api or team1_api in team1_target) and
                                        (team2_target in team2_api or team2_api in team2_target)) or \
                                       ((team1_target in team2_api or team2_api in team1_target) and
                                        (team2_target in team1_api or team1_api in team2_target)):
                                        
                                        logger.info(f"✅ PARTIDA ENCONTRADA: {team1_api} vs {team2_api}")
                                        
                                        # Extrai composições dos games
                                        games = event.get('match', {}).get('games', [])
                                        
                                        for game in games:
                                            if game.get('state') in ['inProgress', 'completed']:
                                                # Obtém dados detalhados do game
                                                game_id = game.get('id')
                                                if game_id:
                                                    detailed_comp = await self._get_game_draft_details(game_id, headers)
                                                    if detailed_comp:
                                                        return detailed_comp
                                                
                                                # Fallback: extrai do que está disponível
                                                team1_comp, team2_comp = await self._extract_compositions_from_game(game)
                                                
                                                if len(team1_comp) == 5 and len(team2_comp) == 5:
                                                    return CompositionData(
                                                        team1_composition=team1_comp,
                                                        team2_composition=team2_comp,
                                                        source='riot_esports_graphql',
                                                        draft_complete=True,
                                                        confidence=0.95
                                                    )
                else:
                    logger.warning(f"⚠️ Riot Esports API retornou status: {response.status}")
                    
        except Exception as e:
            logger.debug(f"Riot Esports GraphQL API error: {e}")
        
        return None
    
    async def _get_game_draft_details(self, game_id: str, headers: dict) -> Optional[CompositionData]:
        """Obtém detalhes específicos do draft via getGameDetails"""
        try:
            url = 'https://esports-api.lolesports.com/persisted/gw/getGameDetails'
            params = {'id': game_id}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    game_data = data.get('data', {}).get('game', {})
                    
                    teams = game_data.get('teams', [])
                    if len(teams) >= 2:
                        team1_comp = self._extract_team_composition(teams[0])
                        team2_comp = self._extract_team_composition(teams[1])
                        
                        if len(team1_comp) == 5 and len(team2_comp) == 5:
                            logger.info(f"✅ DRAFT COMPLETO via getGameDetails: {len(team1_comp + team2_comp)}/10 champions")
                            return CompositionData(
                                team1_composition=team1_comp,
                                team2_composition=team2_comp,
                                source='riot_esports_details',
                                draft_complete=True,
                                confidence=0.98
                            )
                        
        except Exception as e:
            logger.debug(f"Game details error: {e}")
        
        return None
    
    def _extract_team_composition(self, team_data: dict) -> List[str]:
        """Extrai composição de um time da estrutura da API"""
        composition = []
        
        # Busca participantes
        participants = team_data.get('participants', [])
        for participant in participants:
            # Tenta diferentes campos para o campeão
            champion = (participant.get('championId') or 
                       participant.get('champion') or 
                       participant.get('championName'))
            
            if champion:
                # Se é ID numérico, converte para nome
                if isinstance(champion, int):
                    champion_name = self._champion_id_to_name(champion)
                else:
                    champion_name = str(champion)
                
                if champion_name and champion_name not in composition:
                    composition.append(champion_name)
        
        return composition
    
    async def _extract_compositions_from_game(self, game: dict) -> Tuple[List[str], List[str]]:
        """Extrai composições de ambos os times do game"""
        team1_comp = []
        team2_comp = []
        
        teams = game.get('teams', [])
        if len(teams) >= 2:
            team1_comp = self._extract_team_composition(teams[0])
            team2_comp = self._extract_team_composition(teams[1])
        
        return team1_comp, team2_comp
    
    def _champion_id_to_name(self, champion_id: int) -> str:
        """Converte ID do campeão para nome usando mapeamento básico"""
        # Mapeamento dos IDs mais comuns (expandir conforme necessário)
        champion_map = {
            1: "Annie", 2: "Olaf", 3: "Galio", 4: "TwistedFate", 5: "XinZhao",
            6: "Urgot", 7: "LeBlanc", 8: "Vladimir", 9: "Fiddlesticks", 10: "Kayle",
            11: "MasterYi", 12: "Alistar", 13: "Ryze", 14: "Sion", 15: "Sivir",
            16: "Soraka", 17: "Teemo", 18: "Tristana", 19: "Warwick", 20: "Nunu",
            21: "MissFortune", 22: "Ashe", 23: "Tryndamere", 24: "Jax", 25: "Morgana",
            26: "Zilean", 27: "Singed", 28: "Evelynn", 29: "Twitch", 30: "Karthus",
            31: "Chogath", 32: "Amumu", 33: "Rammus", 34: "Anivia", 35: "Shaco",
            36: "DrMundo", 37: "Sona", 38: "Kassadin", 39: "Irelia", 40: "Janna",
            41: "Gangplank", 42: "Corki", 43: "Karma", 44: "Taric", 45: "Veigar",
            48: "Trundle", 50: "Swain", 51: "Caitlyn", 53: "Blitzcrank", 54: "Malphite",
            55: "Katarina", 56: "Nocturne", 57: "Maokai", 58: "Renekton", 59: "JarvanIV",
            60: "Elise", 61: "Orianna", 62: "Wukong", 63: "Brand", 64: "LeeSin",
            67: "Vayne", 68: "Rumble", 69: "Cassiopeia", 72: "Skarner", 74: "Heimerdinger",
            75: "Nasus", 76: "Nidalee", 77: "Udyr", 78: "Poppy", 79: "Gragas",
            80: "Pantheon", 81: "Ezreal", 82: "Mordekaiser", 83: "Yorick", 84: "Akali",
            85: "Kennen", 86: "Garen", 89: "Leona", 90: "Malzahar", 91: "Talon",
            92: "Riven", 96: "KogMaw", 98: "Shen", 99: "Lux", 101: "Xerath",
            102: "Shyvana", 103: "Ahri", 104: "Graves", 105: "Fizz", 106: "Volibear",
            107: "Rengar", 110: "Varus", 111: "Nautilus", 112: "Viktor", 113: "Sejuani",
            114: "Fiora", 115: "Ziggs", 117: "Lulu", 119: "Draven", 120: "Hecarim",
            121: "Khazix", 122: "Darius", 126: "Jayce", 127: "Lissandra", 131: "Diana",
            133: "Quinn", 134: "Syndra", 136: "AurelionSol", 141: "Kayn", 142: "Zoe",
            143: "Zyra", 145: "Kaisa", 147: "Seraphine", 150: "Gnar", 154: "Zac",
            157: "Yasuo", 161: "Velkoz", 163: "Taliyah", 164: "Camille", 166: "Akshan",
            200: "Belveth", 201: "Braum", 202: "Jhin", 203: "Kindred", 221: "Zeri",
            222: "Jinx", 223: "TahmKench", 234: "Viego", 235: "Senna", 236: "Lucian",
            238: "Zed", 240: "Kled", 245: "Ekko", 246: "Qiyana", 254: "Vi",
            266: "Aatrox", 267: "Nami", 268: "Azir", 350: "Yuumi", 360: "Samira",
            412: "Thresh", 420: "Illaoi", 421: "RekSai", 427: "Ivern", 429: "Kalista",
            432: "Bard", 516: "Ornn", 517: "Sylas", 518: "Neeko", 523: "Aphelios",
            526: "Rell", 555: "Pyke", 711: "Vex", 777: "Yone", 875: "Sett",
            876: "Lillia", 887: "Gwen", 888: "Renata", 895: "Nilah", 897: "Ksante",
            901: "Smolder", 902: "Ambessa", 910: "Hwei", 950: "Naafiri"
        }
        
        return champion_map.get(champion_id, f"Champion_{champion_id}")
    
    def _match_teams_esports(self, api_teams, match_data):
        """Verifica se os times da API correspondem ao match_data com matching melhorado"""
        if not (hasattr(match_data, 'team1_name') and hasattr(match_data, 'team2_name')):
            return False
        
        team1_target = match_data.team1_name.lower().strip()
        team2_target = match_data.team2_name.lower().strip()
        team1_api = api_teams[0].get('name', '').lower().strip()
        team2_api = api_teams[1].get('name', '').lower().strip()
        
        # Verifica correspondência (ordem pode variar)
        return ((team1_target in team1_api or team1_api in team1_target) and
                (team2_target in team2_api or team2_api in team2_target)) or \
               ((team1_target in team2_api or team2_api in team1_target) and
                (team2_target in team1_api or team1_api in team2_target))
    
    async def _extract_game_compositions_esports(self, game, headers):
        """Extrai composições de um game específico da Riot Esports API"""
        try:
            # Tenta dados detalhados primeiro via getGameDetails
            game_id = game.get('id')
            if game_id:
                detailed = await self._get_detailed_compositions_esports(game_id, headers)
                if detailed:
                    return detailed
            
            # Fallback: dados básicos do game
            teams = game.get('teams', [])
            if len(teams) >= 2:
                team1_comp = self._extract_team_composition(teams[0])
                team2_comp = self._extract_team_composition(teams[1])
                
                if len(team1_comp) >= 3 and len(team2_comp) >= 3:  # Pelo menos dados parciais
                    return CompositionData(
                        team1_composition=team1_comp,
                        team2_composition=team2_comp,
                        source='riot_esports_graphql',
                        draft_complete=(len(team1_comp) == 5 and len(team2_comp) == 5),
                        confidence=0.95
                    )
        except Exception as e:
            logger.debug(f"Error extracting esports compositions: {e}")
        
        return None
    
    async def _get_detailed_compositions_esports(self, game_id: str, headers: dict) -> Optional[CompositionData]:
        """Obtém composições detalhadas via getGameDetails"""
        try:
            url = 'https://esports-api.lolesports.com/persisted/gw/getGameDetails'
            params = {'id': game_id}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    game_data = data.get('data', {}).get('game', {})
                    
                    teams = game_data.get('teams', [])
                    if len(teams) >= 2:
                        team1_comp = self._extract_team_composition(teams[0])
                        team2_comp = self._extract_team_composition(teams[1])
                        
                        if len(team1_comp) >= 3 and len(team2_comp) >= 3:
                            logger.info(f"✅ COMPOSIÇÕES DETALHADAS: T1={len(team1_comp)}, T2={len(team2_comp)}")
                            return CompositionData(
                                team1_composition=team1_comp,
                                team2_composition=team2_comp,
                                source='riot_esports_details',
                                draft_complete=(len(team1_comp) == 5 and len(team2_comp) == 5),
                                confidence=0.98
                            )
                elif response.status == 404:
                    logger.debug(f"Game {game_id} não encontrado em getGameDetails")
                else:
                    logger.debug(f"getGameDetails retornou {response.status} para game {game_id}")
                    
        except Exception as e:
            logger.debug(f"Detailed compositions error: {e}")
        
        return None
    
    async def _scrape_game_stats(self, match_data) -> Optional[CompositionData]:
        """Scraping de última instância para dados de composição"""
        try:
            # Busca por padrões conhecidos de APIs públicas
            team1_name = getattr(match_data, 'team1_name', '')
            team2_name = getattr(match_data, 'team2_name', '')
            
            if not team1_name or not team2_name:
                return None
            
            # Endpoint genérico para busca de matches
            search_urls = [
                f"https://www.op.gg/modes/pro-matches",
                f"https://gol.gg/esports/home/",
                f"https://lol.fandom.com/wiki/Special:RunQuery/TournamentStatistics"
            ]
            
            # Por ora, retorna None - implementação de scraping seria mais complexa
            # e pode violar ToS de sites
            
        except Exception as e:
            logger.debug(f"Scraping error: {e}")
        
        return None
    
    async def _get_champion_name(self, champion_id: int) -> Optional[str]:
        """Converte champion ID para nome usando Data Dragon"""
        try:
            if not self._champion_id_map:
                await self._load_champion_data()
            
            return self._champion_id_map.get(champion_id)
            
        except Exception as e:
            logger.debug(f"Champion name lookup error: {e}")
            return f"Champion_{champion_id}"
    
    async def _load_champion_data(self):
        """Carrega dados de champions do Data Dragon"""
        try:
            # Pega versão mais recente
            versions_url = 'https://ddragon.leagueoflegends.com/api/versions.json'
            
            async with self.session.get(versions_url) as response:
                if response.status == 200:
                    versions = await response.json()
                    latest_version = versions[0]
                    
                    # Carrega dados dos champions
                    champ_url = f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json'
                    
                    async with self.session.get(champ_url) as champ_response:
                        if champ_response.status == 200:
                            champ_data = await champ_response.json()
                            
                            # Cria mapeamento ID -> Nome
                            for champ_name, champ_info in champ_data['data'].items():
                                champ_id = int(champ_info['key'])
                                self._champion_id_map[champ_id] = champ_name
                            
                            logger.debug(f"Carregados {len(self._champion_id_map)} champions")
                            
        except Exception as e:
            logger.error(f"Erro ao carregar dados de champions: {e}")
    
    async def _get_game_draft_data(self, game_id: str) -> Optional[CompositionData]:
        """Obtém dados específicos de draft de um game"""
        try:
            # URL para dados específicos do game
            url = f'https://feed.lolesports.com/livestats/v1/details/{game_id}'
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Processa dados de draft específicos
                    frames = data.get('frames', [])
                    
                    # Busca pelo frame com draft completo
                    for frame in reversed(frames):  # Começa do mais recente
                        participants = frame.get('participants', {})
                        
                        if len(participants) == 10:
                            team1_comp = []
                            team2_comp = []
                            
                            for participant in participants.values():
                                champion_id = participant.get('championId')
                                team_id = participant.get('teamId')
                                
                                if champion_id and team_id:
                                    champion_name = await self._get_champion_name(champion_id)
                                    if champion_name:
                                        if team_id == '100':
                                            team1_comp.append(champion_name)
                                        else:
                                            team2_comp.append(champion_name)
                            
                            if len(team1_comp) == 5 and len(team2_comp) == 5:
                                return CompositionData(
                                    team1_composition=team1_comp,
                                    team2_composition=team2_comp,
                                    source='game_draft',
                                    draft_complete=True,
                                    confidence=0.95
                                )
                    
        except Exception as e:
            logger.debug(f"Game draft data error: {e}")
        
        return None

# Função de conveniência para uso standalone
async def get_match_compositions(match_data) -> Optional[CompositionData]:
    """Função de conveniência para obter composições de um match"""
    async with AlternativeAPIClient() as client:
        return await client.get_compositions_for_match(match_data) 