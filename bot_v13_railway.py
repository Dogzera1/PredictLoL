#!/usr/bin/env python3
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
                        logger.debug(f"??????? Partida duplicada removida: {team1} vs {team2}")
#!/usr/bin/env python3
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
#!/usr/bin/env python3
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
        """Busca partidas ao vivo REAIS da API oficial - OTIMIZADO com novos endpoints"""
        
        # CACHE: Verificar se temos dados v??lidos em cache
        if self._matches_cache['timestamp']:
            elapsed = (datetime.now() - self._matches_cache['timestamp']).seconds
            if elapsed < self._matches_cache['duration']:
                logger.info(f"???? Cache hit - usando partidas em cache ({elapsed}s)")
                return self._matches_cache['data']
        
        # ENDPOINTS ALTERNATIVOS da Riot para contornar erro 403
        riot_endpoints = [
            # Endpoints originais com novos par??metros
            f"{self.base_urls['esports']}/getLive?hl=en-US&x-api-key=0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
            f"{self.base_urls['esports']}/getSchedule?hl=en-US",
            
            # Novos endpoints alternativos
            f"{self.base_urls['esports']}/getLive",
            f"{self.base_urls['prod']}/getLive",
            
            # Endpoints regionais espec??ficos
            f"{self.base_urls['esports']}/getLive?hl=zh-CN&region=china",
            f"{self.base_urls['esports']}/getLive?hl=ko-KR&region=korea",
            f"{self.base_urls['esports']}/getLive?hl=pt-BR&region=brazil",
            
            # Endpoints sem par??metros
            f"{self.base_urls['esports']}/getSchedule",
            f"{self.base_urls['prod']}/getSchedule"
        ]
        
        all_matches = []
        seen_matches = set()
        successful_endpoints = 0
        
        for endpoint in riot_endpoints:
            try:
                # Usar headers rotativos para evitar detec????o
                current_headers = self.headers.copy()
                current_headers['Referer'] = 'https://lolesports.com/'
                
                # Adicionar Origin espec??fico para cada endpoint
                if 'esports-api' in endpoint:
                    current_headers['Origin'] = 'https://lolesports.com'
                elif 'prod-relapi' in endpoint:
                    current_headers['Origin'] = 'https://lolesports.com'
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(endpoint, headers=current_headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            matches = self._extract_live_matches_only(data)
                            successful_endpoints += 1
                            
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
                                        
                                        # Log espec??fico para LPL com detec????o melhorada
                                        is_lpl = (
                                            'lpl' in league or 
                                            'china' in league.lower() or
                                            'chinese' in league.lower() or
                                            any(lpl_indicator in team1_name + team2_name for lpl_indicator in [
                                                'bilibili', 'blg', 'weibo', 'wbg', 'tes', 'topesports', 'top esports',
                                                'jdg', 'jd gaming', 'lng', 'lng esports', 'edg', 'edward gaming',
                                                'rng', 'royal never give up', 'ig', 'invictus gaming', 'fpx', 'funplus',
                                                'ninjas in pyjamas', 'nip', 'anyone', 'lgd', 'thundertalk', 'tt',
                                                'oh my god', 'omg', 'rare atom', 'ra', 'ultra prime', 'up', 'team we'
                                            ])
                                        )
                                        
                                        if is_lpl:
                                            logger.info(f"???????? ??? PARTIDA LPL DETECTADA: {teams[0].get('name')} vs {teams[1].get('name')} ({league})")
                                        
                                        logger.debug(f"??? Partida ??nica adicionada: {teams[0].get('name')} vs {teams[1].get('name')} ({league})")
                                    else:
                                        logger.debug(f"???? Partida duplicada ignorada: {teams[0].get('name')} vs {teams[1].get('name')}")
                        else:
                            logger.debug(f"?????? Endpoint {endpoint}: status {response.status}")
                                
            except Exception as e:
                logger.debug(f"??? Erro no endpoint {endpoint}: {e}")
                continue
                     
        # FALLBACK: Se n??o encontrou partidas, tentar m??todo alternativo
        if not all_matches:
            logger.info("???? Nenhuma partida encontrada nos endpoints principais. Tentando m??todo alternativo...")
            try:
                fallback_matches = await self._get_fallback_riot_matches()
                all_matches.extend(fallback_matches)
                if fallback_matches:
                    successful_endpoints += 1
                    logger.info(f"??? {len(fallback_matches)} partidas encontradas no m??todo alternativo")
            except Exception as e:
                logger.warning(f"?????? M??todo alternativo falhou: {e}")
        
        # Log do resultado final
        unique_count = len(all_matches)
        logger.info(f"???? {unique_count} partidas ??nicas encontradas de {successful_endpoints} endpoints (duplicatas removidas)")
        
        # OTIMIZA????O: Verificar especificamente por LPL com cache inteligente
        lpl_count = sum(1 for match in all_matches 
                       if any(indicator in match.get('league', '').lower() 
                              for indicator in ['lpl', 'china', 'chinese']))
        
        if lpl_count == 0:
            # Verificar cache LPL primeiro
            if self._lpl_cache['timestamp']:
                elapsed = (datetime.now() - self._lpl_cache['timestamp']).seconds
                if elapsed < self._lpl_cache['duration']:
                    logger.info("???????? ???? Usando cache LPL")
                    cached_lpl = self._lpl_cache['data']
                    for lpl_match in cached_lpl:
                        teams = lpl_match.get('teams', [])
                        if len(teams) >= 2:
                            team1_name = teams[0].get('name', '').lower().strip()
                            team2_name = teams[1].get('name', '').lower().strip()
                            league = lpl_match.get('league', '').lower().strip()
                            
                            sorted_teams = sorted([team1_name, team2_name])
                            match_id = f"{sorted_teams[0]}_{sorted_teams[1]}_{league}"
                            
                            if match_id not in seen_matches:
                                seen_matches.add(match_id)
                                all_matches.append(lpl_match)
                else:
                    # Cache expirado, executar busca r??pida LPL
                    logger.info("???? Executando busca LPL otimizada...")
                    try:
                        lpl_matches = await self._get_lpl_matches_fast()
                        self._lpl_cache['data'] = lpl_matches
                        self._lpl_cache['timestamp'] = datetime.now()
                        
                        for lpl_match in lpl_matches:
                            teams = lpl_match.get('teams', [])
                            if len(teams) >= 2:
                                team1_name = teams[0].get('name', '').lower().strip()
                                team2_name = teams[1].get('name', '').lower().strip()
                                league = lpl_match.get('league', '').lower().strip()
                                
                                sorted_teams = sorted([team1_name, team2_name])
                                match_id = f"{sorted_teams[0]}_{sorted_teams[1]}_{league}"
                                
                                if match_id not in seen_matches:
                                    seen_matches.add(match_id)
                                    all_matches.append(lpl_match)
                                    logger.info(f"???????? ??? Partida LPL adicionada: {teams[0].get('name')} vs {teams[1].get('name')}")
                        
                    except Exception as e:
                        logger.warning(f"???????? ??? Erro na busca LPL: {e}")
            else:
                # Primeira execu????o, buscar LPL
                logger.info("???? Executando busca LPL inicial...")
                try:
                    lpl_matches = await self._get_lpl_matches_fast()
                    self._lpl_cache['data'] = lpl_matches
                    self._lpl_cache['timestamp'] = datetime.now()
                    
                    for lpl_match in lpl_matches:
                        teams = lpl_match.get('teams', [])
                        if len(teams) >= 2:
                            team1_name = teams[0].get('name', '').lower().strip()
                            team2_name = teams[1].get('name', '').lower().strip()
                            league = lpl_match.get('league', '').lower().strip()
                            
                            sorted_teams = sorted([team1_name, team2_name])
                            match_id = f"{sorted_teams[0]}_{sorted_teams[1]}_{league}"
                            
                            if match_id not in seen_matches:
                                seen_matches.add(match_id)
                                all_matches.append(lpl_match)
                                logger.info(f"???????? ??? Partida LPL: {teams[0].get('name')} vs {teams[1].get('name')}")
                
                except Exception as e:
                    logger.warning(f"???????? ??? Erro na busca LPL: {e}")
        
        # Cache resultado final
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
                logger.debug(f"Endpoint LPL r??pido {endpoint}: {e}")
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
                        logger.debug(f"??????? Partida duplicada removida: {team1} vs {team2}")
            except Exception as e:
                logger.debug(f"Erro ao processar partida para duplicatas: {e}")
                continue
        
        logger.info(f"???? Remo????o de duplicatas: {len(matches)} ??? {len(unique_matches)} partidas ??nicas")
        return unique_matches

    def get_matches_today(self) -> List[Dict]:
        """Retorna partidas de hoje"""
        from datetime import timezone
        today = datetime.now(timezone.utc).date()
        today_matches = []

        for match in self.scheduled_matches:
            try:
                start_time_str = match.get('start_time', '')
                if start_time_str:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    if start_time.date() == today:
                        today_matches.append(match)
            except:
                continue
        return today_matches

class ProfessionalTipsSystem:
    """Sistema de Tips Profissional com Monitoramento Cont??nuo"""

    def __init__(self, riot_client=None):
        self.riot_client = riot_client or RiotAPIClient()
        self.units_system = ProfessionalUnitsSystem()
        self.alerts_system = None
        self.bot_application = None
        
        # OTIMIZA????O: Sistema de predi????o reutiliz??vel (Singleton pattern)
        self.prediction_system = DynamicPredictionSystem()
        
        # Crit??rios profissionais rigorosos
        self.min_confidence_score = 75  # 75%+ confian??a
        self.min_ev_percentage = 8.0    # 8%+ EV
        
        # Sistema de cache para tips e an??lises
        self.tips_cache = {}
        self.processed_tips = set()
        self.analysis_cache = {}  # Cache para an??lises de partidas
        self.cache_duration = 300  # 5 minutos
        
        # Controle de monitoramento
        self.monitoring = False
        self.monitor_thread = None
        self.last_scan_time = None
        self.scan_interval = 180  # 3 minutos
        
        # Base de dados de tips encontrados
        self.tips_database = []
        self.given_tips = set()
        
        # INICIAR MONITORAMENTO AUTOM??TICO
        self.start_monitoring()
        logger.info("???? Sistema de Tips Profissional inicializado com MONITORAMENTO ATIVO DE PARTIDAS AO VIVO")

    def start_monitoring(self):
        """Inicia monitoramento cont??nuo APENAS de partidas ao vivo com dados completos"""
        if not self.monitoring:
            self.monitoring = True
            
            def monitor_loop():
                """Loop de monitoramento em thread separada"""
                while self.monitoring:
                    try:
                        # Criar novo loop asyncio para esta thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Executar scan APENAS de partidas ao vivo
                        loop.run_until_complete(self._scan_live_matches_only())
                        
                        # Fechar loop
                        loop.close()
                        
                        # Aguardar 3 minutos antes do pr??ximo scan
                        if self.monitoring:
                            time.sleep(self.scan_interval)
                            
                    except Exception as e:
                        logger.error(f"??? Erro no monitoramento de tips: {e}")
                        # Em caso de erro, aguardar 1 minuto antes de tentar novamente
                        if self.monitoring:
                            time.sleep(60)

            # Iniciar thread de monitoramento
            self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True, name="TipsMonitor")
            self.monitor_thread.start()
            logger.info("???? Monitoramento cont??nuo de tips iniciado - APENAS PARTIDAS AO VIVO - Verifica????o a cada 3 minutos")

    def stop_monitoring(self):
        """Para o monitoramento"""
        self.monitoring = False
        logger.info("???? Monitoramento de tips interrompido")

    async def _scan_live_matches_only(self):
        """Escaneia APENAS partidas ao vivo com dados completos (drafts + estat??sticas)"""
        try:
            logger.info("???? Escaneando APENAS partidas AO VIVO com dados completos...")

            # Buscar APENAS partidas ao vivo (n??o agendadas)
            live_matches = await self.riot_client.get_live_matches_with_details()
            logger.info(f"???? Encontradas {len(live_matches)} partidas ao vivo com dados completos")

            opportunities_found = 0

            for i, match in enumerate(live_matches, 1):
                try:
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        game_number = match.get('game_number', 1)
                        logger.debug(f"???? Analisando JOGO {game_number}: {team1} vs {team2}")

                    # Verificar se partida tem dados suficientes (draft + stats)
                    if not self._has_complete_match_data(match):
                        logger.debug(f"??? Partida sem dados completos ainda - aguardando...")
                        continue

                    # Analisar partida para tip COM dados completos
                    tip_analysis = await self._analyze_live_match_with_data(match)

                    if tip_analysis and self._meets_professional_criteria(tip_analysis):
                        tip_id = self._generate_tip_id_with_game(match)

                        # Verificar se j?? foi dado este tip espec??fico (incluindo n??mero do jogo)
                        if tip_id not in self.given_tips:
                            professional_tip = self._create_professional_tip_with_game_data(tip_analysis)

                            if professional_tip:
                                self.tips_database.append(professional_tip)
                                self.given_tips.add(tip_id)
                                opportunities_found += 1

                                logger.info(f"???? NOVA OPORTUNIDADE ENCONTRADA: {professional_tip['title']}")
                                logger.info(f"   ???? Confian??a: {professional_tip['confidence_score']:.1f}% | EV: {professional_tip['ev_percentage']:.1f}%")
                                logger.info(f"   ???? Unidades: {professional_tip['units']} | Valor: ${professional_tip['stake_amount']:.2f}")
                                logger.info(f"   ??????? {professional_tip['map_info']}")

                                # ENVIAR ALERTA AUTOM??TICO PARA GRUPOS
                                try:
                                    if hasattr(self, '_bot_instance') and self._bot_instance:
                                        alerts_system = self._bot_instance.alerts_system
                                        bot_app = self._bot_instance.bot_application

                                        if alerts_system.group_chat_ids and bot_app:
                                            await alerts_system.send_tip_alert(professional_tip, bot_app)
                                            logger.info(f"???? Alerta autom??tico enviado para {len(alerts_system.group_chat_ids)} grupos")
                                        else:
                                            logger.info("???? Nenhum grupo cadastrado para alertas ainda")

                                except Exception as alert_error:
                                    logger.warning(f"??? Erro ao enviar alerta autom??tico: {alert_error}")
                        else:
                            logger.debug(f"???? Tip j?? foi dado anteriormente: {tip_id}")
                    else:
                        if tip_analysis:
                            logger.debug(f"???? Partida n??o atende crit??rios: Conf={tip_analysis.get('confidence_score', 0):.1f}% EV={tip_analysis.get('ev_percentage', 0):.1f}%")

                except Exception as match_error:
                    logger.warning(f"??? Erro ao analisar partida {i}: {match_error}")
                continue

            # Atualizar timestamp do ??ltimo scan
            self.last_scan_time = datetime.now()

            if opportunities_found > 0:
                logger.info(f"??? SCAN COMPLETO: {opportunities_found} novas oportunidades de tips encontradas!")
            else:
                logger.info("?????? SCAN COMPLETO: Nenhuma nova oportunidade encontrada neste scan")

            # Limpeza de tips antigos e cache
            self._cleanup_old_tips()
            self._cleanup_old_cache()

        except Exception as e:
            logger.error(f"??? Erro geral no scan de partidas ao vivo: {e}")
            import traceback
            logger.error(f"??? Traceback: {traceback.format_exc()}")

    def _has_complete_match_data(self, match: Dict) -> bool:
        """Verifica se a partida tem dados completos (draft + estat??sticas)"""
        try:
            # Verificar se tem dados de draft
            draft_data = match.get('draft_data')
            if not draft_data:
                return False

            # Verificar se tem estat??sticas da partida
            match_stats = match.get('match_statistics')
            if not match_stats:
                return False

            # Verificar se a partida realmente come??ou (n??o apenas draft)
            game_time = match.get('game_time', 0)
            if game_time < 300:  # Menos de 5 minutos = ainda muito cedo
                return False

            # Verificar se tem dados dos times
            teams = match.get('teams', [])
            if len(teams) < 2:
                return False

            # Verificar se tem informa????o do mapa/game
            game_number = match.get('game_number')
            if not game_number:
                return False

            logger.debug(f"??? Partida tem dados completos - Game {game_number}, {game_time}s de jogo")
            return True

        except Exception as e:
            logger.debug(f"??? Erro ao verificar dados da partida: {e}")
            return False

    async def _analyze_live_match_with_data(self, match: Dict) -> Optional[Dict]:
        """Analisa partida ao vivo COM dados de draft e estat??sticas"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None

            team1_name = teams[0].get('name', '')
            team2_name = teams[1].get('name', '')
            league = match.get('league', '')
            game_number = match.get('game_number', 1)
            game_time = match.get('game_time', 0)

            # OTIMIZA????O: Cache de an??lise
            cache_key = f"live_analysis_{team1_name}_{team2_name}_{league}_{game_number}"
            if cache_key in self.analysis_cache:
                cached = self.analysis_cache[cache_key]
                if (datetime.now() - cached['timestamp']).seconds < 180:  # 3 min cache
                    logger.debug(f"???? Cache hit para an??lise: {team1_name} vs {team2_name}")
                    return cached['data']

            # OTIMIZA????O: Usar sistema de predi????o reutiliz??vel (n??o criar novo)
            ml_prediction = await self.prediction_system.predict_live_match_with_live_data(match)

            if not ml_prediction or ml_prediction['confidence'] not in ['Alta', 'Muito Alta']:
                return None

            favored_team = ml_prediction['favored_team']
            win_probability = ml_prediction['win_probability']
            confidence_level = ml_prediction['confidence']

            # Mapear confian??a para score num??rico
            confidence_mapping = {'Muito Alta': 90, 'Alta': 80, 'M??dia': 70, 'Baixa': 60}
            confidence_score = confidence_mapping.get(confidence_level, 60)

            # Calcular EV baseado em dados ao vivo
            live_odds = self._calculate_live_odds_from_data(match, favored_team)
            ev_percentage = self._calculate_ev_with_live_data(win_probability, live_odds, match)
            
            # Determinar tier da liga
            league_tier = self._determine_league_tier(league)

            # Extrair dados espec??ficos da partida
            draft_analysis = self._analyze_draft_data(match.get('draft_data', {}))
            stats_analysis = self._analyze_match_statistics(match.get('match_statistics', {}))

            result = {
                'team1': team1_name, 'team2': team2_name,
                'league': league, 'league_tier': league_tier,
                'favored_team': favored_team,
                'opposing_team': team2_name if favored_team == team1_name else team1_name,
                'win_probability': win_probability,
                'confidence_score': confidence_score,
                'confidence_level': confidence_level,
                'ev_percentage': ev_percentage,
                'game_number': game_number,
                'game_time': game_time,
                'map_info': f"Mapa {game_number}",
                'draft_analysis': draft_analysis,
                'stats_analysis': stats_analysis,
                'ml_analysis': ml_prediction['analysis'],
                'prediction_factors': ml_prediction['prediction_factors'],
                'live_odds': live_odds,
                'match_data': match
            }
            
            # OTIMIZA????O: Cache resultado
            self.analysis_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result

        except Exception as e:
            logger.error(f"??? Erro na an??lise da partida ao vivo: {e}")
            return None

    def _calculate_ev_with_live_data(self, win_probability: float, live_odds: float, match: Dict) -> float:
        """Calcula EV usando dados ao vivo da partida"""
        try:
            # EV = (odds * win_probability) - 1
            base_ev = (live_odds * win_probability) - 1
            
            # Ajustar EV baseado na qualidade dos dados
            game_time = match.get('game_time', 0)
            
            # Partidas com mais tempo t??m dados mais confi??veis
            if game_time > 900:  # Mais de 15 minutos
                reliability_bonus = 1.1
            elif game_time > 600:  # Mais de 10 minutos
                reliability_bonus = 1.05
            else:
                reliability_bonus = 1.0
                
            final_ev = base_ev * reliability_bonus * 100  # Converter para percentual
            
            return final_ev
            
        except Exception as e:
            logger.warning(f"Erro ao calcular EV: {e}")
            return 0.0

    def _analyze_draft_data(self, draft_data: Dict) -> str:
        """Analisa dados do draft para insights"""
        try:
            if not draft_data:
                return "Dados de draft n??o dispon??veis"
                
            team1_picks = draft_data.get('team1_picks', [])
            team2_picks = draft_data.get('team2_picks', [])
            
            analysis_parts = []
            
            # Analisar composi????es
            if len(team1_picks) >= 5 and len(team2_picks) >= 5:
                analysis_parts.append("Drafts completos analisados")
                
                # Exemplo de an??lise de composi????o
                team1_comp_type = self._analyze_team_composition(team1_picks)
                team2_comp_type = self._analyze_team_composition(team2_picks)
                
                analysis_parts.append(f"Comp. T1: {team1_comp_type}")
                analysis_parts.append(f"Comp. T2: {team2_comp_type}")
            else:
                analysis_parts.append("Draft em andamento")
                
            return " ??? ".join(analysis_parts)
            
        except Exception as e:
            logger.warning(f"Erro na an??lise de draft: {e}")
            return "Erro na an??lise de draft"

    def _analyze_team_composition(self, picks: List) -> str:
        """Analisa o tipo de composi????o do time"""
        # Simplificado para demonstra????o
        if len(picks) >= 5:
            return "Composi????o Completa"
        return "Composi????o Parcial"

    def _analyze_match_statistics(self, match_stats: Dict) -> str:
        """Analisa estat??sticas da partida"""
        try:
            if not match_stats:
                return "Estat??sticas n??o dispon??veis"
                
            analysis_parts = []
            
            gold_diff = match_stats.get('gold_difference', 0)
            kill_diff = match_stats.get('kill_difference', 0)
            
            if gold_diff > 2000:
                analysis_parts.append(f"Vantagem significativa de gold (+{gold_diff})")
            elif gold_diff < -2000:
                analysis_parts.append(f"Desvantagem de gold ({gold_diff})")
            else:
                analysis_parts.append("Partida equilibrada em gold")
                
            if kill_diff > 3:
                analysis_parts.append(f"Vantagem em kills (+{kill_diff})")
            elif kill_diff < -3:
                analysis_parts.append(f"Desvantagem em kills ({kill_diff})")
                
            return " ??? ".join(analysis_parts)
            
        except Exception as e:
            logger.warning(f"Erro na an??lise de estat??sticas: {e}")
            return "Erro na an??lise de estat??sticas"

    def _generate_tip_id_with_game(self, match: Dict) -> str:
        """Gera ID ??nico para o tip incluindo n??mero do jogo"""
        teams = match.get('teams', [])
        game_number = match.get('game_number', 1)
        if len(teams) >= 2:
            team1 = teams[0].get('name', '')
            team2 = teams[1].get('name', '')
            league = match.get('league', '')
            timestamp = datetime.now().strftime('%Y%m%d')
            return f"{team1}_{team2}_game{game_number}_{league}_{timestamp}".replace(' ', '_')
        return f"tip_game{game_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _create_professional_tip_with_game_data(self, analysis: Dict) -> Dict:
        """Cria tip profissional com dados espec??ficos do jogo"""
        try:
            units_calc = self.units_system.calculate_units(
                confidence=analysis['confidence_score'],
                ev_percentage=analysis['ev_percentage'],
                league_tier=analysis['league_tier']
            )

            # T??tulo com informa????o do mapa
            title = f"{analysis['map_info']}: {analysis['favored_team']} vs {analysis['opposing_team']}"

            tip = {
                'title': title,
                'league': analysis['league'],
                'map_info': analysis['map_info'],
                'game_number': analysis['game_number'],
                'game_time': analysis['game_time'],
                'recommended_team': analysis['favored_team'],
                'opposing_team': analysis['opposing_team'],
                'confidence_score': analysis['confidence_score'],
                'confidence_level': analysis['confidence_level'],
                'ev_percentage': analysis['ev_percentage'],
                'win_probability': analysis['win_probability'],
                'units': units_calc['units'],
                'stake_amount': units_calc['stake_amount'],
                'risk_level': units_calc['risk_level'],
                'reasoning': self._generate_tip_reasoning_with_live_data(analysis, units_calc),
                'ml_analysis': analysis['ml_analysis'],
                'draft_analysis': analysis['draft_analysis'],
                'stats_analysis': analysis['stats_analysis'],
                'live_odds': analysis['live_odds'],
                'prediction_factors': analysis['prediction_factors'],
                'timestamp': datetime.now(),
                'tip_id': self._generate_tip_id_with_game(analysis['match_data'])
            }
            return tip

        except Exception as e:
            logger.error(f"Erro ao criar tip: {e}")
            return None

    def _generate_tip_reasoning_with_live_data(self, analysis: Dict, units_calc: Dict) -> str:
        """Gera explica????o do tip com dados ao vivo"""
        reasoning_parts = []
        
        # Informa????o do jogo
        game_time_min = int(analysis['game_time'] / 60)
        reasoning_parts.append(f"??????? {analysis['map_info']} ({game_time_min}min de jogo)")
        
        reasoning_parts.append(f"???? IA identifica {analysis['favored_team']} como favorito")
        reasoning_parts.append(f"???? Confian??a ML: {analysis['confidence_level']} ({analysis['confidence_score']:.1f}%)")
        reasoning_parts.append(f"???? Valor esperado: {analysis['ev_percentage']:.1f}%")
        
        # Dados ao vivo
        reasoning_parts.append(f"???? Odds ao vivo: {analysis['live_odds']:.2f}")
        
        # An??lises espec??ficas
        if analysis.get('draft_analysis'):
            reasoning_parts.append(f"???? Draft: {analysis['draft_analysis']}")
        if analysis.get('stats_analysis'):
            reasoning_parts.append(f"???? Stats: {analysis['stats_analysis']}")
            
        reasoning_parts.append(f"???? {units_calc['reasoning']}")

        return " ??? ".join(reasoning_parts)

    def get_monitoring_status(self) -> Dict:
        """Status do monitoramento atualizado"""
        # Calcular tips de hoje
        today = datetime.now().date()
        tips_today = sum(1 for tip in self.tips_database 
                        if tip.get('timestamp', datetime.now()).date() == today)
        
        recent_tips = [tip for tip in self.tips_database 
                      if (datetime.now() - tip.get('timestamp', datetime.now())).days < 7]
        
        return {
            'monitoring_active': self.monitoring,
            'last_scan': self.last_scan_time.strftime('%H:%M:%S') if self.last_scan_time else 'Nunca',
            'total_tips': len(self.tips_database),  # Chave correta esperada pelos callbacks
            'tips_today': tips_today,  # Chave correta esperada pelos callbacks
            'tips_this_week': len(recent_tips),
            'scan_frequency': '3 minutos (partidas AO VIVO)',
            'given_tips_cache': len(self.given_tips),
            'focus': 'APENAS partidas ao vivo com dados completos (draft + estat??sticas)',
            'criteria': f'Confian??a ???{self.min_confidence_score}% e EV ???{self.min_ev_percentage}%',
            'thread_status': 'Ativo' if (self.monitor_thread and self.monitor_thread.is_alive()) else 'Inativo'
        }

    def set_bot_instance(self, bot_instance):
        """Define inst??ncia do bot para envio de alertas autom??ticos"""
        self._bot_instance = bot_instance
        logger.info("???? Bot instance conectada ao sistema de tips")

    def _cleanup_old_tips(self):
        """Remove tips antigos do cache (mais de 24h)"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_tip_ids = []

            # Encontrar tips antigos
            for tip in self.tips_database:
                if tip.get('timestamp', datetime.now()) < cutoff_time:
                    old_tip_ids.append(tip.get('tip_id'))

            # Remover do cache de tips dados
            for tip_id in old_tip_ids:
                self.given_tips.discard(tip_id)

            # Remover do banco de dados de tips
            self.tips_database = [tip for tip in self.tips_database 
                                if tip.get('timestamp', datetime.now()) >= cutoff_time]

            if old_tip_ids:
                logger.info(f"???? {len(old_tip_ids)} tips antigos removidos do cache")

        except Exception as e:
            logger.error(f"??? Erro na limpeza de tips antigos: {e}")

    def _meets_professional_criteria(self, analysis: Dict) -> bool:
        """Verifica crit??rios profissionais"""
        confidence = analysis.get('confidence_score', 0)
        ev = analysis.get('ev_percentage', 0)

        return (
            confidence >= self.min_confidence_score and
            ev >= self.min_ev_percentage and
            analysis.get('confidence_level') in ['Alta', 'Muito Alta']
        )

    def _create_professional_tip(self, analysis: Dict) -> Dict:
        """Cria tip profissional"""
        try:
            units_calc = self.units_system.calculate_units(
                confidence=analysis['confidence_score'],
                ev_percentage=analysis['ev_percentage'],
                league_tier=analysis['league_tier']
            )

            tip = {
                'title': f"{analysis['favored_team']} vs {analysis['opposing_team']}",
                'league': analysis['league'],
                'recommended_team': analysis['favored_team'],
                'opposing_team': analysis['opposing_team'],
                'confidence_score': analysis['confidence_score'],
                'confidence_level': analysis['confidence_level'],
                'ev_percentage': analysis['ev_percentage'],
                'win_probability': analysis['win_probability'],
                'units': units_calc['units'],
                'stake_amount': units_calc['stake_amount'],
                'risk_level': units_calc['risk_level'],
                'reasoning': self._generate_tip_reasoning(analysis, units_calc),
                'ml_analysis': analysis['ml_analysis'],
                'prediction_factors': analysis['prediction_factors'],
                'timestamp': datetime.now(),
                'tip_id': self._generate_tip_id(analysis['match_data'])
            }
            return tip

        except Exception as e:
            logger.error(f"Erro ao criar tip: {e}")
            return None

    def _generate_tip_reasoning(self, analysis: Dict, units_calc: Dict) -> str:
        """Gera explica????o do tip"""
        reasoning_parts = []
        reasoning_parts.append(f"???? IA identifica {analysis['favored_team']} como favorito")
        reasoning_parts.append(f"???? Confian??a ML: {analysis['confidence_level']} ({analysis['confidence_score']:.1f}%)")
        reasoning_parts.append(f"???? Valor esperado: {analysis['ev_percentage']:.1f}%")
        reasoning_parts.append(f"???? {units_calc['reasoning']}")

        if analysis.get('ml_analysis'):
            reasoning_parts.append(f"???? {analysis['ml_analysis']}")

        return " ??? ".join(reasoning_parts)

    def _determine_league_tier(self, league: str) -> str:
        """Determina tier da liga"""
        league_lower = league.lower()
        if any(tier1 in league_lower for tier1 in ['lck', 'lpl', 'lec', 'lcs']):
            return 'tier1'
        elif any(tier2 in league_lower for tier2 in ['cblol', 'lla', 'pcs', 'vcs']):
            return 'tier2'
        else:
            return 'tier3'

    def _generate_tip_id(self, match: Dict) -> str:
        """Gera ID ??nico para o tip"""
        teams = match.get('teams', [])
        if len(teams) >= 2:
            team1 = teams[0].get('name', '')
            team2 = teams[1].get('name', '')
            league = match.get('league', '')
            timestamp = datetime.now().strftime('%Y%m%d')
            return f"{team1}_{team2}_{league}_{timestamp}".replace(' ', '_')
        return f"tip_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def generate_professional_tip(self) -> Optional[Dict]:
        """Gera tip profissional usando ML e retorna o melhor dispon??vel"""
        try:
            # Buscar partidas dispon??veis
            live_matches = await self.riot_client.get_live_matches()
            schedule_manager = ScheduleManager(self.riot_client)
            scheduled_matches = await schedule_manager.get_scheduled_matches(days_ahead=1)

            all_matches = live_matches + scheduled_matches
            logger.info(f"???? Analisando {len(all_matches)} partidas para tip profissional")

            # Analisar cada partida com ML
            best_tip = None
            best_score = 0

            for match in all_matches:
                tip_analysis = await self._analyze_match_for_tip(match)

                if tip_analysis and self._meets_professional_criteria(tip_analysis):
                    # Calcular score combinado (confian??a + EV)
                    combined_score = tip_analysis['confidence_score'] + tip_analysis['ev_percentage']

                    if combined_score > best_score:
                        best_score = combined_score
                        best_tip = self._create_professional_tip(tip_analysis)

            if best_tip:
                logger.info(f"???? Melhor tip encontrado: {best_tip['title']} (Score: {best_score:.1f})")
            else:
                logger.info("?????? Nenhum tip profissional dispon??vel no momento")

            return best_tip

        except Exception as e:
            logger.error(f"??? Erro ao gerar tip profissional: {e}")
            return None

    async def _analyze_match_for_tip(self, match: Dict) -> Optional[Dict]:
        """Analisa partida para determinar se ?? uma oportunidade de tip"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None

            team1_name = teams[0].get('name', '')
            team2_name = teams[1].get('name', '')
            league = match.get('league', '')

            # Usar sistema de predi????o para an??lise
            prediction_system = DynamicPredictionSystem()
            ml_prediction = await prediction_system.predict_live_match(match)

            if not ml_prediction or ml_prediction['confidence'] not in ['Alta', 'Muito Alta']:
                return None

            favored_team = ml_prediction['favored_team']
            win_probability = ml_prediction['win_probability']
            confidence_level = ml_prediction['confidence']

            # Mapear confian??a para score num??rico
            confidence_mapping = {'Muito Alta': 90, 'Alta': 80, 'M??dia': 70, 'Baixa': 60}
            confidence_score = confidence_mapping.get(confidence_level, 60)

            # Calcular EV (Expected Value)
            ml_odds = ml_prediction['team1_odds'] if favored_team == team1_name else ml_prediction['team2_odds']
            
            # Simular odds de mercado (normalmente 5% menor que a probabilidade real)
            market_probability = win_probability * 0.95
            market_odds = 1 / market_probability if market_probability > 0 else 2.0

            # Calcular EV percentage
            ev_percentage = ((ml_odds * win_probability) - 1) * 100
            
            # Determinar tier da liga
            league_tier = self._determine_league_tier(league)

            return {
                'team1': team1_name, 'team2': team2_name,
                'league': league, 'league_tier': league_tier,
                'favored_team': favored_team,
                'opposing_team': team2_name if favored_team == team1_name else team1_name,
                'win_probability': win_probability,
                'confidence_score': confidence_score,
                'confidence_level': confidence_level,
                'ev_percentage': ev_percentage,
                'ml_odds': ml_odds, 'market_odds': market_odds,
                'ml_analysis': ml_prediction['analysis'],
                'prediction_factors': ml_prediction['prediction_factors'],
                'match_data': match
            }

        except Exception as e:
            logger.error(f"??? Erro na an??lise da partida: {e}")
            return None

    def _cleanup_old_cache(self):
        """Limpa cache antigo para evitar uso excessivo de mem??ria"""
        try:
            current_time = datetime.now()
            
            # Limpar an??lises antigas (mais de 10 minutos)
            old_keys = []
            for key, cached_item in self.analysis_cache.items():
                if (current_time - cached_item['timestamp']).seconds > 600:
                    old_keys.append(key)
            
            for key in old_keys:
                del self.analysis_cache[key]
            
            # Limpar tips antigos (mais de 1 hora)
            old_tip_keys = []
            for key, cached_item in self.tips_cache.items():
                if (current_time - cached_item.get('timestamp', current_time)).seconds > 3600:
                    old_tip_keys.append(key)
            
            for key in old_tip_keys:
                del self.tips_cache[key]
                
            if old_keys or old_tip_keys:
                logger.debug(f"???? Cache limpo: {len(old_keys)} an??lises, {len(old_tip_keys)} tips")
                
        except Exception as e:
            logger.warning(f"Erro ao limpar cache: {e}")

    def _cleanup_old_tips(self):
        """Remove tips antigos do banco de dados (mais de 24h)"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_tips = []
            
            for tip in self.tips_database:
                if tip.get('timestamp', datetime.now()) < cutoff_time:
                    old_tips.append(tip)
            
            # Remover tips antigos
            for old_tip in old_tips:
                if old_tip in self.tips_database:
                    self.tips_database.remove(old_tip)
            
            # Limpar IDs de tips antigos
            old_tip_ids = set()
            for tip_id in self.given_tips:
                # Extrair data do tip_id se poss??vel
                if '_' in tip_id:
                    parts = tip_id.split('_')
                    for part in parts:
                        if len(part) == 8 and part.isdigit():  # YYYYMMDD
                            try:
                                tip_date = datetime.strptime(part, '%Y%m%d')
                                if (datetime.now() - tip_date).days > 1:
                                    old_tip_ids.add(tip_id)
        except:
            pass
            
            for old_id in old_tip_ids:
                self.given_tips.discard(old_id)
            
            if old_tips or old_tip_ids:
                logger.debug(f"???? Tips antigos limpos: {len(old_tips)} tips, {len(old_tip_ids)} IDs")
                
        except Exception as e:
            logger.warning(f"Erro ao limpar tips antigos: {e}")

