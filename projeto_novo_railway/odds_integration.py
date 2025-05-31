#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA DE INTEGRAÇÃO COM APIS DE ODDS REAIS
PandaScore + The Odds API + Sistema Híbrido
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Configurações das APIs
PANDASCORE_API_KEY = os.getenv('PANDASCORE_API_KEY', '90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ')
THE_ODDS_API_KEY = os.getenv('THE_ODDS_API_KEY', '8cff2fb4dafc21c0ac5c04862903990d')
USE_REAL_ODDS = os.getenv('USE_REAL_ODDS', 'true').lower() == 'true'

class PandaScoreClient:
    """Cliente para PandaScore API - eSports odds e dados"""
    
    def __init__(self):
        self.api_key = PANDASCORE_API_KEY
        self.base_url = "https://api.pandascore.co"
        self.cache = {}
        self.cache_duration = 300  # 5 minutos
        
        # Headers para autenticação
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
        
        logger.info("🐼 PandaScore Client inicializado")
    
    async def get_live_lol_matches(self) -> List[Dict]:
        """Busca partidas de LoL ao vivo com odds"""
        cache_key = "live_lol_matches"
        
        # Verificar cache
        if self._is_cache_valid(cache_key):
            logger.debug("📊 Usando cache para partidas LoL ao vivo")
            return self.cache[cache_key]['data']
        
        try:
            url = f"{self.base_url}/lol/matches/running"
            params = {
                'sort': '',
                'page': 1,
                'per_page': 50
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches = self._process_live_matches(data)
                        
                        # Cache dos resultados
                        self.cache[cache_key] = {
                            'data': matches,
                            'timestamp': time.time()
                        }
                        
                        logger.info(f"🐼 PandaScore: {len(matches)} partidas LoL ao vivo")
                        return matches
                    
                    elif response.status == 401:
                        logger.error("❌ PandaScore: API Key inválida")
                        return []
                    
                    elif response.status == 429:
                        logger.warning("⚠️ PandaScore: Rate limit atingido")
                        return []
                    
                    else:
                        logger.warning(f"⚠️ PandaScore: Status {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar partidas PandaScore: {e}")
            return []
    
    async def get_match_odds(self, match_id: str) -> Optional[Dict]:
        """Busca odds específicas para uma partida"""
        cache_key = f"odds_{match_id}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            url = f"{self.base_url}/lol/matches/{match_id}/betting-odds"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        odds = self._process_odds(data)
                        
                        # Cache
                        self.cache[cache_key] = {
                            'data': odds,
                            'timestamp': time.time()
                        }
                        
                        return odds
                    
                    else:
                        logger.debug(f"PandaScore odds indisponíveis para match {match_id}")
                        return None
        
        except Exception as e:
            logger.debug(f"Erro ao buscar odds PandaScore: {e}")
            return None
    
    async def get_upcoming_matches(self, days_ahead: int = 7) -> List[Dict]:
        """Busca próximas partidas de LoL com odds"""
        cache_key = f"upcoming_lol_{days_ahead}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Data limite
            end_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
            
            url = f"{self.base_url}/lol/matches/upcoming"
            params = {
                'sort': 'begin_at',
                'page': 1,
                'per_page': 100,
                'filter[begin_at]': f'<{end_date}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches = self._process_upcoming_matches(data)
                        
                        # Cache
                        self.cache[cache_key] = {
                            'data': matches,
                            'timestamp': time.time()
                        }
                        
                        logger.info(f"🐼 PandaScore: {len(matches)} próximas partidas")
                        return matches
                    
                    else:
                        logger.warning(f"PandaScore upcoming matches: Status {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Erro ao buscar próximas partidas PandaScore: {e}")
            return []
    
    def _process_live_matches(self, data: List[Dict]) -> List[Dict]:
        """Processa dados de partidas ao vivo"""
        processed = []
        
        for match in data:
            try:
                processed_match = {
                    'id': str(match.get('id', '')),
                    'team1': {
                        'name': match.get('opponents', [{}])[0].get('opponent', {}).get('name', 'Team 1'),
                        'id': str(match.get('opponents', [{}])[0].get('opponent', {}).get('id', ''))
                    },
                    'team2': {
                        'name': match.get('opponents', [{}])[1].get('opponent', {}).get('name', 'Team 2') if len(match.get('opponents', [])) > 1 else 'Team 2',
                        'id': str(match.get('opponents', [{}])[1].get('opponent', {}).get('id', '')) if len(match.get('opponents', [])) > 1 else ''
                    },
                    'league': match.get('serie', {}).get('full_name', match.get('league', {}).get('name', 'Unknown')),
                    'status': match.get('status', 'live'),
                    'begin_at': match.get('begin_at', ''),
                    'game_time': match.get('game_time', 0),
                    'source': 'pandascore'
                }
                processed.append(processed_match)
                
            except Exception as e:
                logger.debug(f"Erro ao processar partida live PandaScore: {e}")
                continue
        
        return processed
    
    def _process_upcoming_matches(self, data: List[Dict]) -> List[Dict]:
        """Processa dados de próximas partidas"""
        processed = []
        
        for match in data:
            try:
                processed_match = {
                    'id': str(match.get('id', '')),
                    'team1': {
                        'name': match.get('opponents', [{}])[0].get('opponent', {}).get('name', 'Team 1'),
                        'id': str(match.get('opponents', [{}])[0].get('opponent', {}).get('id', ''))
                    },
                    'team2': {
                        'name': match.get('opponents', [{}])[1].get('opponent', {}).get('name', 'Team 2') if len(match.get('opponents', [])) > 1 else 'Team 2',
                        'id': str(match.get('opponents', [{}])[1].get('opponent', {}).get('id', '')) if len(match.get('opponents', [])) > 1 else ''
                    },
                    'league': match.get('serie', {}).get('full_name', match.get('league', {}).get('name', 'Unknown')),
                    'status': 'scheduled',
                    'begin_at': match.get('begin_at', ''),
                    'scheduled_at': match.get('scheduled_at', ''),
                    'source': 'pandascore'
                }
                processed.append(processed_match)
                
            except Exception as e:
                logger.debug(f"Erro ao processar partida upcoming PandaScore: {e}")
                continue
        
        return processed
    
    def _process_odds(self, data: List[Dict]) -> Dict:
        """Processa dados de odds"""
        if not data:
            return {
                'available': False,
                'team1_odds': None,
                'team2_odds': None,
                'bookmaker': 'PandaScore'
            }
        
        try:
            # Pegar primeira entrada disponível
            odds_entry = data[0]
            
            if 'outcomes' in odds_entry and len(odds_entry['outcomes']) >= 2:
                outcomes = odds_entry['outcomes']
                
                return {
                    'available': True,
                    'team1_odds': float(outcomes[0].get('odds', 0)),
                    'team2_odds': float(outcomes[1].get('odds', 0)),
                    'bookmaker': odds_entry.get('bookmaker', {}).get('name', 'PandaScore'),
                    'margin': self._calculate_margin(float(outcomes[0].get('odds', 0)), float(outcomes[1].get('odds', 0))),
                    'source': 'pandascore'
                }
            
            else:
                return {
                    'available': False,
                    'team1_odds': None,
                    'team2_odds': None,
                    'bookmaker': 'PandaScore'
                }
        
        except Exception as e:
            logger.debug(f"Erro ao processar odds: {e}")
            return {
                'available': False,
                'team1_odds': None,
                'team2_odds': None,
                'bookmaker': 'PandaScore'
            }
    
    def _calculate_margin(self, odds1: float, odds2: float) -> float:
        """Calcula margem da casa de apostas"""
        if odds1 > 0 and odds2 > 0:
            prob1 = 1 / odds1
            prob2 = 1 / odds2
            margin = ((prob1 + prob2) - 1) * 100
            return round(margin, 2)
        return 0.0
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica se cache é válido"""
        if key not in self.cache:
            return False
        
        elapsed = time.time() - self.cache[key]['timestamp']
        return elapsed < self.cache_duration
    
    def clear_cache(self):
        """Limpa cache"""
        self.cache.clear()
        logger.info("🐼 Cache PandaScore limpo")


class TheOddsAPIClient:
    """Cliente para The Odds API - Odds de casas de apostas reais"""
    
    def __init__(self):
        self.api_key = THE_ODDS_API_KEY
        self.base_url = "https://api.the-odds-api.com/v4"
        self.cache = {}
        self.cache_duration = 180  # 3 minutos para odds
        
        logger.info(f"💰 The Odds API Client inicializado")
    
    async def get_esports_odds(self, region: str = "us") -> List[Dict]:
        """Busca odds de eSports - usando endpoint geral de esportes"""
        cache_key = f"esports_odds_{region}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # The Odds API não tem endpoint específico para esports
            # Vamos buscar esportes que podem incluir esports
            url = f"{self.base_url}/sports"
            params = {
                'apiKey': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                # Primeiro buscar lista de esportes disponíveis
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        sports_data = await response.json()
                        logger.debug(f"💰 The Odds API: {len(sports_data)} esportes disponíveis")
                        
                        # Não retornar dados agora, pois seria necessário fazer muitas chamadas
                        # para cada esporte individualmente. Retornar lista vazia por agora.
                        
                        # Cache resultado vazio
                        self.cache[cache_key] = {
                            'data': [],
                            'timestamp': time.time()
                        }
                        
                        return []
                    
                    elif response.status == 401:
                        logger.error("❌ The Odds API: API Key inválida")
                        return []
                    
                    elif response.status == 429:
                        logger.warning("⚠️ The Odds API: Rate limit atingido")
                        return []
                    
                    else:
                        logger.warning(f"⚠️ The Odds API: Status {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar esportes The Odds API: {e}")
            return []
    
    async def find_match_odds(self, team1: str, team2: str) -> Optional[Dict]:
        """Encontra odds para uma partida específica - busca em esportes populares"""
        try:
            # The Odds API funciona por esporte específico
            # Para eSports, tentaremos alguns esportes que podem ter cobertura
            
            # Por simplicidade, não vamos fazer múltiplas chamadas
            # Retornamos None para usar o fallback simulado
            logger.debug(f"⚠️ The Odds API: Busca por esports ainda não implementada completamente")
            logger.debug(f"💡 Para implementar: seria necessário chamar endpoint específico por esporte")
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds da partida: {e}")
            return None
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica se cache é válido"""
        if key not in self.cache:
            return False
        
        elapsed = time.time() - self.cache[key]['timestamp']
        return elapsed < self.cache_duration


class HybridOddsSystem:
    """Sistema híbrido que combina PandaScore + The Odds API + simulação"""
    
    def __init__(self):
        self.pandascore = PandaScoreClient() if USE_REAL_ODDS else None
        self.theodds = TheOddsAPIClient() if USE_REAL_ODDS else None
        self.use_real_odds = USE_REAL_ODDS
        
        logger.info(f"🔄 Sistema Híbrido de Odds inicializado (Real: {USE_REAL_ODDS})")
    
    async def get_match_odds(self, team1: str, team2: str, match_id: str = None) -> Dict:
        """Busca odds de múltiplas fontes com fallback"""
        
        if not self.use_real_odds:
            return self._generate_simulated_odds(team1, team2)
        
        odds_results = []
        
        # 1. Tentar PandaScore (se temos match_id)
        if self.pandascore and match_id:
            try:
                panda_odds = await self.pandascore.get_match_odds(match_id)
                if panda_odds and panda_odds.get('available'):
                    odds_results.append(panda_odds)
                    logger.debug(f"✅ Odds PandaScore obtidas para {team1} vs {team2}")
            except Exception as e:
                logger.debug(f"PandaScore odds error: {e}")
        
        # 2. Tentar The Odds API
        if self.theodds:
            try:
                theodds_odds = await self.theodds.find_match_odds(team1, team2)
                if theodds_odds and theodds_odds.get('available'):
                    odds_results.append(theodds_odds)
                    logger.debug(f"✅ Odds The Odds API obtidas para {team1} vs {team2}")
            except Exception as e:
                logger.debug(f"The Odds API error: {e}")
        
        # 3. Processar resultados
        if odds_results:
            # Usar primeira fonte válida ou combinar múltiplas fontes
            best_odds = self._select_best_odds(odds_results)
            best_odds['sources_count'] = len(odds_results)
            best_odds['sources'] = [result.get('source', 'unknown') for result in odds_results]
            return best_odds
        
        else:
            # Fallback para odds simuladas
            logger.debug(f"📊 Usando odds simuladas para {team1} vs {team2}")
            return self._generate_simulated_odds(team1, team2)
    
    async def get_live_matches_with_odds(self) -> List[Dict]:
        """Busca partidas ao vivo com odds"""
        
        if not self.use_real_odds:
            return []
        
        all_matches = []
        
        # 1. PandaScore live matches
        if self.pandascore:
            try:
                panda_matches = await self.pandascore.get_live_lol_matches()
                all_matches.extend(panda_matches)
            except Exception as e:
                logger.debug(f"PandaScore live matches error: {e}")
        
        # 2. Enriquecer com odds de múltiplas fontes
        for match in all_matches:
            try:
                odds = await self.get_match_odds(
                    match['team1']['name'], 
                    match['team2']['name'], 
                    match.get('id')
                )
                match['odds'] = odds
                
            except Exception as e:
                logger.debug(f"Erro ao obter odds para partida: {e}")
                match['odds'] = self._generate_simulated_odds(
                    match['team1']['name'], 
                    match['team2']['name']
                )
        
        return all_matches
    
    async def get_upcoming_matches_with_odds(self, days_ahead: int = 7) -> List[Dict]:
        """Busca próximas partidas com odds"""
        
        if not self.use_real_odds:
            return []
        
        all_matches = []
        
        # PandaScore upcoming matches
        if self.pandascore:
            try:
                panda_matches = await self.pandascore.get_upcoming_matches(days_ahead)
                all_matches.extend(panda_matches)
            except Exception as e:
                logger.debug(f"PandaScore upcoming matches error: {e}")
        
        # Enriquecer com odds
        for match in all_matches:
            try:
                odds = await self.get_match_odds(
                    match['team1']['name'], 
                    match['team2']['name'], 
                    match.get('id')
                )
                match['odds'] = odds
                
            except Exception as e:
                logger.debug(f"Erro ao obter odds para partida upcoming: {e}")
                match['odds'] = self._generate_simulated_odds(
                    match['team1']['name'], 
                    match['team2']['name']
                )
        
        return all_matches
    
    def _select_best_odds(self, odds_results: List[Dict]) -> Dict:
        """Seleciona as melhores odds dentre múltiplas fontes"""
        if not odds_results:
            return {}
        
        # Por enquanto, usar primeira fonte válida
        # No futuro, pode implementar lógica para escolher melhor odd
        best = odds_results[0].copy()
        
        # Se há múltiplas fontes, marcar como verificado
        if len(odds_results) > 1:
            best['verified'] = True
            best['confidence'] = 'high'
        else:
            best['verified'] = False
            best['confidence'] = 'medium'
        
        return best
    
    def _generate_simulated_odds(self, team1: str, team2: str) -> Dict:
        """Gera odds simuladas baseadas em probabilidades"""
        import random
        
        # Simular probabilidades baseadas em nomes dos times (mock)
        base_prob = 0.5 + (random.random() - 0.5) * 0.3  # 0.35 a 0.65
        
        # Aplicar margem da casa (5-8%)
        margin = 0.06
        team1_prob = base_prob * (1 - margin)
        team2_prob = (1 - base_prob) * (1 - margin)
        
        team1_odds = 1 / team1_prob if team1_prob > 0 else 2.0
        team2_odds = 1 / team2_prob if team2_prob > 0 else 2.0
        
        return {
            'available': True,
            'team1_odds': round(team1_odds, 2),
            'team2_odds': round(team2_odds, 2),
            'bookmaker': 'Simulado',
            'margin': margin * 100,
            'source': 'simulated',
            'confidence': 'low',
            'verified': False
        }
    
    async def get_system_status(self) -> Dict:
        """Status do sistema de odds"""
        status = {
            'real_odds_enabled': self.use_real_odds,
            'pandascore_available': self.pandascore is not None,
            'theodds_available': self.theodds is not None,
            'api_keys_configured': {
                'pandascore': bool(PANDASCORE_API_KEY and PANDASCORE_API_KEY != 'NOT_SET'),
                'theodds': bool(THE_ODDS_API_KEY and THE_ODDS_API_KEY != 'NOT_SET')
            }
        }
        
        return status


# Instância global
odds_system = HybridOddsSystem()


async def main():
    """Teste das funcionalidades"""
    print("🎲 TESTE DO SISTEMA DE ODDS HÍBRIDO")
    print("=" * 50)
    
    # Status do sistema
    status = await odds_system.get_system_status()
    print(f"\n📊 Status do Sistema:")
    print(f"   • Odds reais habilitadas: {status['real_odds_enabled']}")
    print(f"   • PandaScore disponível: {status['pandascore_available']}")
    print(f"   • The Odds API disponível: {status['theodds_available']}")
    
    # Teste de odds para partida simulada
    print(f"\n🎯 Teste de Odds para Partida:")
    odds = await odds_system.get_match_odds("T1", "GenG")
    print(f"   • T1 vs GenG:")
    print(f"     - Odds T1: {odds.get('team1_odds', 'N/A')}")
    print(f"     - Odds GenG: {odds.get('team2_odds', 'N/A')}")
    print(f"     - Casa: {odds.get('bookmaker', 'N/A')}")
    print(f"     - Fonte: {odds.get('source', 'N/A')}")
    
    if USE_REAL_ODDS:
        # Teste de partidas ao vivo
        print(f"\n⚡ Buscando Partidas ao Vivo...")
        live_matches = await odds_system.get_live_matches_with_odds()
        print(f"   • {len(live_matches)} partidas ao vivo encontradas")
        
        # Teste de próximas partidas
        print(f"\n📅 Buscando Próximas Partidas...")
        upcoming = await odds_system.get_upcoming_matches_with_odds(days_ahead=3)
        print(f"   • {len(upcoming)} próximas partidas encontradas")
    
    print(f"\n✅ Teste concluído!")


if __name__ == "__main__":
    asyncio.run(main()) 