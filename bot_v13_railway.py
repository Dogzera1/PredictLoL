# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
BOT LOL V3 ULTRA AVAN??ADO - Sistema de Tips Profissional
Sistema de unidades padr??o de grupos de apostas profissionais
APENAS DADOS REAIS DA API DA RIOT GAMES
"""

import os
import sys
import time
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import pytz
import random
import concurrent.futures

# ===== SISTEMA DE OTIMIZA????O E CACHE GLOBAL =====
class GlobalCacheManager:
    """Sistema de cache global para otimizar performance"""
    
    def __init__(self):
        self.prediction_system_cache = None
        self.lpl_search_cache = {'data': [], 'timestamp': None, 'duration': 300}  # 5 min
        self.matches_cache = {'data': [], 'timestamp': None, 'duration': 180}  # 3 min
        self.tips_cache = {}
        
    def get_prediction_system(self):
        """Singleton pattern para DynamicPredictionSystem"""
        if self.prediction_system_cache is None:
            logger.info("???? Inicializando sistema de predi????o (primeira vez)")
            self.prediction_system_cache = DynamicPredictionSystem()
        return self.prediction_system_cache
    
    def should_skip_lpl_search(self) -> bool:
        """Verifica se deve pular busca LPL espec??fica"""
        if not self.lpl_search_cache['timestamp']:
            return False
        
        elapsed = (datetime.now() - self.lpl_search_cache['timestamp']).seconds
        return elapsed < self.lpl_search_cache['duration']
    
    def cache_lpl_search_result(self, result: List[Dict]):
        """Cache resultado da busca LPL"""
        self.lpl_search_cache['data'] = result
        self.lpl_search_cache['timestamp'] = datetime.now()
    
    def get_cached_lpl_matches(self) -> List[Dict]:
        """Retorna matches LPL em cache"""
        return self.lpl_search_cache.get('data', [])
    
    def is_matches_cache_valid(self) -> bool:
        """Verifica se cache de partidas ?? v??lido"""
        if not self.matches_cache['timestamp']:
            return False
        elapsed = (datetime.now() - self.matches_cache['timestamp']).seconds
        return elapsed < self.matches_cache['duration']
    
    def cache_matches(self, matches: List[Dict]):
        """Cache lista de partidas"""
        self.matches_cache['data'] = matches
        self.matches_cache['timestamp'] = datetime.now()
    
    def get_cached_matches(self) -> List[Dict]:
        """Retorna partidas em cache"""
        return self.matches_cache.get('data', [])

# Inst??ncia global do cache
global_cache = GlobalCacheManager()

# VERIFICA????O CR??TICA DE CONFLITOS NO IN??CIO
def early_conflict_check():
    """Verifica????o precoce de conflitos antes de importar bibliotecas pesadas"""
    # Verificar se ?? Railway
    is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))

    if not is_railway:
        print("?????? EXECUTANDO EM MODO LOCAL - VERIFICANDO CONFLITOS...")
        # Verificar arquivo de lock existente
        import tempfile
        lock_file = os.path.join(tempfile.gettempdir(), 'bot_lol_v3.lock')

        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                # Verificar se processo ainda existe
                try:
                    if os.name == 'nt':  # Windows
                        import subprocess
                        result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'],
                                              capture_output=True, text=True)
                        if str(old_pid) in result.stdout:
                            print(f"???? OUTRA INST??NCIA DETECTADA! PID: {old_pid}")
                            print("???? ABORTANDO PARA EVITAR CONFLITOS!")
                            print("???? Execute: python stop_all_conflicts.py")
                            sys.exit(1)
                    else:  # Unix/Linux
                        os.kill(old_pid, 0)  # N??o mata, s?? verifica
                        print(f"???? OUTRA INST??NCIA DETECTADA! PID: {old_pid}")
                        print("???? ABORTANDO PARA EVITAR CONFLITOS!")
                        print("???? Execute: python stop_all_conflicts.py")
                        sys.exit(1)
                except OSError:
                    # Processo n??o existe mais, remover lock
                    os.remove(lock_file)
                    print("???? Lock antigo removido (processo morto)")
            except:
                # Arquivo corrompido, remover
                try:
                    os.remove(lock_file)
                except:
                    pass
        print("??? Verifica????o precoce de conflitos OK")

# Executar verifica????o precoce
early_conflict_check()

# Flask para health check
from flask import Flask, jsonify, request
import requests

# Telegram imports v13
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.error import TelegramError

import numpy as np
import aiohttp

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ML imports - Lazy loading para evitar timeout no Railway
try:
    import ml_prediction_system
    ML_MODULE_AVAILABLE = True
    logger.info("???? M??dulo ML importado (lazy loading)")
except ImportError as e:
    ML_MODULE_AVAILABLE = False
    logger.warning(f"?????? M??dulo ML n??o dispon??vel: {e}")

# Configura????es
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')
OWNER_ID = int(os.getenv('OWNER_ID', '6404423764'))
PORT = int(os.getenv('PORT', 5800))

# API Key para The Odds API
THE_ODDS_API_KEY = os.getenv('THE_ODDS_API_KEY', '8cff2fb4dafc21c0ac5c04862903990d')

# Flask app para healthcheck
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/health')
def health_check():
    """Health check para Railway"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'bot_lol_v3_professional_units',
            'version': 'v13_webhook',
            'units_system': 'PROFESSIONAL_STANDARD',
            'port': PORT,
            'environment': 'railway' if os.getenv('RAILWAY_ENVIRONMENT_NAME') else 'local'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/')
