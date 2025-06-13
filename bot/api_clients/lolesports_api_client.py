from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientTimeout

from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class LoLEsportsAPIError(Exception):
    """Exceção customizada para erros da API LoL Esports"""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class LoLEsportsAPIClient:
    """Cliente para a API LoL Esports baseado na documentação OpenAPI"""

    # Usando API alternativa que funciona
    BASE_URL = "https://api.lol-esports.mckernant1.com"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_ttl = 300  # 5 minutos
        
        # Headers padrão
        self.headers = {
            "User-Agent": "PredictLoL/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        logger.info("LoLEsportsAPIClient inicializado com sucesso")

    async def __aenter__(self) -> 'LoLEsportsAPIClient':
        """Context manager entry"""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        await self.close_session()

    async def start_session(self) -> None:
        """Inicia sessão HTTP"""
        if not self.session or self.session.closed:
            timeout = ClientTimeout(total=15.0)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=aiohttp.TCPConnector(limit=50, limit_per_host=10),
            )
            logger.debug("Sessão HTTP iniciada")

    async def close_session(self) -> None:
        """Fecha sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Sessão HTTP fechada")

    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Gera chave de cache"""
        params_str = json.dumps(params or {}, sort_keys=True)
        return f"{endpoint}:{params_str}"

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Recupera dados do cache se válidos"""
        if key in self.cache:
            data, expires_at = self.cache[key]
            if time.time() < expires_at:
                return data
            else:
                del self.cache[key]
        return None

    def _set_cache(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Armazena dados no cache"""
        ttl = ttl or self.cache_ttl
        expires_at = time.time() + ttl
        self.cache[key] = (data, expires_at)

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Faz requisição HTTP com cache"""
        if not self.session:
            await self.start_session()

        # Verifica cache
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit para {endpoint}")
            return cached_data

        # Constrói URL
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            logger.debug(f"Fazendo requisição: {url}")
            if params:
                logger.debug(f"Parâmetros: {params}")
                
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Armazena no cache
                    self._set_cache(cache_key, data, cache_ttl)
                    logger.debug(f"Requisição bem-sucedida: {endpoint}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Erro na requisição {endpoint}: {response.status} - {error_text}")
                    raise LoLEsportsAPIError(
                        f"Erro HTTP {response.status}: {error_text}",
                        status_code=response.status
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Erro de conexão para {endpoint}: {e}")
            raise LoLEsportsAPIError(f"Erro de conexão: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado para {endpoint}: {e}")
            raise LoLEsportsAPIError(f"Erro inesperado: {e}")

    async def get_leagues(self, hl: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Obtém lista de ligas disponíveis
        
        Args:
            hl: Código do idioma (ex: "pt-BR", "en-US")
            
        Returns:
            Lista de ligas com seus torneios
        """
        try:
            # API alternativa usa endpoint diferente
            response = await self._make_request("/leagues")
            
            # Resposta direta é uma lista
            if isinstance(response, list):
                leagues = response
            else:
                leagues = response.get("data", response)
                
            logger.info(f"Encontradas {len(leagues)} ligas")
            return leagues
            
        except Exception as e:
            logger.error(f"Erro ao buscar ligas: {e}")
            return []

    async def get_events(self, hl: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Obtém eventos (partidas) disponíveis
        
        Args:
            hl: Código do idioma
            
        Returns:
            Lista de eventos com suas partidas
        """
        try:
            # Primeiro busca ligas para obter IDs
            leagues = await self.get_leagues()
            all_events = []
            
            # Pega as primeiras 5 ligas para testar
            for league in leagues[:5]:
                league_id = league.get("id")
                if league_id:
                    try:
                        # Busca partidas para esta liga
                        response = await self._make_request(f"/matches", {"leagueId": league_id})
                        
                        if isinstance(response, list):
                            events = response
                        else:
                            events = response.get("data", response)
                        
                        if events:
                            all_events.extend(events)
                            
                    except Exception as league_error:
                        logger.debug(f"Liga {league_id} falhou: {league_error}")
                        continue
            
            logger.info(f"Encontrados {len(all_events)} eventos total")
            return all_events
            
        except Exception as e:
            logger.error(f"Erro ao buscar eventos: {e}")
            return []

    async def get_teams(self, hl: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Obtém informações dos times
        
        Args:
            hl: Código do idioma
            
        Returns:
            Lista de times
        """
        try:
            response = await self._make_request("/teams")
            
            if isinstance(response, list):
                teams = response
            else:
                teams = response.get("data", response)
                
            logger.info(f"Encontrados {len(teams)} times")
            return teams
            
        except Exception as e:
            logger.error(f"Erro ao buscar times: {e}")
            return []

    async def get_match_details(self, match_id: str, hl: str = "pt-BR") -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes completos de uma partida
        
        Args:
            match_id: ID da partida
            hl: Código do idioma
            
        Returns:
            Detalhes da partida ou None se não encontrada
        """
        try:
            params = {"id": match_id, "hl": hl}
            response = await self._make_request("/getMatchDetails", params)
            
            match_data = response.get("data", {}).get("match")
            if match_data:
                logger.info(f"Detalhes da partida {match_id} obtidos com sucesso")
            else:
                logger.warning(f"Partida {match_id} não encontrada")
                
            return match_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes da partida {match_id}: {e}")
            return None

    async def get_live_matches(self, hl: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Obtém partidas ao vivo ou próximas
        
        Args:
            hl: Código do idioma
            
        Returns:
            Lista de partidas ao vivo/próximas
        """
        try:
            events = await self.get_events(hl)
            live_matches = []
            
            for event in events:
                matches = event.get("matches", [])
                for match in matches:
                    state = match.get("state", "").lower()
                    if state in ["inprogress", "upcoming"]:
                        # Adiciona informações do evento à partida
                        match["event"] = {
                            "id": event.get("id"),
                            "name": event.get("name"),
                            "slug": event.get("slug"),
                            "leagueId": event.get("leagueId"),
                            "tournamentId": event.get("tournamentId")
                        }
                        live_matches.append(match)
            
            logger.info(f"Encontradas {len(live_matches)} partidas ao vivo/próximas")
            return live_matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return []

    async def get_upcoming_matches(self, hours_ahead: int = 24, hl: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Obtém partidas que acontecerão nas próximas horas
        
        Args:
            hours_ahead: Quantas horas à frente buscar
            hl: Código do idioma
            
        Returns:
            Lista de partidas próximas
        """
        try:
            events = await self.get_events(hl)
            upcoming_matches = []
            
            current_time = time.time()
            cutoff_time = current_time + (hours_ahead * 3600)  # horas em segundos
            
            for event in events:
                matches = event.get("matches", [])
                for match in matches:
                    state = match.get("state", "").lower()
                    start_date = match.get("startDate")
                    
                    if state == "upcoming" and start_date:
                        try:
                            # Converte data para timestamp (assumindo formato ISO)
                            from datetime import datetime
                            match_time = datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp()
                            
                            if current_time <= match_time <= cutoff_time:
                                match["event"] = {
                                    "id": event.get("id"),
                                    "name": event.get("name"),
                                    "slug": event.get("slug"),
                                    "leagueId": event.get("leagueId"),
                                    "tournamentId": event.get("tournamentId")
                                }
                                upcoming_matches.append(match)
                        except Exception as date_error:
                            logger.warning(f"Erro ao processar data da partida: {date_error}")
                            continue
            
            logger.info(f"Encontradas {len(upcoming_matches)} partidas nas próximas {hours_ahead}h")
            return upcoming_matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas próximas: {e}")
            return []

    async def get_highlander_tournaments(self, hl: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Obtém torneios via API Highlander (legada)
        
        Args:
            hl: Código do idioma
            
        Returns:
            Lista de torneios
        """
        try:
            params = {"hl": hl} if hl else None
            response = await self._make_request("/getHighlanderTournaments", params)
            
            tournaments = response.get("data", {}).get("highlanderTournaments", [])
            logger.info(f"Encontrados {len(tournaments)} torneios (Highlander)")
            return tournaments
            
        except Exception as e:
            logger.error(f"Erro ao buscar torneios Highlander: {e}")
            return []

    async def get_highlander_matches(self, hl: str = "pt-BR") -> List[Dict[str, Any]]:
        """
        Obtém partidas via API Highlander (legada)
        
        Args:
            hl: Código do idioma
            
        Returns:
            Lista de partidas
        """
        try:
            params = {"hl": hl} if hl else None
            response = await self._make_request("/getHighlanderMatches", params)
            
            matches = response.get("data", {}).get("highlanderMatches", [])
            logger.info(f"Encontradas {len(matches)} partidas (Highlander)")
            return matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas Highlander: {e}")
            return []

    async def health_check(self) -> bool:
        """
        Verifica se a API está funcionando
        
        Returns:
            True se API estiver funcionando, False caso contrário
        """
        try:
            leagues = await self.get_leagues()
            return len(leagues) > 0
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False

    def clear_cache(self) -> None:
        """Limpa todo o cache"""
        self.cache.clear()
        logger.info("Cache limpo")

    def cleanup_cache(self) -> None:
        """Remove itens expirados do cache"""
        now = time.time()
        expired_keys = [key for key, (_, expires_at) in self.cache.items() if now >= expires_at]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.debug(f"Removidos {len(expired_keys)} itens expirados do cache")
