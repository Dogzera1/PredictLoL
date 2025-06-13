from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .lolesports_api_client import LoLEsportsAPIClient
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class HybridLoLEsportsClient:
    """
    Cliente híbrido que combina dados reais da API LoL Esports com dados simulados
    Garante que o sistema sempre tenha dados para funcionar
    """
    
    def __init__(self):
        self.real_api_client = LoLEsportsAPIClient()
        self.use_real_api = True
        self.last_api_check = 0
        self.api_check_interval = 300  # 5 minutos
        
        # Dados simulados como fallback
        self.simulated_teams = [
            {"id": "t1", "name": "T1", "code": "T1", "slug": "t1", "region": "LCK"},
            {"id": "geng", "name": "Gen.G", "code": "GEN", "slug": "geng", "region": "LCK"},
            {"id": "drx", "name": "DRX", "code": "DRX", "slug": "drx", "region": "LCK"},
            {"id": "g2", "name": "G2 Esports", "code": "G2", "slug": "g2", "region": "LEC"},
            {"id": "fnc", "name": "Fnatic", "code": "FNC", "slug": "fnatic", "region": "LEC"},
            {"id": "mad", "name": "MAD Lions", "code": "MAD", "slug": "mad", "region": "LEC"},
            {"id": "tl", "name": "Team Liquid", "code": "TL", "slug": "tl", "region": "LCS"},
            {"id": "c9", "name": "Cloud9", "code": "C9", "slug": "c9", "region": "LCS"},
            {"id": "100t", "name": "100 Thieves", "code": "100", "slug": "100t", "region": "LCS"},
        ]
        
        self.simulated_leagues = [
            {"id": "lck", "name": "LCK", "slug": "lck", "region": "Korea"},
            {"id": "lec", "name": "LEC", "slug": "lec", "region": "Europe"},
            {"id": "lcs", "name": "LCS", "slug": "lcs", "region": "North America"},
            {"id": "lpl", "name": "LPL", "slug": "lpl", "region": "China"},
        ]
        
        logger.info("HybridLoLEsportsClient inicializado")

    async def __aenter__(self) -> 'HybridLoLEsportsClient':
        """Context manager entry"""
        await self.real_api_client.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        await self.real_api_client.close_session()

    async def _check_api_health(self) -> bool:
        """Verifica se a API real está funcionando"""
        now = time.time()
        
        # Só verifica a cada 5 minutos para não sobrecarregar
        if now - self.last_api_check < self.api_check_interval:
            return self.use_real_api
        
        try:
            self.last_api_check = now
            is_healthy = await self.real_api_client.health_check()
            self.use_real_api = is_healthy
            
            if is_healthy:
                logger.info("✅ API real funcionando - usando dados reais")
            else:
                logger.warning("⚠️ API real offline - usando dados simulados")
                
            return self.use_real_api
            
        except Exception as e:
            logger.error(f"Erro ao verificar API: {e}")
            self.use_real_api = False
            return False

    async def get_leagues(self) -> List[Dict[str, Any]]:
        """Obtém ligas - tenta API real primeiro, fallback para simulado"""
        try:
            if await self._check_api_health():
                real_leagues = await self.real_api_client.get_leagues()
                if real_leagues and len(real_leagues) > 0:
                    logger.info(f"📊 Usando {len(real_leagues)} ligas reais da API")
                    return real_leagues
            
            # Fallback para dados simulados
            logger.info(f"📊 Usando {len(self.simulated_leagues)} ligas simuladas")
            return self.simulated_leagues
            
        except Exception as e:
            logger.error(f"Erro ao buscar ligas: {e}")
            return self.simulated_leagues

    async def get_teams(self) -> List[Dict[str, Any]]:
        """Obtém times - tenta API real primeiro, fallback para simulado"""
        try:
            if await self._check_api_health():
                real_teams = await self.real_api_client.get_teams()
                if real_teams and len(real_teams) > 0:
                    logger.info(f"👥 Usando {len(real_teams)} times reais da API")
                    return real_teams
            
            # Fallback para dados simulados
            logger.info(f"👥 Usando {len(self.simulated_teams)} times simulados")
            return self.simulated_teams
            
        except Exception as e:
            logger.error(f"Erro ao buscar times: {e}")
            return self.simulated_teams

    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """Obtém partidas ao vivo - tenta API real primeiro, fallback para simulado"""
        try:
            if await self._check_api_health():
                real_matches = await self.real_api_client.get_live_matches()
                if real_matches and len(real_matches) > 0:
                    logger.info(f"🔴 Usando {len(real_matches)} partidas reais ao vivo")
                    return real_matches
            
            # Fallback para partidas simuladas
            simulated_matches = await self._generate_simulated_matches()
            logger.info(f"🔴 Usando {len(simulated_matches)} partidas simuladas")
            return simulated_matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return await self._generate_simulated_matches()

    async def get_upcoming_matches(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Obtém partidas próximas - tenta API real primeiro, fallback para simulado"""
        try:
            if await self._check_api_health():
                real_matches = await self.real_api_client.get_upcoming_matches(hours_ahead)
                if real_matches and len(real_matches) > 0:
                    logger.info(f"📅 Usando {len(real_matches)} partidas próximas reais")
                    return real_matches
            
            # Fallback para partidas simuladas
            simulated_matches = await self._generate_upcoming_matches(hours_ahead)
            logger.info(f"📅 Usando {len(simulated_matches)} partidas próximas simuladas")
            return simulated_matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas próximas: {e}")
            return await self._generate_upcoming_matches(hours_ahead)

    async def _generate_simulated_matches(self) -> List[Dict[str, Any]]:
        """Gera partidas simuladas para demonstração"""
        matches = []
        
        # Simula 2-3 partidas ao vivo
        for i in range(2):
            team1 = self.simulated_teams[i * 2]
            team2 = self.simulated_teams[i * 2 + 1]
            
            match = {
                "id": f"sim_live_{i}",
                "state": "inProgress",
                "startTime": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "teams": [team1, team2],
                "league": self.simulated_leagues[i % len(self.simulated_leagues)],
                "event": {
                    "name": f"Simulação {self.simulated_leagues[i % len(self.simulated_leagues)]['name']} 2025",
                    "id": f"sim_event_{i}"
                },
                "type": "match",
                "games": [
                    {
                        "id": f"sim_game_{i}_1",
                        "state": "inProgress",
                        "number": 1
                    }
                ]
            }
            matches.append(match)
        
        return matches

    async def _generate_upcoming_matches(self, hours_ahead: int) -> List[Dict[str, Any]]:
        """Gera partidas próximas simuladas"""
        matches = []
        
        # Simula 3-5 partidas nas próximas horas
        for i in range(4):
            team1 = self.simulated_teams[(i * 2) % len(self.simulated_teams)]
            team2 = self.simulated_teams[(i * 2 + 1) % len(self.simulated_teams)]
            
            # Partidas em horários diferentes
            start_time = datetime.now() + timedelta(hours=i * 6, minutes=30)
            
            match = {
                "id": f"sim_upcoming_{i}",
                "state": "upcoming",
                "startTime": start_time.isoformat(),
                "teams": [team1, team2],
                "league": self.simulated_leagues[i % len(self.simulated_leagues)],
                "event": {
                    "name": f"Simulação {self.simulated_leagues[i % len(self.simulated_leagues)]['name']} 2025",
                    "id": f"sim_event_upcoming_{i}"
                },
                "type": "match",
                "games": []
            }
            matches.append(match)
        
        return matches

    async def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Obtém detalhes de uma partida específica"""
        try:
            if await self._check_api_health():
                real_details = await self.real_api_client.get_match_details(match_id)
                if real_details:
                    logger.info(f"📋 Detalhes reais da partida {match_id}")
                    return real_details
            
            # Fallback para detalhes simulados
            if match_id.startswith("sim_"):
                return await self._generate_simulated_match_details(match_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes da partida {match_id}: {e}")
            return None

    async def _generate_simulated_match_details(self, match_id: str) -> Dict[str, Any]:
        """Gera detalhes simulados de uma partida"""
        return {
            "id": match_id,
            "state": "inProgress" if "live" in match_id else "upcoming",
            "type": "match",
            "startTime": datetime.now().isoformat(),
            "teams": [
                self.simulated_teams[0],
                self.simulated_teams[1]
            ],
            "games": [
                {
                    "id": f"{match_id}_game_1",
                    "state": "inProgress" if "live" in match_id else "upcoming",
                    "number": 1,
                    "teams": [
                        {
                            "id": self.simulated_teams[0]["id"],
                            "side": "blue",
                            "players": []
                        },
                        {
                            "id": self.simulated_teams[1]["id"],
                            "side": "red",
                            "players": []
                        }
                    ]
                }
            ]
        }

    def get_data_source_status(self) -> Dict[str, Any]:
        """Retorna status da fonte de dados atual"""
        return {
            "using_real_api": self.use_real_api,
            "last_api_check": self.last_api_check,
            "data_source": "API Real" if self.use_real_api else "Dados Simulados",
            "simulated_teams_count": len(self.simulated_teams),
            "simulated_leagues_count": len(self.simulated_leagues)
        }

    async def force_api_check(self) -> bool:
        """Força uma verificação da API real"""
        self.last_api_check = 0  # Reset timer
        return await self._check_api_health()

    def clear_cache(self) -> None:
        """Limpa cache do cliente real"""
        self.real_api_client.clear_cache()

    async def health_check(self) -> bool:
        """Verifica se o sistema híbrido está funcionando"""
        try:
            # Testa se consegue obter dados (reais ou simulados)
            leagues = await self.get_leagues()
            teams = await self.get_teams()
            
            return len(leagues) > 0 and len(teams) > 0
            
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False 