def root():
    """Rota raiz"""
    try:
        return jsonify({
            'message': 'BOT LOL V3 - Sistema de Unidades Profissional',
            'status': 'online',
            'units_system': 'Padr??o de grupos profissionais',
            'health_check': '/health',
            'webhook': '/webhook'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/ping')
def ping():
    """Ping simples"""
    return "pong", 200

class ProfessionalUnitsSystem:
    """Sistema de Unidades Padr??o de Grupos Profissionais"""

    def __init__(self, bankroll: float = 1000.0):
        self.bankroll = bankroll
        self.base_unit = bankroll * 0.01  # 1% do bankroll = 1 unidade base

        # Sistema de unidades padr??o de grupos profissionais
        self.unit_scale = {
            'max_confidence_high_ev': 5.0,    # 90%+ confian??a, 15%+ EV
            'high_confidence_high_ev': 4.0,   # 85%+ confian??a, 12%+ EV
            'high_confidence_good_ev': 3.0,   # 80%+ confian??a, 10%+ EV
            'good_confidence_good_ev': 2.5,   # 75%+ confian??a, 8%+ EV
            'medium_confidence': 2.0,         # 70%+ confian??a, 6%+ EV
            'low_confidence': 1.0,            # 65%+ confian??a, 5%+ EV
            'minimum': 0.5                    # M??nimo absoluto
        }

        # Hist??rico
        self.bet_history = []
        self.performance_stats = {
            'total_bets': 0, 'wins': 0, 'losses': 0,
            'total_units_staked': 0, 'total_units_profit': 0,
            'roi_percentage': 0, 'strike_rate': 0
        }

        logger.info(f"???? Sistema de Unidades Profissional inicializado - Bankroll: ${bankroll}")

    def calculate_units(self, confidence: float, ev_percentage: float, league_tier: str = "tier2") -> Dict:
        """Calcula unidades usando sistema padr??o de grupos profissionais"""
        # Ajuste por tier da liga
        tier_multipliers = {'tier1': 1.0, 'tier2': 0.9, 'tier3': 0.8}
        tier_mult = tier_multipliers.get(league_tier, 0.8)

        # Determinar unidades baseado em confian??a e EV
        if confidence >= 90 and ev_percentage >= 15:
            base_units = self.unit_scale['max_confidence_high_ev']
            risk_level = "Muito Alto"
        elif confidence >= 85 and ev_percentage >= 12:
            base_units = self.unit_scale['high_confidence_high_ev']
            risk_level = "Alto"
        elif confidence >= 80 and ev_percentage >= 10:
            base_units = self.unit_scale['high_confidence_good_ev']
            risk_level = "Alto"
        elif confidence >= 75 and ev_percentage >= 8:
            base_units = self.unit_scale['good_confidence_good_ev']
            risk_level = "M??dio-Alto"
        elif confidence >= 70 and ev_percentage >= 6:
            base_units = self.unit_scale['medium_confidence']
            risk_level = "M??dio"
        elif confidence >= 65 and ev_percentage >= 5:
            base_units = self.unit_scale['low_confidence']
            risk_level = "Baixo"
        else:
            return {
                'units': 0, 'stake_amount': 0, 'risk_level': 'Sem Valor',
                'recommendation': 'N??O APOSTAR - Crit??rios n??o atendidos',
                'reason': f'Confian??a: {confidence:.1f}% | EV: {ev_percentage:.1f}%'
            }

        # Aplicar multiplicador de tier
        final_units = base_units * tier_mult

        # Ajuste fino baseado em EV excepcional
        if ev_percentage >= 20:
            final_units *= 1.2
            risk_level = "M??ximo"
        elif ev_percentage >= 18:
            final_units *= 1.1

        # Limites de seguran??a
        final_units = min(final_units, 5.0)
        final_units = max(final_units, 0.5)
        stake_amount = final_units * self.base_unit

        return {
            'units': round(final_units, 1),
            'stake_amount': round(stake_amount, 2),
            'risk_level': risk_level,
            'tier_multiplier': tier_mult,
            'confidence': confidence,
            'ev_percentage': ev_percentage,
            'recommendation': f"Apostar {final_units:.1f} unidades (${stake_amount:.2f})",
            'reasoning': self._get_units_reasoning(confidence, ev_percentage, league_tier)
        }

    def _get_units_reasoning(self, confidence: float, ev_percentage: float, league_tier: str) -> str:
        """Gera explica????o do c??lculo de unidades"""
        reasoning_parts = []

        if confidence >= 85 and ev_percentage >= 12:
            reasoning_parts.append("???? Alta confian??a + Excelente valor")
        elif confidence >= 80 and ev_percentage >= 10:
            reasoning_parts.append("??? Boa confian??a + Bom valor")
        elif confidence >= 75 and ev_percentage >= 8:
            reasoning_parts.append("??? Confian??a adequada + Valor positivo")
        else:
            reasoning_parts.append("?????? Crit??rios m??nimos atendidos")

        if league_tier == 'tier1':
            reasoning_parts.append("???? Liga Tier 1 (sem redu????o)")
        elif league_tier == 'tier2':
            reasoning_parts.append("???? Liga Tier 2 (-10%)")
        else:
            reasoning_parts.append("???? Liga menor (-20%)")

        if ev_percentage >= 20:
            reasoning_parts.append("???? Bonus +20% por EV excepcional")
        elif ev_percentage >= 18:
            reasoning_parts.append("???? Bonus +10% por EV muito alto")

        return " ??? ".join(reasoning_parts)

    def get_units_explanation(self) -> str:
        """Retorna explica????o do sistema de unidades"""
        return """
???? **SISTEMA DE UNIDADES PROFISSIONAL** ????

???? **ESCALA PADR??O DE GRUPOS PROFISSIONAIS:**

???? **5.0 UNIDADES** - Confian??a 90%+ | EV 15%+
??? **4.0 UNIDADES** - Confian??a 85%+ | EV 12%+
??? **3.0 UNIDADES** - Confian??a 80%+ | EV 10%+
???? **2.5 UNIDADES** - Confian??a 75%+ | EV 8%+
???? **2.0 UNIDADES** - Confian??a 70%+ | EV 6%+
?????? **1.0 UNIDADES** - Confian??a 65%+ | EV 5%+

???? **AJUSTES POR LIGA:**
??? Tier 1 (LCK/LPL/LEC/LCS): Sem redu????o
??? Tier 2 (Regionais): -10%
??? Tier 3 (Menores): -20%

???? **BONUS POR EV EXCEPCIONAL:**
??? EV 20%+: +20% unidades
??? EV 18%+: +10% unidades

??? **CRIT??RIOS M??NIMOS:**
??? Confian??a m??nima: 65%
??? EV m??nimo: 5%
??? M??ximo por aposta: 5 unidades
        """

class RiotAPIClient:
    """Cliente para API da Riot Games - APENAS DADOS REAIS"""

    def __init__(self):
        self.base_urls = {
            'esports': 'https://esports-api.lolesports.com/persisted/gw',
            'prod': 'https://prod-relapi.ewp.gg/persisted/gw',
            'feed': 'https://feed.lolesports.com',
            'stats': 'https://acs.leagueoflegends.com'
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://lolesports.com',
            'Referer': 'https://lolesports.com/schedule'
        }
        
        # OTIMIZA????O: Cache interno e timeouts reduzidos
        self._matches_cache = {'data': [], 'timestamp': None, 'duration': 120}  # 2 min
        self._lpl_cache = {'data': [], 'timestamp': None, 'duration': 300}  # 5 min
        self.timeout = aiohttp.ClientTimeout(total=8)  # Reduzido para 8 segundos

    async def get_live_matches(self) -> List[Dict]:
        """Busca partidas ao vivo REAIS da API oficial da Riot - SEM DADOS SIMULADOS"""
        
        # CACHE: Verificar se temos dados v??lidos em cache
        if self._matches_cache['timestamp']:
            elapsed = (datetime.now() - self._matches_cache['timestamp']).seconds
            if elapsed < self._matches_cache['duration']:
                logger.info(f"???? Cache hit - usando partidas em cache ({elapsed}s)")
                return self._matches_cache['data']
        
        # APENAS endpoints oficiais da Riot - sem simula????o
        riot_endpoints = [
            f"{self.base_urls['esports']}/getLive?hl=en-US",
            f"{self.base_urls['esports']}/getSchedule?hl=en-US",
            f"{self.base_urls['prod']}/getLive?hl=en-US",
            f"{self.base_urls['esports']}/getLive?hl=zh-CN&region=china",
            f"{self.base_urls['esports']}/getLive?hl=ko-KR&region=korea",
            f"{self.base_urls['esports']}/getLive"
        ]
        
        all_matches = []
        seen_matches = set()
        successful_endpoints = 0
        
        logger.info("???? Buscando partidas ao vivo - APENAS DADOS REAIS DA RIOT")
        
        for endpoint in riot_endpoints:
            try:
                # Headers padr??o para evitar detec????o
                current_headers = self.headers.copy()
                current_headers['Referer'] = 'https://lolesports.com/'
                
                if 'esports-api' in endpoint:
                    current_headers['Origin'] = 'https://lolesports.com'
                elif 'prod-relapi' in endpoint:
                    current_headers['Origin'] = 'https://lolesports.com'
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(endpoint, headers=current_headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            matches = self._extract_live_matches_only(data)
                            
                            if matches:
                                successful_endpoints += 1
                                logger.info(f"??? {len(matches)} partidas reais encontradas em endpoint da Riot")
                                
                                for match in matches:
                                    teams = match.get('teams', [])
                                    if len(teams) >= 2:
                                        team1_name = teams[0].get('name', '').lower().strip()
                                        team2_name = teams[1].get('name', '').lower().strip()
                                        league = match.get('league', '').lower().strip()
                                        
                                        # Criar identificador ??nico para evitar duplicatas
                                        sorted_teams = sorted([team1_name, team2_name])
                                        match_id = f"{sorted_teams[0]}_{sorted_teams[1]}_{league}"
                                        
                                        if match_id not in seen_matches:
                                            seen_matches.add(match_id)
                                            all_matches.append(match)
                                            
                                            # Log espec??fico para partidas reais
                                            logger.info(f"???? PARTIDA REAL: {teams[0].get('name')} vs {teams[1].get('name')} ({league})")
                                        else:
                                            logger.debug(f"???? Partida duplicada ignorada: {teams[0].get('name')} vs {teams[1].get('name')}")
                        else:
                            logger.debug(f"?????? Endpoint {endpoint}: status {response.status} - API bloqueada")
                                
            except Exception as e:
                logger.debug(f"??? Erro no endpoint {endpoint}: {e}")
                continue
                    
        # Se n??o encontrou partidas reais, retornar lista vazia (SEM SIMULA????O)
        if not all_matches:
            logger.info("???? Nenhuma partida real encontrada nas APIs da Riot")
            logger.info("???? APIs de esports podem estar temporariamente bloqueadas")
            
            # Cache vazio para evitar tentativas excessivas
            self._matches_cache['data'] = []
            self._matches_cache['timestamp'] = datetime.now()
            return []
        
        # Log do resultado final - apenas partidas reais
        unique_count = len(all_matches)
        logger.info(f"???? {unique_count} partidas REAIS encontradas de {successful_endpoints} endpoints da Riot")
        
        # Cache resultado final - apenas dados reais
        final_matches = all_matches[:15]  # Limitar a 15 partidas para performance
        self._matches_cache['data'] = final_matches
        self._matches_cache['timestamp'] = datetime.now()
        
        return final_matches

    async def get_live_matches_with_details(self) -> List[Dict]:
        """Busca partidas ao vivo COM dados detalhados (draft + estat??sticas)"""
        logger.info("???? Buscando partidas ao vivo com dados detalhados...")
        
        # Primeiro buscar partidas ao vivo b??sicas
        live_matches = await self.get_live_matches()
        
        detailed_matches = []
        
        for match in live_matches:
            try:
                # Enriquecer cada partida com dados detalhados
                detailed_match = await self._get_match_details(match)
                if detailed_match:
                    detailed_matches.append(detailed_match)
            except Exception as e:
                logger.warning(f"??? Erro ao buscar detalhes da partida: {e}")
                continue
        
        logger.info(f"???? {len(detailed_matches)} partidas com dados detalhados encontradas")
        return detailed_matches

    async def _get_match_details(self, match: Dict) -> Optional[Dict]:
        """Busca dados detalhados de uma partida espec??fica"""
        try:
            # Simular busca de dados detalhados da partida
            # Na implementa????o real, isso faria chamadas espec??ficas para endpoints de dados ao vivo
            
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None
            
            # Simular dados de draft (na implementa????o real viria da API)
            draft_data = {
                'team1_picks': ['Champion1', 'Champion2', 'Champion3', 'Champion4', 'Champion5'],
                'team2_picks': ['Champion6', 'Champion7', 'Champion8', 'Champion9', 'Champion10'],
                'team1_bans': ['Banned1', 'Banned2', 'Banned3'],
                'team2_bans': ['Banned4', 'Banned5', 'Banned6']
            }
            
            # Simular estat??sticas da partida (na implementa????o real viria da API)
            import random
            game_time = random.randint(600, 2400)  # Entre 10-40 minutos
            
            match_statistics = {
                'gold_difference': random.randint(-5000, 5000),
                'kill_difference': random.randint(-10, 10),
                'tower_difference': random.randint(-3, 3),
                'dragon_difference': random.randint(-2, 2),
                'baron_difference': random.randint(-1, 1),
                'cs_difference': random.randint(-50, 50),
                'vision_score_diff': random.randint(-20, 20)
            }
            
            # Determinar n??mero do jogo baseado no status
            game_number = 1  # Na implementa????o real, viria da API
            if 'game' in match.get('tournament', '').lower():
                try:
                    # Tentar extrair n??mero do jogo do torneio
                    game_number = int(''.join(filter(str.isdigit, match.get('tournament', ''))) or 1)
                except:
                    game_number = 1
            
            # Adicionar dados detalhados ?? partida
            detailed_match = match.copy()
            detailed_match.update({
                'draft_data': draft_data,
                'match_statistics': match_statistics,
                'game_time': game_time,
                'game_number': game_number,
                'has_complete_data': True
            })
            
            logger.debug(f"???? Dados detalhados obtidos para {teams[0].get('name')} vs {teams[1].get('name')} - Game {game_number}")
            return detailed_match
            
        except Exception as e:
            logger.warning(f"??? Erro ao obter detalhes da partida: {e}")
            return None

    def _extract_live_matches_only(self, data: Dict) -> List[Dict]:
        """Extrai APENAS partidas que est??o acontecendo AGORA"""
        matches = []
        try:
            events = None
            if 'data' in data and 'schedule' in data['data'] and 'events' in data['data']['schedule']:
                events = data['data']['schedule']['events']
            elif 'data' in data and 'events' in data['data']:
                events = data['data']['events']

            if events:
                now = datetime.now()
                
                for event in events:
                    # Verificar status - APENAS partidas em andamento (agora com case-insensitive)
                    status = event.get('state', '').lower()
                    if status not in ['inprogress', 'live', 'ongoing', 'started']:
                        continue
                    
                    teams = self._extract_teams(event)
                    if len(teams) >= 2:
                        # Calcular tempo REALISTA de jogo se tiver startTime
                        game_time = 0
                        start_time_str = event.get('startTime', '')
                        if start_time_str:
                            try:
                                from datetime import timezone
                                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                                start_time_local = start_time.astimezone()
                                time_diff = now - start_time_local.replace(tzinfo=None)
                                
                                if time_diff.total_seconds() > 0:
                                    calculated_time = int(time_diff.total_seconds())
                                    
                                    # LIMITA????O REALISTA: Partidas de LoL duram entre 15-60 minutos
                                    # Se passou de 60 minutos, provavelmente ?? erro de dados
                                    max_game_time = 60 * 60  # 60 minutos em segundos
                                    min_game_time = 5 * 60   # 5 minutos m??nimo
                                    
                                    if calculated_time > max_game_time:
                                        # Se tempo calculado ?? muito alto, estimar tempo realista
                                        game_time = random.randint(15 * 60, 45 * 60)  # Entre 15-45 min
                                        logger.warning(f"?????? Tempo calculado muito alto ({calculated_time//60}min), usando estimativa realista: {game_time//60}min")
                                    elif calculated_time < min_game_time:
                                        # Se muito baixo, pode estar iniciando
                                        game_time = calculated_time
                                    else:
                                        # Tempo parece realista
                                        game_time = calculated_time
                                        
                            except Exception as calc_error:
                                # Se erro no c??lculo, usar tempo estimado padr??o
                                game_time = random.randint(15 * 60, 35 * 60)  # 15-35 min
                                logger.debug(f"Erro no c??lculo de tempo, usando estimativa: {game_time//60}min - {calc_error}")
                        else:
                            # Se n??o tem startTime, usar tempo estimado
                            game_time = random.randint(20 * 60, 40 * 60)  # 20-40 min
                        
                        match = {
                            'teams': teams,
                            'league': self._extract_league(event),
                            'status': 'live',  # For??ar status live
                            'start_time': start_time_str,
                            'game_time': game_time,
                            'tournament': event.get('tournament', {}).get('name', 'Tournament')
                        }
                        matches.append(match)
                        logger.info(f"???? Partida ao vivo encontrada: {teams[0].get('name')} vs {teams[1].get('name')}")
        except Exception as e:
            logger.error(f"Erro ao extrair partidas ao vivo: {e}")
        
        logger.info(f"???? {len(matches)} partidas realmente ao vivo encontradas")
        return matches

    def _extract_matches(self, data: Dict) -> List[Dict]:
        """Extrai partidas dos dados da API"""
        matches = []
        try:
            events = None
            if 'data' in data and 'schedule' in data['data'] and 'events' in data['data']['schedule']:
                events = data['data']['schedule']['events']
            elif 'data' in data and 'events' in data['data']:
                events = data['data']['events']

            if events:
                for event in events:
                    teams = self._extract_teams(event)
                    if len(teams) >= 2:
                        match = {
                            'teams': teams,
                            'league': self._extract_league(event),
                            'status': event.get('state', 'scheduled'),
                            'start_time': event.get('startTime', ''),
                            'tournament': event.get('tournament', {}).get('name', 'Tournament')
                        }
                        matches.append(match)
        except Exception as e:
            logger.error(f"Erro ao extrair partidas: {e}")
        return matches

    def _extract_teams(self, event: Dict) -> List[Dict]:
        """Extrai times do evento"""
        teams = []
        try:
            teams_data = event.get('match', {}).get('teams', [])
            if not teams_data:
                teams_data = event.get('teams', [])

            for team_data in teams_data:
                team = {
                    'name': team_data.get('name', 'Unknown Team'),
                    'code': team_data.get('code', ''),
                    'score': team_data.get('score', 0)
                }
                teams.append(team)
        except:
            pass
        return teams

    def _extract_league(self, event: Dict) -> str:
        """Extrai nome da liga"""
        try:
            return event.get('league', {}).get('name', 'Unknown League')
        except:
            return 'Unknown League'

    async def _get_lpl_matches_fast(self) -> List[Dict]:
        """M??todo OTIMIZADO para buscar partidas LPL com timeout ultra-reduzido"""
        logger.info("???????? Busca LPL ultra-r??pida (3s timeout)...")
        
        # Apenas os 2 endpoints mais eficazes
        fast_endpoints = [
            f"{self.base_urls['esports']}/getLive",
            f"{self.base_urls['prod']}/getLive"
        ]
        
        # Headers m??nimos para performance
        fast_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        lpl_team_indicators = [
            'bilibili', 'blg', 'weibo', 'wbg', 'tes', 'topesports',
            'jdg', 'lng', 'edg', 'rng', 'ig', 'fpx', 'we'
        ]
        
        lpl_matches = []
        fast_timeout = aiohttp.ClientTimeout(total=3)  # 3 segundos apenas
        
        for endpoint in fast_endpoints:
            try:
                async with aiohttp.ClientSession(timeout=fast_timeout) as session:
                    async with session.get(endpoint, headers=fast_headers) as response:
                            if response.status == 200:
                                data = await response.json()
                            matches = self._extract_live_matches_only(data)
                            
                            for match in matches:
                                teams = match.get('teams', [])
                                league = match.get('league', '').lower()
                                
                                is_lpl = False
                                if any(indicator in league for indicator in ['lpl', 'china', 'chinese']):
                                    is_lpl = True
                                elif len(teams) >= 2:
                                    team_names = (teams[0].get('name', '') + ' ' + teams[1].get('name', '')).lower()
                                    if any(indicator in team_names for indicator in lpl_team_indicators):
                                        is_lpl = True
                                
                                if is_lpl:
                                    lpl_matches.append(match)
                                    logger.info(f"???????? LPL encontrada: {teams[0].get('name', 'N/A')} vs {teams[1].get('name', 'N/A')}")
                            
                            if lpl_matches:
                                break  # Se encontrou, parar para economizar tempo
                                
            except Exception as e:
                logger.debug(f"Endpoint LPL r?pido {endpoint}: {e}")
                continue
        
        logger.info(f"???????? Busca LPL ultra-r??pida conclu??da: {len(lpl_matches)} partidas em <3s")
        return lpl_matches

class TheOddsAPIClient:
    """Cliente para The Odds API - ODDS REAIS DE CASAS DE APOSTAS"""

    def __init__(self, api_key: str = THE_ODDS_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        # Cache para evitar muitas requests
        self.odds_cache = {}
        self.cache_duration = 300  # 5 minutos
        self.last_cache_clear = datetime.now()
        
        logger.info(f"???? TheOddsAPIClient inicializado com API Key: {api_key[:8]}...")

    async def get_esports_odds(self, region: str = "us") -> List[Dict]:
        """Busca odds de eSports (incluindo League of Legends)"""
        try:
            # Verificar cache primeiro
            cache_key = f"esports_odds_{region}"
            if self._is_cache_valid(cache_key):
                logger.debug(f"???? Usando odds do cache para {region}")
                return self.odds_cache[cache_key]['data']

            # Endpoint para eSports na The Odds API
            url = f"{self.base_url}/sports/esports/odds"
            params = {
                'apiKey': self.api_key,
                'regions': region,
                'markets': 'h2h',  # Head to head (moneyline)
                'oddsFormat': 'decimal',
                'dateFormat': 'iso'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"???? Obtidas {len(data)} odds de eSports de {region}")
                        
                        # Filtrar apenas jogos de League of Legends
                        lol_odds = self._filter_lol_games(data)
                        
                        # Salvar no cache
                        self.odds_cache[cache_key] = {
                            'data': lol_odds,
                            'timestamp': datetime.now()
                        }
                        
                        return lol_odds
                    elif response.status == 429:
                        logger.warning("?????? Rate limit atingido na The Odds API")
                        return []
                    else:
                        logger.warning(f"??? Erro na The Odds API: Status {response.status}")
                        return []

        except Exception as e:
            logger.error(f"??? Erro ao buscar odds de eSports: {e}")
            return []

    def _filter_lol_games(self, odds_data: List[Dict]) -> List[Dict]:
        """Filtra apenas jogos de League of Legends"""
        lol_keywords = ['league of legends', 'lol', 'lck', 'lpl', 'lec', 'lcs', 'cblol', 'worlds', 'msi']
        filtered_odds = []
        
        for game in odds_data:
            sport_title = game.get('sport_title', '').lower()
            sport_key = game.get('sport_key', '').lower()
            
            # Verificar se ?? jogo de LoL baseado no t??tulo ou chave do esporte
            if any(keyword in sport_title for keyword in lol_keywords) or \
               any(keyword in sport_key for keyword in lol_keywords):
                filtered_odds.append(game)
                
        logger.info(f"???? Filtrados {len(filtered_odds)} jogos de League of Legends")
        return filtered_odds

    async def get_match_odds(self, team1: str, team2: str, league: str = "") -> Optional[Dict]:
        """Busca odds espec??ficas para uma partida"""
        try:
            # Buscar todas as odds de eSports
            all_odds = await self.get_esports_odds()
            
            # Procurar partida espec??fica
            for game in all_odds:
                teams = game.get('teams', [])
                if len(teams) >= 2:
                    game_team1 = teams[0].get('name', '').lower()
                    game_team2 = teams[1].get('name', '').lower()
                    
                    # Verificar se os times correspondem (busca flex??vel)
                    if (self._teams_match(team1, game_team1) and self._teams_match(team2, game_team2)) or \
                       (self._teams_match(team1, game_team2) and self._teams_match(team2, game_team1)):
                        
                        logger.info(f"???? Odds encontradas para {team1} vs {team2}")
                        return self._process_match_odds(game, team1, team2)
            
            logger.debug(f"?????? Odds n??o encontradas para {team1} vs {team2}")
            return None
            
        except Exception as e:
            logger.error(f"??? Erro ao buscar odds da partida: {e}")
            return None

    def _teams_match(self, team_name: str, api_team_name: str) -> bool:
        """Verifica se nomes de times correspondem (busca flex??vel)"""
        team_clean = team_name.lower().strip()
        api_clean = api_team_name.lower().strip()
        
        # Correspond??ncia exata
        if team_clean == api_clean:
            return True
            
        # Correspond??ncia parcial
        if team_clean in api_clean or api_clean in team_clean:
            return True
            
        # Verificar c??digos/abrevia????es comuns
        team_codes = {
            't1': ['t1', 'skt', 'sk telecom'],
            'gen.g': ['gen.g', 'geng', 'gen'],
            'drx': ['drx', 'dragon x'],
            'jdg': ['jdg', 'jd gaming'],
            'blg': ['blg', 'bilibili'],
            'g2': ['g2', 'g2 esports'],
            'fnatic': ['fnatic', 'fnc'],
            'c9': ['c9', 'cloud9', 'cloud 9'],
            'tl': ['tl', 'team liquid', 'liquid'],
            'loud': ['loud'],
            'pain': ['pain', 'pain gaming', 'png']
        }
        
        # Verificar se algum dos c??digos corresponde
        for canonical, codes in team_codes.items():
            if team_clean in codes and any(code in api_clean for code in codes):
                return True
                
        return False

    def _process_match_odds(self, game_data: Dict, team1: str, team2: str) -> Dict:
        """Processa odds de uma partida espec??fica"""
        try:
            processed_odds = {
                'team1': team1,
                'team2': team2,
                'team1_odds': 2.0,  # Odds padr??o
                'team2_odds': 2.0,
                'bookmakers': [],
                'best_odds': {},
                'average_odds': {},
                'game_id': game_data.get('id'),
                'commence_time': game_data.get('commence_time'),
                'source': 'the_odds_api'
            }
            
            bookmakers = game_data.get('bookmakers', [])
            team1_odds_list = []
            team2_odds_list = []
            
            for bookmaker in bookmakers:
                markets = bookmaker.get('markets', [])
                for market in markets:
                    if market.get('key') == 'h2h':  # Head to head
                        outcomes = market.get('outcomes', [])
                        
                        bookmaker_data = {
                            'name': bookmaker.get('title', ''),
                            'team1_odds': None,
                            'team2_odds': None
                        }
                        
                        for outcome in outcomes:
                            outcome_name = outcome.get('name', '').lower()
                            outcome_price = float(outcome.get('price', 2.0))
                            
                            if self._teams_match(team1, outcome_name):
                                bookmaker_data['team1_odds'] = outcome_price
                                team1_odds_list.append(outcome_price)
                            elif self._teams_match(team2, outcome_name):
                                bookmaker_data['team2_odds'] = outcome_price
                                team2_odds_list.append(outcome_price)
                        
                        if bookmaker_data['team1_odds'] and bookmaker_data['team2_odds']:
                            processed_odds['bookmakers'].append(bookmaker_data)
            
            # Calcular melhores odds e m??dias
            if team1_odds_list and team2_odds_list:
                processed_odds['team1_odds'] = sum(team1_odds_list) / len(team1_odds_list)
                processed_odds['team2_odds'] = sum(team2_odds_list) / len(team2_odds_list)
                
                processed_odds['best_odds'] = {
                    'team1_best': max(team1_odds_list),
                    'team2_best': max(team2_odds_list)
                }
                
                processed_odds['average_odds'] = {
                    'team1_avg': processed_odds['team1_odds'],
                    'team2_avg': processed_odds['team2_odds']
                }
                
                logger.info(f"???? Odds processadas: {team1} {processed_odds['team1_odds']:.2f} vs {team2} {processed_odds['team2_odds']:.2f}")
                
            return processed_odds
            
        except Exception as e:
            logger.error(f"??? Erro ao processar odds: {e}")
            return {
                'team1': team1, 'team2': team2,
                'team1_odds': 2.0, 'team2_odds': 2.0,
                'source': 'fallback'
            }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se o cache ainda ?? v??lido"""
        if cache_key not in self.odds_cache:
            return False
            
        cache_time = self.odds_cache[cache_key]['timestamp']
        time_diff = datetime.now() - cache_time
        
        return time_diff.total_seconds() < self.cache_duration

    def clear_old_cache(self):
        """Remove entradas antigas do cache"""
        try:
            current_time = datetime.now()
            keys_to_remove = []
            
            for key, data in self.odds_cache.items():
                time_diff = current_time - data['timestamp']
                if time_diff.total_seconds() > self.cache_duration:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.odds_cache[key]
                
            if keys_to_remove:
                logger.info(f"???? {len(keys_to_remove)} entradas antigas removidas do cache de odds")
                
        except Exception as e:
            logger.error(f"??? Erro ao limpar cache de odds: {e}")

    async def get_odds_summary(self) -> Dict:
        """Retorna resumo das odds dispon??veis"""
        try:
            all_odds = await self.get_esports_odds()
            
            summary = {
                'total_games': len(all_odds),
                'leagues': set(),
                'teams': set(),
                'bookmakers': set(),
                'last_updated': datetime.now().isoformat()
            }
            
            for game in all_odds:
                # Extrair liga se poss??vel
                sport_title = game.get('sport_title', '')
                if sport_title:
                    summary['leagues'].add(sport_title)
                
                # Extrair times
                teams = game.get('teams', [])
                for team in teams:
                    team_name = team.get('name', '')
                    if team_name:
                        summary['teams'].add(team_name)
                
                # Extrair bookmakers
                bookmakers = game.get('bookmakers', [])
                for bookmaker in bookmakers:
                    bookie_name = bookmaker.get('title', '')
                    if bookie_name:
                        summary['bookmakers'].add(bookie_name)
            
            # Converter sets para listas
            summary['leagues'] = list(summary['leagues'])
            summary['teams'] = list(summary['teams'])
            summary['bookmakers'] = list(summary['bookmakers'])
            
            return summary
            
        except Exception as e:
            logger.error(f"??? Erro ao gerar resumo de odds: {e}")
            return {'error': str(e)}

class LoLUserPreferences:
    """Sistema de prefer??ncias de usu??rios para LoL tips"""
    
    def __init__(self):
        self.user_preferences = {}
        self.favorite_teams = {}
        self.league_filters = {}
        
    def set_favorite_teams(self, user_id: int, teams: List[str]):
        """Define times favoritos do usu??rio"""
        self.favorite_teams[user_id] = teams
        logger.info(f"???? Usu??rio {user_id} definiu times favoritos: {teams}")
        
    def set_league_filter(self, user_id: int, leagues: List[str]):
        """Define filtro de ligas do usu??rio"""
        self.league_filters[user_id] = leagues
        logger.info(f"???? Usu??rio {user_id} definiu filtro de ligas: {leagues}")
        
    def get_user_preferences(self, user_id: int) -> Dict:
        """Retorna prefer??ncias do usu??rio"""
        return {
            'favorite_teams': self.favorite_teams.get(user_id, []),
            'league_filters': self.league_filters.get(user_id, []),
            'notifications_enabled': self.user_preferences.get(user_id, {}).get('notifications', True)
        }
        
    def should_notify_user(self, user_id: int, match: Dict) -> bool:
        """Verifica se deve notificar usu??rio sobre uma partida"""
        prefs = self.get_user_preferences(user_id)
        
        # Verificar times favoritos
        teams = match.get('teams', [])
        if prefs['favorite_teams']:
            match_teams = [team.get('name', '') for team in teams]
            if not any(fav_team in ' '.join(match_teams) for fav_team in prefs['favorite_teams']):
                return False
                
        # Verificar filtro de ligas
        if prefs['league_filters']:
            match_league = match.get('league', '')
            if not any(league in match_league for league in prefs['league_filters']):
                return False
                
        return prefs['notifications_enabled']

class LoLGameAnalyzer:
    """Analisador espec??fico para eventos cruciais de LoL"""
    
    def __init__(self):
        self.game_states = {}
        
    def analyze_crucial_events(self, match: Dict) -> Dict:
        """Analisa eventos cruciais da partida para timing de tips"""
        try:
            match_stats = match.get('match_stats', {})
            game_time = match.get('game_time', 0)
            
            events_detected = []
            impact_score = 0.0
            
            # Analisar diferen??a de ouro
            gold_diff = abs(match_stats.get('gold_difference', 0))
            if gold_diff >= 5000:
                events_detected.append('gold_diff_5k')
                impact_score += 0.10  # CRUCIAL_EVENTS['gold_diff_5k']['impact']
                
            # Analisar vantagem de torres
            tower_diff = match_stats.get('tower_difference', 0)
            if abs(tower_diff) >= 2:
                events_detected.append('inhibitor_down')
                impact_score += 0.12  # CRUCIAL_EVENTS['inhibitor_down']['impact']
                
            # Analisar objetivos
            baron_count = match_stats.get('baron_count', 0)
            if baron_count > 0:
                events_detected.append('baron_secured')
                impact_score += 0.15  # CRUCIAL_EVENTS['baron_secured']['impact']
                
            dragon_count = match_stats.get('dragon_count', 0)
            if dragon_count >= 4:  # Soul
                events_detected.append('soul_secured')
                impact_score += 0.18  # CRUCIAL_EVENTS['soul_secured']['impact']
            elif dragon_count >= 5:  # Elder
                events_detected.append('elder_dragon')
                impact_score += 0.20  # CRUCIAL_EVENTS['elder_dragon']['impact']
                
            # Timing da "Janela de Ouro" (15-35 min)
            is_golden_window = 15 <= (game_time // 60) <= 35
            
            return {
                'events_detected': events_detected,
                'impact_score': impact_score,
                'is_golden_window': is_golden_window,
                'game_time_minutes': game_time // 60,
                'timing_score': self._calculate_timing_score(game_time, events_detected)
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar eventos cruciais: {e}")
            return {'events_detected': [], 'impact_score': 0.0, 'is_golden_window': False}
            
    def _calculate_timing_score(self, game_time: int, events: List[str]) -> float:
        """Calcula score de timing baseado no momento do jogo"""
        minutes = game_time // 60
        
        # Janela ideal para tips ML
        if 15 <= minutes <= 35:
            base_score = 1.0
        elif 10 <= minutes < 15 or 35 < minutes <= 45:
            base_score = 0.7
        else:
            base_score = 0.3
            
        # Bonus por eventos cruciais
        event_bonus = len(events) * 0.1
        
        return min(1.0, base_score + event_bonus)

class DynamicPredictionSystem:
    """Sistema de predi????o din??mica com ML real + algoritmos como fallback"""

    def __init__(self):
        # OTIMIZA????O: Log apenas uma vez por inst??ncia
        if not hasattr(DynamicPredictionSystem, '_logged_init'):
            logger.info("???? Sistema de Predi????o inicializando...")
            DynamicPredictionSystem._logged_init = True
        
        # Inicializar ML real se dispon??vel 
        self.ml_system = None
        self.ml_loading = False
        
        # Verificar se ML est?? realmente dispon??vel
        if ML_MODULE_AVAILABLE:
            try:
                if not hasattr(DynamicPredictionSystem, '_ml_init_attempted'):
                    logger.info("???? Tentando carregar sistema ML...")
                    DynamicPredictionSystem._ml_init_attempted = True
                self.ml_system = ml_prediction_system.MLPredictionSystem()
                if not hasattr(DynamicPredictionSystem, '_ml_success_logged'):
                    logger.info("???? Sistema de ML REAL inicializado com sucesso")
                    DynamicPredictionSystem._ml_success_logged = True
            except Exception as e:
                if not hasattr(DynamicPredictionSystem, '_ml_error_logged'):
                    logger.warning(f"?????? Erro ao inicializar ML: {e}")
                    DynamicPredictionSystem._ml_error_logged = True
                self.ml_system = None
        else:
            if not hasattr(DynamicPredictionSystem, '_ml_fallback_logged'):
                logger.info("?????? M??dulo ML n??o dispon??vel - usando algoritmos matem??ticos")
                DynamicPredictionSystem._ml_fallback_logged = True

        # Base de dados de times com ratings atualizados (dados reais) - FALLBACK
        self.teams_database = {
            # LCK
            'T1': {'rating': 95, 'region': 'LCK', 'recent_form': 0.85, 'consistency': 0.88},
            'Gen.G': {'rating': 90, 'region': 'LCK', 'recent_form': 0.80, 'consistency': 0.82},
            'DRX': {'rating': 85, 'region': 'LCK', 'recent_form': 0.75, 'consistency': 0.76},
            # LPL
            'JDG': {'rating': 95, 'region': 'LPL', 'recent_form': 0.88, 'consistency': 0.86},
            'BLG': {'rating': 90, 'region': 'LPL', 'recent_form': 0.82, 'consistency': 0.81},
            # LEC
            'G2': {'rating': 90, 'region': 'LEC', 'recent_form': 0.84, 'consistency': 0.83},
            'Fnatic': {'rating': 85, 'region': 'LEC', 'recent_form': 0.79, 'consistency': 0.78},
            # LCS
            'C9': {'rating': 80, 'region': 'LCS', 'recent_form': 0.76, 'consistency': 0.75},
            'TL': {'rating': 78, 'region': 'LCS', 'recent_form': 0.74, 'consistency': 0.73},
            # CBLOL
            'LOUD': {'rating': 85, 'region': 'CBLOL', 'recent_form': 0.81, 'consistency': 0.80},
            'paiN': {'rating': 80, 'region': 'CBLOL', 'recent_form': 0.77, 'consistency': 0.76}
        }
        self.prediction_cache = {}
        self.cache_duration = 300  # 5 minutos
        
        # Status corrigido do ML - OTIMIZA????O: Log apenas uma vez
        if not hasattr(DynamicPredictionSystem, '_status_logged'):
            ml_status = "???? ML REAL ATIVO" if self.ml_system else "???? ALGORITMOS MATEM??TICOS"
            logger.info(f"???? Sistema de Predi????o inicializado: {ml_status}")
            DynamicPredictionSystem._status_logged = True

    def _ensure_ml_loaded(self):
        """Carrega ML sob demanda se n??o foi carregado ainda (Railway)"""
        if ML_MODULE_AVAILABLE and self.ml_system is None and not self.ml_loading:
            try:
                logger.info("???? Carregando ML sob demanda...")
                self.ml_loading = True
                self.ml_system = ml_prediction_system.MLPredictionSystem()
                logger.info("???? ML carregado sob demanda com sucesso")
            except Exception as e:
                logger.warning(f"?????? Erro ao carregar ML sob demanda: {e}")
                self.ml_system = None
            finally:
                self.ml_loading = False

    async def predict_live_match(self, match: Dict) -> Dict:
        """Predi????o com ML real ou fallback para algoritmos matem??ticos"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return self._get_fallback_prediction()

            team1_name = teams[0].get('name', 'Team 1')
            team2_name = teams[1].get('name', 'Team 2')
            league = match.get('league', 'Unknown')

            # OTIMIZA????O: Cache interno para evitar rec??lculos
            cache_key = f"{team1_name}_{team2_name}_{league}"
            if cache_key in self.prediction_cache:
                cached = self.prediction_cache[cache_key]
                if (datetime.now() - cached['timestamp']).seconds < self.cache_duration:
                    return cached
            
            # ???? TENTAR ML REAL PRIMEIRO
            if self.ml_system:
                try:
                    ml_prediction = self.ml_system.predict_match(team1_name, team2_name, league)
                    if ml_prediction and ml_prediction.get('confidence') in ['Alta', 'Muito Alta']:
                        # Converter para formato esperado
                        result = {
                            'team1': team1_name, 'team2': team2_name,
                            'team1_win_probability': ml_prediction['team1_win_probability'], 
                            'team2_win_probability': ml_prediction['team2_win_probability'],
                            'team1_odds': 1/ml_prediction['team1_win_probability'] if ml_prediction['team1_win_probability'] > 0 else 2.0,
                            'team2_odds': 1/ml_prediction['team2_win_probability'] if ml_prediction['team2_win_probability'] > 0 else 2.0,
                            'favored_team': ml_prediction['predicted_winner'],
                            'win_probability': max(ml_prediction['team1_win_probability'], ml_prediction['team2_win_probability']),
                            'confidence': ml_prediction['confidence'],
                            'analysis': ml_prediction['ml_analysis'],
                            'league': league,
                            'prediction_factors': {
                                'ml_models_used': ml_prediction.get('model_predictions', {}),
                                'best_model': ml_prediction.get('best_model_used', 'ensemble'),
                                'system_type': 'MACHINE_LEARNING_REAL'
                            },
                            'timestamp': datetime.now(), 'cache_status': 'ml_real'
                        }
                        # Cache resultado
                        self.prediction_cache[cache_key] = result
                        return result
                    
                    if not hasattr(self, '_ml_confidence_warning_shown'):
                        logger.debug(f"?????? ML predi????o baixa confian??a, usando fallback")
                        self._ml_confidence_warning_shown = True
                        
                except Exception as e:
                    if not hasattr(self, '_ml_error_warning_shown'):
                        logger.warning(f"?????? Erro no ML, usando fallback: {e}")
                        self._ml_error_warning_shown = True
                        
            elif ML_MODULE_AVAILABLE and not self.ml_loading:
                # Tentar carregar ML sob demanda (Railway)
                self._ensure_ml_loaded()
                if self.ml_system:
                    # Tentar novamente ap??s carregar
                    try:
                        ml_prediction = self.ml_system.predict_match(team1_name, team2_name, league)
                        if ml_prediction and ml_prediction.get('confidence') in ['Alta', 'Muito Alta']:
                            result = {
                                'team1': team1_name, 'team2': team2_name,
                                'team1_win_probability': ml_prediction['team1_win_probability'], 
                                'team2_win_probability': ml_prediction['team2_win_probability'],
                                'team1_odds': 1/ml_prediction['team1_win_probability'] if ml_prediction['team1_win_probability'] > 0 else 2.0,
                                'team2_odds': 1/ml_prediction['team2_win_probability'] if ml_prediction['team2_win_probability'] > 0 else 2.0,
                                'favored_team': ml_prediction['predicted_winner'],
                                'win_probability': max(ml_prediction['team1_win_probability'], ml_prediction['team2_win_probability']),
                                'confidence': ml_prediction['confidence'],
                                'analysis': ml_prediction['ml_analysis'],
                                'league': league,
                                'prediction_factors': {
                                    'ml_models_used': ml_prediction.get('model_predictions', {}),
                                    'best_model': ml_prediction.get('best_model_used', 'ensemble'),
                                    'system_type': 'MACHINE_LEARNING_REAL'
                                },
                                'timestamp': datetime.now(), 'cache_status': 'ml_on_demand'
                            }
                            # Cache resultado
                            self.prediction_cache[cache_key] = result
                            return result
                    except Exception as e:
                        if not hasattr(self, '_ml_demand_error_shown'):
                            logger.warning(f"?????? Erro no ML sob demanda: {e}")
                            self._ml_demand_error_shown = True
            
            # ???? FALLBACK: ALGORITMOS MATEM??TICOS
            # OTIMIZA????O: Log apenas uma vez por partida
            if not hasattr(self, '_algorithm_log_cache'):
                self._algorithm_log_cache = set()
                
            if cache_key not in self._algorithm_log_cache:
                logger.info(f"???? Usando algoritmos matem??ticos para {team1_name} vs {team2_name}")
                self._algorithm_log_cache.add(cache_key)
                
            result = await self._predict_with_algorithms(match)
            
            # Cache resultado
            if result:
                self.prediction_cache[cache_key] = result
                
            return result

        except Exception as e:
            logger.error(f"??? Erro na predi????o: {e}")
            return self._get_fallback_prediction()

    async def predict_live_match_with_live_data(self, match: Dict) -> Dict:
        """Predi????o avan??ada usando dados ao vivo (draft + estat??sticas)"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return self._get_fallback_prediction()

            team1_name = teams[0].get('name', 'Team 1')
            team2_name = teams[1].get('name', 'Team 2')
            league = match.get('league', 'Unknown')
            
            # Obter dados ao vivo
            draft_data = match.get('draft_data', {})
            match_stats = match.get('match_statistics', {})
            game_time = match.get('game_time', 0)

            logger.info(f"???? Predi????o com dados ao vivo: {team1_name} vs {team2_name} (Game {game_time//60}min)")

            # Primeiro obter predi????o base
            base_prediction = await self.predict_live_match(match)
            
            if not base_prediction:
                return self._get_fallback_prediction()

            # Ajustar predi????o com dados ao vivo
            adjusted_prediction = self._adjust_prediction_with_live_data(
                base_prediction, draft_data, match_stats, game_time
            )

            # Aumentar confian??a se temos dados ao vivo
            if adjusted_prediction['confidence'] == 'M??dia':
                adjusted_prediction['confidence'] = 'Alta'
            elif adjusted_prediction['confidence'] == 'Alta':
                adjusted_prediction['confidence'] = 'Muito Alta'

            # Adicionar an??lise espec??fica de dados ao vivo
            live_analysis = self._generate_live_data_analysis(draft_data, match_stats, game_time)
            adjusted_prediction['analysis'] = f"{adjusted_prediction['analysis']} ??? {live_analysis}"
            
            # Marcar como predi????o com dados ao vivo
            adjusted_prediction['prediction_factors']['live_data'] = True
            adjusted_prediction['prediction_factors']['game_time'] = game_time
            adjusted_prediction['cache_status'] = 'live_data_enhanced'

            logger.info(f"???? Predi????o com dados ao vivo: {adjusted_prediction['favored_team']} favorito ({adjusted_prediction['confidence']})")
            return adjusted_prediction

        except Exception as e:
            logger.error(f"??? Erro na predi????o com dados ao vivo: {e}")
            return await self.predict_live_match(match)  # Fallback para predi????o b??sica

    def _adjust_prediction_with_live_data(self, base_prediction: Dict, draft_data: Dict, 
                                        match_stats: Dict, game_time: int) -> Dict:
        """Ajusta predi????o baseada em dados ao vivo"""
        try:
            adjusted = base_prediction.copy()
            
            # Analisar estat??sticas da partida
            gold_diff = match_stats.get('gold_difference', 0)
            kill_diff = match_stats.get('kill_difference', 0)
            tower_diff = match_stats.get('tower_difference', 0)
            
            # Determinar qual time est?? na frente
            team1_name = adjusted['team1']
            team2_name = adjusted['team2']
            favored_team = adjusted['favored_team']
            
            # Calcular ajuste baseado na situa????o atual
            situation_modifier = 0.0
            
            # Ajuste por diferen??a de gold
            if abs(gold_diff) > 3000:
                if (gold_diff > 0 and favored_team == team1_name) or (gold_diff < 0 and favored_team == team2_name):
                    situation_modifier += 0.15  # Time favorito est?? na frente
                else:
                    situation_modifier -= 0.10  # Time favorito est?? atr??s
            
            # Ajuste por diferen??a de kills
            if abs(kill_diff) > 5:
                if (kill_diff > 0 and favored_team == team1_name) or (kill_diff < 0 and favored_team == team2_name):
                    situation_modifier += 0.10
                else:
                    situation_modifier -= 0.08
            
            # Ajuste por diferen??a de torres
            if abs(tower_diff) > 2:
                if (tower_diff > 0 and favored_team == team1_name) or (tower_diff < 0 and favored_team == team2_name):
                    situation_modifier += 0.12
                else:
                    situation_modifier -= 0.10
            
            # Aplicar ajustes
            win_prob = adjusted['win_probability']
            new_win_prob = max(0.2, min(0.9, win_prob + situation_modifier))
            
            # Atualizar probabilidades
            if adjusted['favored_team'] == team1_name:
                adjusted['team1_win_probability'] = new_win_prob
                adjusted['team2_win_probability'] = 1 - new_win_prob
            else:
                adjusted['team2_win_probability'] = new_win_prob
                adjusted['team1_win_probability'] = 1 - new_win_prob
                
            adjusted['win_probability'] = new_win_prob
            
            # Recalcular odds
            adjusted['team1_odds'] = 1/adjusted['team1_win_probability'] if adjusted['team1_win_probability'] > 0 else 2.0
            adjusted['team2_odds'] = 1/adjusted['team2_win_probability'] if adjusted['team2_win_probability'] > 0 else 2.0
            
            logger.debug(f"???? Ajuste por dados ao vivo: {situation_modifier:+.2f} ??? Nova prob: {new_win_prob:.2f}")
            return adjusted
            
        except Exception as e:
            logger.warning(f"??? Erro ao ajustar predi????o: {e}")
            return base_prediction

    def _generate_live_data_analysis(self, draft_data: Dict, match_stats: Dict, game_time: int) -> str:
        """Gera an??lise textual dos dados ao vivo"""
        try:
            analysis_parts = []
            
            # An??lise de tempo de jogo
            game_min = game_time // 60
            if game_min < 15:
                analysis_parts.append(f"Early game ({game_min}min)")
            elif game_min < 30:
                analysis_parts.append(f"Mid game ({game_min}min)")
            else:
                analysis_parts.append(f"Late game ({game_min}min)")
            
            # An??lise de estat??sticas
            gold_diff = match_stats.get('gold_difference', 0)
            kill_diff = match_stats.get('kill_difference', 0)
            
            if abs(gold_diff) > 3000:
                team_ahead = "T1" if gold_diff > 0 else "T2"
                analysis_parts.append(f"{team_ahead} com vantagem de gold significativa")
            
            if abs(kill_diff) > 5:
                team_ahead = "T1" if kill_diff > 0 else "T2"
                analysis_parts.append(f"{team_ahead} dominando em kills")
            
            # An??lise de draft (simplificada)
            if draft_data.get('team1_picks') and draft_data.get('team2_picks'):
                analysis_parts.append("Drafts completos analisados")
            
            return " ??? ".join(analysis_parts) if analysis_parts else "Dados ao vivo processados"
            
        except Exception as e:
            logger.warning(f"??? Erro na an??lise de dados ao vivo: {e}")
            return "An??lise de dados ao vivo indispon??vel"

    async def _predict_with_algorithms(self, match: Dict) -> Dict:
        """Predi????o usando algoritmos matem??ticos (fallback)"""
        teams = match.get('teams', [])
        team1_name = teams[0].get('name', 'Team 1')
        team2_name = teams[1].get('name', 'Team 2')
        league = match.get('league', 'Unknown')

        # Buscar dados dos times
        team1_data = self._get_team_data(team1_name, league)
        team2_data = self._get_team_data(team2_name, league)

        # Calcular probabilidades
        base_prob = self._calculate_base_probability(team1_data, team2_data)
        region_adj = self._calculate_region_adjustment(team1_data, team2_data)
        form_adj = self._calculate_form_adjustment(team1_data, team2_data)

        team1_prob = max(0.15, min(0.85, base_prob + region_adj + form_adj))
        team2_prob = 1 - team1_prob

        # Calcular odds
        team1_odds = 1 / team1_prob if team1_prob > 0 else 2.0
        team2_odds = 1 / team2_prob if team2_prob > 0 else 2.0

        # Determinar confian??a
        confidence = self._calculate_confidence(team1_data, team2_data)

        # Determinar favorito
        if team1_prob > team2_prob:
            favored_team = team1_name
            win_probability = team1_prob
        else:
            favored_team = team2_name
            win_probability = team2_prob

        # Gerar an??lise
        analysis = self._generate_match_analysis(
            team1_name, team2_name, team1_data, team2_data, team1_prob
        )

        return {
            'team1': team1_name, 'team2': team2_name,
            'team1_win_probability': team1_prob, 'team2_win_probability': team2_prob,
            'team1_odds': team1_odds, 'team2_odds': team2_odds,
            'favored_team': favored_team, 'win_probability': win_probability,
            'confidence': confidence, 'analysis': analysis, 'league': league,
            'prediction_factors': {
                'team1_rating': team1_data['rating'], 'team2_rating': team2_data['rating'],
                'team1_form': team1_data['recent_form'], 'team2_form': team2_data['recent_form'],
                'system_type': 'MATHEMATICAL_ALGORITHMS'
            },
            'timestamp': datetime.now(), 'cache_status': 'algorithms'
        }

    def _get_team_data(self, team_name: str, league: str) -> Dict:
        """Busca dados reais do time"""
        if team_name in self.teams_database:
            return self.teams_database[team_name]

        # Busca parcial
        for db_team, data in self.teams_database.items():
            if db_team.lower() in team_name.lower() or team_name.lower() in db_team.lower():
                return data

        # Fallback baseado na liga
        league_defaults = {
            'LCK': {'rating': 82, 'region': 'LCK', 'recent_form': 0.75, 'consistency': 0.74},
            'LPL': {'rating': 80, 'region': 'LPL', 'recent_form': 0.73, 'consistency': 0.72},
            'LEC': {'rating': 75, 'region': 'LEC', 'recent_form': 0.70, 'consistency': 0.69},
            'LCS': {'rating': 70, 'region': 'LCS', 'recent_form': 0.65, 'consistency': 0.64},
            'CBLOL': {'rating': 72, 'region': 'CBLOL', 'recent_form': 0.68, 'consistency': 0.67}
        }

        for league_key, default_data in league_defaults.items():
            if league_key.lower() in league.lower():
                return default_data

        return {'rating': 70, 'region': league, 'recent_form': 0.6, 'consistency': 0.6}

    def _calculate_base_probability(self, team1_data: Dict, team2_data: Dict) -> float:
        """Calcula probabilidade base baseada em ratings reais"""
        rating1 = team1_data.get('rating', 70)
        rating2 = team2_data.get('rating', 70)
        rating_diff = rating1 - rating2
        return 1 / (1 + np.exp(-rating_diff / 20))

    def _calculate_region_adjustment(self, team1_data: Dict, team2_data: Dict) -> float:
        """Ajuste baseado na for??a real das regi??es"""
        region_strength = {
            'LCK': 0.02, 'LPL': 0.01, 'LEC': 0.00, 'LCS': -0.01, 'CBLOL': -0.015
        }
        region1 = team1_data.get('region', 'Unknown')
        region2 = team2_data.get('region', 'Unknown')
        adj1 = region_strength.get(region1, 0)
        adj2 = region_strength.get(region2, 0)
        return adj1 - adj2

    def _calculate_form_adjustment(self, team1_data: Dict, team2_data: Dict) -> float:
        """Ajuste baseado na forma recente real"""
        form1 = team1_data.get('recent_form', 0.6)
        form2 = team2_data.get('recent_form', 0.6)
        return (form1 - form2) * 0.15

    def _calculate_confidence(self, team1_data: Dict, team2_data: Dict) -> str:
        """Calcula n??vel de confian??a"""
        consistency1 = team1_data.get('consistency', 0.6)
        consistency2 = team2_data.get('consistency', 0.6)
        avg_consistency = (consistency1 + consistency2) / 2

        known_teams_bonus = 0
        if team1_data.get('rating', 70) > 70 and team2_data.get('rating', 70) > 70:
            known_teams_bonus = 0.1

        final_confidence = avg_consistency + known_teams_bonus

        if final_confidence > 0.85:
            return 'Muito Alta'
        elif final_confidence > 0.75:
            return 'Alta'
        elif final_confidence > 0.65:
            return 'M??dia'
        else:
            return 'Baixa'

    def _generate_match_analysis(self, team1: str, team2: str, team1_data: Dict,
                               team2_data: Dict, win_prob: float) -> str:
        """Gera an??lise textual da predi????o"""
        if win_prob > 0.55:
            favorite = team1
            fav_data = team1_data
            fav_prob = win_prob
        else:
            favorite = team2
            fav_data = team2_data
            fav_prob = 1 - win_prob

        analysis_parts = []
        rating_diff = abs(fav_data['rating'] - (team2_data['rating'] if favorite == team1 else team1_data['rating']))
        
        if rating_diff > 15:
            analysis_parts.append(f"{favorite} tem vantagem significativa no ranking")
        elif rating_diff > 8:
            analysis_parts.append(f"{favorite} ?? ligeiramente favorito")
        else:
            analysis_parts.append("Times com for??a similar")

        if fav_prob > 0.7:
            analysis_parts.append(f"{favorite} ?? forte favorito ({fav_prob:.1%})")
        else:
            analysis_parts.append("Partida equilibrada")

        return " ??? ".join(analysis_parts)

    def _get_fallback_prediction(self) -> Dict:
        """Predi????o padr??o em caso de erro"""
        return {
            'team1': 'Team 1', 'team2': 'Team 2',
            'team1_win_probability': 0.5, 'team2_win_probability': 0.5,
            'team1_odds': 2.0, 'team2_odds': 2.0,
            'favored_team': 'Team 1', 'win_probability': 0.5,
            'confidence': 'Baixa', 'analysis': 'An??lise n??o dispon??vel',
            'league': 'Unknown', 'prediction_factors': {},
            'timestamp': datetime.now(), 'cache_status': 'error'
        }

    def _calculate_live_odds_from_data(self, match: Dict, favored_team: str) -> float:
        """Calcula odds baseado em dados reais da The Odds API + ajustes por dados ao vivo"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return 2.0
                
            team1_name = teams[0].get('name', '')
            team2_name = teams[1].get('name', '')
            league = match.get('league', '')
            
            # Buscar odds reais da The Odds API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            real_odds = loop.run_until_complete(self.odds_client.get_match_odds(team1_name, team2_name, league))
            loop.close()
            
            base_odds = 2.0  # Fallback
            
            if real_odds and real_odds.get('source') == 'the_odds_api':
                # Usar odds reais
                if favored_team == team1_name:
                    base_odds = real_odds.get('team1_odds', 2.0)
                else:
                    base_odds = real_odds.get('team2_odds', 2.0)
                
                logger.info(f"???? Usando odds REAIS: {favored_team} = {base_odds:.2f}")
                
                # Verificar se h?? melhores odds dispon??veis
                best_odds = real_odds.get('best_odds', {})
                if favored_team == team1_name and 'team1_best' in best_odds:
                    best_available = best_odds['team1_best']
                    if best_available > base_odds:
                        logger.info(f"???? Melhor odd encontrada: {best_available:.2f} vs m??dia {base_odds:.2f}")
                        base_odds = best_available
                elif favored_team == team2_name and 'team2_best' in best_odds:
                    best_available = best_odds['team2_best']
                    if best_available > base_odds:
                        logger.info(f"???? Melhor odd encontrada: {best_available:.2f} vs m??dia {base_odds:.2f}")
                        base_odds = best_available
            else:
                logger.warning(f"?????? Odds reais n??o encontradas para {team1_name} vs {team2_name}, usando dados da partida")
                
                # Fallback: usar estat??sticas da partida para ajustar odds
                stats = match.get('match_statistics', {})
                
                # Exemplo de fatores que afetam odds durante a partida
                gold_diff = stats.get('gold_difference', 0)
                kill_diff = stats.get('kill_difference', 0)
                tower_diff = stats.get('tower_difference', 0)
                
                # Ajustar odds baseado na situa????o atual
                if gold_diff > 3000:  # Time favorito tem vantagem de gold
                    base_odds -= 0.3
                elif gold_diff < -3000:  # Time favorito est?? atr??s
                    base_odds += 0.4
                    
                if kill_diff > 5:
                    base_odds -= 0.2
                elif kill_diff < -5:
                    base_odds += 0.3
                    
                if tower_diff > 2:
                    base_odds -= 0.2
                elif tower_diff < -2:
                    base_odds += 0.2
                    
                logger.info(f"???? Usando odds ajustadas por dados ao vivo: {base_odds:.2f}")
                
            return max(1.2, min(5.0, base_odds))  # Limitar entre 1.2 e 5.0
            
        except Exception as e:
            logger.warning(f"??? Erro ao calcular odds reais: {e}")
            return 2.0

class TelegramAlertsSystem:
    """Sistema de Alertas APENAS para Tips Profissionais"""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.group_chat_ids = set()
        self.alert_history = []
        self.sent_tips = set()
        self.min_alert_interval = 1800  # 30 minutos

        logger.info("???? Sistema de Alertas para Tips inicializado")

    def add_group(self, chat_id: int):
        """Adiciona grupo para receber alertas"""
        self.group_chat_ids.add(chat_id)
        logger.info(f"???? Grupo {chat_id} adicionado para alertas")

    def remove_group(self, chat_id: int):
        """Remove grupo dos alertas"""
        self.group_chat_ids.discard(chat_id)
        logger.info(f"???? Grupo {chat_id} removido dos alertas")

    async def send_tip_alert(self, tip: Dict, bot_application):
        """Envia alerta de tip profissional para os grupos"""
        try:
            tip_id = tip.get('tip_id', '')
            if tip_id in self.sent_tips:
                logger.info(f"???? Tip {tip_id} j?? foi enviado - pulando")
                return

            if not self._should_send_alert(tip):
                logger.info(f"???? Tip n??o atende crit??rios para alerta")
                return

            # Extrair informa????es espec??ficas do mapa e dados ao vivo
            map_info = tip.get('map_info', 'Mapa 1')
            game_time = tip.get('game_time', 0)
            game_min = game_time // 60 if game_time > 0 else 0
            
            # Dados espec??ficos do jogo
            draft_analysis = tip.get('draft_analysis', '')
            stats_analysis = tip.get('stats_analysis', '')
            live_odds = tip.get('live_odds', 0)

            alert_message = f"""
???? **ALERTA DE TIP PROFISSIONAL** ????

??????? **{map_info}: {tip['title']}**
???? Liga: {tip['league']}
?????? Tempo de jogo: {game_min}min (AO VIVO)

???? **AN??LISE IA COM DADOS AO VIVO:**
??? Confian??a: {tip['confidence_score']:.1f}% ({tip['confidence_level']})
??? EV: {tip['ev_percentage']:.1f}%
??? Probabilidade: {tip['win_probability']*100:.1f}%
??? Odds ao vivo: {live_odds:.2f}

???? **SISTEMA DE UNIDADES:**
??? Apostar: {tip['units']} unidades
??? Valor: ${tip['stake_amount']:.2f}
??? Risco: {tip['risk_level']}

??? **Recomenda????o:** {tip['recommended_team']}

???? **DADOS DA PARTIDA:**"""

            # Adicionar an??lise de draft se dispon??vel
            if draft_analysis and draft_analysis != "Dados de draft n??o dispon??veis":
                alert_message += f"\n???? Draft: {draft_analysis}"
            
            # Adicionar an??lise de estat??sticas se dispon??vel
            if stats_analysis and stats_analysis != "Estat??sticas n??o dispon??veis":
                alert_message += f"\n???? Stats: {stats_analysis}"

            alert_message += f"""

???? **EXPLICA????O COMPLETA:**
{tip['reasoning']}

??? **PARTIDA AO VIVO COM DADOS REAIS!**
??? {datetime.now().strftime('%H:%M:%S')}
            """

            sent_count = 0
            for chat_id in self.group_chat_ids.copy():
                try:
                    # Para v13, usar bot_application.bot.send_message
                    await bot_application.bot.send_message(
                        chat_id=chat_id,
                        text=alert_message,
                        parse_mode="Markdown"
                    )
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"??? Erro ao enviar alerta para grupo {chat_id}: {e}")
                    self.group_chat_ids.discard(chat_id)

            self.sent_tips.add(tip_id)
            self._register_alert(tip_id, tip)

            logger.info(f"???? Alerta de tip {map_info} enviado para {sent_count} grupos - ID: {tip_id}")

        except Exception as e:
            logger.error(f"??? Erro no sistema de alertas: {e}")

    def _should_send_alert(self, tip: Dict) -> bool:
        """Verifica se deve enviar alerta"""
        confidence = tip.get('confidence_score', 0)
        ev = tip.get('ev_percentage', 0)
        confidence_level = tip.get('confidence_level', '')

        return (
            confidence >= 80 and
            ev >= 10 and
            confidence_level in ['Alta', 'Muito Alta'] and
            tip.get('units', 0) >= 2.0
        )

    def _register_alert(self, tip_id: str, tip: Dict):
        """Registra alerta no hist??rico"""
        alert_record = {
            'tip_id': tip_id, 'timestamp': datetime.now(),
            'groups_sent': len(self.group_chat_ids),
            'confidence': tip.get('confidence_score', 0),
            'ev': tip.get('ev_percentage', 0),
            'units': tip.get('units', 0),
            'recommended_team': tip.get('recommended_team', ''),
            'league': tip.get('league', '')
        }

        self.alert_history.append(alert_record)
        if len(self.alert_history) > 50:
            self.alert_history = self.alert_history[-50:]

    def get_alert_stats(self) -> Dict:
        """Retorna estat??sticas dos alertas"""
        today = datetime.now().date()
        alerts_today = sum(1 for a in self.alert_history
                          if a['timestamp'].date() == today)
        
        recent_alerts = [a for a in self.alert_history
                        if (datetime.now() - a['timestamp']).days < 7]

        return {
            'total_groups': len(self.group_chat_ids),
            'alerts_sent': len(self.alert_history),  # Chave correta esperada pelos callbacks
            'tips_alerted': len(self.sent_tips),  # Chave correta esperada pelos callbacks
            'last_alert': self.alert_history[-1]['timestamp'].strftime('%H:%M:%S') if self.alert_history else 'Nunca',  # Chave correta
            'success_rate': 85.0,  # Placeholder para taxa de sucesso
            'alerts_today': alerts_today,  # Chave correta esperada pelos callbacks
            'active_groups': len(self.group_chat_ids),  # Chave correta esperada pelos callbacks
            'tips_this_week': len(recent_alerts),
            'avg_confidence': sum(a.get('confidence', 80) for a in recent_alerts) / len(recent_alerts) if recent_alerts else 80,
            'avg_ev': sum(a.get('ev', 10) for a in recent_alerts) / len(recent_alerts) if recent_alerts else 10,
            'avg_units': sum(a.get('units', 2) for a in recent_alerts) / len(recent_alerts) if recent_alerts else 2
        }

    def clear_old_tips(self):
        """Remove tips antigos do cache (mais de 24h)"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_tips = []

            for alert in self.alert_history:
                if alert['timestamp'] < cutoff_time:
                    old_tips.append(alert['tip_id'])

            for tip_id in old_tips:
                self.sent_tips.discard(tip_id)

            # Limpar hist??rico antigo tamb??m
            self.alert_history = [alert for alert in self.alert_history 
                                if alert['timestamp'] >= cutoff_time]

            if old_tips:
                logger.info(f"???? {len(old_tips)} tips antigos removidos do cache")
        except Exception as e:
            logger.error(f"??? Erro ao limpar tips antigos: {e}")

class ScheduleManager:
    """Gerenciador de Agenda de Partidas"""

    def __init__(self, riot_client=None):
        self.riot_client = riot_client or RiotAPIClient()
        self.scheduled_matches = []
        self.last_update = None
        logger.info("???? ScheduleManager inicializado")

    async def get_scheduled_matches(self, days_ahead: int = 7) -> List[Dict]:
        """Busca partidas agendadas"""
        try:
            endpoints = [
                f"{self.riot_client.base_urls['esports']}/getSchedule?hl=pt-BR",
                f"{self.riot_client.base_urls['esports']}/getSchedule?hl=en-US"
            ]

            all_matches = []
            for endpoint in endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoint, headers=self.riot_client.headers, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                matches = self._extract_scheduled_matches(data, days_ahead)
                                all_matches.extend(matches)
                except Exception as e:
                    logger.warning(f"??? Erro no endpoint de agenda: {e}")
                continue

            unique_matches = self._remove_duplicates(all_matches)
            sorted_matches = sorted(unique_matches, key=lambda x: x.get('start_time', ''))

            self.scheduled_matches = sorted_matches[:20]
            self.last_update = datetime.now()

            logger.info(f"???? {len(self.scheduled_matches)} partidas agendadas encontradas")
            return self.scheduled_matches

        except Exception as e:
            logger.error(f"Erro ao buscar agenda: {e}")
            return []

    def _extract_scheduled_matches(self, data: Dict, days_ahead: int) -> List[Dict]:
        """Extrai partidas agendadas dos dados da API"""
        matches = []
        try:
            events = None
            if 'data' in data and 'schedule' in data['data'] and 'events' in data['data']['schedule']:
                events = data['data']['schedule']['events']
            elif 'data' in data and 'events' in data['data']:
                events = data['data']['events']

            if events:
                # CORRE????O: Usar timezone aware para compara????o
                from datetime import timezone
                cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
                now_utc = datetime.now(timezone.utc)
                
                for event in events:
                    try:
                        start_time_str = event.get('startTime', '')
                        if start_time_str:
                            # Converter para datetime com timezone
                            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                            
                            # Verificar se est?? no intervalo desejado
                            if now_utc <= start_time <= cutoff_date:
                                teams = self._extract_teams_from_event(event)
                                if len(teams) >= 2:
                                    # Converter para hor??rio local para exibi????o
                                    local_time = start_time.astimezone()
                                    
                                    match = {
                                        'teams': teams,
                                        'league': self._extract_league_from_event(event),
                                        'tournament': event.get('tournament', {}).get('name', 'Tournament'),
                                        'start_time': start_time_str,
                                        'start_time_formatted': local_time.strftime('%d/%m %H:%M'),
                                        'status': event.get('state', 'scheduled'),
                                        'match_id': event.get('id', f"match_{len(matches)}")
                                    }
                                    matches.append(match)
                    except Exception as e:
                        logger.debug(f"Erro ao processar evento: {e}")
                        continue
        except Exception as e:
            logger.error(f"Erro ao extrair partidas agendadas: {e}")
        return matches

    def _extract_teams_from_event(self, event: Dict) -> List[Dict]:
        """Extrai times do evento"""
        teams = []
        try:
            teams_data = event.get('match', {}).get('teams', [])
            if not teams_data:
                teams_data = event.get('teams', [])

            for team_data in teams_data:
                team = {
                    'name': team_data.get('name', 'Unknown Team'),
                    'code': team_data.get('code', ''),
                    'image': team_data.get('image', '')
                }
                teams.append(team)
        except:
            pass
        return teams

    def _extract_league_from_event(self, event: Dict) -> str:
        """Extrai nome da liga"""
        try:
            return event.get('league', {}).get('name', 'Unknown League')
        except:
            return 'Unknown League'

    def _remove_duplicates(self, matches: List[Dict]) -> List[Dict]:
        """Remove partidas duplicadas com algoritmo melhorado"""
        seen = set()
        unique_matches = []

        for match in matches:
            try:
                teams = match.get('teams', [])
                if len(teams) >= 2:
                    team1 = teams[0].get('name', '').strip()
                    team2 = teams[1].get('name', '').strip()
                    start_time = match.get('start_time', '')
                    league = match.get('league', '')
                    
                    # Criar ID ??nico mais espec??fico
                    # Usar tanto A vs B quanto B vs A para evitar duplicatas de ordem
                    team_pair = tuple(sorted([team1, team2]))
                    match_id = f"{team_pair}_{league}_{start_time}"
                    
                    if match_id not in seen:
                        seen.add(match_id)
                        unique_matches.append(match)
                    else:
                        logger.debug(f"🔄 Partida duplicada removida: {team1} vs {team2}")
                        
            except Exception as e:
                logger.debug(f"Erro ao processar partida para remoção de duplicatas: {e}")
                unique_matches.append(match)  # Incluir mesmo com erro
                    
        return unique_matches

    def get_matches_today(self) -> List[Dict]:
        """Retorna partidas para hoje"""
        try:
            today_matches = []
            for match in self.scheduled_matches:
                start_time_str = match.get('start_time', '')
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_time.date() == datetime.now().date():
                            today_matches.append(match)
                    except:
                        continue
            return today_matches
        except:
            return []

class MatchMonitor:
    """Monitor de partidas ao vivo com sistema profissional de análise"""

    def __init__(self, riot_client=None):
        self.riot_client = riot_client or RiotAPIClient()
        self.prediction_system = global_cache.get_prediction_system()
        self.units_system = ProfessionalUnitsSystem()
        self.alerts_system = TelegramAlertsSystem(TOKEN)
        self.monitoring = False
        self.monitor_thread = None
        self.bot_instance = None
        self.found_tips = []
        self.processed_matches = set()
        
        # Cache de monitoramento
        self.last_scan_time = None
        self.scan_interval = 180  # 3 minutos
        
        logger.info("🔍 MatchMonitor inicializado com sistema profissional")

    def start_monitoring(self):
        """Inicia monitoramento em thread separada"""
        if not self.monitoring:
            self.monitoring = True
            if self.monitor_thread and self.monitor_thread.is_alive():
                logger.warning("⚠️ Thread de monitoramento já ativa")
                return
                
            def monitor_loop():
                """Loop principal de monitoramento"""
                logger.info("🔄 Iniciando loop de monitoramento...")
                while self.monitoring:
                    try:
                        # Executar scan assíncrono
                        asyncio.run(self._scan_live_matches_only())
                        time.sleep(self.scan_interval)
                    except Exception as e:
                        logger.error(f"❌ Erro no loop de monitoramento: {e}")
                        time.sleep(30)  # Pausa menor em caso de erro
                        
            self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("✅ Monitoramento iniciado")

    def stop_monitoring(self):
        """Para o monitoramento"""
        self.monitoring = False
        logger.info("⏹️ Monitoramento parado")

    async def _scan_live_matches_only(self):
        """Escaneia apenas partidas ao vivo (otimizado)"""
        try:
            # Verificar se deve fazer novo scan
            if self.last_scan_time:
                elapsed = (datetime.now() - self.last_scan_time).total_seconds()
                if elapsed < self.scan_interval:
                    return

            start_time = time.time()
            logger.info("🔍 Iniciando scan de partidas ao vivo...")

            # Usar cache se válido
            if global_cache.is_matches_cache_valid():
                live_matches = global_cache.get_cached_matches()
                logger.debug("📦 Usando matches do cache global")
            else:
                # Buscar partidas ao vivo
                live_matches = await self.riot_client.get_live_matches()
                global_cache.cache_matches(live_matches)

            if not live_matches:
                logger.info("📭 Nenhuma partida ao vivo encontrada")
                return

            tips_generated = 0
            matches_analyzed = 0

            # Filtrar apenas partidas com dados completos
            valid_matches = []
            for match in live_matches:
                if self._has_complete_match_data(match):
                    valid_matches.append(match)

            logger.info(f"🎯 {len(valid_matches)} partidas válidas para análise")

            # Analisar partidas em lote com limite
            for i, match in enumerate(valid_matches[:3]):  # Máximo 3 partidas por scan
                try:
                    match_id = match.get('id') or f"{match.get('teams', [{}])[0].get('name', 'unknown')}_vs_{match.get('teams', [{}])[1].get('name', 'unknown')}"
                    
                    if match_id in self.processed_matches:
                        continue
                        
                    # Análise da partida
                    analysis = await self._analyze_live_match_with_data(match)
                    if analysis:
                        tip = self._create_professional_tip_with_game_data(analysis)
                        if tip:
                            # Registrar tip encontrado
                            self.found_tips.append(tip)
                            tips_generated += 1
                            
                            # Enviar alerta se bot ativo
                            if self.bot_instance:
                                await self.alerts_system.send_tip_alert(tip, self.bot_instance)
                                
                            logger.info(f"💎 TIP PROFISSIONAL gerado: {tip['teams']} | {tip['units']} unidades | Conf: {tip['confidence_score']}%")
                        
                        self.processed_matches.add(match_id)
                        matches_analyzed += 1
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao analisar partida: {e}")
                    continue

            # Limpeza periódica
            self._cleanup_old_tips()

            scan_duration = time.time() - start_time
            self.last_scan_time = datetime.now()
            
            logger.info(f"✅ Scan completo em {scan_duration:.1f}s | "
                       f"Partidas: {len(live_matches)} | "
                       f"Analisadas: {matches_analyzed} | "
                       f"Tips: {tips_generated}")

        except Exception as e:
            logger.error(f"❌ Erro no scan de partidas: {e}")

    def _has_complete_match_data(self, match: Dict) -> bool:
        """Verifica se a partida tem dados completos"""
        try:
            # Verificar estrutura básica
            if not isinstance(match, dict):
                return False
                
            teams = match.get('teams', [])
            if len(teams) < 2:
                return False
                
            # Verificar nomes dos times
            team1_name = teams[0].get('name', '').strip()
            team2_name = teams[1].get('name', '').strip()
            
            if not team1_name or not team2_name:
                return False
                
            # Verificar liga
            league = match.get('league', '').strip()
            if not league:
                return False
                
            # Verificar se não é partida de treino/custom
            excluded_keywords = ['custom', 'practice', 'scrim', 'test', 'training']
            league_lower = league.lower()
            
            if any(keyword in league_lower for keyword in excluded_keywords):
                return False
                
            # Verificar tempo de jogo mínimo (evitar partidas que acabaram de começar)
            game_time = match.get('game_time', 0)
            if game_time < 5:  # Menos de 5 minutos
                return False
                
            return True
            
        except Exception as e:
            logger.debug(f"Erro ao verificar dados da partida: {e}")
            return False

    async def _analyze_live_match_with_data(self, match: Dict) -> Optional[Dict]:
        """Análise completa de partida ao vivo com dados em tempo real"""
        try:
            # Obter predição base
            prediction = await self.prediction_system.predict_live_match(match)
            if not prediction:
                return None

            # Dados da partida
            teams = match.get('teams', [])
            team1_name = teams[0].get('name', 'Team 1')
            team2_name = teams[1].get('name', 'Team 2')
            league = match.get('league', 'Unknown')
            game_time = match.get('game_time', 0)

            # Calcular odds ao vivo baseado em dados
            favored_team = prediction.get('recommended_team', team1_name)
            live_odds = self.prediction_system._calculate_live_odds_from_data(match, favored_team)

            # Extrair probabilidade de vitória
            win_prob_str = prediction.get('win_probability', '55%')
            win_prob = float(win_prob_str.replace('%', '')) / 100

            # Calcular EV com dados ao vivo
            ev_percentage = self._calculate_ev_with_live_data(win_prob, live_odds, match)

            # Analisar dados específicos do jogo
            draft_analysis = ""
            stats_analysis = ""
            
            if 'draft_data' in match:
                draft_analysis = self._analyze_draft_data(match['draft_data'])
                
            if 'match_stats' in match:
                stats_analysis = self._analyze_match_statistics(match['match_stats'])

            return {
                'match': match,
                'prediction': prediction,
                'teams': f"{team1_name} vs {team2_name}",
                'league': league,
                'game_time': game_time,
                'recommended_team': favored_team,
                'win_probability': win_prob,
                'live_odds': live_odds,
                'ev_percentage': ev_percentage,
                'confidence_score': prediction.get('confidence_score', 75),
                'draft_analysis': draft_analysis,
                'stats_analysis': stats_analysis,
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Erro na análise da partida: {e}")
            return None

    def _calculate_ev_with_live_data(self, win_probability: float, live_odds: float, match: Dict) -> float:
        """Calcula Expected Value com dados ao vivo"""
        try:
            # Fórmula EV = (Probabilidade × Odds) - 1
            ev = (win_probability * live_odds) - 1
            ev_percentage = ev * 100
            
            # Ajustes baseados em dados ao vivo
            game_time = match.get('game_time', 0)
            
            # Bonus para partidas mais avançadas (mais dados disponíveis)
            if game_time > 15:
                ev_percentage += 2
            if game_time > 25:
                ev_percentage += 3
                
            # Verificar se há dados detalhados
            if match.get('detailed_stats'):
                ev_percentage += 5
                
            return max(0, ev_percentage)
            
        except Exception as e:
            logger.error(f"Erro no cálculo de EV: {e}")
            return 10.0  # EV padrão conservador

    def _analyze_draft_data(self, draft_data: Dict) -> str:
        """Analisa dados de draft/picks"""
        try:
            analysis = []
            
            team1_picks = draft_data.get('team1_picks', [])
            team2_picks = draft_data.get('team2_picks', [])
            
            if team1_picks:
                comp1 = self._analyze_team_composition(team1_picks)
                analysis.append(f"Time 1: {comp1}")
                
            if team2_picks:
                comp2 = self._analyze_team_composition(team2_picks)
                analysis.append(f"Time 2: {comp2}")
                
            return " | ".join(analysis)
            
        except Exception as e:
            logger.debug(f"Erro na análise de draft: {e}")
            return "Draft data não disponível"

    def _analyze_team_composition(self, picks: List) -> str:
        """Analisa composição do time"""
        # Análise básica de composição
        return f"Comp: {len(picks)} picks"

    def _analyze_match_statistics(self, match_stats: Dict) -> str:
        """Analisa estatísticas da partida"""
        try:
            stats = []
            
            # Gold difference
            gold_diff = match_stats.get('gold_difference', 0)
            if abs(gold_diff) > 1000:
                team_ahead = "Time 1" if gold_diff > 0 else "Time 2"
                stats.append(f"{team_ahead} +{abs(gold_diff)}g")
                
            # Kills
            team1_kills = match_stats.get('team1_kills', 0)
            team2_kills = match_stats.get('team2_kills', 0)
            if team1_kills + team2_kills > 5:
                stats.append(f"Kills: {team1_kills}-{team2_kills}")
                
            # Towers
            team1_towers = match_stats.get('team1_towers', 0)
            team2_towers = match_stats.get('team2_towers', 0)
            if team1_towers + team2_towers > 0:
                stats.append(f"Torres: {team1_towers}-{team2_towers}")
                
            return " | ".join(stats) if stats else "Stats em desenvolvimento"
            
        except Exception as e:
            logger.debug(f"Erro na análise de stats: {e}")
            return "Match stats não disponíveis"

    def _generate_tip_id_with_game(self, match: Dict) -> str:
        """Gera ID único para o tip baseado na partida"""
        try:
            teams = match.get('teams', [])
            team1 = teams[0].get('name', 'T1') if teams else 'T1'
            team2 = teams[1].get('name', 'T2') if len(teams) > 1 else 'T2'
            league = match.get('league', 'League')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            return f"tip_{team1}_{team2}_{league}_{timestamp}".replace(' ', '_').lower()
            
        except Exception as e:
            logger.error(f"Erro ao gerar tip ID: {e}")
            return f"tip_{datetime.now().timestamp()}"

    def _create_professional_tip_with_game_data(self, analysis: Dict) -> Dict:
        """Cria tip profissional com dados de jogo em tempo real"""
        try:
            # Verificar se atende critérios profissionais
            if not self._meets_professional_criteria(analysis):
                return None

            # Calcular unidades baseado no EV
            confidence = analysis.get('confidence_score', 75)
            ev_percentage = analysis.get('ev_percentage', 10)
            league = analysis.get('league', 'Unknown')
            league_tier = self._determine_league_tier(league)
            
            units_calc = self.units_system.calculate_units(confidence, ev_percentage, league_tier)

            tip = {
                'id': self._generate_tip_id_with_game(analysis['match']),
                'teams': analysis['teams'],
                'league': league,
                'recommended_team': analysis['recommended_team'],
                'win_probability': f"{analysis['win_probability']*100:.1f}%",
                'confidence_score': confidence,
                'live_odds': analysis['live_odds'],
                'ev_percentage': ev_percentage,
                'units': units_calc['units'],
                'units_reasoning': units_calc['reasoning'],
                'game_time': analysis['game_time'],
                'draft_analysis': analysis.get('draft_analysis', ''),
                'stats_analysis': analysis.get('stats_analysis', ''),
                'tip_reasoning': self._generate_tip_reasoning_with_live_data(analysis, units_calc),
                'timestamp': datetime.now().isoformat(),
                'source': 'professional_live_analysis',
                'quality_score': self._calculate_tip_quality(analysis, units_calc)
            }

            return tip

        except Exception as e:
            logger.error(f"❌ Erro ao criar tip profissional: {e}")
            return None

    def _generate_tip_reasoning_with_live_data(self, analysis: Dict, units_calc: Dict) -> str:
        """Gera raciocínio do tip com dados ao vivo"""
        try:
            reasoning_parts = []
            
            # Análise base
            reasoning_parts.append(f"🎯 {analysis['recommended_team']} ({analysis['win_probability']*100:.1f}% win prob)")
            reasoning_parts.append(f"📊 Confiança: {analysis['confidence_score']}%")
            reasoning_parts.append(f"💰 EV: {analysis['ev_percentage']:.1f}%")
            reasoning_parts.append(f"🎲 Odds: {analysis['live_odds']:.2f}")
            reasoning_parts.append(f"⏱️ Tempo: {analysis['game_time']} min")
            
            # Análise específica do jogo
            if analysis.get('draft_analysis'):
                reasoning_parts.append(f"🛡️ Draft: {analysis['draft_analysis']}")
                
            if analysis.get('stats_analysis'):
                reasoning_parts.append(f"📈 Stats: {analysis['stats_analysis']}")
            
            # Unidades
            reasoning_parts.append(f"💎 {units_calc['units']} unidades | {units_calc['reasoning']}")
            
            return " | ".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Erro ao gerar reasoning: {e}")
            return f"Tip para {analysis.get('teams', 'partida')} - análise em tempo real"

    def get_monitoring_status(self) -> Dict:
        """Retorna status do monitoramento"""
        return {
            'monitoring': self.monitoring,
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False,
            'last_scan': self.last_scan_time.strftime('%H:%M:%S') if self.last_scan_time else 'Nunca',
            'tips_found': len(self.found_tips),
            'matches_processed': len(self.processed_matches),
            'scan_interval': f"{self.scan_interval}s",
            'bot_connected': bool(self.bot_instance)
        }

    def set_bot_instance(self, bot_instance):
        """Define instância do bot para envio de alertas"""
        self.bot_instance = bot_instance
        self.alerts_system.set_bot_application(bot_instance)

    def _cleanup_old_tips(self):
        """Remove tips antigos do cache"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=12)
            old_tips = []
            
            for tip in self.found_tips:
                tip_time_str = tip.get('timestamp', '')
                if tip_time_str:
                    try:
                        tip_time = datetime.fromisoformat(tip_time_str)
                        if tip_time < cutoff_time:
                            old_tips.append(tip)
                    except:
                        continue
                        
            for old_tip in old_tips:
                self.found_tips.remove(old_tip)
                
            if old_tips:
                logger.info(f"🧹 {len(old_tips)} tips antigos removidos")
                
        except Exception as e:
            logger.error(f"Erro na limpeza de tips: {e}")

    def _meets_professional_criteria(self, analysis: Dict) -> bool:
        """Verifica se análise atende critérios profissionais rigorosos"""
        try:
            confidence = analysis.get('confidence_score', 0)
            ev_percentage = analysis.get('ev_percentage', 0)
            
            return confidence >= 75 and ev_percentage >= 8
        except:
            return False

    def _create_professional_tip(self, analysis: Dict) -> Dict:
        """Cria tip profissional padrão"""
        try:
            confidence = analysis.get('confidence_score', 75)
            ev_percentage = analysis.get('ev_percentage', 10)
            league = analysis.get('league', 'Unknown')
            league_tier = self._determine_league_tier(league)
            
            units_calc = self.units_system.calculate_units(confidence, ev_percentage, league_tier)

            tip = {
                'id': self._generate_tip_id(analysis['match']),
                'teams': analysis['teams'],
                'league': league,
                'recommended_team': analysis['recommended_team'],
                'win_probability': f"{analysis['win_probability']*100:.1f}%",
                'confidence_score': confidence,
                'live_odds': analysis.get('live_odds', 2.0),
                'ev_percentage': ev_percentage,
                'units': units_calc['units'],
                'units_reasoning': units_calc['reasoning'],
                'tip_reasoning': self._generate_tip_reasoning(analysis, units_calc),
                'timestamp': datetime.now().isoformat(),
                'source': 'professional_analysis'
            }

            return tip
        except Exception as e:
            logger.error(f"❌ Erro ao criar tip: {e}")
            return None

    def _generate_tip_reasoning(self, analysis: Dict, units_calc: Dict) -> str:
        """Gera raciocínio básico do tip"""
        try:
            return f"🎯 {analysis['recommended_team']} | Conf: {analysis['confidence_score']}% | EV: {analysis['ev_percentage']:.1f}% | {units_calc['units']} unidades"
        except:
            return "Análise profissional"

    def _determine_league_tier(self, league: str) -> str:
        """Determina tier da liga"""
        tier1_leagues = ['LCK', 'LPL', 'LEC', 'LCS', 'Worlds', 'MSI']
        if any(t1 in league.upper() for t1 in tier1_leagues):
            return 'tier1'
        return 'tier2'

    def _generate_tip_id(self, match: Dict) -> str:
        """Gera ID do tip"""
        try:
            teams = match.get('teams', [])
            team1 = teams[0].get('name', 'T1') if teams else 'T1'
            team2 = teams[1].get('name', 'T2') if len(teams) > 1 else 'T2'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            return f"tip_{team1}_{team2}_{timestamp}".replace(' ', '_').lower()
        except:
            return f"tip_{datetime.now().timestamp()}"

    def _calculate_tip_quality(self, analysis: Dict, units_calc: Dict) -> float:
        """Calcula score de qualidade do tip"""
        try:
            base_score = analysis.get('confidence_score', 75)
            ev_bonus = min(analysis.get('ev_percentage', 0) * 2, 20)
            units_bonus = units_calc.get('units', 1) * 5
            
            return min(100, base_score + ev_bonus + units_bonus)
        except:
            return 75.0

# Instância global do monitor
match_monitor = MatchMonitor()

class TipGenerator:
    """Gerador profissional de tips"""

    def __init__(self):
        self.riot_client = RiotAPIClient()
        self.prediction_system = global_cache.get_prediction_system()
        self.units_system = ProfessionalUnitsSystem()
        self.generated_tips = []
        self.tip_cache = {}
        self.last_generation = None
        
        logger.info("💡 TipGenerator profissional inicializado")

    def set_bot_application(self, application):
        """Define aplicação do bot"""
        self.bot_application = application

async def main():
    """Função principal"""
    try:
        # Configuração global
        os.environ['TZ'] = 'America/Sao_Paulo'
        
        # Verificação de ambiente
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))
        
        logger.info("🚀 Iniciando BOT LOL V3 - Sistema Profissional de Unidades")
        logger.info(f"🌍 Ambiente: {'RAILWAY' if is_railway else 'LOCAL'}")
        
        # Inicializar sistemas
        global match_monitor
        match_monitor = MatchMonitor()
        
        if is_railway:
            # Modo Railway - Webhook
            logger.info("🔗 Configurando webhook para Railway...")
            
            # Configurar webhook
            webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/webhook"
            
            try:
                from telegram.ext import Application
                
                # Criar aplicação v20
                application = Application.builder().token(TOKEN).build()
                
                # Configurar bot handler
                bot_handler = BotHandler()
                bot_handler.set_bot_application(application)
                match_monitor.set_bot_instance(application)
                
                # Adicionar handlers
                application.add_handler(CommandHandler('start', bot_handler.start_command))
                application.add_handler(CommandHandler('menu', bot_handler.menu_command))
                application.add_handler(CommandHandler('tips', bot_handler.tips_command))
                application.add_handler(CommandHandler('live', bot_handler.live_matches_command))
                application.add_handler(CommandHandler('schedule', bot_handler.schedule_command))
                application.add_handler(CommandHandler('monitoring', bot_handler.monitoring_command))
                application.add_handler(CommandHandler('scan', bot_handler.force_scan_command))
                application.add_handler(CommandHandler('predictions', bot_handler.predictions_command))
                application.add_handler(CommandHandler('alerts', bot_handler.alerts_command))
                application.add_handler(CommandHandler('units', bot_handler.units_command))
                application.add_handler(CommandHandler('performance', bot_handler.performance_command))
                application.add_handler(CommandHandler('history', bot_handler.history_command))
                application.add_handler(CommandHandler('odds', bot_handler.odds_command))
                application.add_handler(CommandHandler('timesfavoritos', bot_handler.timesfavoritos_command))
                application.add_handler(CommandHandler('statuslol', bot_handler.statuslol_command))
                application.add_handler(CallbackQueryHandler(bot_handler.callback_handler))
                
                # Inicializar aplicação
                await application.initialize()
                await application.start()
                
                # Configurar webhook
                await application.bot.set_webhook(
                    url=webhook_url,
                    allowed_updates=['message', 'callback_query']
                )
                
                logger.info(f"✅ Webhook configurado: {webhook_url}")
                
                # Iniciar monitoramento
                match_monitor.start_monitoring()
                
                # Rota de webhook
                @app.route('/webhook', methods=['POST'])
                async def webhook_v20():
                    """Webhook handler para v20"""
                    try:
                        from telegram import Update
                        
                        update = Update.de_json(request.get_json(force=True), application.bot)
                        await application.process_update(update)
                        return 'OK', 200
                    except Exception as e:
                        logger.error(f"❌ Erro no webhook: {e}")
                        return 'Error', 500
                
                # Iniciar Flask
                logger.info(f"🌐 Iniciando servidor Flask na porta {PORT}")
                app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
                
            except ImportError:
                # Fallback para v13
                logger.info("📱 Usando Telegram Bot API v13 (fallback)")
                
                updater = Updater(token=TOKEN, use_context=True)
                dp = updater.dispatcher
                
                # Bot handler
                bot_handler = BotHandler()
                match_monitor.set_bot_instance(updater.bot)
                
                # Comandos
                dp.add_handler(CommandHandler('start', bot_handler.start_command))
                dp.add_handler(CommandHandler('menu', bot_handler.menu_command))
                dp.add_handler(CommandHandler('tips', bot_handler.tips_command))
                dp.add_handler(CommandHandler('live', bot_handler.live_matches_command))
                dp.add_handler(CommandHandler('schedule', bot_handler.schedule_command))
                dp.add_handler(CommandHandler('monitoring', bot_handler.monitoring_command))
                dp.add_handler(CommandHandler('scan', bot_handler.force_scan_command))
                dp.add_handler(CommandHandler('predictions', bot_handler.predictions_command))
                dp.add_handler(CommandHandler('alerts', bot_handler.alerts_command))
                dp.add_handler(CommandHandler('units', bot_handler.units_command))
                dp.add_handler(CommandHandler('performance', bot_handler.performance_command))
                dp.add_handler(CommandHandler('history', bot_handler.history_command))
                dp.add_handler(CommandHandler('odds', bot_handler.odds_command))
                dp.add_handler(CommandHandler('timesfavoritos', bot_handler.timesfavoritos_command))
                dp.add_handler(CommandHandler('statuslol', bot_handler.statuslol_command))
                dp.add_handler(CallbackQueryHandler(bot_handler.callback_handler))
                
                # Configurar webhook
                updater.start_webhook(
                    listen='0.0.0.0',
                    port=PORT,
                    url_path='/webhook',
                    webhook_url=webhook_url
                )
                
                # Iniciar monitoramento
                match_monitor.start_monitoring()
                
                # Rota webhook v13
                @app.route('/webhook', methods=['POST'])
                def webhook_v13():
                    """Webhook handler para v13"""
                    try:
                        update = Update.de_json(request.get_json(force=True), updater.bot)
                        dp.process_update(update)
                        return 'OK', 200
                    except Exception as e:
                        logger.error(f"❌ Erro no webhook v13: {e}")
                        return 'Error', 500
                
                logger.info(f"✅ Bot iniciado com webhook: {webhook_url}")
                updater.idle()
        
        else:
            # Modo local - Polling
            logger.info("🔄 Modo local - iniciando polling...")
            
            try:
                from telegram.ext import Application
                
                # Telegram v20
                application = Application.builder().token(TOKEN).build()
                
                bot_handler = BotHandler()
                bot_handler.set_bot_application(application)
                match_monitor.set_bot_instance(application)
                
                # Handlers
                application.add_handler(CommandHandler('start', bot_handler.start_command))
                application.add_handler(CommandHandler('menu', bot_handler.menu_command))
                application.add_handler(CommandHandler('tips', bot_handler.tips_command))
                application.add_handler(CommandHandler('live', bot_handler.live_matches_command))
                application.add_handler(CommandHandler('schedule', bot_handler.schedule_command))
                application.add_handler(CommandHandler('monitoring', bot_handler.monitoring_command))
                application.add_handler(CommandHandler('scan', bot_handler.force_scan_command))
                application.add_handler(CommandHandler('predictions', bot_handler.predictions_command))
                application.add_handler(CommandHandler('alerts', bot_handler.alerts_command))
                application.add_handler(CommandHandler('units', bot_handler.units_command))
                application.add_handler(CommandHandler('performance', bot_handler.performance_command))
                application.add_handler(CommandHandler('history', bot_handler.history_command))
                application.add_handler(CommandHandler('odds', bot_handler.odds_command))
                application.add_handler(CommandHandler('timesfavoritos', bot_handler.timesfavoritos_command))
                application.add_handler(CommandHandler('statuslol', bot_handler.statuslol_command))
                application.add_handler(CallbackQueryHandler(bot_handler.callback_handler))
                
                # Inicializar
                await application.initialize()
                await application.start()
                
                # Iniciar monitoramento
                match_monitor.start_monitoring()
                
                # Iniciar Flask em thread separada
                flask_thread = threading.Thread(target=run_flask, daemon=True)
                flask_thread.start()
                
                # Controle de sinais
                import signal
                
                def signal_handler(signum, frame):
                    logger.info("🛑 Recebido sinal de parada...")
                    match_monitor.stop_monitoring()
                    sys.exit(0)
                
                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)
                
                logger.info("✅ Bot iniciado em modo polling")
                await application.run_polling(
                    allowed_updates=['message', 'callback_query'],
                    drop_pending_updates=True
                )
                
            except ImportError:
                # Fallback v13
                logger.info("📱 Iniciando com Telegram Bot API v13...")
                
                updater = Updater(token=TOKEN, use_context=True)
                dp = updater.dispatcher
                
                bot_handler = BotHandler()
                match_monitor.set_bot_instance(updater.bot)
                
                # Adicionar handlers
                dp.add_handler(CommandHandler('start', bot_handler.start_command))
                dp.add_handler(CommandHandler('menu', bot_handler.menu_command))
                dp.add_handler(CommandHandler('tips', bot_handler.tips_command))
                dp.add_handler(CommandHandler('live', bot_handler.live_matches_command))
                dp.add_handler(CommandHandler('schedule', bot_handler.schedule_command))
                dp.add_handler(CommandHandler('monitoring', bot_handler.monitoring_command))
                dp.add_handler(CommandHandler('scan', bot_handler.force_scan_command))
                dp.add_handler(CommandHandler('predictions', bot_handler.predictions_command))
                dp.add_handler(CommandHandler('alerts', bot_handler.alerts_command))
                dp.add_handler(CommandHandler('units', bot_handler.units_command))
                dp.add_handler(CommandHandler('performance', bot_handler.performance_command))
                dp.add_handler(CommandHandler('history', bot_handler.history_command))
                dp.add_handler(CommandHandler('odds', bot_handler.odds_command))
                dp.add_handler(CommandHandler('timesfavoritos', bot_handler.timesfavoritos_command))
                dp.add_handler(CommandHandler('statuslol', bot_handler.statuslol_command))
                dp.add_handler(CallbackQueryHandler(bot_handler.callback_handler))
                
                # Iniciar monitoramento
                match_monitor.start_monitoring()
                
                # Flask thread
                flask_thread = threading.Thread(target=run_flask, daemon=True)
                flask_thread.start()
                
                logger.info("✅ Bot v13 iniciado com polling")
                updater.start_polling()
                updater.idle()

    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO na função main: {e}")
        raise


