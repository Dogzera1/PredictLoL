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
    RIOT_API_ENDPOINTS,
    RIOT_API_RATE_LIMITS,
    RIOT_HEADERS,
    RIOT_API_KEY,
    HTTP_HEADERS,
    VALID_LIVE_STATUSES,
    LEAGUE_TIERS,
)
from ..utils.helpers import normalize_team_name
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class RiotAPIError(Exception):
    """Exceção customizada para erros da API da Riot"""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimiter:
    """Sistema de rate limiting para respeitar os limites da API da Riot"""

    def __init__(self, requests_per_second: int = 20, requests_per_two_minutes: int = 100):
        self.requests_per_second = requests_per_second
        self.requests_per_two_minutes = requests_per_two_minutes
        self.second_window: List[float] = []
        self.two_minute_window: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Aguarda até que seja seguro fazer uma requisição"""
        async with self._lock:
            now = time.time()

            # Limpa janelas antigas
            self.second_window = [t for t in self.second_window if now - t < 1.0]
            self.two_minute_window = [t for t in self.two_minute_window if now - t < 120.0]

            # Verifica se precisa aguardar
            if len(self.second_window) >= self.requests_per_second:
                sleep_time = 1.0 - (now - self.second_window[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit: aguardando {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)

            if len(self.two_minute_window) >= self.requests_per_two_minutes:
                sleep_time = 120.0 - (now - self.two_minute_window[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit: aguardando {sleep_time:.2f}s (janela 2min)")
                    await asyncio.sleep(sleep_time)

            # Registra a requisição
            now = time.time()
            self.second_window.append(now)
            self.two_minute_window.append(now)


class APICache:
    """Cache inteligente para dados da API com TTL configurável"""

    def __init__(self, default_ttl: int = 300):  # 5 minutos padrão
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Recupera item do cache se ainda válido"""
        if key in self.cache:
            data, expires_at = self.cache[key]
            if time.time() < expires_at:
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Armazena item no cache com TTL"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        self.cache[key] = (data, expires_at)

    def clear(self) -> None:
        """Limpa todo o cache"""
        self.cache.clear()

    def cleanup(self) -> None:
        """Remove itens expirados do cache"""
        now = time.time()
        expired_keys = [key for key, (_, expires_at) in self.cache.items() if now >= expires_at]
        for key in expired_keys:
            del self.cache[key]


