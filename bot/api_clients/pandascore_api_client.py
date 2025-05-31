from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientTimeout

from ..utils.constants import HTTP_HEADERS, MIN_ODDS, MAX_ODDS
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

    BASE_URL = "https://api.pandascore.co"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ"
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