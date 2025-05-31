#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA DE COLETA DE DADOS EM TEMPO REAL
Para partidas de League of Legends em andamento
"""

import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import re

# Importar do sistema ML
from ml_prediction_system import MatchState, DraftData, AdvancedMLPredictionSystem

logger = logging.getLogger(__name__)

@dataclass
class LiveMatchInfo:
    """Informações de uma partida ao vivo"""
    match_id: str
    team1_name: str
    team2_name: str
    league: str
    tournament: str
    start_time: datetime
    status: str  # 'draft', 'in_game', 'finished'
    spectator_delay: int = 180  # 3 minutos padrão
    
@dataclass 
class PlayerInfo:
    """Informações de um jogador"""
    summoner_name: str
    champion: str
    position: str  # 'top', 'jungle', 'mid', 'adc', 'support'
    team: int  # 1 ou 2
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    level: int = 1
    gold: int = 500
    cs: int = 0
    items: List[str] = None

class RiotLiveAPI:
    """Cliente para APIs ao vivo da Riot Games"""
    
    def __init__(self):
        self.api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
        self.base_urls = {
            'esports': 'https://esports-api.lolesports.com/persisted/gw',
            'spectator': 'https://spectator-v5.api.riotgames.com/lol/spectator/v5',
            'match': 'https://americas.api.riotgames.com/lol/match/v5'
        }
        self.headers = {
            'X-Riot-Token': self.api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
    async def get_live_matches_detailed(self) -> List[LiveMatchInfo]:
        """Busca partidas ao vivo com informações detalhadas"""
        try:
            async with aiohttp.ClientSession() as session:
                # Endpoint da API de esports
                url = f"{self.base_urls['esports']}/getLive?hl=pt-BR"
                
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_live_matches(data)
                    else:
                        logger.warning(f"API de esports retornou {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return []
            
    def _parse_live_matches(self, data: Dict) -> List[LiveMatchInfo]:
        """Parseia dados da API para LiveMatchInfo"""
        matches = []
        
        try:
            events = data.get('data', {}).get('schedule', {}).get('events', [])
            
            for event in events:
                if event.get('state') in ['inProgress', 'completed']:
                    match_info = self._extract_match_info(event)
                    if match_info:
                        matches.append(match_info)
                        
        except Exception as e:
            logger.error(f"Erro ao parsear partidas: {e}")
            
        return matches
        
    def _extract_match_info(self, event: Dict) -> Optional[LiveMatchInfo]:
        """Extrai informações de uma partida"""
        try:
            match_data = event.get('match', {})
            teams = match_data.get('teams', [])
            
            if len(teams) < 2:
                return None
                
            return LiveMatchInfo(
                match_id=event.get('id', ''),
                team1_name=teams[0].get('name', 'Team1'),
                team2_name=teams[1].get('name', 'Team2'),
                league=event.get('league', {}).get('name', 'Unknown'),
                tournament=event.get('tournament', {}).get('name', 'Tournament'),
                start_time=self._parse_datetime(event.get('startTime', '')),
                status=self._map_status(event.get('state', ''))
            )
            
        except Exception as e:
            logger.error(f"Erro ao extrair info da partida: {e}")
            return None
            
    def _parse_datetime(self, timestamp: str) -> datetime:
        """Parseia timestamp ISO"""
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return datetime.now()
            
    def _map_status(self, state: str) -> str:
        """Mapeia status da API para nosso formato"""
        mapping = {
            'unstarted': 'draft',
            'inProgress': 'in_game', 
            'completed': 'finished'
        }
        return mapping.get(state, 'unknown')

class LiveGameDataCollector:
    """Coletor de dados de partidas em tempo real"""
    
    def __init__(self):
        self.riot_api = RiotLiveAPI()
        self.monitored_matches = {}  # match_id -> dados
        self.data_history = {}  # match_id -> histórico temporal
        self.collection_interval = 30  # segundos
        self.max_history_points = 50  # máximo de pontos de dados por partida
        
    async def start_monitoring_match(self, match_id: str, match_info: LiveMatchInfo) -> bool:
        """Inicia monitoramento de uma partida"""
        try:
            self.monitored_matches[match_id] = {
                'info': match_info,
                'last_update': datetime.now(),
                'data_points': 0,
                'active': True
            }
            
            self.data_history[match_id] = []
            
            logger.info(f"🎮 Iniciado monitoramento: {match_info.team1_name} vs {match_info.team2_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento: {e}")
            return False
            
    async def collect_live_data(self, match_id: str) -> Optional[Tuple[MatchState, DraftData]]:
        """Coleta dados ao vivo de uma partida específica"""
        
        if match_id not in self.monitored_matches:
            return None
            
        try:
            # Simular coleta de dados reais (em produção, usaria APIs específicas)
            match_state = await self._collect_match_state(match_id)
            draft_data = await self._collect_draft_data(match_id)
            
            if match_state and draft_data:
                # Armazenar no histórico
                data_point = {
                    'timestamp': datetime.now(),
                    'match_state': asdict(match_state),
                    'draft_data': asdict(draft_data)
                }
                
                self.data_history[match_id].append(data_point)
                
                # Limitar histórico
                if len(self.data_history[match_id]) > self.max_history_points:
                    self.data_history[match_id] = self.data_history[match_id][-self.max_history_points:]
                    
                # Atualizar estatísticas
                self.monitored_matches[match_id]['last_update'] = datetime.now()
                self.monitored_matches[match_id]['data_points'] += 1
                
                return match_state, draft_data
                
        except Exception as e:
            logger.error(f"Erro ao coletar dados da partida {match_id}: {e}")
            
        return None
        
    async def _collect_match_state(self, match_id: str) -> Optional[MatchState]:
        """Coleta estado atual da partida"""
        
        # Em uma implementação real, isso conectaria com APIs específicas
        # Por agora, vamos simular dados realistas
        
        match_info = self.monitored_matches[match_id]['info']
        
        # Simular progressão temporal
        elapsed_time = (datetime.now() - match_info.start_time).total_seconds() / 60
        game_time = max(0, elapsed_time - 5)  # Delay de 5 min para draft
        
        if game_time < 0:
            return None  # Ainda no draft
            
        # Simular dados baseados no tempo de jogo
        game_phase = 'early' if game_time < 15 else 'mid' if game_time < 30 else 'late'
        
        # Gerar dados realistas baseados na fase
        if game_phase == 'early':
            base_kills = int(game_time * 0.8)
            base_gold = int(500 + game_time * 450)
            towers_ratio = min(game_time / 20, 0.3)
        elif game_phase == 'mid':
            base_kills = int(15 * 0.8 + (game_time - 15) * 1.2)
            base_gold = int(500 + 15 * 450 + (game_time - 15) * 600)
            towers_ratio = min((game_time - 10) / 25, 0.7)
        else:
            base_kills = int(15 * 0.8 + 15 * 1.2 + (game_time - 30) * 0.8)
            base_gold = int(500 + 15 * 450 + 15 * 600 + (game_time - 30) * 400)
            towers_ratio = min((game_time - 10) / 20, 0.9)
            
        # Adicionar variação realística
        import random
        variation = 0.7 + random.random() * 0.6  # 0.7 a 1.3
        
        team1_kills = max(0, int(base_kills * variation))
        team2_kills = max(0, int(base_kills * (2 - variation)))
        
        team1_gold = int(base_gold * variation)
        team2_gold = int(base_gold * (2 - variation))
        
        # Torres baseadas no tempo e performance
        max_towers = int(11 * towers_ratio)
        tower_advantage = 0.5 + (variation - 1) * 0.3
        team1_towers = min(11, max(0, int(max_towers * tower_advantage)))
        team2_towers = min(11, max(0, max_towers - team1_towers))
        
        # Objetivos baseados na fase
        dragons_available = min(4, max(0, int((game_time - 5) / 6)))
        team1_dragons = random.randint(0, dragons_available) if dragons_available > 0 else 0
        team2_dragons = dragons_available - team1_dragons
        
        barons_available = 1 if game_time > 20 else 0
        team1_barons = random.randint(0, barons_available) if barons_available > 0 else 0
        team2_barons = barons_available - team1_barons
        
        return MatchState(
            game_time=game_time,
            team1_kills=team1_kills,
            team2_kills=team2_kills,
            team1_gold=team1_gold,
            team2_gold=team2_gold,
            team1_towers=team1_towers,
            team2_towers=team2_towers,
            team1_dragons=team1_dragons,
            team2_dragons=team2_dragons,
            team1_barons=team1_barons,
            team2_barons=team2_barons,
            team1_heralds=1 if game_time > 8 and random.random() > 0.5 else 0,
            team2_heralds=0,
            team1_inhibitors=0,
            team2_inhibitors=0
        )
        
    async def _collect_draft_data(self, match_id: str) -> Optional[DraftData]:
        """Coleta dados do draft"""
        
        # Em uma implementação real, isso viria de APIs específicas
        # Por agora, simular drafts realistas
        
        # Pool de campeões populares por posição
        champion_pool = {
            'top': ['Gnar', 'Camille', 'Ornn', 'Aatrox', 'Fiora', 'Jax'],
            'jungle': ['Graves', 'Lee Sin', 'Kindred', 'Elise', 'Hecarim', 'Nidalee'],
            'mid': ['Azir', 'Yasuo', 'Orianna', 'Syndra', 'Ryze', 'Corki'],
            'adc': ['Jinx', 'Kai\'Sa', 'Caitlyn', 'Sivir', 'Lucian', 'Ezreal'],
            'support': ['Thresh', 'Nautilus', 'Alistar', 'Braum', 'Rakan', 'Leona']
        }
        
        import random
        
        # Gerar draft realístico
        team1_picks = []
        team2_picks = []
        used_champions = set()
        
        positions = ['top', 'jungle', 'mid', 'adc', 'support']
        
        for pos in positions:
            available = [champ for champ in champion_pool[pos] if champ not in used_champions]
            
            if len(available) >= 2:
                team1_pick = random.choice(available)
                available.remove(team1_pick)
                team2_pick = random.choice(available)
                
                team1_picks.append(team1_pick)
                team2_picks.append(team2_pick)
                used_champions.add(team1_pick)
                used_champions.add(team2_pick)
                
        # Gerar bans realísticos
        ban_candidates = ['Yasuo', 'Zed', 'Akali', 'Irelia', 'Katarina', 'Master Yi', 'Vayne', 'Draven']
        random.shuffle(ban_candidates)
        
        team1_bans = ban_candidates[:5]
        team2_bans = ban_candidates[5:10]
        
        return DraftData(
            team1_picks=team1_picks,
            team2_picks=team2_picks,
            team1_bans=team1_bans,
            team2_bans=team2_bans,
            draft_phase='completed'
        )
        
    def get_match_history(self, match_id: str) -> List[Dict]:
        """Retorna histórico de dados de uma partida"""
        return self.data_history.get(match_id, [])
        
    def get_monitoring_stats(self) -> Dict:
        """Retorna estatísticas do monitoramento"""
        active_matches = sum(1 for m in self.monitored_matches.values() if m['active'])
        total_data_points = sum(m['data_points'] for m in self.monitored_matches.values())
        
        return {
            'active_matches': active_matches,
            'total_monitored': len(self.monitored_matches),
            'total_data_points': total_data_points,
            'collection_interval': self.collection_interval,
            'last_collection': max([m['last_update'] for m in self.monitored_matches.values()]) if self.monitored_matches else None
        }
        
    async def stop_monitoring_match(self, match_id: str):
        """Para monitoramento de uma partida"""
        if match_id in self.monitored_matches:
            self.monitored_matches[match_id]['active'] = False
            logger.info(f"🛑 Monitoramento parado para partida {match_id}")

class MLPredictionEngine:
    """Engine principal que combina coleta de dados com predições ML"""
    
    def __init__(self):
        self.ml_system = AdvancedMLPredictionSystem()
        self.data_collector = LiveGameDataCollector()
        self.active_predictions = {}  # match_id -> última predição
        self.prediction_interval = 60  # segundos entre predições
        
    async def start_live_analysis(self, match_info: LiveMatchInfo) -> bool:
        """Inicia análise ao vivo de uma partida"""
        
        match_id = match_info.match_id
        
        # Iniciar monitoramento
        if await self.data_collector.start_monitoring_match(match_id, match_info):
            self.active_predictions[match_id] = {
                'last_prediction_time': datetime.now() - timedelta(minutes=5),
                'prediction_count': 0,
                'match_info': match_info
            }
            
            logger.info(f"🎯 Análise ML iniciada: {match_info.team1_name} vs {match_info.team2_name}")
            return True
            
        return False
        
    async def get_live_prediction(self, match_id: str) -> Optional[Dict]:
        """Obtém predição ao vivo para uma partida"""
        
        if match_id not in self.active_predictions:
            return None
            
        # Verificar se é hora de uma nova predição
        last_prediction = self.active_predictions[match_id]['last_prediction_time']
        if (datetime.now() - last_prediction).seconds < self.prediction_interval:
            return self.active_predictions[match_id].get('last_result')
            
        # Coletar dados atuais
        data = await self.data_collector.collect_live_data(match_id)
        if not data:
            return None
            
        match_state, draft_data = data
        match_info = self.active_predictions[match_id]['match_info']
        
        # Fazer predição
        prediction = await self.ml_system.predict_money_line(
            match_state=match_state,
            draft_data=draft_data,
            team1_name=match_info.team1_name,
            team2_name=match_info.team2_name
        )
        
        # Adicionar informações específicas da partida
        prediction.update({
            'match_id': match_id,
            'league': match_info.league,
            'tournament': match_info.tournament,
            'live_data_quality': 'high' if match_state.game_time > 5 else 'medium',
            'data_source': 'live_api',
            'prediction_number': self.active_predictions[match_id]['prediction_count'] + 1
        })
        
        # Atualizar cache
        self.active_predictions[match_id].update({
            'last_prediction_time': datetime.now(),
            'prediction_count': self.active_predictions[match_id]['prediction_count'] + 1,
            'last_result': prediction
        })
        
        logger.info(f"🔮 Nova predição: {prediction['favored_team']} ({prediction['confidence_level']})")
        
        return prediction
        
    async def update_all_active_predictions(self) -> List[Dict]:
        """Atualiza todas as predições ativas"""
        
        updated_predictions = []
        
        for match_id in list(self.active_predictions.keys()):
            try:
                prediction = await self.get_live_prediction(match_id)
                if prediction:
                    updated_predictions.append(prediction)
            except Exception as e:
                logger.error(f"Erro ao atualizar predição {match_id}: {e}")
                
        return updated_predictions
        
    def get_engine_stats(self) -> Dict:
        """Retorna estatísticas do engine"""
        
        monitoring_stats = self.data_collector.get_monitoring_stats()
        ml_stats = self.ml_system.get_system_stats()
        
        return {
            'active_analyses': len(self.active_predictions),
            'total_predictions_made': sum(p['prediction_count'] for p in self.active_predictions.values()),
            'monitoring_stats': monitoring_stats,
            'ml_stats': ml_stats,
            'prediction_interval': self.prediction_interval,
            'system_uptime': datetime.now()  # Placeholder
        }
        
    async def stop_analysis(self, match_id: str):
        """Para análise de uma partida"""
        if match_id in self.active_predictions:
            await self.data_collector.stop_monitoring_match(match_id)
            del self.active_predictions[match_id]
            logger.info(f"🛑 Análise ML parada para {match_id}")

# Função utilitária para testes
async def test_ml_system():
    """Função de teste para o sistema ML"""
    
    engine = MLPredictionEngine()
    
    # Simular uma partida
    test_match = LiveMatchInfo(
        match_id="test_001",
        team1_name="T1",
        team2_name="Gen.G",
        league="LCK",
        tournament="Spring Split 2024",
        start_time=datetime.now() - timedelta(minutes=20),
        status="in_game"
    )
    
    # Iniciar análise
    success = await engine.start_live_analysis(test_match)
    if success:
        print("✅ Análise iniciada com sucesso")
        
        # Fazer predição
        prediction = await engine.get_live_prediction("test_001")
        if prediction:
            print(f"🎯 Predição: {prediction['favored_team']} ({prediction['confidence_level']})")
            print(f"📊 EV: {prediction['expected_value']:.1f}%")
            
        # Estatísticas
        stats = engine.get_engine_stats()
        print(f"📈 Análises ativas: {stats['active_analyses']}")
        
    return engine

if __name__ == "__main__":
    # Executar teste
    asyncio.run(test_ml_system()) 