class RiotAPIClient:
    """Cliente profissional para API da Riot/Lolesports baseado no openapi.yaml"""

    # URLs baseadas no openapi.yaml
    ESPORTS_API_BASE = "https://esports-api.lolesports.com/persisted/gw"
    LIVESTATS_API_BASE = "https://feed.lolesports.com/livestats/v1"
    HIGHLANDER_API_BASE = "https://api.lolesports.com/api/v1"
    
    # API Key fixa conforme documentação
    API_KEY = RIOT_API_KEY
    
    def __init__(self, api_key: Optional[str] = None):
        # Usa a chave das constantes ou a fornecida
        self.api_key = api_key or RIOT_API_KEY
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter()
        self.cache = APICache()

        # Headers padrão conforme documentação
        self.headers = {
            **HTTP_HEADERS,
            "x-api-key": self.api_key,
        }

        logger.info("RiotAPIClient (Lolesports) inicializado com sucesso")

    async def __aenter__(self) -> RiotAPIClient:
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
                connector=aiohttp.TCPConnector(limit=100, limit_per_host=20),
            )
            logger.debug("Sessão HTTP iniciada")

    async def close_session(self) -> None:
        """Fecha sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Sessão HTTP fechada")

    async def _make_request(
        self,
        base_url: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Faz requisição HTTP com rate limiting e cache"""
        if not self.session:
            await self.start_session()

        # Verifica cache primeiro
        cache_key = f"{base_url}:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit para {endpoint}")
            return cached_data

        # Rate limiting
        await self.rate_limiter.acquire()

        # Constrói URL corretamente
        if endpoint.startswith("/"):
            url = base_url + endpoint
        else:
            url = f"{base_url}/{endpoint}"

        # Headers para esta requisição (garantindo x-api-key)
        request_headers = {
            **HTTP_HEADERS,
            "x-api-key": self.api_key,
        }

        try:
            logger.debug(f"Fazendo requisição: {url}")
            logger.debug(f"Headers: {request_headers}")
            async with self.session.get(url, params=params, headers=request_headers) as response:
                response_data = await response.json()

                if response.status == 200:
                    # Armazena no cache
                    self.cache.set(cache_key, response_data, cache_ttl)
                    logger.debug(f"Requisição bem-sucedida: {endpoint}")
                    return response_data

                elif response.status == 429:
                    # Rate limit excedido
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limit excedido. Aguardando {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(base_url, endpoint, params, cache_ttl)

                elif response.status == 404:
                    logger.warning(f"Recurso não encontrado: {endpoint}")
                    raise RiotAPIError(f"Recurso não encontrado: {endpoint}", 404, response_data)

                else:
                    logger.error(f"Erro na API: {response.status} - {response_data}")
                    raise RiotAPIError(
                        f"Erro na API: {response.status}",
                        response.status,
                        response_data,
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Erro de conexão: {e}")
            raise RiotAPIError(f"Erro de conexão: {e}")

    async def get_live_matches(self, locale: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Busca partidas ao vivo usando endpoint /getLive
        
        Args:
            locale: Locale para dados (padrão pt-BR)
            
        Returns:
            Lista de partidas ao vivo (apenas dados reais)
        """
        try:
            endpoint = "/getLive"
            params = {"hl": locale}
            
            data = await self._make_request(
                self.ESPORTS_API_BASE,
                endpoint,
                params,
                cache_ttl=180  # Cache 3 minutos
            )
            
            # Extrai eventos da resposta
            events = data.get("data", {}).get("schedule", {}).get("events", [])
            logger.info(f"Encontrados {len(events)} eventos ao vivo")
            return events
            
        except RiotAPIError as e:
            if e.status_code == 403:
                logger.warning("Riot API: Autenticação falhou - sem dados disponíveis")
                return []  # Retorna lista vazia ao invés de dados mock
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return []

    async def get_leagues(self, locale: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Busca todas as ligas disponíveis usando endpoint /getLeagues
        
        Args:
            locale: Locale para dados
            
        Returns:
            Lista de ligas
        """
        try:
            endpoint = "/getLeagues"
            params = {"hl": locale}
            
            data = await self._make_request(
                self.ESPORTS_API_BASE,
                endpoint,
                params,
                cache_ttl=3600  # Cache 1 hora
            )
            
            leagues = data.get("data", {}).get("leagues", [])
            logger.info(f"Encontradas {len(leagues)} ligas disponíveis")
            return leagues
            
        except Exception as e:
            logger.error(f"Erro ao buscar ligas: {e}")
            return []

    async def get_schedule(
        self, 
        league_ids: Optional[List[int]] = None, 
        locale: str = "pt-BR",
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca cronograma de partidas usando endpoint /getSchedule
        
        Args:
            league_ids: IDs das ligas para filtrar
            locale: Locale para dados
            page_token: Token de paginação
            
        Returns:
            Dados do cronograma
        """
        try:
            endpoint = "/getSchedule"
            params = {"hl": locale}
            
            if league_ids:
                params["leagueId"] = league_ids
            
            if page_token:
                params["pageToken"] = page_token
            
            data = await self._make_request(
                self.ESPORTS_API_BASE,
                endpoint,
                params,
                cache_ttl=300  # Cache 5 minutos
            )
            
            schedule_data = data.get("data", {}).get("schedule", {})
            events = schedule_data.get("events", [])
            
            logger.info(f"Cronograma obtido com {len(events)} eventos")
            return schedule_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar cronograma: {e}")
            return {}

    async def get_event_details(self, event_id: int, locale: str = "pt-BR") -> Optional[Dict[str, Any]]:
        """
        Busca detalhes de um evento específico usando endpoint /getEventDetails
        
        Args:
            event_id: ID do evento
            locale: Locale para dados
            
        Returns:
            Detalhes do evento ou None
        """
        try:
            endpoint = "/getEventDetails"
            params = {"hl": locale, "id": event_id}
            
            data = await self._make_request(
                self.ESPORTS_API_BASE,
                endpoint,
                params,
                cache_ttl=600  # Cache 10 minutos
            )
            
            event_data = data.get("data", {}).get("event", {})
            if event_data:
                logger.debug(f"Detalhes obtidos para evento {event_id}")
                return event_data
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes do evento {event_id}: {e}")
            return None

    async def get_teams(self, team_slugs: List[str], locale: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Busca informações de times usando endpoint /getTeams
        
        Args:
            team_slugs: Lista de slugs dos times
            locale: Locale para dados
            
        Returns:
            Lista de dados dos times
        """
        try:
            endpoint = "/getTeams"
            params = {"hl": locale, "id": team_slugs}
            
            data = await self._make_request(
                self.ESPORTS_API_BASE,
                endpoint,
                params,
                cache_ttl=1800  # Cache 30 minutos
            )
            
            teams = data.get("data", {}).get("teams", [])
            logger.info(f"Dados obtidos para {len(teams)} times")
            return teams
            
        except Exception as e:
            logger.error(f"Erro ao buscar times {team_slugs}: {e}")
            return []

    async def get_live_match_window(self, game_id: int, starting_time: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Busca dados ao vivo de uma partida usando endpoint /window/{gameId}
        
        Args:
            game_id: ID do jogo
            starting_time: Tempo de início (RFC3339)
            
        Returns:
            Dados da janela ao vivo ou None
        """
        try:
            endpoint = f"/window/{game_id}"
            params = {}
            
            if starting_time:
                params["startingTime"] = starting_time
            
            data = await self._make_request(
                self.LIVESTATS_API_BASE,
                endpoint,
                params,
                cache_ttl=30  # Cache 30 segundos para dados ao vivo
            )
            
            if data:
                logger.debug(f"Dados ao vivo obtidos para jogo {game_id}")
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados ao vivo do jogo {game_id}: {e}")
            return None

    async def get_live_match_details(self, game_id: int, starting_time: Optional[str] = None, participant_ids: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Busca detalhes ao vivo de uma partida usando endpoint /details/{gameId}
        
        Args:
            game_id: ID do jogo
            starting_time: Tempo de início (RFC3339)
            participant_ids: IDs dos participantes separados por underscore
            
        Returns:
            Detalhes ao vivo ou None
        """
        try:
            endpoint = f"/details/{game_id}"
            params = {}
            
            if starting_time:
                params["startingTime"] = starting_time
                
            if participant_ids:
                params["participantIds"] = participant_ids
            
            data = await self._make_request(
                self.LIVESTATS_API_BASE,
                endpoint,
                params,
                cache_ttl=30  # Cache 30 segundos
            )
            
            if data:
                logger.debug(f"Detalhes ao vivo obtidos para jogo {game_id}")
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes ao vivo do jogo {game_id}: {e}")
            return None

    async def get_tournaments_for_league(self, league_id: int, locale: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Busca torneios de uma liga usando endpoint /getTournamentsForLeague
        
        Args:
            league_id: ID da liga
            locale: Locale para dados
            
        Returns:
            Lista de torneios
        """
        try:
            endpoint = "/getTournamentsForLeague"
            params = {"hl": locale, "leagueId": league_id}
            
            data = await self._make_request(
                self.ESPORTS_API_BASE,
                endpoint,
                params,
                cache_ttl=1800  # Cache 30 minutos
            )
            
            leagues_data = data.get("data", {}).get("leagues", [])
            tournaments = []
            
            for league_data in leagues_data:
                tournaments.extend(league_data.get("tournaments", []))
            
            logger.info(f"Encontrados {len(tournaments)} torneios para liga {league_id}")
            return tournaments
            
        except Exception as e:
            logger.error(f"Erro ao buscar torneios da liga {league_id}: {e}")
            return []

    async def get_standings(self, tournament_ids: List[str], locale: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Busca classificações usando endpoint /getStandings
        
        Args:
            tournament_ids: IDs dos torneios
            locale: Locale para dados
            
        Returns:
            Lista de classificações
        """
        try:
            endpoint = "/getStandings"
            params = {"hl": locale, "tournamentId": tournament_ids}
            
            data = await self._make_request(
                self.ESPORTS_API_BASE,
                endpoint,
                params,
                cache_ttl=600  # Cache 10 minutos
            )
            
            standings = data.get("data", {}).get("standings", [])
            logger.info(f"Classificações obtidas para {len(standings)} torneios")
            return standings
            
        except Exception as e:
            logger.error(f"Erro ao buscar classificações: {e}")
            return []

    async def filter_live_matches_only(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra apenas partidas que estão realmente ao vivo
        
        Args:
            events: Lista de eventos
            
        Returns:
            Lista filtrada de partidas ao vivo
        """
        live_matches = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            # Verifica status da partida
            state = event.get("state", "").lower()
            event_type = event.get("type", "")
            
            # Filtra apenas partidas ao vivo
            if state in VALID_LIVE_STATUSES and event_type == "match":
                live_matches.append(event)
        
        logger.info(f"Filtradas {len(live_matches)} partidas ao vivo de {len(events)} eventos")
        return live_matches

    async def get_comprehensive_live_data(self) -> List[Dict[str, Any]]:
        """
        Busca dados abrangentes de partidas ao vivo combinando múltiplos endpoints
        
        Returns:
            Lista de partidas ao vivo com dados completos
        """
        try:
            # Busca eventos ao vivo
            live_events = await self.get_live_matches()
            
            # Filtra apenas partidas realmente ao vivo
            live_matches = await self.filter_live_matches_only(live_events)
            
            # Enriquece dados das partidas ao vivo
            enriched_matches = []
            
            for match in live_matches:
                try:
                    # Tenta obter detalhes adicionais do evento
                    event_id = match.get("id")
                    if event_id:
                        event_details = await self.get_event_details(int(event_id))
                        if event_details:
                            match["detailed_data"] = event_details
                    
                    # Extrai game IDs para dados ao vivo
                    games = match.get("match", {}).get("games", [])
                    for game in games:
                        game_id = game.get("id")
                        if game_id and game.get("state") == "inProgress":
                            # Busca dados ao vivo do jogo
                            live_data = await self.get_live_match_window(int(game_id))
                            if live_data:
                                game["live_stats"] = live_data
                    
                    enriched_matches.append(match)
                    
                except Exception as e:
                    logger.warning(f"Erro ao enriquecer dados da partida: {e}")
                    enriched_matches.append(match)  # Adiciona mesmo sem dados extras
            
            logger.info(f"Dados abrangentes obtidos para {len(enriched_matches)} partidas ao vivo")
            return enriched_matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados abrangentes ao vivo: {e}")
            return []

    async def health_check(self) -> bool:
        """
        Verifica se a API está funcionando (apenas dados reais)
        
        Returns:
            True se API funciona, False caso contrário
        """
        try:
            await self.start_session()
            data = await self._make_request(
                self.ESPORTS_API_BASE,
                "/getLive",
                {"hl": "en-US"},
                cache_ttl=60
            )
            
            # Verifica se resposta é válida
            if isinstance(data, dict) and "data" in data:
                logger.info("Riot API: Health check passou")
                return True
            else:
                logger.warning("Riot API: Resposta inválida no health check")
                return False
                
        except RiotAPIError as e:
            if e.status_code == 403:
                logger.warning("Riot API: Falha de autenticação - API indisponível")
                return False
            logger.error(f"Riot API: Erro no health check - {e}")
            return False
        except Exception as e:
            logger.error(f"Riot API: Health check falhou - {e}")
            return False
        finally:
            await self.close_session()

    def cleanup_cache(self) -> None:
        """Limpa cache expirado"""
        self.cache.cleanup()
        logger.debug("Cache da Riot API limpo")

    async def get_match_timeline(self, region: str, match_id: str) -> Optional[Dict[str, Any]]:
        """Busca timeline detalhada de uma partida"""
        try:
            endpoint = f"/lol/match/v5/matches/{match_id}/timeline"
            return await self._make_request(endpoint, region, cache_ttl=3600)  # Cache 1 hora
        except Exception as e:
            logger.error(f"Erro ao buscar timeline da partida {match_id}: {e}")
            return None

    async def get_champion_rotations(self, region: str) -> Optional[Dict[str, Any]]:
        """Busca rotação de campeões gratuitos"""
        try:
            endpoint = "/lol/platform/v3/champion-rotations"
            return await self._make_request(endpoint, region, cache_ttl=86400)  # Cache 24 horas
        except Exception as e:
            logger.error(f"Erro ao buscar rotação de campeões: {e}")
            return None 