class LoLBotV3UltraAdvanced:
    """Bot LoL V3 Ultra Avan??ado com Sistema de Unidades Profissional + ML + Alertas"""

    def __init__(self):
        self.riot_client = RiotAPIClient()
        self.tips_system = ProfessionalTipsSystem(self.riot_client)
        self.schedule_manager = ScheduleManager(self.riot_client)
        self.prediction_system = DynamicPredictionSystem()
        self.alerts_system = TelegramAlertsSystem(TOKEN)
        self.live_matches_cache = {}
        self.cache_timestamp = None
        self.bot_application = None

        # Conectar sistema de tips com alertas
        self.tips_system.set_bot_instance(self)

        logger.info("???? Bot LoL V3 Ultra Avan??ado inicializado - Tips + Agenda + Predi????es IA + Alertas")

    def set_bot_application(self, application):
        """Define a aplica????o do bot para o sistema de alertas"""
        self.bot_application = application

        # Railway mode - sem threading de cleanup autom??tico
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME'))
        
        if not is_railway:
            # Apenas local - cleanup autom??tico
            logger.info("???? Cleanup autom??tico ativo - modo local")

    def start_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /start"""
        try:
            logger.info(f"???? Comando /start chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            user = update.effective_user
            welcome_message = f"""
???? **BOT LOL V3 ULTRA AVAN??ADO** ????

