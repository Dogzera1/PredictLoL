"""
Sistema Multi-API para League of Legends - APIs GRATUITAS
Integra múltiplas APIs gratuitas para complementar PandaScore/Riot API
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MultiAPIClient:
    """Cliente para múltiplas APIs gratuitas de LoL"""
    
    def __init__(self):
        self.session = None
        self.free_apis = {
            'community_dragon': 'https://cdn.communitydragon.org/latest',
            'ddragon': 'https://ddragon.leagueoflegends.com/cdn',
            'thesportsdb': 'https://www.thesportsdb.com/api/v1/json/3'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_champion_details(self, champion_name: str) -> Optional[Dict]:
        """🆓 CommunityDragon API - Dados detalhados de champions"""
        try:
            url = f"{self.free_apis['community_dragon']}/champion/{champion_name}/data"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'champion': champion_name,
                        'abilities': data.get('abilities', []),
                        'passive': data.get('passive', {}),
                        'stats': data.get('stats', {}),
                        'skins': data.get('skins', []),
                        'source': 'community_dragon_free',
                        'api_cost': 'FREE'
                    }
        except Exception as e:
            logger.warning(f"❌ CommunityDragon falhou para {champion_name}: {e}")
            return None
    
    async def get_current_patch(self) -> Optional[str]:
        """🆓 Data Dragon - Versão atual do patch"""
        try:
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            async with self.session.get(url) as response:
                if response.status == 200:
                    versions = await response.json()
                    return versions[0] if versions else None
        except Exception as e:
            logger.warning(f"❌ Erro ao buscar patch: {e}")
            return None
    
    async def get_all_champions_stats(self, patch: str = None) -> Optional[Dict]:
        """🆓 Data Dragon - Stats de todos os champions"""
        try:
            if not patch:
                patch = await self.get_current_patch()
            
            url = f"{self.free_apis['ddragon']}/{patch}/data/en_US/champion.json"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'patch': patch,
                        'champions': data.get('data', {}),
                        'source': 'data_dragon_free',
                        'api_cost': 'FREE'
                    }
        except Exception as e:
            logger.warning(f"❌ Erro ao buscar stats dos champions: {e}")
            return None
    
    async def get_enhanced_match_analysis(self, team1_champions: List[str], team2_champions: List[str]) -> Optional[Dict]:
        """🆓 Análise combinada usando múltiplas APIs gratuitas"""
        try:
            # Busca dados de ambos os times em paralelo
            tasks = []
            for champion in team1_champions + team2_champions:
                tasks.append(self.get_champion_details(champion))
            
            champions_data = await asyncio.gather(*tasks)
            valid_data = [data for data in champions_data if data is not None]
            
            if not valid_data:
                return None
            
            # Separa dados por time
            team1_data = valid_data[:len(team1_champions)]
            team2_data = valid_data[len(team1_champions):]
            
            analysis = {
                'analysis_timestamp': datetime.now().isoformat(),
                'team1': {
                    'champions': team1_champions,
                    'data': team1_data,
                    'composition_score': self._calculate_team_score(team1_data),
                    'damage_types': self._analyze_damage_types(team1_data),
                    'power_spikes': self._analyze_power_spikes(team1_data)
                },
                'team2': {
                    'champions': team2_champions,
                    'data': team2_data,
                    'composition_score': self._calculate_team_score(team2_data),
                    'damage_types': self._analyze_damage_types(team2_data),
                    'power_spikes': self._analyze_power_spikes(team2_data)
                },
                'match_prediction': self._predict_match_outcome(team1_data, team2_data),
                'source': 'multi_api_free_analysis',
                'apis_used': ['community_dragon', 'data_dragon'],
                'total_cost': 'FREE'
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise combinada: {e}")
            return None
    
    def _calculate_team_score(self, team_data: List[Dict]) -> int:
        """Calcula score da composição do time (0-100)"""
        if not team_data:
            return 0
        
        score = 50  # Base score
        
        # Ajusta baseado no número de champions analisados
        coverage = len(team_data) / 5  # Assume 5 champions por time
        score += int(coverage * 20)
        
        # Análise básica de stats
        total_hp = 0
        total_damage = 0
        
        for champ in team_data:
            stats = champ.get('stats', {})
            total_hp += stats.get('hp', 500)
            total_damage += stats.get('attackdamage', 50)
        
        # Normaliza scores
        avg_hp = total_hp / len(team_data) if team_data else 500
        avg_damage = total_damage / len(team_data) if team_data else 50
        
        # HP score (tankiness)
        if avg_hp > 600:
            score += 10
        elif avg_hp < 450:
            score -= 5
        
        # Damage score
        if avg_damage > 60:
            score += 10
        elif avg_damage < 45:
            score -= 5
        
        return max(0, min(100, score))
    
    def _analyze_damage_types(self, team_data: List[Dict]) -> Dict:
        """Analisa distribuição de tipos de dano"""
        damage_analysis = {
            'physical_heavy': 0,
            'magic_heavy': 0,
            'mixed': 0,
            'balance_score': 50
        }
        
        for champ in team_data:
            stats = champ.get('stats', {})
            ad = stats.get('attackdamage', 50)
            ap = stats.get('ap', 0)  # Caso tenha
            
            if ad > ap + 30:
                damage_analysis['physical_heavy'] += 1
            elif ap > ad + 30:
                damage_analysis['magic_heavy'] += 1
            else:
                damage_analysis['mixed'] += 1
        
        # Calcula balance score
        total = len(team_data)
        if total > 0:
            physical_ratio = damage_analysis['physical_heavy'] / total
            magic_ratio = damage_analysis['magic_heavy'] / total
            
            # Time balanceado tem mix de dano
            if 0.3 <= physical_ratio <= 0.7 and 0.3 <= magic_ratio <= 0.7:
                damage_analysis['balance_score'] = 80
            elif physical_ratio > 0.8 or magic_ratio > 0.8:
                damage_analysis['balance_score'] = 30  # Muito unidimensional
                
        return damage_analysis
    
    def _analyze_power_spikes(self, team_data: List[Dict]) -> Dict:
        """Analisa power spikes do time"""
        return {
            'early_game': 60,  # Score base
            'mid_game': 70,
            'late_game': 75,
            'key_items': ['Mythic Items', 'Core Items'],
            'team_fight_potential': 65
        }
    
    def _predict_match_outcome(self, team1_data: List[Dict], team2_data: List[Dict]) -> Dict:
        """Predição simples baseada nos dados gratuitos"""
        team1_score = self._calculate_team_score(team1_data)
        team2_score = self._calculate_team_score(team2_data)
        
        if abs(team1_score - team2_score) < 10:
            prediction = "Even match"
            confidence = 55
        elif team1_score > team2_score:
            prediction = "Team1 favored"
            confidence = min(90, 50 + (team1_score - team2_score))
        else:
            prediction = "Team2 favored"
            confidence = min(90, 50 + (team2_score - team1_score))
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'team1_score': team1_score,
            'team2_score': team2_score,
            'data_quality': 'good' if len(team1_data) + len(team2_data) >= 8 else 'limited'
        }
    
    async def get_champion_tips(self, champion_name: str) -> Optional[Dict]:
        """🆓 Gera tips específicos do champion usando dados gratuitos"""
        try:
            champ_data = await self.get_champion_details(champion_name)
            
            if not champ_data:
                return None
            
            stats = champ_data.get('stats', {})
            abilities = champ_data.get('abilities', [])
            
            tips = []
            
            # Tips baseados em stats
            hp = stats.get('hp', 500)
            if hp < 500:
                tips.append(f"{champion_name} é frágil - foque em posicionamento")
            elif hp > 650:
                tips.append(f"{champion_name} é tanque - pode iniciar fights")
            
            # Tips baseados em habilidades
            if len(abilities) >= 4:
                tips.append(f"{champion_name} tem kit completo - versátil em teamfights")
            
            return {
                'champion': champion_name,
                'tips': tips,
                'stats_summary': {
                    'survivability': 'high' if hp > 600 else 'medium' if hp > 450 else 'low',
                    'damage_potential': 'high' if stats.get('attackdamage', 50) > 60 else 'medium'
                },
                'source': 'free_api_tips',
                'api_cost': 'FREE'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar tips para {champion_name}: {e}")
            return None
    
    async def health_check(self) -> Dict[str, bool]:
        """🆓 Verifica saúde das APIs gratuitas"""
        health_status = {}
        
        # Test CommunityDragon
        try:
            url = f"{self.free_apis['community_dragon']}/champion/Aatrox/data"
            async with self.session.get(url, timeout=5) as response:
                health_status['community_dragon'] = response.status == 200
        except:
            health_status['community_dragon'] = False
        
        # Test Data Dragon
        try:
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            async with self.session.get(url, timeout=5) as response:
                health_status['data_dragon'] = response.status == 200
        except:
            health_status['data_dragon'] = False
        
        logger.info(f"🔍 Health check APIs gratuitas: {health_status}")
        return health_status
    
    def get_supported_apis(self) -> Dict[str, str]:
        """📋 Lista APIs gratuitas suportadas"""
        return {
            'community_dragon': '🆓 Assets, champions, abilities',
            'data_dragon': '🆓 Stats oficiais, patches, items',
            'thesportsdb': '🆓 Metadados esportivos (futuro)',
            'grid_open_access': '🆓 Dados oficiais Riot (futuro)',
            'total_cost': 'GRATUITO'
        }
