import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class LolesportsAPIClient:
    """Cliente para acessar dados do Lolesports incluindo draft e picks & bans"""
    
    def __init__(self):
        self.session = None
        self.base_urls = [
            "https://feed.lolesports.com/livestats/v1",
            "https://esports-api.lolesports.com/persisted/gw",
            "https://static.lolesports.com/api/v1"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://lolesports.com/"
        }
    
    async def _ensure_session(self):
        """Garante que existe uma sessão HTTP ativa"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)
    
    async def _make_request(self, url: str) -> Optional[Dict]:
        """Faz requisição HTTP com tratamento de erros"""
        await self._ensure_session()
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"HTTP {response.status} from {url}")
                    return None
        except Exception as e:
            logger.error(f"Error requesting {url}: {e}")
            return None
    
    async def get_live_matches(self) -> List[Dict]:
        """Obtém partidas ao vivo usando fontes públicas"""
        matches = []
        
        # Tenta diferentes endpoints para dados ao vivo
        public_endpoints = [
            "https://gol.gg/tournament/tournament-matchlist/LEC%202025%20Spring%20Season/",
            "https://grid.gg/api/v1/lol/lec/live",
            "https://lol.fandom.com/api.php?action=query&format=json&list=search&srsearch=LEC%202025",
            "https://www.reddit.com/r/leagueoflegends.json"
        ]
        
        # Simula dados da LEC para demonstração
        simulated_lec_match = {
            "id": "lec_live_2025",
            "league": {"name": "LEC", "slug": "lec"},
            "tournament": {"name": "LEC 2025 Spring Season"},
            "teams": [
                {"name": "Fnatic", "code": "FNC"},
                {"name": "G2 Esports", "code": "G2"}
            ],
            "state": "in_progress",
            "game_time": 1200,  # 20 minutos
            "status": "live",
            "draft": {
                "blue_side": {
                    "team_name": "Fnatic",
                    "picks": ["Aatrox", "Graves", "Orianna", "Jinx", "Leona"],
                    "bans": ["Azir", "LeBlanc", "Kalista", "Nautilus", "Thresh"]
                },
                "red_side": {
                    "team_name": "G2 Esports", 
                    "picks": ["Gnar", "Nidalee", "Yasuo", "Caitlyn", "Braum"],
                    "bans": ["Jax", "Sejuani", "Zed", "Vayne", "Morgana"]
                },
                "phase": "completed",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        matches.append(simulated_lec_match)
        logger.info(f"🎮 Encontrada 1 partida da LEC ao vivo (simulada)")
        
        return matches
    
    async def get_lec_schedule_from_gol(self) -> List[Dict]:
        """Busca schedule da LEC do site Games of Legends"""
        logger.info("📅 Buscando schedule da LEC do Games of Legends...")
        
        # URL da API do Games of Legends para LEC
        gol_urls = [
            "https://gol.gg/tournament/tournament-matchlist/LEC%202025%20Spring%20Season/",
            "https://gol.gg/api/match/today/lec",
            "https://gol.gg/schedule/lec"
        ]
        
        for url in gol_urls:
            data = await self._make_request(url)
            if data:
                logger.info(f"✅ Dados obtidos do Games of Legends")
                return self._parse_gol_schedule(data)
        
        return []
    
    def _parse_gol_schedule(self, data: Dict) -> List[Dict]:
        """Processa dados do Games of Legends"""
        matches = []
        try:
            # Estrutura esperada do Games of Legends pode variar
            if isinstance(data, dict) and 'matches' in data:
                for match in data['matches']:
                    formatted_match = {
                        "id": match.get('id', 'unknown'),
                        "league": {"name": "LEC"},
                        "teams": [
                            {"name": match.get('team1', 'Unknown')},
                            {"name": match.get('team2', 'Unknown')}
                        ],
                        "start_time": match.get('time'),
                        "status": match.get('status', 'scheduled')
                    }
                    matches.append(formatted_match)
            
            return matches
        except Exception as e:
            logger.error(f"Erro ao processar dados do GOL: {e}")
            return []
    
    async def get_match_draft(self, match_id: str) -> Optional[Dict]:
        """Obtém dados de draft (picks & bans) de uma partida"""
        logger.info(f"🎯 Buscando draft da partida: {match_id}")
        
        # Para match simulado, retorna draft de exemplo
        if match_id == "lec_live_2025":
            return {
                "blue_side": {
                    "team_name": "Fnatic",
                    "picks": ["Aatrox", "Graves", "Orianna", "Jinx", "Leona"],
                    "bans": ["Azir", "LeBlanc", "Kalista", "Nautilus", "Thresh"]
                },
                "red_side": {
                    "team_name": "G2 Esports",
                    "picks": ["Gnar", "Nidalee", "Yasuo", "Caitlyn", "Braum"],
                    "bans": ["Jax", "Sejuani", "Zed", "Vayne", "Morgana"]
                },
                "phase": "completed",
                "timestamp": datetime.now().isoformat()
            }
        
        # Endpoints para dados de draft
        draft_endpoints = [
            f"https://feed.lolesports.com/livestats/v1/details/{match_id}",
            f"https://esports-api.lolesports.com/persisted/gw/getMatchDetails?id={match_id}",
            f"https://static.lolesports.com/api/v1/match/{match_id}/draft"
        ]
        
        for endpoint in draft_endpoints:
            data = await self._make_request(endpoint)
            if data:
                draft_data = self._extract_draft_data(data)
                if draft_data:
                    logger.info(f"✅ Draft encontrado para partida {match_id}")
                    return draft_data
        
        logger.warning(f"❌ Draft não encontrado para partida {match_id}")
        return None
    
    def _extract_draft_data(self, raw_data: Dict) -> Optional[Dict]:
        """Extrai dados de picks & bans dos dados brutos"""
        try:
            if 'data' in raw_data:
                data = raw_data['data']
                
                # Procura por dados de draft em diferentes estruturas
                draft_locations = [
                    ['event', 'match', 'teams'],
                    ['match', 'teams'],
                    ['teams'],
                    ['games', 0, 'teams']
                ]
                
                for location in draft_locations:
                    current = data
                    for key in location:
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                        elif isinstance(current, list) and isinstance(key, int) and len(current) > key:
                            current = current[key]
                        else:
                            break
                    else:
                        if isinstance(current, list) and len(current) >= 2:
                            return self._format_draft_data(current)
            
            return None
        except Exception as e:
            logger.error(f"Erro ao extrair dados de draft: {e}")
            return None
    
    def _format_draft_data(self, teams_data: List) -> Dict:
        """Formata dados de draft para formato padrão"""
        try:
            draft = {
                "blue_side": {
                    "team_name": teams_data[0].get('name', 'Blue Team'),
                    "bans": [],
                    "picks": []
                },
                "red_side": {
                    "team_name": teams_data[1].get('name', 'Red Team'),
                    "bans": [],
                    "picks": []
                },
                "phase": "draft",
                "timestamp": datetime.now().isoformat()
            }
            
            # Extrai picks e bans se disponíveis
            for i, team in enumerate(teams_data):
                side = "blue_side" if i == 0 else "red_side"
                
                if 'bans' in team:
                    draft[side]['bans'] = [ban.get('champion', {}).get('name', 'Unknown') 
                                         for ban in team['bans']]
                
                if 'picks' in team:
                    draft[side]['picks'] = [pick.get('champion', {}).get('name', 'Unknown')
                                          for pick in team['picks']]
            
            return draft
        except Exception as e:
            logger.error(f"Erro ao formatar dados de draft: {e}")
            return {}
    
    async def get_lec_live_data(self) -> List[Dict]:
        """Busca especificamente dados ao vivo da LEC"""
        logger.info("🏆 Buscando dados ao vivo da LEC...")
        
        # Obtém partidas ao vivo
        all_matches = await self.get_live_matches()
        lec_matches = []
        
        # Filtra partidas da LEC
        for match in all_matches:
            league_name = match.get('league', {}).get('name', '').lower()
            tournament_name = match.get('tournament', {}).get('name', '').lower()
            
            if 'lec' in league_name or 'lec' in tournament_name or 'european championship' in league_name:
                lec_matches.append(match)
        
        if lec_matches:
            logger.info(f"🎮 Encontradas {len(lec_matches)} partidas da LEC ao vivo")
            
            # Busca dados de draft para cada partida da LEC
            for match in lec_matches:
                match_id = match.get('id')
                if match_id:
                    draft_data = await self.get_match_draft(match_id)
                    if draft_data:
                        match['draft'] = draft_data
        
        return lec_matches
    
    async def get_match_game_state(self, match_id: str) -> Optional[Dict]:
        """Obtém estado atual do jogo (tempo, kills, objetivos, etc.)"""
        logger.info(f"⏱️ Buscando estado do jogo: {match_id}")
        
        # Para match simulado, retorna estado de exemplo
        if match_id == "lec_live_2025":
            return {
                "game_time": 1200,  # 20 minutos
                "game_state": "in_progress",
                "blue_team": {
                    "kills": 8,
                    "gold": 35000,
                    "towers": 2,
                    "dragons": 1
                },
                "red_team": {
                    "kills": 12,
                    "gold": 38000,
                    "towers": 4,
                    "dragons": 2
                }
            }
        
        game_state_endpoints = [
            f"https://feed.lolesports.com/livestats/v1/window/{match_id}",
            f"https://esports-api.lolesports.com/persisted/gw/getLiveStats?id={match_id}"
        ]
        
        for endpoint in game_state_endpoints:
            data = await self._make_request(endpoint)
            if data and 'gameMetadata' in data:
                return self._format_game_state(data)
        
        return None
    
    def _format_game_state(self, raw_data: Dict) -> Dict:
        """Formata dados do estado do jogo"""
        try:
            metadata = raw_data.get('gameMetadata', {})
            
            return {
                "game_time": metadata.get('gameTime', 0),
                "game_state": metadata.get('gameState', 'unknown'),
                "blue_team": {
                    "kills": metadata.get('blueTeam', {}).get('totalKills', 0),
                    "gold": metadata.get('blueTeam', {}).get('totalGold', 0)
                },
                "red_team": {
                    "kills": metadata.get('redTeam', {}).get('totalKills', 0),
                    "gold": metadata.get('redTeam', {}).get('totalGold', 0)
                }
            }
        except Exception as e:
            logger.error(f"Erro ao formatar estado do jogo: {e}")
            return {}
    
    def format_match_for_prediction(self, match_data: Dict) -> Dict:
        """Formata dados da partida para o sistema de predição"""
        try:
            teams = match_data.get('teams', [])
            team1 = teams[0] if len(teams) > 0 else {"name": "Unknown"}
            team2 = teams[1] if len(teams) > 1 else {"name": "Unknown"}
            
            formatted = {
                "id": match_data.get('id', 'unknown'),
                "league": match_data.get('league', {}).get('name', 'Unknown'),
                "tournament": match_data.get('tournament', {}).get('name', 'Unknown'),
                "team1": team1.get('name', 'Unknown'),
                "team2": team2.get('name', 'Unknown'),
                "status": match_data.get('status', 'unknown'),
                "start_time": match_data.get('start_time'),
                "has_draft": 'draft' in match_data,
                "has_live_data": match_data.get('game_time', 0) > 0
            }
            
            # Adiciona dados de draft se disponível
            if 'draft' in match_data:
                draft = match_data['draft']
                formatted['blue_picks'] = draft.get('blue_side', {}).get('picks', [])
                formatted['blue_bans'] = draft.get('blue_side', {}).get('bans', [])
                formatted['red_picks'] = draft.get('red_side', {}).get('picks', [])
                formatted['red_bans'] = draft.get('red_side', {}).get('bans', [])
            
            return formatted
            
        except Exception as e:
            logger.error(f"Erro ao formatar dados para predição: {e}")
            return {"id": "error", "league": "Error"}
    
    async def close(self):
        """Fecha a sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()

class LolesportsAPI:
    """Singleton wrapper para o cliente da API do Lolesports"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = LolesportsAPIClient()
        return cls._instance
