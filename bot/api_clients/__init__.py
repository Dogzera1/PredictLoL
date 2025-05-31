"""
Clientes para APIs externas

Este módulo contém os clientes para integração com:
- Riot Games API / Lolesports API: Dados oficiais de partidas LoL
- PandaScore API: Odds de casas de apostas para esports
"""

from .riot_api_client import RiotAPIClient
from .pandascore_api_client import PandaScoreAPIClient

__all__ = ['RiotAPIClient', 'PandaScoreAPIClient'] 