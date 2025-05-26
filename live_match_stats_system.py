#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Avançado de Estatísticas de Partidas ao Vivo - BOT LOL V3
Captura dados detalhados como kills, mortes, assists, dragões, barão, gold, CS, etc.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

class LiveMatchStatsSystem:
    """Sistema para capturar estatísticas detalhadas de partidas ao vivo"""
    
    def __init__(self):
        self.api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
        self.base_urls = {
            'esports': 'https://esports-api.lolesports.com/persisted/gw',
            'feed': 'https://feed.lolesports.com',
            'stats': 'https://feed.lolesports.com/livestats/v1'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'x-api-key': self.api_key
        }
        self.active_matches = {}
        self.stats_cache = {}
        logger.info("🎮 LiveMatchStatsSystem inicializado")
    
    async def get_live_matches_with_stats(self) -> List[Dict]:
        """Busca partidas ao vivo com estatísticas detalhadas"""
        logger.info("🔍 Buscando partidas ao vivo com estatísticas...")
        
        # Primeiro, buscar partidas ao vivo básicas
        live_matches = await self._get_basic_live_matches()
        
        if not live_matches:
            logger.info("ℹ️ Nenhuma partida ao vivo encontrada")
            return []
        
        # Para cada partida, buscar estatísticas detalhadas
        matches_with_stats = []
        for match in live_matches:
            try:
                stats = await self._get_match_detailed_stats(match)
                if stats:
                    match['detailed_stats'] = stats
                    matches_with_stats.append(match)
                    logger.info(f"✅ Estatísticas obtidas para {match.get('match_name', 'Partida')}")
                else:
                    # Adicionar mesmo sem stats detalhadas
                    match['detailed_stats'] = self._get_fallback_stats()
                    matches_with_stats.append(match)
                    logger.info(f"⚠️ Usando stats básicas para {match.get('match_name', 'Partida')}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao obter stats para partida: {e}")
                continue
        
        return matches_with_stats
    
    async def _get_basic_live_matches(self) -> List[Dict]:
        """Busca informações básicas de partidas ao vivo"""
        endpoints = [
            f"{self.base_urls['esports']}/getLive?hl=en-US",
            f"{self.base_urls['stats']}/window",
            f"{self.base_urls['feed']}/livestats/v1/details",
            f"{self.base_urls['esports']}/getEventDetails?hl=en-US"
        ]
        
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, headers=self.headers, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            matches = self._extract_live_matches_basic(data)
                            if matches:
                                logger.info(f"🎮 {len(matches)} partidas encontradas em {endpoint}")
                                return matches
                        else:
                            logger.warning(f"⚠️ Endpoint {endpoint} retornou status {response.status}")
                            
            except Exception as e:
                logger.warning(f"❌ Erro no endpoint {endpoint}: {e}")
                continue
        
        return []
    
    def _extract_live_matches_basic(self, data: Dict) -> List[Dict]:
        """Extrai informações básicas das partidas"""
        matches = []
        
        try:
            # Tentar diferentes estruturas de dados
            possible_paths = [
                ['data', 'schedule', 'events'],
                ['data', 'events'],
                ['events'],
                ['data', 'live'],
                ['live'],
                ['matches'],
                ['data', 'matches']
            ]
            
            events = None
            for path in possible_paths:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    events = current
                    break
            
            if not events or not isinstance(events, list):
                return []
            
            for event in events:
                if not isinstance(event, dict):
                    continue
                
                # Verificar se é uma partida ao vivo
                status = event.get('state', event.get('status', '')).lower()
                if status in ['inprogress', 'live', 'ongoing', 'started']:
                    
                    # Extrair informações básicas
                    teams = self._extract_teams_info(event)
                    if len(teams) >= 2:
                        match = {
                            'match_id': event.get('id', f"match_{int(time.time())}"),
                            'match_name': f"{teams[0]['name']} vs {teams[1]['name']}", 
                            'teams': teams,
                            'league': self._extract_league_info(event),
                            'status': status,
                            'start_time': event.get('startTime', ''),
                            'tournament': event.get('tournament', {}).get('name', 'Unknown'),
                            'game_number': event.get('gameNumber', 1),
                            'series_type': event.get('strategy', {}).get('type', 'BO1')
                        }
                        matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Erro ao extrair partidas básicas: {e}")
            return []
    
    def _extract_teams_info(self, event: Dict) -> List[Dict]:
        """Extrai informações detalhadas dos times"""
        teams = []
        
        # Tentar diferentes estruturas
        possible_paths = [
            ['teams'],
            ['match', 'teams'],
            ['competitors'],
            ['participants']
        ]
        
        teams_data = None
        for path in possible_paths:
            current = event
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    break
            else:
                teams_data = current
                break
        
        if teams_data and isinstance(teams_data, list):
            for team_data in teams_data:
                if isinstance(team_data, dict):
                    team = {
                        'name': team_data.get('name', team_data.get('teamName', 'Unknown Team')),
                        'code': team_data.get('code', team_data.get('tricode', '')),
                        'score': team_data.get('score', 0),
                        'side': team_data.get('side', 'unknown'),
                        'id': team_data.get('id', ''),
                        'region': team_data.get('homeLeague', {}).get('name', 'Unknown')
                    }
                    teams.append(team)
        
        return teams
    
    def _extract_league_info(self, event: Dict) -> Dict:
        """Extrai informações da liga"""
        league_data = event.get('league', event.get('tournament', {}))
        
        return {
            'name': league_data.get('name', 'Unknown League'),
            'region': league_data.get('region', 'Unknown'),
            'tier': self._get_league_tier(league_data.get('name', '')),
            'id': league_data.get('id', '')
        }
    
    def _get_league_tier(self, league_name: str) -> str:
        """Determina o tier da liga"""
        tier1 = ['LCK', 'LPL', 'LEC', 'LCS']
        tier2 = ['CBLOL', 'LJL', 'PCS', 'VCS']
        
        league_upper = league_name.upper()
        
        if any(t1 in league_upper for t1 in tier1):
            return 'Tier 1'
        elif any(t2 in league_upper for t2 in tier2):
            return 'Tier 2'
        else:
            return 'Tier 3'
    
    async def _get_match_detailed_stats(self, match: Dict) -> Optional[Dict]:
        """Busca estatísticas detalhadas de uma partida específica"""
        match_id = match.get('match_id')
        
        if not match_id:
            return None
        
        # Tentar diferentes endpoints para stats detalhadas
        stats_endpoints = [
            f"{self.base_urls['stats']}/window/{match_id}",
            f"{self.base_urls['stats']}/details/{match_id}",
            f"{self.base_urls['feed']}/livestats/v1/window/{match_id}",
            f"{self.base_urls['esports']}/getWindow?gameId={match_id}"
        ]
        
        for endpoint in stats_endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, headers=self.headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            stats = self._parse_detailed_stats(data, match)
                            if stats:
                                return stats
                        else:
                            logger.debug(f"Stats endpoint {endpoint} retornou {response.status}")
                            
            except Exception as e:
                logger.debug(f"Erro no stats endpoint {endpoint}: {e}")
                continue
        
        # Se não conseguir dados reais, gerar stats simuladas baseadas no tempo
        return self._generate_realistic_stats(match)
    
    def _parse_detailed_stats(self, data: Dict, match: Dict) -> Optional[Dict]:
        """Parseia dados detalhados da API"""
        try:
            # Tentar extrair dados de diferentes estruturas
            game_data = data.get('gameMetadata', data.get('data', data))
            
            if not game_data:
                return None
            
            # Extrair estatísticas dos times
            teams_stats = []
            participants = game_data.get('participants', [])
            
            # Agrupar por time
            team1_players = []
            team2_players = []
            
            for participant in participants:
                if participant.get('teamId') == 100:
                    team1_players.append(participant)
                elif participant.get('teamId') == 200:
                    team2_players.append(participant)
            
            # Calcular stats dos times
            team1_stats = self._calculate_team_stats(team1_players, match['teams'][0])
            team2_stats = self._calculate_team_stats(team2_players, match['teams'][1])
            
            # Extrair objetivos
            objectives = self._extract_objectives(game_data)
            
            # Informações do jogo
            game_info = {
                'game_time': game_data.get('gameTime', 0),
                'game_length': self._format_game_time(game_data.get('gameTime', 0)),
                'patch': game_data.get('platformId', 'Unknown'),
                'map_id': game_data.get('mapId', 11)
            }
            
            return {
                'game_info': game_info,
                'teams': [team1_stats, team2_stats],
                'objectives': objectives,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao parsear stats detalhadas: {e}")
            return None
    
    def _calculate_team_stats(self, players: List[Dict], team_info: Dict) -> Dict:
        """Calcula estatísticas do time baseado nos jogadores"""
        if not players:
            return self._get_empty_team_stats(team_info)
        
        total_kills = sum(p.get('kills', 0) for p in players)
        total_deaths = sum(p.get('deaths', 0) for p in players)
        total_assists = sum(p.get('assists', 0) for p in players)
        total_gold = sum(p.get('goldEarned', 0) for p in players)
        total_cs = sum(p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0) for p in players)
        
        return {
            'team_info': team_info,
            'kills': total_kills,
            'deaths': total_deaths,
            'assists': total_assists,
            'kda': f"{total_kills}/{total_deaths}/{total_assists}",
            'gold': total_gold,
            'cs': total_cs,
            'avg_level': sum(p.get('champLevel', 1) for p in players) / len(players),
            'players': [self._format_player_stats(p) for p in players]
        }
    
    def _format_player_stats(self, player: Dict) -> Dict:
        """Formata estatísticas de um jogador"""
        return {
            'name': player.get('summonerName', 'Unknown'),
            'champion': player.get('championName', 'Unknown'),
            'kills': player.get('kills', 0),
            'deaths': player.get('deaths', 0),
            'assists': player.get('assists', 0),
            'cs': player.get('totalMinionsKilled', 0) + player.get('neutralMinionsKilled', 0),
            'gold': player.get('goldEarned', 0),
            'level': player.get('champLevel', 1),
            'items': player.get('items', [])
        }
    
    def _extract_objectives(self, game_data: Dict) -> Dict:
        """Extrai objetivos do jogo (dragões, barão, torres, etc.)"""
        objectives = {
            'dragons': {'team1': 0, 'team2': 0, 'types': []},
            'barons': {'team1': 0, 'team2': 0},
            'heralds': {'team1': 0, 'team2': 0},
            'towers': {'team1': 0, 'team2': 0},
            'inhibitors': {'team1': 0, 'team2': 0}
        }
        
        # Tentar extrair de diferentes estruturas
        events = game_data.get('events', game_data.get('timeline', {}).get('events', []))
        
        for event in events:
            event_type = event.get('type', '')
            team_id = event.get('teamId', 0)
            
            team_key = 'team1' if team_id == 100 else 'team2'
            
            if event_type == 'ELITE_MONSTER_KILL':
                monster_type = event.get('monsterType', '').lower()
                if 'dragon' in monster_type:
                    objectives['dragons'][team_key] += 1
                    objectives['dragons']['types'].append(monster_type)
                elif 'baron' in monster_type:
                    objectives['barons'][team_key] += 1
                elif 'herald' in monster_type:
                    objectives['heralds'][team_key] += 1
            
            elif event_type == 'BUILDING_KILL':
                building_type = event.get('buildingType', '').lower()
                if 'tower' in building_type:
                    objectives['towers'][team_key] += 1
                elif 'inhibitor' in building_type:
                    objectives['inhibitors'][team_key] += 1
        
        return objectives
    
    def _get_empty_team_stats(self, team_info: Dict) -> Dict:
        """Retorna stats vazias para um time"""
        return {
            'team_info': team_info,
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'kda': '0/0/0',
            'gold': 0,
            'cs': 0,
            'avg_level': 1,
            'players': []
        }
    
    def _generate_realistic_stats(self, match: Dict) -> Dict:
        """Gera estatísticas realistas baseadas no tempo de jogo"""
        import random
        
        # Estimar tempo de jogo baseado no horário de início
        start_time = match.get('start_time', '')
        if start_time:
            try:
                start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                game_time_minutes = (datetime.now() - start).total_seconds() / 60
                game_time_minutes = max(5, min(game_time_minutes, 60))  # Entre 5-60 minutos
            except:
                game_time_minutes = random.randint(15, 35)
        else:
            game_time_minutes = random.randint(15, 35)
        
        # Gerar stats baseadas no tempo
        base_kills = int(game_time_minutes * 0.8)  # ~0.8 kills por minuto por time
        base_gold = int(game_time_minutes * 1500)  # ~1500 gold por minuto por time
        base_cs = int(game_time_minutes * 8)  # ~8 CS por minuto por jogador
        
        team1_kills = random.randint(max(1, base_kills - 5), base_kills + 5)
        team2_kills = random.randint(max(1, base_kills - 5), base_kills + 5)
        
        # Dragões baseados no tempo (spawn a cada 5 min após 5 min)
        max_dragons = max(0, int((game_time_minutes - 5) / 5))
        total_dragons = min(random.randint(0, max_dragons + 1), 4)
        
        team1_dragons = random.randint(0, total_dragons)
        team2_dragons = total_dragons - team1_dragons
        
        # Barão (disponível após 20 min)
        baron_available = game_time_minutes > 20
        total_barons = random.randint(0, 1) if baron_available else 0
        team1_barons = random.randint(0, total_barons)
        team2_barons = total_barons - team1_barons
        
        return {
            'game_info': {
                'game_time': int(game_time_minutes * 60),
                'game_length': self._format_game_time(int(game_time_minutes * 60)),
                'patch': '14.10',
                'map_id': 11
            },
            'teams': [
                {
                    'team_info': match['teams'][0],
                    'kills': team1_kills,
                    'deaths': team2_kills,
                    'assists': team1_kills * 2,
                    'kda': f"{team1_kills}/{team2_kills}/{team1_kills * 2}",
                    'gold': base_gold + random.randint(-5000, 5000),
                    'cs': base_cs * 5 + random.randint(-50, 50),
                    'avg_level': min(18, 6 + int(game_time_minutes / 3)),
                    'players': []
                },
                {
                    'team_info': match['teams'][1],
                    'kills': team2_kills,
                    'deaths': team1_kills,
                    'assists': team2_kills * 2,
                    'kda': f"{team2_kills}/{team1_kills}/{team2_kills * 2}",
                    'gold': base_gold + random.randint(-5000, 5000),
                    'cs': base_cs * 5 + random.randint(-50, 50),
                    'avg_level': min(18, 6 + int(game_time_minutes / 3)),
                    'players': []
                }
            ],
            'objectives': {
                'dragons': {'team1': team1_dragons, 'team2': team2_dragons, 'types': ['infernal', 'mountain', 'cloud', 'ocean'][:total_dragons]},
                'barons': {'team1': team1_barons, 'team2': team2_barons},
                'heralds': {'team1': random.randint(0, 1), 'team2': random.randint(0, 1)},
                'towers': {'team1': random.randint(0, 6), 'team2': random.randint(0, 6)},
                'inhibitors': {'team1': random.randint(0, 2), 'team2': random.randint(0, 2)}
            },
            'last_updated': datetime.now().isoformat(),
            'data_source': 'simulated_realistic'
        }
    
    def _get_fallback_stats(self) -> Dict:
        """Retorna stats básicas quando não há dados disponíveis"""
        return {
            'game_info': {
                'game_time': 0,
                'game_length': '00:00',
                'patch': 'Unknown',
                'map_id': 11
            },
            'teams': [],
            'objectives': {
                'dragons': {'team1': 0, 'team2': 0, 'types': []},
                'barons': {'team1': 0, 'team2': 0},
                'heralds': {'team1': 0, 'team2': 0},
                'towers': {'team1': 0, 'team2': 0},
                'inhibitors': {'team1': 0, 'team2': 0}
            },
            'last_updated': datetime.now().isoformat(),
            'data_source': 'fallback'
        }
    
    def _format_game_time(self, seconds: int) -> str:
        """Formata tempo de jogo em MM:SS"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    def format_match_stats_message(self, match: Dict) -> str:
        """Formata estatísticas da partida para exibição"""
        stats = match.get('detailed_stats', {})
        
        if not stats or not stats.get('teams'):
            return self._format_basic_match(match)
        
        game_info = stats.get('game_info', {})
        teams = stats.get('teams', [])
        objectives = stats.get('objectives', {})
        
        if len(teams) < 2:
            return self._format_basic_match(match)
        
        team1, team2 = teams[0], teams[1]
        
        message = f"🔴 **{match.get('match_name', 'Partida ao Vivo')}**\n"
        message += f"🏆 **{match.get('league', {}).get('name', 'Unknown League')}**\n"
        message += f"⏱️ **Tempo:** {game_info.get('game_length', '00:00')}\n\n"
        
        # Placar de Kills
        message += f"⚔️ **PLACAR DE KILLS:**\n"
        message += f"🔵 **{team1['team_info']['name']}:** {team1['kills']} kills\n"
        message += f"🔴 **{team2['team_info']['name']}:** {team2['kills']} kills\n\n"
        
        # KDA dos times
        message += f"📊 **KDA DOS TIMES:**\n"
        message += f"🔵 {team1['team_info']['code']}: {team1['kda']}\n"
        message += f"🔴 {team2['team_info']['code']}: {team2['kda']}\n\n"
        
        # Gold
        message += f"💰 **GOLD:**\n"
        message += f"🔵 {team1['gold']:,}g vs 🔴 {team2['gold']:,}g\n"
        gold_diff = team1['gold'] - team2['gold']
        if gold_diff > 0:
            message += f"📈 Vantagem: {team1['team_info']['code']} (+{gold_diff:,}g)\n\n"
        elif gold_diff < 0:
            message += f"📈 Vantagem: {team2['team_info']['code']} (+{abs(gold_diff):,}g)\n\n"
        else:
            message += f"⚖️ Gold equilibrado\n\n"
        
        # Objetivos
        dragons = objectives.get('dragons', {})
        barons = objectives.get('barons', {})
        towers = objectives.get('towers', {})
        
        message += f"🐉 **OBJETIVOS:**\n"
        message += f"🐲 Dragões: {dragons.get('team1', 0)} - {dragons.get('team2', 0)}\n"
        message += f"🦅 Barão: {barons.get('team1', 0)} - {barons.get('team2', 0)}\n"
        message += f"🏰 Torres: {towers.get('team1', 0)} - {towers.get('team2', 0)}\n\n"
        
        # CS
        message += f"🗡️ **CS TOTAL:**\n"
        message += f"🔵 {team1['cs']} vs 🔴 {team2['cs']}\n\n"
        
        # Fonte dos dados
        data_source = stats.get('data_source', 'api')
        if data_source == 'simulated_realistic':
            message += f"📊 *Dados simulados baseados no tempo de jogo*\n"
        elif data_source == 'api':
            message += f"📡 *Dados em tempo real da API oficial*\n"
        else:
            message += f"📊 *Dados básicos disponíveis*\n"
        
        message += f"🔄 Atualizado: {datetime.now().strftime('%H:%M:%S')}"
        
        return message
    
    def _format_basic_match(self, match: Dict) -> str:
        """Formata partida básica sem stats detalhadas"""
        teams = match.get('teams', [])
        if len(teams) >= 2:
            message = f"🔴 **{teams[0]['name']} vs {teams[1]['name']}**\n"
            message += f"🏆 **{match.get('league', {}).get('name', 'Unknown League')}**\n"
            message += f"📊 **Status:** {match.get('status', 'Ao vivo').title()}\n"
            message += f"⚠️ *Estatísticas detalhadas não disponíveis*"
            return message
        else:
            return "❌ Dados da partida incompletos"

# Função para testar o sistema
async def test_live_stats_system():
    """Testa o sistema de estatísticas ao vivo"""
    print("🎮 TESTANDO SISTEMA DE ESTATÍSTICAS AO VIVO")
    print("=" * 50)
    
    stats_system = LiveMatchStatsSystem()
    
    try:
        matches = await stats_system.get_live_matches_with_stats()
        
        if matches:
            print(f"✅ {len(matches)} partidas encontradas com estatísticas!")
            
            for i, match in enumerate(matches, 1):
                print(f"\n📊 PARTIDA {i}:")
                print("-" * 30)
                message = stats_system.format_match_stats_message(match)
                print(message)
                
        else:
            print("ℹ️ Nenhuma partida ao vivo encontrada no momento")
            print("🎭 Gerando exemplo com dados simulados...")
            
            # Criar exemplo simulado
            example_match = {
                'match_id': 'example_123',
                'match_name': 'T1 vs GEN',
                'teams': [
                    {'name': 'T1', 'code': 'T1', 'score': 0, 'side': 'blue'},
                    {'name': 'Gen.G', 'code': 'GEN', 'score': 0, 'side': 'red'}
                ],
                'league': {'name': 'LCK', 'region': 'Korea', 'tier': 'Tier 1'},
                'status': 'live',
                'start_time': (datetime.now() - timedelta(minutes=25)).isoformat()
            }
            
            stats = await stats_system._get_match_detailed_stats(example_match)
            example_match['detailed_stats'] = stats
            
            print("\n📊 EXEMPLO DE PARTIDA COM ESTATÍSTICAS:")
            print("-" * 40)
            message = stats_system.format_match_stats_message(example_match)
            print(message)
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_stats_system()) 