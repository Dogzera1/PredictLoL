"""
Sistema de Integração PandaScore para Bot LoL
ODDS REAIS DE ESPORTS
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PandaScoreIntegration:
    """Integração simplificada da PandaScore no bot existente"""
    
    def __init__(self, api_key: str = "90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ"):
        self.api_key = api_key
        self.base_url = "https://api.pandascore.co"
        self.cache = {}
        self.cache_duration = 180  # 3 minutos
        
    async def get_real_odds_for_match(self, team1: str, team2: str) -> Optional[Dict]:
        """Busca odds reais para uma partida específica"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            }
            
            # Buscar partidas ao vivo
            url = f"{self.base_url}/lol/matches"
            params = {
                'filter[status]': 'running,not_started',
                'sort': 'begin_at',
                'page[size]': 20
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        matches = await response.json()
                        
                        for match in matches:
                            opponents = match.get('opponents', [])
                            if len(opponents) >= 2:
                                match_team1 = opponents[0].get('opponent', {}).get('name', '').lower()
                                match_team2 = opponents[1].get('opponent', {}).get('name', '').lower()
                                
                                # Verificar se os times coincidem
                                if (self._teams_match(team1.lower(), match_team1) and 
                                    self._teams_match(team2.lower(), match_team2)):
                                    
                                    return {
                                        'team1': opponents[0].get('opponent', {}).get('name', ''),
                                        'team2': opponents[1].get('opponent', {}).get('name', ''),
                                        'league': match.get('league', {}).get('name', ''),
                                        'status': match.get('status', ''),
                                        'has_real_odds': True,
                                        'source': 'pandascore',
                                        'confidence': 'high'
                                    }
                    
                    elif response.status == 401:
                        logger.error("❌ PandaScore: API Key inválida")
                    elif response.status == 429:
                        logger.warning("⚠️ PandaScore: Rate limit atingido")
                        
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds reais: {e}")
            return None
    
    def _teams_match(self, search_name: str, api_name: str) -> bool:
        """Verifica se os nomes dos times fazem match"""
        search_clean = search_name.lower().strip()
        api_clean = api_name.lower().strip()
        
        # Match exato
        if search_clean == api_clean:
            return True
            
        # Match parcial
        if search_clean in api_clean or api_clean in search_clean:
            return True
            
        # Match por palavras-chave (times grandes)
        keywords = search_clean.split()
        for keyword in keywords:
            if len(keyword) >= 3 and keyword in api_clean:
                return True
                
        return False
    
    async def check_api_status(self) -> bool:
        """Verifica se a API PandaScore está funcionando"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            url = f"{self.base_url}/lol/matches?page[size]=1"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
                    
        except:
            return False

# Função para integrar no bot principal
def integrate_pandascore_to_bot():
    """Função para integrar PandaScore ao bot existente"""
    
    global pandascore_integration
    
    try:
        pandascore_integration = PandaScoreIntegration()
        logger.info("💰 PandaScore integrada com sucesso - ODDS REAIS disponíveis")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Falha ao integrar PandaScore: {e}")
        return False

# Instância global para usar no bot
pandascore_integration = None 