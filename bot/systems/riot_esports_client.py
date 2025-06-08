"""
Cliente otimizado para Riot Esports GraphQL API
Focado em obter dados de draft (picks & bans) em tempo real
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EsportsDraftData:
    """Dados de draft obtidos da Riot Esports API"""
    team1_composition: List[str]
    team2_composition: List[str]
    team1_bans: List[str]
    team2_bans: List[str]
    team1_name: str
    team2_name: str
    game_number: int
    league_name: str
    source: str = "riot_esports"
    draft_complete: bool = False
    game_state: str = "unknown"
    confidence: float = 1.0

class RiotEsportsClient:
    """Cliente para Riot Esports GraphQL API - Dados de Draft em Tempo Real"""
    
    def __init__(self):
        self.session = None
        self.base_url = "https://esports-api.lolesports.com/persisted/gw"
        # X-API-Key extraída do site oficial lolesports.com
        self.headers = {
            "x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_live_draft_data(self, match_data) -> Optional[EsportsDraftData]:
        """
        Método principal para obter dados de draft de partidas ao vivo
        Otimizado para o sistema PredictLoL
        """
        try:
            # 1. Busca partidas ao vivo
            live_events = await self._get_live_events()
            
            if not live_events:
                logger.debug("❌ Nenhuma partida ao vivo encontrada")
                return None
            
            # 2. Encontra a partida correspondente
            target_event = self._find_matching_event(live_events, match_data)
            
            if not target_event:
                logger.debug("❌ Partida não encontrada nos eventos ao vivo")
                return None
            
            # 3. Obtém dados detalhados do draft
            draft_data = await self._get_event_draft_details(target_event)
            
            if draft_data and draft_data.draft_complete:
                logger.info(f"✅ Draft completo obtido: {draft_data.team1_name} vs {draft_data.team2_name}")
                return draft_data
            
            return draft_data
            
        except Exception as e:
            logger.error(f"Erro ao obter dados de draft: {e}")
            return None
    
    async def _get_live_events(self) -> List[Dict]:
        """Obtém lista de eventos/partidas ao vivo"""
        try:
            url = f"{self.base_url}/getLive"
            params = {"hl": "pt-BR"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get("data", {}).get("schedule", {}).get("events", [])
                    
                    # Filtra apenas eventos em progresso
                    live_events = [
                        event for event in events 
                        if event.get("state") in ["inProgress", "completed"]
                    ]
                    
                    logger.debug(f"🔍 Encontrados {len(live_events)} eventos ao vivo")
                    return live_events
                else:
                    logger.warning(f"⚠️ Erro na API: {response.status}")
                    
        except Exception as e:
            logger.error(f"Erro ao buscar eventos ao vivo: {e}")
        
        return []
    
    def _find_matching_event(self, live_events: List[Dict], match_data) -> Optional[Dict]:
        """Encontra o evento correspondente ao match_data"""
        if not hasattr(match_data, 'team1_name') or not hasattr(match_data, 'team2_name'):
            return None
        
        team1_target = match_data.team1_name.lower().strip()
        team2_target = match_data.team2_name.lower().strip()
        
        for event in live_events:
            try:
                teams = event.get("match", {}).get("teams", [])
                if len(teams) >= 2:
                    team1_api = teams[0].get("name", "").lower().strip()
                    team2_api = teams[1].get("name", "").lower().strip()
                    
                    # Verifica correspondência (ordem pode variar)
                    if ((team1_target in team1_api or team1_api in team1_target) and
                        (team2_target in team2_api or team2_api in team2_target)) or \
                       ((team1_target in team2_api or team2_api in team1_target) and
                        (team2_target in team1_api or team1_api in team2_target)):
                        
                        logger.debug(f"✅ Partida encontrada: {team1_api} vs {team2_api}")
                        return event
                        
            except Exception as e:
                logger.debug(f"Erro ao processar evento: {e}")
                continue
        
        return None
    
    async def _get_event_draft_details(self, event: Dict) -> Optional[EsportsDraftData]:
        """Obtém detalhes do draft do evento"""
        try:
            # Informações básicas do evento
            teams = event.get("match", {}).get("teams", [])
            league_name = event.get("league", {}).get("name", "Unknown")
            
            if len(teams) < 2:
                return None
            
            team1_name = teams[0].get("name", "Team1")
            team2_name = teams[1].get("name", "Team2")
            
            # Busca games ativos
            games = event.get("match", {}).get("games", [])
            active_game = None
            game_number = 1
            
            for game in games:
                state = game.get("state", "")
                if state in ["inProgress", "completed"]:
                    active_game = game
                    game_number = game.get("number", 1)
                    break
            
            if not active_game:
                logger.debug("❌ Nenhum game ativo encontrado")
                return None
            
            # Obtém dados detalhados do game usando getGameDetails
            game_id = active_game.get("id")
            if game_id:
                detailed_data = await self._get_game_details(game_id)
                if detailed_data:
                    detailed_data.team1_name = team1_name
                    detailed_data.team2_name = team2_name
                    detailed_data.game_number = game_number
                    detailed_data.league_name = league_name
                    return detailed_data
            
            # Fallback: usa dados básicos disponíveis
            teams_data = active_game.get("teams", [])
            if len(teams_data) >= 2:
                team1_comp = self._extract_composition(teams_data[0])
                team2_comp = self._extract_composition(teams_data[1])
                team1_bans = self._extract_bans(teams_data[0])
                team2_bans = self._extract_bans(teams_data[1])
                
                draft_complete = (len(team1_comp) == 5 and len(team2_comp) == 5)
                
                return EsportsDraftData(
                    team1_composition=team1_comp,
                    team2_composition=team2_comp,
                    team1_bans=team1_bans,
                    team2_bans=team2_bans,
                    team1_name=team1_name,
                    team2_name=team2_name,
                    game_number=game_number,
                    league_name=league_name,
                    draft_complete=draft_complete,
                    game_state=active_game.get("state", "unknown")
                )
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do draft: {e}")
        
        return None
    
    async def _get_game_details(self, game_id: str) -> Optional[EsportsDraftData]:
        """Obtém detalhes específicos do game via getGameDetails"""
        try:
            url = f"{self.base_url}/getGameDetails"
            params = {"id": game_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    game_data = data.get("data", {}).get("game", {})
                    
                    teams = game_data.get("teams", [])
                    if len(teams) >= 2:
                        team1_comp = self._extract_composition(teams[0])
                        team2_comp = self._extract_composition(teams[1])
                        team1_bans = self._extract_bans(teams[0])
                        team2_bans = self._extract_bans(teams[1])
                        
                        draft_complete = (len(team1_comp) == 5 and len(team2_comp) == 5)
                        
                        return EsportsDraftData(
                            team1_composition=team1_comp,
                            team2_composition=team2_comp,
                            team1_bans=team1_bans,
                            team2_bans=team2_bans,
                            team1_name="",  # Será preenchido depois
                            team2_name="",  # Será preenchido depois
                            game_number=0,  # Será preenchido depois
                            league_name="", # Será preenchido depois
                            draft_complete=draft_complete,
                            game_state=game_data.get("state", "unknown")
                        )
                        
        except Exception as e:
            logger.debug(f"Erro ao obter detalhes do game: {e}")
        
        return None
    
    def _extract_composition(self, team_data: Dict) -> List[str]:
        """Extrai composição (picks) de um time"""
        composition = []
        
        # Busca em diferentes estruturas possíveis
        participants = team_data.get("participants", [])
        for participant in participants:
            champion = participant.get("championId")
            if champion:
                # Converte ID para nome se necessário
                champion_name = self._champion_id_to_name(champion)
                if champion_name:
                    composition.append(champion_name)
        
        return composition
    
    def _extract_bans(self, team_data: Dict) -> List[str]:
        """Extrai bans de um time"""
        bans = []
        
        # Busca estrutura de bans
        team_bans = team_data.get("bans", [])
        for ban in team_bans:
            champion = ban.get("championId")
            if champion:
                champion_name = self._champion_id_to_name(champion)
                if champion_name:
                    bans.append(champion_name)
        
        return bans
    
    def _champion_id_to_name(self, champion_id) -> str:
        """Converte ID do campeão para nome (implementação básica)"""
        # Se já é string, retorna
        if isinstance(champion_id, str):
            return champion_id
        
        # Mapeamento básico (expandir conforme necessário)
        champion_map = {
            1: "Annie", 2: "Olaf", 3: "Galio", 4: "TwistedFate", 5: "XinZhao",
            # ... adicionar mais conforme necessário
        }
        
        return champion_map.get(champion_id, f"Champion_{champion_id}")


# Função helper para integração com sistema existente
async def get_esports_draft_data(match_data) -> Optional[EsportsDraftData]:
    """
    Função helper para obter dados de draft da Riot Esports API
    Compatível com sistema existente AlternativeAPIClient
    """
    async with RiotEsportsClient() as client:
        return await client.get_live_draft_data(match_data) 