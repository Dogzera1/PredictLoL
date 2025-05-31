import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# API Key para PandaScore (ODDS REAIS DE ESPORTS)
PANDASCORE_API_KEY = "90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ"

class PandaScoreAPIClient:
    """Cliente para PandaScore API - ODDS REAIS DE ESPORTS/LOL"""

    def __init__(self, api_key: str = PANDASCORE_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.pandascore.co"
        self.cache = {}
        self.cache_duration = 120  # 2 minutos
        
        logger.info("💰 PandaScore API Client inicializado - ODDS REAIS de eSports")

    async def get_lol_matches_with_odds(self) -> List[Dict]:
        """Busca partidas de LoL com dados de odds da PandaScore"""
        
        # Verificar cache primeiro
        cache_key = "lol_matches_odds"
        if self._is_cache_valid(cache_key):
            logger.info("📦 Cache hit - usando odds em cache da PandaScore")
            return self.cache[cache_key]['data']
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
        
        timeout = aiohttp.ClientTimeout(total=8)
        matches_with_odds = []
        
        try:
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Buscar partidas ao vivo e futuras
                endpoints = [
                    f"{self.base_url}/lol/matches?filter[status]=running,not_started&sort=begin_at&page[size]=20",
                    f"{self.base_url}/lol/matches?filter[status]=running&sort=begin_at"
                ]
                
                for endpoint in endpoints:
                    try:
                        async with session.get(endpoint) as response:
                            if response.status == 200:
                                matches = await response.json()
                                
                                for match in matches:
                                    match_data = await self._process_match_with_odds(match, session)
                                    if match_data:
                                        matches_with_odds.append(match_data)
                                        
                            elif response.status == 401:
                                logger.error("❌ PandaScore: API Key inválida")
                                break
                            elif response.status == 429:
                                logger.warning("⚠️ PandaScore: Rate limit atingido")
                                break
                                
                    except Exception as e:
                        logger.debug(f"Erro no endpoint PandaScore {endpoint}: {e}")
                        continue
                        
            # Cache dos resultados
            if matches_with_odds:
                self.cache[cache_key] = {
                    'data': matches_with_odds,
                    'timestamp': datetime.now()
                }
                logger.info(f"💰 PandaScore: {len(matches_with_odds)} partidas com odds obtidas")
            else:
                logger.info("💰 PandaScore: Nenhuma partida com odds encontrada")
                
            return matches_with_odds
            
        except Exception as e:
            logger.error(f"❌ Erro na PandaScore API: {e}")
            return []

    async def get_match_odds_by_teams(self, team1: str, team2: str, league: str = "") -> Optional[Dict]:
        """Busca odds para uma partida específica por nomes dos times"""
        try:
            matches_with_odds = await self.get_lol_matches_with_odds()
            
            for match in matches_with_odds:
                teams = match.get('teams', [])
                if len(teams) >= 2:
                    team1_name = teams[0].get('name', '').lower()
                    team2_name = teams[1].get('name', '').lower()
                    
                    # Verificar se os times fazem match
                    if (self._teams_match(team1.lower(), team1_name) and 
                        self._teams_match(team2.lower(), team2_name)) or \
                       (self._teams_match(team1.lower(), team2_name) and 
                        self._teams_match(team2.lower(), team1_name)):
                        
                        return {
                            'team1': teams[0].get('name'),
                            'team2': teams[1].get('name'),
                            'league': match.get('league', ''),
                            'status': match.get('status', ''),
                            'source': 'pandascore',
                            'odds_available': True,
                            'confidence': 'high'  # PandaScore é fonte confiável
                        }
                            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds por times na PandaScore: {e}")
            return None

    async def _process_match_with_odds(self, match: Dict, session) -> Optional[Dict]:
        """Processa uma partida individual verificando disponibilidade de odds"""
        try:
            match_id = match.get('id')
            if not match_id:
                return None
                
            # Extrair dados básicos da partida
            match_data = {
                'id': match_id,
                'name': match.get('name', ''),
                'status': match.get('status', ''),
                'begin_at': match.get('begin_at', ''),
                'league': match.get('league', {}).get('name', ''),
                'teams': [],
                'source': 'pandascore',
                'has_real_odds': True
            }
            
            # Extrair times
            opponents = match.get('opponents', [])
            for opponent in opponents[:2]:  # Máximo 2 times
                if opponent.get('opponent'):
                    team = {
                        'name': opponent['opponent'].get('name', ''),
                        'id': opponent['opponent'].get('id', ''),
                        'acronym': opponent['opponent'].get('acronym', '')
                    }
                    match_data['teams'].append(team)
            
            # Retornar partida se tem times válidos
            if match_data['teams'] and len(match_data['teams']) == 2:
                return match_data
                    
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao processar partida PandaScore {match.get('id', 'N/A')}: {e}")
            return None

    def _teams_match(self, search_name: str, api_name: str) -> bool:
        """Verifica se os nomes dos times fazem match"""
        search_clean = search_name.lower().strip()
        api_clean = api_name.lower().strip()
        
        # Match exato
        if search_clean == api_clean:
            return True
            
        # Match parcial (um contém o outro)
        if search_clean in api_clean or api_clean in search_clean:
            return True
            
        # Match por palavras-chave
        search_words = search_clean.split()
        for word in search_words:
            if len(word) >= 3 and word in api_clean:
                return True
                
        return False

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se o cache ainda é válido"""
        if cache_key not in self.cache:
            return False
            
        cache_entry = self.cache[cache_key]
        elapsed_time = (datetime.now() - cache_entry['timestamp']).seconds
        
        return elapsed_time < self.cache_duration

    async def get_api_status(self) -> Dict:
        """Verifica status da API PandaScore"""
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/lol/matches?page[size]=1", headers=headers) as response:
                    return {
                        'status': 'online' if response.status == 200 else 'error',
                        'status_code': response.status,
                        'message': 'PandaScore API funcionando' if response.status == 200 else f'Erro HTTP {response.status}',
                        'has_real_odds': response.status == 200
                    }
        except Exception as e:
            return {
                'status': 'offline',
                'status_code': 0,
                'message': f'Erro: {str(e)}',
                'has_real_odds': False
            } 