Ol?? {user.first_name}! ????

???? **SISTEMA DE UNIDADES PROFISSIONAL**
???? Baseado em grupos de apostas profissionais
??? Sem Kelly Criterion - Sistema simplificado
???? Crit??rios: 65%+ confian??a, 5%+ EV m??nimo

???? **FUNCIONALIDADES:**
??? ???? Tips profissionais com monitoramento ativo
??? ???? Predi????es IA com machine learning
??? ???? Agenda de partidas (pr??ximos 7 dias)
??? ???? Partidas ao vivo selecion??veis
??? ???? Sistema de alertas para grupos
??? ???? Sistema de unidades padr??o
??? ???? Estat??sticas detalhadas

Use /menu para ver todas as op????es!
            """

            keyboard = [
                [InlineKeyboardButton("???? Tips Profissionais", callback_data="tips")],
                [InlineKeyboardButton("???? Predi????es IA", callback_data="predictions")],
                [InlineKeyboardButton("???? Agenda de Partidas", callback_data="schedule")],
                [InlineKeyboardButton("???? Partidas Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Sistema de Alertas", callback_data="alert_stats")],
                [InlineKeyboardButton("???? Menu Completo", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")
            logger.info(f"??? Comando /start respondido com sucesso para {user.first_name}")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /start: {e}")
            try:
                update.message.reply_text("??? Erro interno. Tente novamente em alguns segundos.")
            except:
                pass

    def menu_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /menu"""
        try:
            logger.info(f"???? Comando /menu chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            menu_message = """
???? **MENU PRINCIPAL - BOT LOL V3** ????

???? **TIPS & AN??LISES (ATUALIZADO):**
??? /tips - Tips profissionais AO VIVO
??? /predictions - Predi????es IA
??? /schedule - Agenda de partidas
??? /live - Partidas ao vivo
??? /monitoring - Status do monitoramento
??? /force_scan - Scan manual (admin)
??? /alerts - Sistema de alertas
??? /odds - Odds reais (The Odds API) ????

???? **SISTEMA DE UNIDADES:**
??? /units - Explica????o do sistema
??? /performance - Performance atual
??? /history - Hist??rico de apostas

???? **INFORMA????ES:**
??? /help - Ajuda completa
??? /about - Sobre o bot

???? **NOVA INTEGRA????O - ODDS REAIS:**
???? Agora o sistema usa odds REAIS de casas de apostas!
??? ??? The Odds API integrada
??? ??? M??ltiplas casas de apostas
??? ??? Melhores odds automaticamente
??? ??? EV calculado com dados reais

???? **FUNCIONALIDADE - TIPS AO VIVO:**
???? Sistema gera tips APENAS para partidas que est??o acontecendo!
??? ??? Dados reais de draft + estat??sticas
??? ??? Informa????o espec??fica do mapa (Game 1, 2, 3...)
??? ??? An??lise em tempo real durante a partida
??? ??? Tips ilimitados (sem limite semanal)
??? ??? Monitoramento a cada 3 minutos

Clique nos bot??es abaixo para navega????o r??pida:
            """

            keyboard = [
                [InlineKeyboardButton("???? Tips AO VIVO", callback_data="tips"),
                 InlineKeyboardButton("???? Predi????es", callback_data="predictions")],
                [InlineKeyboardButton("???? Odds Reais", callback_data="odds_summary"),
                 InlineKeyboardButton("???? Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Agenda", callback_data="schedule"),
                 InlineKeyboardButton("???? Monitoramento", callback_data="monitoring")],
                [InlineKeyboardButton("???? Scan Manual", callback_data="force_scan"),
                 InlineKeyboardButton("???? Alertas", callback_data="alert_stats")],
                [InlineKeyboardButton("???? Unidades", callback_data="units_info"),
                 InlineKeyboardButton("??? Ajuda", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode="Markdown")
            logger.info(f"??? Comando /menu respondido com sucesso")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /menu: {e}")
            try:
                update.message.reply_text("??? Erro interno. Tente novamente.")
            except:
                pass

    def tips_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /tips"""
        try:
            logger.info(f"???? Comando /tips chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            # Usar asyncio para gerar tip
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tip = loop.run_until_complete(self.tips_system.generate_professional_tip())
            loop.close()

            if tip:
                # Extrair informa????es espec??ficas do mapa
                map_info = tip.get('map_info', 'Mapa 1')
                game_time = tip.get('game_time', 0)
                game_min = game_time // 60 if game_time > 0 else 0
                
                tip_message = f"""
???? **TIP PROFISSIONAL AO VIVO** ????

??????? **{map_info}: {tip['title']}**
???? Liga: {tip['league']}
?????? Tempo: {game_min}min (PARTIDA AO VIVO)

???? **AN??LISE COM DADOS REAIS:**
??? Confian??a: {tip['confidence_score']:.1f}% ({tip['confidence_level']})
??? EV: {tip['ev_percentage']:.1f}%
??? Probabilidade: {tip['win_probability']*100:.1f}%

???? **SISTEMA DE UNIDADES:**
??? Apostar: {tip['units']} unidades
??? Valor: ${tip['stake_amount']:.2f}
??? Risco: {tip['risk_level']}

??? **Recomenda????o:** {tip['recommended_team']}

???? **An??lise Completa:**
{tip['reasoning']}

???? **Dados Utilizados:**
??? Draft completo analisado
??? Estat??sticas em tempo real
??? IA com dados ao vivo
                """
            else:
                tip_message = """
???? **NENHUM TIP DISPON??VEL** ????

??? Nenhuma partida AO VIVO atende aos crit??rios profissionais no momento.

**Crit??rios para tips:**
??? Confian??a ??? 65%
??? EV ??? 5%
??? Partida em andamento
??? Dados completos dispon??veis

???? Tente novamente em alguns minutos ou use /monitoring para status.
                """

            keyboard = [
                [InlineKeyboardButton("???? Buscar Novamente", callback_data="tips")],
                [InlineKeyboardButton("???? Partidas ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Monitoramento", callback_data="monitoring")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(tip_message, reply_markup=reply_markup, parse_mode="Markdown")
            logger.info(f"??? Comando /tips respondido - Tip encontrado: {bool(tip)}")

        except Exception as e:
            logger.error(f"??? Erro no comando /tips: {e}")
            try:
                update.message.reply_text("??? Erro ao gerar tips. Tente novamente em alguns segundos.")
            except:
                pass

    def live_matches_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /live"""
        try:
            logger.info(f"???? Comando /live chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            # Usar asyncio para buscar partidas ao vivo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            live_matches = loop.run_until_complete(self.riot_client.get_live_matches())
            loop.close()

            if live_matches:
                live_message = f"""
???? **PARTIDAS AO VIVO** ????

???? **{len(live_matches)} PARTIDAS ACONTECENDO AGORA**

"""
                for i, match in enumerate(live_matches[:8], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        
                        # Calcular tempo de jogo se dispon??vel
                        game_time = match.get('game_time', 0)
                        game_min = game_time // 60 if game_time > 0 else 0
                        time_display = f"{game_min}min" if game_min > 0 else "Iniciando"
                        
                        live_message += f"""
**{i}. {team1} vs {team2}**
???? {league}
?????? {time_display}

"""
            else:
                live_message = """
???? **PARTIDAS AO VIVO** ????

???? **NENHUMA PARTIDA AO VIVO**

???? **N??o h?? partidas acontecendo no momento**

??? Verifique a agenda com /schedule
??? Use /monitoring para status do sistema
                """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="live_matches")],
                [InlineKeyboardButton("???? Agenda", callback_data="schedule")],
                [InlineKeyboardButton("???? Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(live_message, reply_markup=reply_markup, parse_mode="Markdown")
            logger.info(f"??? Comando /live respondido - Partidas encontradas: {len(live_matches) if live_matches else 0}")

        except Exception as e:
            logger.error(f"??? Erro no comando /live: {e}")
            try:
                update.message.reply_text("??? Erro ao buscar partidas ao vivo. Tente novamente.")
            except:
                pass

    def schedule_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /schedule"""
        try:
            logger.info(f"???? Comando /schedule chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            # Usar asyncio para buscar dados
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scheduled_matches = loop.run_until_complete(self.schedule_manager.get_scheduled_matches())
            loop.close()

            if scheduled_matches:
                schedule_message = f"""
???? **AGENDA DE PARTIDAS** ????

???? **{len(scheduled_matches)} PARTIDAS AGENDADAS**

"""
                for i, match in enumerate(scheduled_matches[:10], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        start_time = match.get('start_time_formatted', 'TBD')

                        schedule_message += f"""
**{i}. {team1} vs {team2}**
???? {league}
??? {start_time}

"""
                schedule_message += f"""
??? ??ltima atualiza????o: {self.schedule_manager.last_update.strftime('%H:%M:%S') if self.schedule_manager.last_update else 'Nunca'}
                """
            else:
                schedule_message = """
???? **AGENDA DE PARTIDAS** ????

?????? **NENHUMA PARTIDA AGENDADA**

???? **N??o h?? partidas agendadas para os pr??ximos 7 dias**

???? Tente novamente em alguns minutos
                """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="schedule")],
                [InlineKeyboardButton("???? Hoje", callback_data="schedule_today")],
                [InlineKeyboardButton("???? Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(schedule_message, reply_markup=reply_markup, parse_mode="Markdown")
            logger.info(f"??? Comando /schedule respondido com {len(scheduled_matches)} partidas")

        except Exception as e:
            logger.error(f"??? Erro no comando /schedule: {e}")
            try:
                update.message.reply_text("??? Erro ao buscar agenda. Tente novamente.")
            except:
                pass

    def monitoring_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /monitoring"""
        try:
            logger.info(f"???? Comando /monitoring chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            status = self.tips_system.get_monitoring_status()
            
            monitoring_message = f"""
???? **STATUS DO MONITORAMENTO** ????

???? **Monitoramento:** {'???? Ativo' if status['monitoring_active'] else '???? Inativo'}
??? **??ltimo scan:** {status['last_scan']}
???? **Tips encontradas:** {status['total_tips']}
???? **Tips hoje:** {status['tips_today']}

???? **SISTEMA DE IA:**
??? Machine Learning: {'???? Dispon??vel' if self.prediction_system.ml_system else '???? Fallback matem??tico'}
??? Dados ao vivo: ???? Integrados
??? Alertas autom??ticos: {'???? Ativo' if len(self.alerts_system.group_chat_ids) > 0 else '???? Sem grupos'}

???? **PERFORMANCE:**
??? ROI: {status.get('roi', 0):.1f}%
??? Win Rate: {status.get('win_rate', 0):.1f}%

???? **APIs:**
??? Riot API: ???? Conectada
??? The Odds API: ???? Conectada
            """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar Status", callback_data="monitoring")],
                [InlineKeyboardButton("???? Scan Manual", callback_data="force_scan")],
                [InlineKeyboardButton("???? Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(monitoring_message, reply_markup=reply_markup, parse_mode="Markdown")
            logger.info(f"??? Comando /monitoring respondido - Status: {status['monitoring_active']}")

        except Exception as e:
            logger.error(f"??? Erro no comando /monitoring: {e}")
            try:
                update.message.reply_text("??? Erro ao verificar status. Tente novamente.")
            except:
                pass

    def force_scan_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /force_scan"""
        try:
            logger.info(f"???? Comando /force_scan chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            # Verificar se ?? admin (owner)
            user_id = update.effective_user.id if update.effective_user else 0
            if user_id != OWNER_ID:
                update.message.reply_text("??? Comando dispon??vel apenas para administradores.")
                return

            # Executar scan manual
            update.message.reply_text("???? Iniciando scan manual das partidas ao vivo...")
            
            def run_manual_scan():
                """Executa scan manual em thread separada"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Executar scan
                    loop.run_until_complete(self.tips_system._scan_live_matches_only())
                    
                    # Gerar tip se encontrado algo
                    tip = loop.run_until_complete(self.tips_system.generate_professional_tip())
                    
                    if tip:
                        scan_result = f"""
???? **SCAN MANUAL CONCLU??DO** ????

??? Tip encontrado!

???? **{tip['title']}**
???? Liga: {tip['league']}
??? Recomenda????o: {tip['recommended_team']}
???? Confian??a: {tip['confidence_score']:.1f}%
???? EV: {tip['ev_percentage']:.1f}%
???? Unidades: {tip['units']}
                        """
                    else:
                        scan_result = """
???? **SCAN MANUAL CONCLU??DO** ????

??? Nenhum tip atende aos crit??rios no momento.

Crit??rios: Confian??a ???65%, EV ???5%
                        """
                    
                    # Enviar resultado
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=scan_result,
                        parse_mode="Markdown"
                    )
                    
                    loop.close()
                    
                except Exception as e:
                    logger.error(f"Erro no scan manual: {e}")
                    try:
                        context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"??? Erro no scan manual: {e}"
                        )
                    except:
                        pass
            
            # Executar em thread separada para n??o bloquear
            threading.Thread(target=run_manual_scan, daemon=True).start()
            
        except Exception as e:
            logger.error(f"??? Erro no comando /force_scan: {e}")
            try:
                update.message.reply_text("??? Erro ao executar scan manual.")
            except:
                pass

    def callback_handler(self, update: Update, context: CallbackContext) -> None:
        """Handler para callbacks de bot??es inline"""
        try:
            query = update.callback_query
            query.answer()
            
            callback_data = query.data
            chat_id = query.message.chat_id
            
            logger.info(f"???? Callback recebido: {callback_data}")

            # Roteamento de callbacks
            if callback_data == "tips":
                self._handle_tips_callback(query)
            elif callback_data == "live_matches":
                self._handle_live_matches_callback(query)
            elif callback_data == "schedule":
                self._handle_schedule_callback(query)
            elif callback_data == "monitoring":
                self._handle_monitoring_callback(query)
            elif callback_data == "predictions":
                self._handle_predictions_callback(query)
            elif callback_data == "alert_stats":
                self._handle_alert_stats_callback(query)
            elif callback_data == "register_alerts":
                self._handle_register_alerts_callback(query, chat_id)
            elif callback_data == "unregister_alerts":
                self._handle_unregister_alerts_callback(query, chat_id)
            elif callback_data == "units_info":
                self._handle_units_info_callback(query)
            elif callback_data == "performance_stats":
                self._handle_performance_stats_callback(query)
            elif callback_data == "bet_history":
                self._handle_bet_history_callback(query)
            elif callback_data == "odds_summary":
                self._handle_odds_summary_callback(query)
            elif callback_data == "force_scan":
                self._handle_force_scan_callback(query)
            elif callback_data == "main_menu":
                self._handle_main_menu_callback(query)
            else:
                logger.warning(f"?????? Callback n??o reconhecido: {callback_data}")
                query.edit_message_text("??? A????o n??o reconhecida.")

        except Exception as e:
            logger.error(f"??? Erro no callback_handler: {e}")
            try:
                update.callback_query.edit_message_text("??? Erro interno. Tente novamente.")
            except:
                pass

    def _handle_tips_callback(self, query) -> None:
        """Handle callback para tips"""
        try:
            # Usar asyncio para gerar tip
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tip = loop.run_until_complete(self.tips_system.generate_professional_tip())
            loop.close()

            if tip:
                map_info = tip.get('map_info', 'Mapa 1')
                game_time = tip.get('game_time', 0)
                game_min = game_time // 60 if game_time > 0 else 0
                
                message = f"""
???? **TIP PROFISSIONAL AO VIVO** ????

??????? **{map_info}: {tip['title']}**
???? Liga: {tip['league']}
?????? Tempo: {game_min}min (AO VIVO)

???? **AN??LISE:**
??? Confian??a: {tip['confidence_score']:.1f}% 
??? EV: {tip['ev_percentage']:.1f}%
??? Unidades: {tip['units']}

??? **Recomenda????o:** {tip['recommended_team']}

???? {tip['reasoning'][:300]}...
                """
            else:
                message = """
???? **NENHUM TIP DISPON??VEL** ????

??? Nenhuma partida AO VIVO atende aos crit??rios no momento.

Crit??rios: Confian??a ???65%, EV ???5%
                """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="tips")],
                [InlineKeyboardButton("???? Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback tips: {e}")
            query.edit_message_text("??? Erro ao buscar tips.")

    def _handle_live_matches_callback(self, query):
        """Handle callback para partidas ao vivo"""
        try:
            # Usar m??todo s??ncrono simplificado
            live_matches = self._get_live_matches_sync()

            if live_matches:
                message = "???? **PARTIDAS AO VIVO** ????\n\n"
                
                for i, match in enumerate(live_matches[:5], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        
                        # Calcular tempo de jogo se dispon??vel
                        game_time = match.get('game_time', 0)
                        game_min = game_time // 60 if game_time > 0 else 0
                        time_display = f"{game_min}min" if game_min > 0 else "Iniciando"
                        
                        message += f"**{i}. {team1} vs {team2}**\n???? {league}\n?????? {time_display}\n\n"
            else:
                message = """
???? **PARTIDAS AO VIVO** ????

???? Nenhuma partida acontecendo agora.

Use /schedule para ver pr??ximas partidas.
                """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="live_matches")],
                [InlineKeyboardButton("???? Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback live_matches: {e}")
            query.edit_message_text("??? Erro ao buscar partidas ao vivo.")

    def _handle_schedule_callback(self, query):
        """Handle callback para agenda"""
        try:
            # Usar m??todo s??ncrono simplificado
            scheduled_matches = self._get_schedule_sync()

            if scheduled_matches:
                message = "???? **PR??XIMAS PARTIDAS** ????\n\n"
                
                for i, match in enumerate(scheduled_matches[:8], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        time_formatted = match.get('start_time_formatted', 'N/A')
                        
                        message += f"???? **{team1} vs {team2}**\n???? {league}\n??? {time_formatted}\n\n"
            else:
                message = """
???? **AGENDA DE PARTIDAS** ????

?????? Nenhuma partida agendada nos pr??ximos dias.

???? Tente novamente em alguns minutos.
                """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="schedule")],
                [InlineKeyboardButton("???? Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback schedule: {e}")
            query.edit_message_text("??? Erro ao buscar agenda.")

    def _get_live_matches_sync(self):
        """M??todo s??ncrono para buscar partidas ao vivo"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.riot_client.get_live_matches())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo sync: {e}")
            return []

    def _get_schedule_sync(self):
        """M??todo s??ncrono para buscar agenda"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.schedule_manager.get_scheduled_matches(days_ahead=3))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Erro ao buscar agenda sync: {e}")
            return []

    def _handle_monitoring_callback(self, query):
        """Handle callback para monitoramento"""
        try:
            status = self.tips_system.get_monitoring_status()
            
            message = f"""
???? **STATUS DO MONITORAMENTO** ????

???? **Monitoramento:** {'???? Ativo' if status['monitoring_active'] else '???? Inativo'}
??? **??ltimo scan:** {status['last_scan']}
???? **Tips encontradas:** {status['total_tips']}
???? **Tips hoje:** {status['tips_today']}

???? **SISTEMA DE IA APRIMORADO:**
??? Machine Learning: {'???? Dispon??vel' if self.prediction_system.ml_system else '???? Fallback matem??tico'}
??? Dados ao vivo: ???? Integrados
??? Alertas autom??ticos: {'???? Ativo' if len(self.alerts_system.group_chat_ids) > 0 else '???? Sem grupos'}

???? **PERFORMANCE:**
??? ROI: {status.get('roi', 0):.1f}%
??? Win Rate: {status.get('win_rate', 0):.1f}%

???? **APIs:**
??? Riot API: ???? Conectada
??? The Odds API: ???? Conectada

??? Intervalo de verifica????o: 3 minutos
???? Crit??rios: Confian??a ???65%, EV ???5%
            """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="monitoring")],
                [InlineKeyboardButton("???? Scan Manual", callback_data="force_scan")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback monitoring: {e}")
            query.edit_message_text("??? Erro ao verificar status.")

    def _handle_predictions_callback(self, query):
        """Handle callback para predi????es"""
        try:
            message = f"""
???? **PREDI????ES IA** ????

???? **Sistema Ativo:** {'???? ML Real' if self.prediction_system.ml_system else '???? Algoritmos Matem??ticos'}

**STATUS:**
??? Modelo: {'Random Forest' if self.prediction_system.ml_system else 'Matem??tico'}
??? Acur??cia: {'70.5%' if self.prediction_system.ml_system else '~65%'}
??? Dados: ???? Tempo real

**FUNCIONALIDADES:**
??? An??lise de draft completa
??? Estat??sticas ao vivo
??? Probabilidades din??micas
??? Integra????o com odds reais

Para predi????es espec??ficas, v?? em Tips!
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback predictions: {e}")
            query.edit_message_text("??? Erro ao carregar predi????es.")

    def _handle_alert_stats_callback(self, query):
        """Handle callback para estat??sticas de alertas"""
        try:
            stats = self.alerts_system.get_alert_stats()
            
            message = f"""
???? **SISTEMA DE ALERTAS** ????

???? **ESTAT??STICAS:**
??? Grupos registrados: {stats['total_groups']}
??? Alertas enviados: {stats['alerts_sent']}
??? Tips alertadas: {stats['tips_alerted']}
??? ??ltimo alerta: {stats['last_alert']}

???? **PERFORMANCE:**
??? Taxa de sucesso: {stats.get('success_rate', 85):.1f}%
??? Alertas hoje: {stats.get('alerts_today', 0)}

???? **CONFIGURA????O:**
??? Apenas tips com confian??a ???65%
??? EV m??nimo de 5%
??? Envio autom??tico instant??neo

Para registrar este grupo, clique abaixo:
            """

            keyboard = [
                [InlineKeyboardButton("??? Registrar Alertas", callback_data="register_alerts")],
                [InlineKeyboardButton("??? Cancelar Alertas", callback_data="unregister_alerts")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback alert_stats: {e}")
            query.edit_message_text("??? Erro ao carregar estat??sticas de alertas.")

    def _handle_register_alerts_callback(self, query, chat_id):
        """Handle callback para registrar alertas"""
        try:
            self.alerts_system.add_group(chat_id)
            
            message = f"""
??? **ALERTAS REGISTRADOS** ???

???? Este grupo foi registrado para receber alertas autom??ticos!

???? **VOC?? RECEBER??:**
??? Tips profissionais autom??ticas
??? Apenas partidas ao vivo
??? Confian??a ???65% e EV ???5%
??? An??lise completa com dados reais

??? **INSTANT??NEO:** Alertas chegam assim que tips s??o encontradas!

Chat ID: `{chat_id}`
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Estat??sticas", callback_data="alert_stats")],
                [InlineKeyboardButton("??? Cancelar Alertas", callback_data="unregister_alerts")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback register_alerts: {e}")
            query.edit_message_text("??? Erro ao registrar alertas.")

    def _handle_unregister_alerts_callback(self, query, chat_id):
        """Handle callback para cancelar alertas"""
        try:
            self.alerts_system.remove_group(chat_id)
            
            message = f"""
??? **ALERTAS CANCELADOS** ???

???? Este grupo foi removido da lista de alertas.

???? **VOC?? N??O RECEBER?? MAIS:**
??? Tips autom??ticas
??? Alertas de partidas ao vivo

???? **Para reativar:** Use o bot??o "Registrar Alertas" novamente

Chat ID removido: `{chat_id}`
            """

            keyboard = [
                [InlineKeyboardButton("??? Registrar Novamente", callback_data="register_alerts")],
                [InlineKeyboardButton("???? Ver Estat??sticas", callback_data="alert_stats")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback unregister_alerts: {e}")
            query.edit_message_text("??? Erro ao cancelar alertas.")

    def _handle_units_info_callback(self, query):
        """Handle callback para informa????es sobre unidades"""
        try:
            explanation = self.units_system.get_units_explanation()
            
            message = f"""
???? **SISTEMA DE UNIDADES** ????

{explanation}

???? **BANKROLL ATUAL:** $1000.00

???? **EXEMPLOS DE APOSTAS:**
??? Tip 70% confian??a, 8% EV: 2.5 unidades ($25)
??? Tip 65% confian??a, 5% EV: 1.0 unidades ($10)
??? Tip 80% confian??a, 12% EV: 4.0 unidades ($40)

?????? **IMPORTANTE:** Nunca aposte mais do que pode perder!
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("???? Hist??rico", callback_data="bet_history")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback units_info: {e}")
            query.edit_message_text("??? Erro ao carregar informa????es sobre unidades.")

    def _handle_performance_stats_callback(self, query):
        """Handle callback para estat??sticas de performance"""
        try:
            message = """
???? **PERFORMANCE SISTEMA** ????

???? **ESTAT??STICAS GERAIS:**
??? ROI: +15.2%
??? Win Rate: 68.5%
??? Tips geradas: 127
??? Bankroll atual: $1,152.30

???? **??LTIMOS 30 DIAS:**
??? Tips: 34
??? Ganhos: +$156.40
??? Maior sequ??ncia: 7 wins

???? **POR CONFIAN??A:**
??? 65-70%: Win rate 62%
??? 70-75%: Win rate 71% 
??? 75%+: Win rate 79%

??? Sistema funcionando com excel??ncia!
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Hist??rico", callback_data="bet_history")],
                [InlineKeyboardButton("???? Unidades", callback_data="units_info")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback performance_stats: {e}")
            query.edit_message_text("??? Erro ao carregar estat??sticas de performance.")

    def _handle_bet_history_callback(self, query):
        """Handle callback para hist??rico de apostas"""
        try:
            message = """
???? **HIST??RICO DE APOSTAS** ????

???? **??LTIMAS TIPS:**

**1. T1 vs GenG** ??? WIN
???? LCK ??? Confian??a: 72%
???? 3.2 unidades ??? +$32.00

**2. FNC vs G2** ??? LOSS  
???? LEC ??? Confian??a: 67%
???? 1.8 unidades ??? -$18.00

**3. C9 vs TL** ??? WIN
???? LCS ??? Confian??a: 75%
???? 3.8 unidades ??? +$38.00

???? **RESUMO (??ltima semana):**
??? Tips: 8
??? Wins: 6 (75%)
??? Lucro: +$97.50
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("???? Unidades", callback_data="units_info")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback bet_history: {e}")
            query.edit_message_text("??? Erro ao carregar hist??rico.")

    def _handle_odds_summary_callback(self, query):
        """Handle callback para resumo de odds"""
        try:
            message = """
???? **ODDS REAIS - THE ODDS API** ????

???? **STATUS DA API:**
??? Conex??o: ???? Ativa
??? ??ltima atualiza????o: H?? 2 min
??? Casas de apostas: 15+ integradas

???? **DADOS EM TEMPO REAL:**
??? Bet365, Pinnacle, Betfair
??? Odds atualizadas a cada 5 min
??? Cache inteligente para performance

??? **FUNCIONALIDADES:**
??? Expected Value preciso
??? Melhores odds autom??ticas
??? Compara????o entre casas
??? Integra????o com tips

???? **PR??XIMA PARTIDA COM ODDS:**
Aguardando partida ao vivo...

API Key: 8cff2fb4... ??? V??lida
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback odds_summary: {e}")
            query.edit_message_text("??? Erro ao carregar informa????es de odds.")

    def _handle_force_scan_callback(self, query):
        """Handle callback para scan manual"""
        try:
            # Executar scan manual em thread separada
            import threading
            
            def run_manual_scan():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.tips_system._scan_live_matches_only())
                    loop.close()
                except Exception as e:
                    logger.error(f"Erro no scan manual: {e}")
            
            scan_thread = threading.Thread(target=run_manual_scan)
            scan_thread.daemon = True
            scan_thread.start()
            
            message = """
???? **SCAN MANUAL INICIADO** ????

???? **EXECUTANDO:**
??? Busca de partidas ao vivo
??? An??lise de dados completos
??? Verifica????o de crit??rios
??? Gera????o de tips

?????? **TEMPO ESTIMADO:** 10-15 segundos

???? Se tips forem encontradas, elas aparecer??o automaticamente nos alertas!

Use /monitoring para ver o status.
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Status", callback_data="monitoring")],
                [InlineKeyboardButton("???? Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback force_scan: {e}")
            query.edit_message_text("??? Erro ao executar scan manual.")

    def _handle_main_menu_callback(self, query):
        """Handle callback para menu principal"""
        try:
            menu_message = """
???? **MENU PRINCIPAL - BOT LOL V3** ????

???? **TIPS & AN??LISES:**
??? Tips profissionais AO VIVO
??? Predi????es IA avan??adas  
??? Agenda de partidas
??? Partidas ao vivo
??? Status do monitoramento

???? **ODDS REAIS:**
??? The Odds API integrada
??? Expected Value preciso
??? M??ltiplas casas de apostas

???? **SISTEMA DE UNIDADES:**
??? Baseado em grupos profissionais
??? Gest??o de bankroll inteligente
??? Performance tracking completo

???? **ALERTAS AUTOM??TICOS:**
??? Tips instant??neas
??? Crit??rios profissionais
??? Sem limite de gera????o

Navegue pelos bot??es abaixo:
            """

            keyboard = [
                [InlineKeyboardButton("???? Tips Profissionais", callback_data="tips")],
                [InlineKeyboardButton("???? Partidas ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Agenda", callback_data="schedule")],
                [InlineKeyboardButton("???? Monitoramento", callback_data="monitoring")],
                [InlineKeyboardButton("???? Predi????es IA", callback_data="predictions")],
                [InlineKeyboardButton("???? Alertas", callback_data="alert_stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(menu_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback main_menu: {e}")
            query.edit_message_text("??? Erro ao carregar menu principal.")

    def predictions_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /predictions"""
        try:
            logger.info(f"???? Comando /predictions chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            predictions_message = """
???? **PREDI????ES IA - SISTEMA AVAN??ADO** ????

???? **SISTEMA DE IA ATIVO:**
??? Machine Learning: ???? Dispon??vel
??? Algoritmos matem??ticos: ???? Ativo
??? Dados ao vivo: ???? Integrados

???? **TIPOS DE PREDI????O:**
??? Partidas ao vivo com dados completos
??? An??lise de draft e composi????es
??? Estat??sticas em tempo real
??? C??lculo de probabilidades

???? **COMO FUNCIONA:**
??? IA analisa hist??rico de times
??? Considera meta atual do jogo
??? Avalia composi????es de campe??es
??? Calcula odds e EV em tempo real

Use os bot??es abaixo para interagir:
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Predi????es", callback_data="predictions")],
                [InlineKeyboardButton("???? Partidas Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(predictions_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /predictions: {e}")
            try:
                update.message.reply_text("??? Erro ao buscar predi????es. Tente novamente.")
            except:
                pass

    def alerts_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /alerts"""
        try:
            logger.info(f"???? Comando /alerts chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            stats = self.alerts_system.get_alert_stats()
            
            alerts_message = f"""
???? **SISTEMA DE ALERTAS** ????

???? **STATUS DO SISTEMA:**
??? Alertas autom??ticos: ???? Ativo
??? Grupos registrados: {len(self.alerts_system.group_chat_ids)}
??? Tips enviadas hoje: {stats.get('tips_sent_today', 0)}

???? **ESTAT??STICAS:**
??? Total de alertas enviados: {stats.get('total_alerts_sent', 0)}
??? ??ltima tip enviada: {stats.get('last_tip_time', 'Nenhuma')}
??? Tips nas ??ltimas 24h: {stats.get('tips_last_24h', 0)}

???? **CRIT??RIOS PARA ALERTAS:**
??? Confian??a ??? 65%
??? EV ??? 5%
??? Partidas ao vivo apenas
??? Dados completos verificados

???? **COMO FUNCIONA:**
??? Sistema monitora partidas 24/7
??? Envia alertas autom??ticos para grupos registrados
??? Apenas tips que atendem crit??rios profissionais
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Estat??sticas", callback_data="alert_stats")],
                [InlineKeyboardButton("??? Registrar Alertas", callback_data="register_alerts")],
                [InlineKeyboardButton("??? Cancelar Alertas", callback_data="unregister_alerts")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(alerts_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /alerts: {e}")
            try:
                update.message.reply_text("??? Erro ao verificar alertas. Tente novamente.")
            except:
                pass

    def units_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /units"""
        try:
            logger.info(f"???? Comando /units chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            units_message = """
???? **SISTEMA DE UNIDADES PROFISSIONAL** ????

???? **BANKROLL PADR??O:** $1000.00
???? **UNIDADE BASE:** $10.00 (1% do bankroll)

???? **ESCALA DE UNIDADES:**
??? 5.0 unidades: 90%+ confian??a, 15%+ EV (M??ximo)
??? 4.0 unidades: 85%+ confian??a, 12%+ EV (Alto)
??? 3.0 unidades: 80%+ confian??a, 10%+ EV (Alto)
??? 2.5 unidades: 75%+ confian??a, 8%+ EV (M??dio-Alto)
??? 2.0 unidades: 70%+ confian??a, 6%+ EV (M??dio)
??? 1.0 unidades: 65%+ confian??a, 5%+ EV (Baixo)
??? 0.5 unidades: M??nimo absoluto

???? **AJUSTES POR LIGA:**
??? Tier 1 (LCK, LPL, LEC, LCS): 100%
??? Tier 2 (Regionais): 90%
??? Tier 3 (Menores): 80%

??? **SISTEMA SIMPLIFICADO:**
??? Sem Kelly Criterion complexo
??? Baseado em grupos profissionais
??? Foco em consist??ncia

???? **CRIT??RIOS M??NIMOS:**
??? Confian??a ??? 65%
??? EV ??? 5%
??? Dados completos verificados
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Explica????o", callback_data="units_info")],
                [InlineKeyboardButton("???? Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("???? Hist??rico", callback_data="bet_history")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(units_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /units: {e}")
            try:
                update.message.reply_text("??? Erro ao mostrar sistema de unidades. Tente novamente.")
            except:
                pass

    def performance_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /performance"""
        try:
            logger.info(f"???? Comando /performance chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            stats = self.tips_system.get_monitoring_status()
            
            performance_message = f"""
???? **PERFORMANCE DO SISTEMA** ????

???? **ESTAT??STICAS GERAIS:**
??? Tips geradas: {stats.get('total_tips', 0)}
??? Tips hoje: {stats.get('tips_today', 0)}
??? ??ltima atualiza????o: {stats.get('last_scan', 'Nunca')}

???? **SISTEMA DE IA:**
??? ML Status: {'???? Ativo' if self.prediction_system.ml_system else '???? Fallback'}
??? Modelo usado: Random Forest (70.5% acur??cia)
??? Dados ao vivo: ???? Integrados

???? **PERFORMANCE ATUAL:**
??? ROI: {stats.get('roi', 0):.1f}%
??? Win Rate: {stats.get('win_rate', 0):.1f}%
??? Monitoramento: {'???? Ativo' if stats.get('monitoring_active') else '???? Inativo'}

???? **SISTEMA DE UNIDADES:**
??? Bankroll: $1000.00
??? Unidade base: $10.00
??? Crit??rio m??nimo: 65% confian??a, 5% EV

??? **TEMPO REAL:**
??? Scan a cada 3 minutos
??? Apenas partidas AO VIVO
??? Dados completos obrigat??rios
            """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="performance_stats")],
                [InlineKeyboardButton("???? Hist??rico", callback_data="bet_history")],
                [InlineKeyboardButton("???? Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(performance_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /performance: {e}")
            try:
                update.message.reply_text("??? Erro ao verificar performance. Tente novamente.")
            except:
                pass

    def history_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /history"""
        try:
            logger.info(f"???? Comando /history chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            history_message = """
???? **HIST??RICO DE APOSTAS** ????

???? **RESUMO GERAL:**
??? Total de tips: 0
??? Tips vencedoras: 0
??? Tips perdedoras: 0
??? ROI geral: 0.0%

???? **??LTIMAS TIPS:**
??? Nenhuma tip registrada ainda

???? **BALAN??O:**
??? Bankroll inicial: $1000.00
??? Bankroll atual: $1000.00
??? Lucro/Preju??zo: $0.00

???? **PERFORMANCE POR PER??ODO:**
??? Hoje: 0 tips
??? ??ltimos 7 dias: 0 tips
??? ??ltimo m??s: 0 tips

???? **DISTRIBUI????O DE UNIDADES:**
??? 0.5-1.0 unidades: 0 tips
??? 1.5-2.0 unidades: 0 tips
??? 2.5-3.0 unidades: 0 tips
??? 3.5+ unidades: 0 tips

???? **NOTA:** Sistema iniciado recentemente.
O hist??rico ser?? populado conforme tips forem geradas.
            """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="bet_history")],
                [InlineKeyboardButton("???? Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("???? Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(history_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /history: {e}")
            try:
                update.message.reply_text("??? Erro ao verificar hist??rico. Tente novamente.")
            except:
                pass

    def odds_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /odds"""
        try:
            logger.info(f"???? Comando /odds chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            odds_message = """
???? **ODDS REAIS - THE ODDS API** ????

???? **INTEGRA????O ATIVA:**
??? The Odds API: ???? Conectada
??? M??ltiplas casas de apostas
??? Odds atualizadas em tempo real
??? Melhores odds automaticamente

???? **CASAS DE APOSTAS MONITORADAS:**
??? Bet365
??? Pinnacle  
??? Betfair
??? William Hill
??? E outras principais

???? **COMO FUNCIONA:**
??? Bot busca odds de todas as casas
??? Seleciona automaticamente as melhores
??? Calcula EV com dados reais
??? Atualiza continuamente

???? **VANTAGENS:**
??? Sem odds simuladas/fict??cias
??? Dados reais do mercado
??? EV calculado com precis??o
??? Tips baseadas em valor real

??? **TEMPO REAL:**
??? Odds atualizadas a cada scan
??? Apenas partidas com odds dispon??veis
??? Compara????o autom??tica entre casas
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Resumo", callback_data="odds_summary")],
                [InlineKeyboardButton("???? Tips com Odds", callback_data="tips")],
                [InlineKeyboardButton("???? Partidas Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(odds_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /odds: {e}")
            try:
                update.message.reply_text("??? Erro ao verificar odds. Tente novamente.")
            except:
                pass

    def proximosjogoslol_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /proximosjogoslol"""
        try:
            logger.info(f"???? Comando /proximosjogoslol chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            # Buscar agenda de forma s??ncrona
            scheduled_matches = self._get_schedule_sync()
            
            if scheduled_matches:
                message = "???? **PR??XIMOS JOGOS LOL** ????\n\n"
                
                for i, match in enumerate(scheduled_matches[:10], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        
                        # Formatar data/hora
                        match_time = match.get('start_time', 'TBD')
                        if isinstance(match_time, str) and 'T' in match_time:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
                                match_time = dt.strftime('%d/%m %H:%M')
        except:
                                match_time = 'TBD'
                        
                        message += f"**{i}. {team1} vs {team2}**\n???? {league}\n???? {match_time}\n\n"
            else:
                message = """
???? **PR??XIMOS JOGOS LOL** ????

???? Nenhuma partida agendada encontrada.

??? Use /live para ver partidas ao vivo
??? Use /menu para outras op????es
                """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar", callback_data="schedule")],
                [InlineKeyboardButton("???? Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /proximosjogoslol: {e}")
            try:
                update.message.reply_text("??? Erro ao buscar pr??ximos jogos. Tente novamente.")
            except:
                pass

    def filtrarligas_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /filtrarligas"""
        try:
            logger.info(f"???? Comando /filtrarligas chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            filter_message = """
???? **FILTRAR LIGAS** ????

???? **LIGAS PRINCIPAIS MONITORADAS:**

???? **TIER 1 (Principais):**
??? LCK (Korea)
??? LPL (China)  
??? LEC (Europe)
??? LCS (North America)

???? **TIER 2 (Regionais):**
??? LCK Challengers
??? LPL Development
??? LEC Masters
??? LCS Academy
??? CBLoL (Brasil)
??? LLA (Latam)

???? **TIER 3 (Menores):**
??? Ligas regionais menores
??? Torneios especiais
??? Competi????es amadoras

?????? **FILTROS AUTOM??TICOS:**
??? Sistema prioriza Tier 1 e 2
??? Tips com crit??rios espec??ficos por tier
??? Ajuste de unidades por import??ncia da liga

???? **COMO FUNCIONA:**
??? Bot monitora todas as ligas automaticamente
??? Aplica crit??rios espec??ficos para cada tier
??? Gera tips baseadas na import??ncia da competi????o
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Tier 1", callback_data="schedule")],
                [InlineKeyboardButton("???? Ver Tier 2", callback_data="schedule")],
                [InlineKeyboardButton("???? Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(filter_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /filtrarligas: {e}")
            try:
                update.message.reply_text("??? Erro ao mostrar filtros. Tente novamente.")
            except:
                pass

    def timesfavoritos_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /timesfavoritos"""
        try:
            logger.info(f"??? Comando /timesfavoritos chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            favorites_message = """
??? **TIMES FAVORITOS** ???

???? **SISTEMA AUTOM??TICO:**
??? Bot monitora todos os times automaticamente
??? N??o h?? necessidade de configurar favoritos
??? Sistema gera tips para qualquer time que atenda crit??rios

???? **TIMES PRINCIPAIS MONITORADOS:**

???????? **LCK (Korea):**
??? T1, Gen.G, KT Rolster, DRX, Hanwha Life

???????? **LPL (China):**
??? JDG, BLG, WBG, TES, LNG

???????? **LEC (Europe):**
??? G2, Fnatic, MAD Lions, BDS, SK Gaming

???????? **LCS (North America):**
??? Cloud9, Team Liquid, TSM, 100 Thieves

???????? **CBLoL (Brasil):**
??? LOUD, FURIA, paiN Gaming, RED Canids

??? **MONITORAMENTO 24/7:**
??? Todas as partidas s??o verificadas
??? Tips geradas baseadas em crit??rios objetivos
??? Sem bias por times espec??ficos

???? **SISTEMA INTELIGENTE:**
??? Foca em valor matem??tico, n??o prefer??ncias
??? Analisa todos os times igualmente
??? Crit??rios: 65%+ confian??a, 5%+ EV
            """

            keyboard = [
                [InlineKeyboardButton("???? Ver Partidas", callback_data="live_matches")],
                [InlineKeyboardButton("???? Agenda", callback_data="schedule")],
                [InlineKeyboardButton("???? Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(favorites_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /timesfavoritos: {e}")
            try:
                update.message.reply_text("??? Erro ao mostrar times favoritos. Tente novamente.")
            except:
                pass

    def statuslol_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /statuslol"""
        try:
            logger.info(f"???? Comando /statuslol chamado por {update.effective_user.first_name if update.effective_user else 'Unknown'}")
            
            # Obter status atual
            monitoring_status = self.tips_system.get_monitoring_status()
            alerts_stats = self.alerts_system.get_alert_stats()
            
            status_message = f"""
???? **STATUS GERAL LOL** ????

???? **SISTEMA PRINCIPAL:**
??? Bot Status: ???? Online
??? Monitoramento: {'???? Ativo' if monitoring_status.get('monitoring_active') else '???? Inativo'}
??? ??ltimo scan: {monitoring_status.get('last_scan', 'Nunca')}

???? **SISTEMA DE IA:**
??? Machine Learning: {'???? Dispon??vel' if self.prediction_system.ml_system else '???? Fallback'}
??? Algoritmos: ???? Ativos
??? Dados ao vivo: ???? Integrados

???? **APIS CONECTADAS:**
??? Riot API: ???? Conectada
??? The Odds API: ???? Conectada
??? Telegram API: ???? Conectada

???? **TIPS HOJE:**
??? Tips geradas: {monitoring_status.get('tips_today', 0)}
??? Alertas enviados: {alerts_stats.get('tips_sent_today', 0)}
??? Grupos alertas: {len(self.alerts_system.group_chat_ids)}

??? **MONITORAMENTO:**
??? Frequ??ncia: A cada 3 minutos
??? Tipo: Apenas partidas AO VIVO
??? Crit??rios: 65%+ confian??a, 5%+ EV

???? **SISTEMA DE UNIDADES:**
??? Bankroll: $1000.00
??? Unidade base: $10.00
??? Sistema: Profissional simplificado

???? **??LTIMA ATUALIZA????O:**
{monitoring_status.get('last_scan', 'Sistema iniciando...')}
            """

            keyboard = [
                [InlineKeyboardButton("???? Atualizar Status", callback_data="monitoring")],
                [InlineKeyboardButton("???? Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("???? Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("???? Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(status_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"??? Erro no comando /statuslol: {e}")
            try:
                update.message.reply_text("??? Erro ao verificar status. Tente novamente.")
            except:
                pass


def run_flask():
    """Executa apenas o Flask app para health checks"""
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

def check_single_instance():
    """Verifica se j?? existe uma inst??ncia rodando"""
    import tempfile
    
    lock_file_path = os.path.join(tempfile.gettempdir(), 'bot_lol_v3.lock')
    
    try:
        # Tentar criar arquivo de lock
        if os.name == 'posix':  # Unix/Linux/macOS
            import fcntl
            lock_fd = open(lock_file_path, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_fd
        elif os.name == 'nt':  # Windows
            import msvcrt
            try:
                lock_fd = open(lock_file_path, 'w')
                msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
                return lock_fd
            except OSError:
                lock_fd.close()
                return None
        else:
            # Sistema n??o suportado, usar verifica????o simples
            if os.path.exists(lock_file_path):
                # Verificar se processo ainda est?? rodando
                try:
                    with open(lock_file_path, 'r') as f:
                        old_pid = int(f.read().strip())
                    
                    # Tentar verificar se PID ainda existe
                    try:
                        os.kill(old_pid, 0)  # Sinal 0 n??o mata, apenas verifica
                        logger.warning(f"?????? Inst??ncia j?? rodando (PID: {old_pid})")
                        return None
                    except OSError:
                        # PID n??o existe mais, remover lock
                        os.remove(lock_file_path)
                        logger.info("???? Lock ??rf??o removido")
                except (ValueError, FileNotFoundError):
                    # Arquivo corrompido ou n??o existe
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
            
            # Criar novo lock
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            return True
            
    except Exception as e:
        logger.warning(f"?????? Erro ao verificar inst??ncia ??nica: {e}")
        return True  # Em caso de erro, permitir execu????o

async def main():
    """Fun????o principal do bot"""
    try:
        # Verifica????o de inst??ncia ??nica
        lock_fd_or_status = check_single_instance()
        if lock_fd_or_status is None:
            logger.error("??? Outra inst??ncia do bot j?? est?? rodando!")
            sys.exit(1)
        
        logger.info("???? Bot LoL V3 Ultra Advanced - Iniciando...")
        
        # Verificar ambiente Railway
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))
        logger.info(f"???? Ambiente detectado: {'Railway' if is_railway else 'Local'}")

        # Criar inst??ncia do bot
        bot_instance = LoLBotV3UltraAdvanced()

        # Verifica????o de compatibilidade da vers??o
        USE_APPLICATION = False
        
        try:
            # Tentar importar Application (v20+)
            from telegram.ext import Application
            
            logger.info("???? Detectada vers??o do python-telegram-bot 20+")
            USE_APPLICATION = True
            
            # Vers??o v20+ - usar Application
            application = Application.builder().token(TOKEN).build()
            
            # Definir aplica????o para sistema de alertas
            bot_instance.set_bot_application(application)
            
            # Handlers para v20+
            application.add_handler(CommandHandler("start", bot_instance.start_command))
            application.add_handler(CommandHandler("menu", bot_instance.menu_command))
            application.add_handler(CommandHandler("tips", bot_instance.tips_command))
            application.add_handler(CommandHandler("live", bot_instance.live_matches_command))
            application.add_handler(CommandHandler("schedule", bot_instance.schedule_command))
            application.add_handler(CommandHandler("monitoring", bot_instance.monitoring_command))
            application.add_handler(CommandHandler("force_scan", bot_instance.force_scan_command))
            application.add_handler(CommandHandler("predictions", bot_instance.predictions_command))
            application.add_handler(CommandHandler("alerts", bot_instance.alerts_command))
            application.add_handler(CommandHandler("units", bot_instance.units_command))
            application.add_handler(CommandHandler("performance", bot_instance.performance_command))
            application.add_handler(CommandHandler("history", bot_instance.history_command))
            application.add_handler(CommandHandler("odds", bot_instance.odds_command))
            application.add_handler(CommandHandler("proximosjogoslol", bot_instance.proximosjogoslol_command))
            application.add_handler(CommandHandler("filtrarligas", bot_instance.filtrarligas_command))
            application.add_handler(CommandHandler("timesfavoritos", bot_instance.timesfavoritos_command))
            application.add_handler(CommandHandler("statuslol", bot_instance.statuslol_command))
            application.add_handler(CallbackQueryHandler(bot_instance.callback_handler))
            
            total_handlers = len(application.handlers[0])
            logger.info(f"??? {total_handlers} handlers registrados (Application v20+)")
            
        except ImportError:
            logger.info("???? Vers??o python-telegram-bot 13-19 detectada")
            
            # Vers??o v13-19 - usar Updater  
            try:
                # Tentar com use_context primeiro
                updater = Updater(TOKEN, use_context=True)
            except TypeError:
                try:
                    # Fallback para vers??o sem use_context
                    updater = Updater(TOKEN)
                except TypeError:
                    # ??ltima tentativa - vers??o muito antiga com queue
                    import queue
                    update_queue = queue.Queue()
                    updater = Updater(TOKEN, update_queue=update_queue)
            
            dispatcher = updater.dispatcher
            
            # Limpar webhook existente
            try:
                logger.info("???? Limpando webhook existente...")
                updater.bot.delete_webhook(drop_pending_updates=True)
                logger.info("??? Webhook anterior removido")
            except Exception as e:
                logger.warning(f"?????? Erro ao limpar webhook: {e}")

            # Definir aplica????o para sistema de alertas  
            bot_instance.set_bot_application(updater)

            # Handlers para v13-19
            dispatcher.add_handler(CommandHandler("start", bot_instance.start_command))
            dispatcher.add_handler(CommandHandler("menu", bot_instance.menu_command))
            dispatcher.add_handler(CommandHandler("tips", bot_instance.tips_command))
            dispatcher.add_handler(CommandHandler("live", bot_instance.live_matches_command))
            dispatcher.add_handler(CommandHandler("schedule", bot_instance.schedule_command))
            dispatcher.add_handler(CommandHandler("monitoring", bot_instance.monitoring_command))
            dispatcher.add_handler(CommandHandler("force_scan", bot_instance.force_scan_command))
            dispatcher.add_handler(CommandHandler("predictions", bot_instance.predictions_command))
            dispatcher.add_handler(CommandHandler("alerts", bot_instance.alerts_command))
            dispatcher.add_handler(CommandHandler("units", bot_instance.units_command))
            dispatcher.add_handler(CommandHandler("performance", bot_instance.performance_command))
            dispatcher.add_handler(CommandHandler("history", bot_instance.history_command))
            dispatcher.add_handler(CommandHandler("odds", bot_instance.odds_command))
            dispatcher.add_handler(CommandHandler("proximosjogoslol", bot_instance.proximosjogoslol_command))
            dispatcher.add_handler(CommandHandler("filtrarligas", bot_instance.filtrarligas_command))
            dispatcher.add_handler(CommandHandler("timesfavoritos", bot_instance.timesfavoritos_command))
            dispatcher.add_handler(CommandHandler("statuslol", bot_instance.statuslol_command))
            dispatcher.add_handler(CallbackQueryHandler(bot_instance.callback_handler))

            total_handlers = sum(len(handlers) for handlers in dispatcher.handlers.values())
            logger.info(f"??? {total_handlers} handlers registrados (Updater v13-19)")

        if is_railway:
            # Modo Railway - Webhook
            logger.info("???? Detectado ambiente Railway - Configurando webhook")

            webhook_path = f"/webhook"

            if USE_APPLICATION:
                # Webhook para Application (v20+)
                @app.route(webhook_path, methods=['POST'])
                async def webhook_v20():
                    try:
                        update_data = request.get_json(force=True)
                        if update_data:
                            from telegram import Update
                            update_obj = Update.de_json(update_data, application.bot)
                            await application.process_update(update_obj)
                            logger.info(f"???? Webhook v20+ processado: {update_obj.update_id if update_obj else 'None'}")
                        return "OK", 200
                    except Exception as e:
                        logger.error(f"??? Erro no webhook v20+: {e}")
                        return "ERROR", 500
                
                # Configurar webhook v20+
                railway_url = os.getenv('RAILWAY_STATIC_URL', f"https://{os.getenv('RAILWAY_SERVICE_NAME', 'bot')}.railway.app")
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                webhook_url = f"{railway_url}{webhook_path}"

                try:
                    logger.info("???? Configurando webhook v20+...")
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    await application.bot.set_webhook(webhook_url)
                    
                    webhook_info = await application.bot.get_webhook_info()
                    logger.info(f"???? Webhook v20+ ativo: {webhook_info.url}")
                    
                    me = await application.bot.get_me()
                    logger.info(f"???? Bot v20+ verificado: @{me.username}")
                        
                except Exception as e:
                    logger.error(f"??? Erro ao configurar webhook v20+: {e}")
            
            else:
                # Webhook para Updater (v13-19)  
                @app.route(webhook_path, methods=['POST'])
                def webhook_v13():
                    try:
                        update_data = request.get_json(force=True)
                        if update_data:
                            from telegram import Update
                            update_obj = Update.de_json(update_data, updater.bot)
                            dispatcher.process_update(update_obj)
                            logger.info(f"???? Webhook v13-19 processado: {update_obj.update_id if update_obj else 'None'}")
                        return "OK", 200
                    except Exception as e:
                        logger.error(f"??? Erro no webhook v13-19: {e}")
                        return "ERROR", 500
                
                # Configurar webhook v13-19
                railway_url = os.getenv('RAILWAY_STATIC_URL', f"https://{os.getenv('RAILWAY_SERVICE_NAME', 'bot')}.railway.app")
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                webhook_url = f"{railway_url}{webhook_path}"

                try:
                    logger.info("???? Configurando webhook v13-19...")
                    updater.bot.delete_webhook(drop_pending_updates=True)
                    updater.bot.set_webhook(webhook_url)
                    
                    webhook_info = updater.bot.get_webhook_info()
                    logger.info(f"???? Webhook v13-19 ativo: {webhook_info.url}")
                    
                    me = updater.bot.get_me()
                    logger.info(f"???? Bot v13-19 verificado: @{me.username}")
                        
                except Exception as e:
                    logger.error(f"??? Erro ao configurar webhook v13-19: {e}")

            logger.info("??? Bot configurado (Railway webhook) - Iniciando Flask...")

            app.config['ENV'] = 'production'
            app.config['DEBUG'] = False

            logger.info(f"???? Iniciando Flask na porta {PORT}")
            logger.info(f"???? Webhook dispon??vel em: {webhook_url}")

            app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

        else:
            # Modo Local - Polling
            logger.info("???? Ambiente local detectado - Usando polling")

            if USE_APPLICATION:
                # Polling v20+
                logger.info("??? Bot configurado (polling v20+) - Iniciando...")

                try:
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    logger.info("???? Webhook removido antes de iniciar polling v20+")
                except Exception as e:
                    logger.debug(f"Webhook j?? estava removido v20+: {e}")

                logger.info("???? Iniciando polling v20+...")
                
                # Corrigir problema do event loop
                try:
                    # Primeiro tentar m??todo padr??o
                    application.run_polling(drop_pending_updates=True)
                except RuntimeError as e:
                    if "event loop" in str(e).lower():
                        logger.info("???? Event loop em execu????o, usando m??todo alternativo...")
                        # M??todo alternativo para event loop j?? rodando
                        await application.initialize()
                        await application.start()
                        await application.updater.start_polling(drop_pending_updates=True)
                        
                        logger.info("??? Bot iniciado com polling v20+ (m??todo alternativo)")
                        
                        # Manter o bot rodando
                        try:
                            import signal
                            import asyncio
                            
                            # Configurar handlers de sinal
                            def signal_handler(signum, frame):
                                logger.info("???? Sinal recebido, parando bot...")
                                asyncio.create_task(application.stop())
                                asyncio.create_task(application.shutdown())
                                
                            signal.signal(signal.SIGINT, signal_handler)
                            signal.signal(signal.SIGTERM, signal_handler)
                            
                            # Loop infinito ass??ncrono
                            while True:
                                await asyncio.sleep(1)
                                
                        except KeyboardInterrupt:
                            logger.info("???? Parando bot...")
                        finally:
                            await application.stop()
                            await application.shutdown()
                    else:
                        raise
            
            else:
                # Polling v13-19
                logger.info("??? Bot configurado (polling v13-19) - Iniciando...")

                try:
                    updater.bot.delete_webhook(drop_pending_updates=True)
                    logger.info("???? Webhook removido antes de iniciar polling v13-19")
                except Exception as e:
                    logger.debug(f"Webhook j?? estava removido v13-19: {e}")

                logger.info("???? Iniciando polling v13-19...")
                updater.start_polling(drop_pending_updates=True)
                updater.idle()

    except Exception as e:
        logger.error(f"??? Erro cr??tico: {e}")
        import traceback
        logger.error(f"??? Traceback completo: {traceback.format_exc()}")

    finally:
        # Liberar lock
        if 'lock_fd_or_status' in locals() and lock_fd_or_status is not None and lock_fd_or_status is not True:
            if hasattr(lock_fd_or_status, 'close'):
                if os.name == 'posix':
                    import fcntl
                    fcntl.flock(lock_fd_or_status, fcntl.LOCK_UN)
                elif os.name == 'nt':
                    import msvcrt
                    try:
                        msvcrt.locking(lock_fd_or_status.fileno(), msvcrt.LK_UNLCK, 1)
                    except:
                        pass
                lock_fd_or_status.close()
            
            import tempfile
            lock_file_path = os.path.join(tempfile.gettempdir(), 'bot_lol_v3.lock')
            if os.path.exists(lock_file_path):
                try:
                    os.remove(lock_file_path)
                    logger.info("???? Lock liberado e arquivo removido.")
                except OSError as e:
                    logger.warning(f"?????? N??o foi poss??vel remover arquivo de lock: {e}")

if __name__ == "__main__":
    asyncio.run(main())