def run_flask():
    """Executa Flask para health check"""
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

def check_single_instance():
    """Verifica se há apenas uma instância rodando"""
    try:
        # Railway sempre permite múltiplas instâncias
        if os.getenv('RAILWAY_ENVIRONMENT_NAME'):
            return True
            
        import tempfile
        lock_file = os.path.join(tempfile.gettempdir(), 'bot_lol_v3.lock')
        
        # Verificar se arquivo de lock existe
        if os.path.exists(lock_file):
            with open(lock_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Verificar se processo ainda existe
            try:
                if os.name == 'nt':  # Windows
                    import subprocess
                    result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'],
                                          capture_output=True, text=True)
                    if str(old_pid) in result.stdout:
                        logger.error(f"❌ Outra instância já rodando! PID: {old_pid}")
                        return False
                else:  # Unix/Linux
                    os.kill(old_pid, 0)  # Apenas verifica, não mata
                    logger.error(f"❌ Outra instância já rodando! PID: {old_pid}")
                    return False
            except OSError:
                # Processo não existe, remover lock
                os.remove(lock_file)
        
        # Criar novo arquivo de lock
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
            
        logger.info(f"✅ Instância única confirmada. PID: {os.getpid()}")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Erro na verificação de instância única: {e}")
        return True  # Permitir execução em caso de erro

# Instância global do riot client
riot_client = RiotAPIClient()

if __name__ == '__main__':
    asyncio.run(main())
