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
            ("Live Client Data API", self._get_live_client_data),
            ("Riot Esports API", self._get_esports_data),
            ("LoL Esports API", self._get_lol_esports_data),
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
        """Tenta obter dados da LoL Esports API oficial"""
        try:
            # API endpoint público
            url = 'https://esports-api.lolesports.com/persisted/gw/getLive'
            params = {'hl': 'en-US'}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    events = data.get('data', {}).get('schedule', {}).get('events', [])
                    
                    for event in events:
                        if event.get('state') == 'inProgress':
                            # Verifica se é o match correto
                            teams = event.get('match', {}).get('teams', [])
                            
                            if len(teams) >= 2:
                                team1_name = teams[0].get('name', '')
                                team2_name = teams[1].get('name', '')
                                
                                # Compara com match_data
                                if (hasattr(match_data, 'team1_name') and 
                                    hasattr(match_data, 'team2_name')):
                                    
                                    if (team1_name.lower() in match_data.team1_name.lower() or
                                        team2_name.lower() in match_data.team2_name.lower()):
                                        
                                        # Tenta extrair composições dos games
                                        games = event.get('match', {}).get('games', [])
                                        
                                        for game in games:
                                            if game.get('state') == 'inProgress':
                                                # Busca dados de draft
                                                draft_data = await self._get_game_draft_data(game.get('id'))
                                                if draft_data:
                                                    return draft_data
                    
        except Exception as e:
            logger.debug(f"LoL Esports API error: {e}")
        
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