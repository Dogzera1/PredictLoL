from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientTimeout

from ..utils.constants import (
    HTTP_HEADERS, 
    MIN_ODDS, 
    MAX_ODDS,
    PANDASCORE_API_KEY,
    PANDASCORE_BASE_URL
)
from ..utils.helpers import normalize_team_name, teams_similarity, validate_odds
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class PandaScoreAPIError(Exception):
    """Exceção customizada para erros da API do PandaScore"""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class PandaScoreRateLimiter:
    """Sistema de rate limiting para PandaScore API"""

    def __init__(self, requests_per_second: int = 10, requests_per_hour: int = 1000):
        self.requests_per_second = requests_per_second
        self.requests_per_hour = requests_per_hour
        self.second_window: List[float] = []
        self.hour_window: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Aguarda até que seja seguro fazer uma requisição"""
        async with self._lock:
            now = time.time()

            # Limpa janelas antigas
            self.second_window = [t for t in self.second_window if now - t < 1.0]
            self.hour_window = [t for t in self.hour_window if now - t < 3600.0]

            # Verifica se precisa aguardar
            if len(self.second_window) >= self.requests_per_second:
                sleep_time = 1.0 - (now - self.second_window[0])
                if sleep_time > 0:
                    logger.debug(f"PandaScore rate limit: aguardando {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)

            if len(self.hour_window) >= self.requests_per_hour:
                sleep_time = 3600.0 - (now - self.hour_window[0])
                if sleep_time > 0:
                    logger.warning(f"PandaScore rate limit: aguardando {sleep_time:.2f}s (janela 1h)")
                    await asyncio.sleep(sleep_time)

            # Registra a requisição
            now = time.time()
            self.second_window.append(now)
            self.hour_window.append(now)


class PandaScoreAPIClient:
    """Cliente profissional para PandaScore API - odds de esports"""

    BASE_URL = PANDASCORE_BASE_URL
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or PANDASCORE_API_KEY
        if not self.api_key:
            raise ValueError("PANDASCORE_API_KEY é obrigatória")

        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = PandaScoreRateLimiter()

        # Headers padrão
        self.headers = {
            **HTTP_HEADERS,
            "Authorization": f"Bearer {self.api_key}",
        }

        logger.info("PandaScoreAPIClient inicializado com sucesso")

    async def __aenter__(self) -> PandaScoreAPIClient:
        """Context manager entry"""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        await self.close_session()

    async def start_session(self) -> None:
        """Inicia sessão HTTP"""
        if not self.session or self.session.closed:
            timeout = ClientTimeout(total=10.0)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=aiohttp.TCPConnector(limit=50, limit_per_host=10),
            )
            logger.debug("Sessão HTTP do PandaScore iniciada")

    async def close_session(self) -> None:
        """Fecha sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Sessão HTTP do PandaScore fechada")

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """Faz requisição HTTP com rate limiting"""
        if not self.session:
            await self.start_session()

        # Rate limiting
        await self.rate_limiter.acquire()

        # Constrói URL
        url = urljoin(self.BASE_URL, endpoint)

        try:
            logger.debug(f"PandaScore: {method} {url}")
            
            if method.upper() == "GET":
                async with self.session.get(url, params=params) as response:
                    return await self._handle_response(response, endpoint)
            else:
                async with self.session.request(method, url, params=params) as response:
                    return await self._handle_response(response, endpoint)

        except aiohttp.ClientError as e:
            logger.error(f"Erro de conexão com PandaScore: {e}")
            raise PandaScoreAPIError(f"Erro de conexão: {e}")

    async def _handle_response(self, response: aiohttp.ClientResponse, endpoint: str) -> Dict[str, Any]:
        """Processa resposta da API"""
        try:
            response_data = await response.json()
        except Exception:
            response_data = {}

        if response.status == 200:
            logger.debug(f"PandaScore: requisição bem-sucedida {endpoint}")
            return response_data

        elif response.status == 429:
            # Rate limit excedido
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning(f"PandaScore rate limit excedido. Aguardando {retry_after}s")
            await asyncio.sleep(retry_after)
            raise PandaScoreAPIError("Rate limit excedido", response.status, response_data)

        elif response.status == 401:
            logger.error("PandaScore: API key inválida")
            raise PandaScoreAPIError("API key inválida", response.status, response_data)

        else:
            logger.error(f"Erro na API PandaScore: {response.status} - {response_data}")
            raise PandaScoreAPIError(
                f"Erro na API: {response.status}",
                response.status,
                response_data,
            )

    async def get_lol_live_matches(self) -> List[Dict[str, Any]]:
        """Busca partidas ao vivo de League of Legends"""
        try:
            endpoint = "/lol/matches/running"
            matches = await self._make_request(endpoint)
            
            if isinstance(matches, list):
                logger.info(f"PandaScore: {len(matches)} partidas LoL ao vivo encontradas")
                return matches
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas LoL ao vivo no PandaScore: {e}")
            return []

    async def get_lol_upcoming_matches(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Busca partidas futuras de League of Legends"""
        try:
            endpoint = "/lol/matches/upcoming"
            params = {"per_page": 50}
            
            matches = await self._make_request(endpoint, params)
            
            if isinstance(matches, list):
                logger.info(f"PandaScore: {len(matches)} partidas LoL futuras encontradas")
                return matches
                
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas LoL futuras no PandaScore: {e}")
            return []

    async def get_match_odds(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Busca odds de uma partida específica"""
        try:
            endpoint = f"/lol/matches/{match_id}/odds"
            odds_data = await self._make_request(endpoint)
            
            logger.debug(f"PandaScore: odds obtidas para partida {match_id}")
            return odds_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar odds da partida {match_id}: {e}")
            return None

    async def find_match_odds_by_teams(self, team1: str, team2: str, league: str = "") -> Optional[Dict[str, Any]]:
        """
        Encontra odds de uma partida baseada nos nomes dos times
        
        Args:
            team1: Nome do primeiro time
            team2: Nome do segundo time
            league: Liga (opcional para filtrar)
            
        Returns:
            Dados das odds ou None se não encontrado
        """
        try:
            # Busca partidas ao vivo e futuras
            live_matches = await self.get_lol_live_matches()
            upcoming_matches = await self.get_lol_upcoming_matches()
            
            all_matches = live_matches + upcoming_matches
            
            # Normaliza nomes dos times para comparação
            norm_team1 = normalize_team_name(team1)
            norm_team2 = normalize_team_name(team2)
            
            for match in all_matches:
                if not isinstance(match, dict):
                    continue
                    
                # Extrai nomes dos times da partida
                opponents = match.get("opponents", [])
                if len(opponents) != 2:
                    continue
                
                match_team1 = opponents[0].get("opponent", {}).get("name", "")
                match_team2 = opponents[1].get("opponent", {}).get("name", "")
                
                # Verifica se os times coincidem
                if self._teams_match(norm_team1, norm_team2, match_team1, match_team2):
                    # Verifica liga se especificada
                    if league:
                        match_league = match.get("league", {}).get("name", "")
                        if league.lower() not in match_league.lower():
                            continue
                    
                    # Busca odds desta partida
                    match_id = match.get("id")
                    if match_id:
                        odds = await self.get_match_odds(match_id)
                        if odds:
                            return {
                                "match": match,
                                "odds": odds,
                                "team1": match_team1,
                                "team2": match_team2
                            }
            
            logger.warning(f"PandaScore: Nenhuma partida encontrada para {team1} vs {team2}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar odds por times {team1} vs {team2}: {e}")
            return None

    def _teams_match(self, target_team1: str, target_team2: str, match_team1: str, match_team2: str) -> bool:
        """Verifica se os times da partida coincidem com os procurados"""
        norm_match1 = normalize_team_name(match_team1)
        norm_match2 = normalize_team_name(match_team2)
        
        # Verifica ambas as combinações (A vs B ou B vs A)
        match1 = (
            teams_similarity(target_team1, norm_match1) and 
            teams_similarity(target_team2, norm_match2)
        )
        
        match2 = (
            teams_similarity(target_team1, norm_match2) and 
            teams_similarity(target_team2, norm_match1)
        )
        
        return match1 or match2

    async def get_moneyline_odds(self, team1: str, team2: str, league: str = "") -> Optional[Dict[str, float]]:
        """
        Busca odds de moneyline (ML) para uma partida
        
        Args:
            team1: Nome do primeiro time
            team2: Nome do segundo time
            league: Liga (opcional)
            
        Returns:
            Dicionário com odds {team1: odds1, team2: odds2} ou None
        """
        try:
            match_odds_data = await self.find_match_odds_by_teams(team1, team2, league)
            
            if not match_odds_data:
                return None
            
            odds_data = match_odds_data.get("odds", {})
            
            # Processa diferentes formatos de odds do PandaScore
            moneyline_odds = {}
            
            # Verifica se há odds no formato esperado
            if "moneyline" in odds_data:
                ml_data = odds_data["moneyline"]
                for outcome in ml_data:
                    team_name = outcome.get("name", "")
                    odds_value = outcome.get("odds", 0)
                    
                    if team_name and odds_value:
                        moneyline_odds[team_name] = float(odds_value)
            
            # Formato alternativo
            elif "winner" in odds_data:
                winner_data = odds_data["winner"]
                for outcome in winner_data:
                    team_name = outcome.get("name", "")
                    odds_value = outcome.get("odds", 0)
                    
                    if team_name and odds_value:
                        moneyline_odds[team_name] = float(odds_value)
            
            # Valida odds
            valid_odds = {}
            for team, odds in moneyline_odds.items():
                validated_odds = validate_odds(odds)
                if validated_odds and MIN_ODDS <= validated_odds <= MAX_ODDS:
                    valid_odds[team] = validated_odds
            
            if len(valid_odds) >= 2:
                logger.info(f"PandaScore: odds ML obtidas para {team1} vs {team2}: {valid_odds}")
                return valid_odds
            
            logger.warning(f"PandaScore: odds ML não válidas para {team1} vs {team2}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar odds ML para {team1} vs {team2}: {e}")
            return None

    async def get_leagues(self) -> List[Dict[str, Any]]:
        """Busca ligas disponíveis de League of Legends"""
        try:
            endpoint = "/lol/leagues"
            params = {"per_page": 100}
            
            leagues = await self._make_request(endpoint, params)
            
            if isinstance(leagues, list):
                logger.info(f"PandaScore: {len(leagues)} ligas LoL encontradas")
                return leagues
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar ligas LoL no PandaScore: {e}")
            return []

    async def get_teams(self, league_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Busca times de League of Legends"""
        try:
            endpoint = "/lol/teams"
            params = {"per_page": 100}
            
            if league_id:
                params["filter[league_id]"] = league_id
            
            teams = await self._make_request(endpoint, params)
            
            if isinstance(teams, list):
                logger.info(f"PandaScore: {len(teams)} times LoL encontrados")
                return teams
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar times LoL no PandaScore: {e}")
            return []

    async def health_check(self) -> bool:
        """Verifica se a API está funcionando"""
        try:
            # Testa com um endpoint simples
            await self._make_request("/lol/leagues", {"per_page": 1})
            logger.info("Health check do PandaScore: OK")
            return True
        except Exception as e:
            logger.error(f"Health check do PandaScore falhou: {e}")
            return False

    async def get_odds_summary(self) -> Dict[str, Any]:
        """Retorna resumo das odds disponíveis"""
        try:
            live_matches = await self.get_lol_live_matches()
            upcoming_matches = await self.get_lol_upcoming_matches(6)  # Próximas 6 horas
            
            summary = {
                "live_matches_count": len(live_matches),
                "upcoming_matches_count": len(upcoming_matches),
                "total_matches_with_odds": 0,
                "available_leagues": set(),
                "timestamp": time.time()
            }
            
            # Conta partidas com odds
            all_matches = live_matches + upcoming_matches
            for match in all_matches:
                if isinstance(match, dict):
                    league_name = match.get("league", {}).get("name", "")
                    if league_name:
                        summary["available_leagues"].add(league_name)
                        
                    # Verifica se tem odds (campo pode variar)
                    if match.get("has_odds") or match.get("id"):
                        summary["total_matches_with_odds"] += 1
            
            summary["available_leagues"] = list(summary["available_leagues"])
            
            logger.info(f"PandaScore odds summary: {summary['total_matches_with_odds']} partidas com odds")
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de odds: {e}")
            return {
                "live_matches_count": 0,
                "upcoming_matches_count": 0,
                "total_matches_with_odds": 0,
                "available_leagues": [],
                "timestamp": time.time(),
                "error": str(e)
            }

    async def get_match_composition_data(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca dados de composição (picks & bans) de uma partida específica
        
        Args:
            match_id: ID da partida
            
        Returns:
            Dados de composição ou None se não encontrado
        """
        try:
            endpoint = f"/lol/matches/{match_id}"
            match_data = await self._make_request(endpoint)
            
            if not match_data:
                logger.warning(f"Match {match_id} não encontrado")
                return None
            
            # Extrai dados de composição
            composition_data = await self._extract_composition_data(match_data)
            
            if composition_data:
                logger.info(f"✅ Dados de composição obtidos para match {match_id}")
                return composition_data
            else:
                logger.warning(f"Dados de composição não disponíveis para match {match_id}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar composição da partida {match_id}: {e}")
            return None

    async def get_live_match_compositions(self) -> List[Dict[str, Any]]:
        """
        Busca composições de todas as partidas ao vivo
        
        Returns:
            Lista de composições das partidas ao vivo
        """
        compositions = []
        
        try:
            live_matches = await self.get_lol_live_matches()
            
            for match in live_matches:
                match_id = match.get("id")
                if match_id:
                    composition = await self.get_match_composition_data(match_id)
                    if composition:
                        compositions.append(composition)
                        
            logger.info(f"📊 {len(compositions)} composições de partidas ao vivo coletadas")
            return compositions
            
        except Exception as e:
            logger.error(f"Erro ao buscar composições de partidas ao vivo: {e}")
            return []

    async def get_match_games_data(self, match_id: int) -> List[Dict[str, Any]]:
        """
        Busca dados detalhados dos games de uma partida
        
        Args:
            match_id: ID da partida
            
        Returns:
            Lista de dados dos games
        """
        try:
            endpoint = f"/lol/matches/{match_id}/games"
            games_data = await self._make_request(endpoint)
            
            if isinstance(games_data, list):
                logger.info(f"🎮 {len(games_data)} games encontrados para match {match_id}")
                
                # Processa dados de cada game
                processed_games = []
                for game in games_data:
                    processed_game = await self._process_game_data(game)
                    if processed_game:
                        processed_games.append(processed_game)
                
                return processed_games
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar games da partida {match_id}: {e}")
            return []

    async def _extract_composition_data(self, match_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de composição de uma partida
        
        Args:
            match_data: Dados brutos da partida
            
        Returns:
            Dados de composição estruturados
        """
        try:
            teams = match_data.get("opponents", [])
            if len(teams) != 2:
                logger.warning("Partida não possui exatamente 2 times")
                return None
            
            # Busca dados dos games para obter picks & bans
            match_id = match_data.get("id")
            if not match_id:
                return None
                
            games_data = await self.get_match_games_data(match_id)
            if not games_data:
                logger.warning(f"Dados de games não disponíveis para match {match_id}")
                return None
            
            # Pega o game mais recente (último)
            latest_game = games_data[-1] if games_data else None
            if not latest_game:
                return None
            
            composition_data = {
                "match_id": str(match_id),
                "teams": {
                    "team_a": {
                        "name": teams[0].get("opponent", {}).get("name", "Team A"),
                        "id": teams[0].get("opponent", {}).get("id"),
                        "picks": latest_game.get("team_a_picks", []),
                        "bans": latest_game.get("team_a_bans", [])
                    },
                    "team_b": {
                        "name": teams[1].get("opponent", {}).get("name", "Team B"),
                        "id": teams[1].get("opponent", {}).get("id"),
                        "picks": latest_game.get("team_b_picks", []),
                        "bans": latest_game.get("team_b_bans", [])
                    }
                },
                "patch": latest_game.get("patch", "unknown"),
                "side": {
                    "blue": latest_game.get("blue_side", teams[0].get("opponent", {}).get("name", "Team A")),
                    "red": latest_game.get("red_side", teams[1].get("opponent", {}).get("name", "Team B"))
                },
                "league": match_data.get("league", {}).get("name", "Unknown League"),
                "status": match_data.get("status", "unknown"),
                "timestamp": match_data.get("scheduled_at")
            }
            
            logger.debug(f"✅ Composição extraída para match {match_id}")
            return composition_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de composição: {e}")
            return None

    async def _process_game_data(self, game_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processa dados de um game individual
        
        Args:
            game_data: Dados brutos do game
            
        Returns:
            Dados do game processados
        """
        try:
            # Extrai picks e bans dos times
            teams = game_data.get("teams", [])
            if len(teams) != 2:
                return None
            
            team_a = teams[0]
            team_b = teams[1]
            
            processed_data = {
                "game_id": game_data.get("id"),
                "patch": game_data.get("version", {}).get("name", "unknown"),
                "duration": game_data.get("length"),
                "finished": game_data.get("finished", False),
                "winner": game_data.get("winner", {}).get("name") if game_data.get("winner") else None,
                
                # Picks time A
                "team_a_picks": self._extract_picks_from_team(team_a),
                "team_a_bans": self._extract_bans_from_team(team_a),
                
                # Picks time B  
                "team_b_picks": self._extract_picks_from_team(team_b),
                "team_b_bans": self._extract_bans_from_team(team_b),
                
                # Informações de side
                "blue_side": team_a.get("name") if team_a.get("side") == "blue" else team_b.get("name"),
                "red_side": team_b.get("name") if team_b.get("side") == "red" else team_a.get("name")
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Erro ao processar dados do game: {e}")
            return None

    def _extract_picks_from_team(self, team_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrai picks de um time
        
        Args:
            team_data: Dados do time
            
        Returns:
            Lista de picks estruturados
        """
        picks = []
        
        try:
            players = team_data.get("players", [])
            
            for i, player in enumerate(players):
                champion_data = player.get("champion")
                if champion_data:
                    pick = {
                        "champion": champion_data.get("name", "Unknown"),
                        "champion_id": champion_data.get("id"),
                        "position": self._determine_position_by_order(i),
                        "pick_order": i + 1,
                        "player": player.get("name", "Unknown Player")
                    }
                    picks.append(pick)
            
            return picks
            
        except Exception as e:
            logger.error(f"Erro ao extrair picks: {e}")
            return []

    def _extract_bans_from_team(self, team_data: Dict[str, Any]) -> List[str]:
        """
        Extrai bans de um time
        
        Args:
            team_data: Dados do time
            
        Returns:
            Lista de campeões banidos
        """
        bans = []
        
        try:
            bans_data = team_data.get("bans", [])
            
            for ban in bans_data:
                if isinstance(ban, dict) and ban.get("champion"):
                    bans.append(ban["champion"].get("name", "Unknown"))
                elif isinstance(ban, str):
                    bans.append(ban)
            
            return bans
            
        except Exception as e:
            logger.error(f"Erro ao extrair bans: {e}")
            return []

    def _determine_position_by_order(self, order_index: int) -> str:
        """
        Determina posição baseada na ordem padrão do LoL
        
        Args:
            order_index: Índice da ordem (0-4)
            
        Returns:
            Posição do jogador
        """
        position_map = {
            0: "top",
            1: "jungle", 
            2: "mid",
            3: "adc",
            4: "support"
        }
        
        return position_map.get(order_index, "unknown")

    async def search_matches_by_teams(self, team1: str, team2: str) -> List[Dict[str, Any]]:
        """
        Busca partidas entre dois times específicos
        
        Args:
            team1: Nome do primeiro time
            team2: Nome do segundo time
            
        Returns:
            Lista de partidas encontradas
        """
        try:
            # Busca partidas recentes
            endpoint = "/lol/matches"
            params = {
                "per_page": 50,
                "sort": "-scheduled_at"  # Mais recentes primeiro
            }
            
            matches = await self._make_request(endpoint, params)
            
            if not isinstance(matches, list):
                return []
            
            # Filtra partidas entre os times específicos
            matching_matches = []
            
            for match in matches:
                opponents = match.get("opponents", [])
                if len(opponents) == 2:
                    match_team1 = opponents[0].get("opponent", {}).get("name", "")
                    match_team2 = opponents[1].get("opponent", {}).get("name", "")
                    
                    if self._teams_match(team1, team2, match_team1, match_team2):
                        matching_matches.append(match)
            
            logger.info(f"🔍 {len(matching_matches)} partidas encontradas entre {team1} e {team2}")
            return matching_matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas entre {team1} e {team2}: {e}")
            return [] 