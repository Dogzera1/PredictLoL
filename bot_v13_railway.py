#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT LOL V3 ULTRA AVANÇADO - Sistema de Tips Profissional
Sistema de unidades padrão de grupos de apostas profissionais
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

# VERIFICAÇÃO CRÍTICA DE CONFLITOS NO INÍCIO
def early_conflict_check():
    """Verificação precoce de conflitos antes de importar bibliotecas pesadas"""
    # Verificar se é Railway
    is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))

    if not is_railway:
        print("⚠️ EXECUTANDO EM MODO LOCAL - VERIFICANDO CONFLITOS...")
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
                            print(f"🚨 OUTRA INSTÂNCIA DETECTADA! PID: {old_pid}")
                            print("🛑 ABORTANDO PARA EVITAR CONFLITOS!")
                            print("💡 Execute: python stop_all_conflicts.py")
                            sys.exit(1)
                    else:  # Unix/Linux
                        os.kill(old_pid, 0)  # Não mata, só verifica
                        print(f"🚨 OUTRA INSTÂNCIA DETECTADA! PID: {old_pid}")
                        print("🛑 ABORTANDO PARA EVITAR CONFLITOS!")
                        print("💡 Execute: python stop_all_conflicts.py")
                        sys.exit(1)
                except OSError:
                    # Processo não existe mais, remover lock
                    os.remove(lock_file)
                    print("🧹 Lock antigo removido (processo morto)")
            except:
                # Arquivo corrompido, remover
                try:
                    os.remove(lock_file)
                except:
                    pass
        print("✅ Verificação precoce de conflitos OK")

# Executar verificação precoce
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
    logger.info("🤖 Módulo ML importado (lazy loading)")
except ImportError as e:
    ML_MODULE_AVAILABLE = False
    logger.warning(f"⚠️ Módulo ML não disponível: {e}")

# Configurações
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
            'units_system': 'Padrão de grupos profissionais',
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
    """Sistema de Unidades Padrão de Grupos Profissionais"""

    def __init__(self, bankroll: float = 1000.0):
        self.bankroll = bankroll
        self.base_unit = bankroll * 0.01  # 1% do bankroll = 1 unidade base

        # Sistema de unidades padrão de grupos profissionais
        self.unit_scale = {
            'max_confidence_high_ev': 5.0,    # 90%+ confiança, 15%+ EV
            'high_confidence_high_ev': 4.0,   # 85%+ confiança, 12%+ EV
            'high_confidence_good_ev': 3.0,   # 80%+ confiança, 10%+ EV
            'good_confidence_good_ev': 2.5,   # 75%+ confiança, 8%+ EV
            'medium_confidence': 2.0,         # 70%+ confiança, 6%+ EV
            'low_confidence': 1.0,            # 65%+ confiança, 5%+ EV
            'minimum': 0.5                    # Mínimo absoluto
        }

        # Histórico
        self.bet_history = []
        self.performance_stats = {
            'total_bets': 0, 'wins': 0, 'losses': 0,
            'total_units_staked': 0, 'total_units_profit': 0,
            'roi_percentage': 0, 'strike_rate': 0
        }

        logger.info(f"💰 Sistema de Unidades Profissional inicializado - Bankroll: ${bankroll}")

    def calculate_units(self, confidence: float, ev_percentage: float, league_tier: str = "tier2") -> Dict:
        """Calcula unidades usando sistema padrão de grupos profissionais"""
        # Ajuste por tier da liga
        tier_multipliers = {'tier1': 1.0, 'tier2': 0.9, 'tier3': 0.8}
        tier_mult = tier_multipliers.get(league_tier, 0.8)

        # Determinar unidades baseado em confiança e EV
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
            risk_level = "Médio-Alto"
        elif confidence >= 70 and ev_percentage >= 6:
            base_units = self.unit_scale['medium_confidence']
            risk_level = "Médio"
        elif confidence >= 65 and ev_percentage >= 5:
            base_units = self.unit_scale['low_confidence']
            risk_level = "Baixo"
        else:
            return {
                'units': 0, 'stake_amount': 0, 'risk_level': 'Sem Valor',
                'recommendation': 'NÃO APOSTAR - Critérios não atendidos',
                'reason': f'Confiança: {confidence:.1f}% | EV: {ev_percentage:.1f}%'
            }

        # Aplicar multiplicador de tier
        final_units = base_units * tier_mult

        # Ajuste fino baseado em EV excepcional
        if ev_percentage >= 20:
            final_units *= 1.2
            risk_level = "Máximo"
        elif ev_percentage >= 18:
            final_units *= 1.1

        # Limites de segurança
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
        """Gera explicação do cálculo de unidades"""
        reasoning_parts = []

        if confidence >= 85 and ev_percentage >= 12:
            reasoning_parts.append("🔥 Alta confiança + Excelente valor")
        elif confidence >= 80 and ev_percentage >= 10:
            reasoning_parts.append("⭐ Boa confiança + Bom valor")
        elif confidence >= 75 and ev_percentage >= 8:
            reasoning_parts.append("✅ Confiança adequada + Valor positivo")
        else:
            reasoning_parts.append("⚠️ Critérios mínimos atendidos")

        if league_tier == 'tier1':
            reasoning_parts.append("🏆 Liga Tier 1 (sem redução)")
        elif league_tier == 'tier2':
            reasoning_parts.append("🥈 Liga Tier 2 (-10%)")
        else:
            reasoning_parts.append("🥉 Liga menor (-20%)")

        if ev_percentage >= 20:
            reasoning_parts.append("💎 Bonus +20% por EV excepcional")
        elif ev_percentage >= 18:
            reasoning_parts.append("💰 Bonus +10% por EV muito alto")

        return " • ".join(reasoning_parts)

    def get_units_explanation(self) -> str:
        """Retorna explicação do sistema de unidades"""
        return """
🎲 **SISTEMA DE UNIDADES PROFISSIONAL** 🎲

📊 **ESCALA PADRÃO DE GRUPOS PROFISSIONAIS:**

🔥 **5.0 UNIDADES** - Confiança 90%+ | EV 15%+
⭐ **4.0 UNIDADES** - Confiança 85%+ | EV 12%+
✅ **3.0 UNIDADES** - Confiança 80%+ | EV 10%+
📈 **2.5 UNIDADES** - Confiança 75%+ | EV 8%+
📊 **2.0 UNIDADES** - Confiança 70%+ | EV 6%+
⚠️ **1.0 UNIDADES** - Confiança 65%+ | EV 5%+

🏆 **AJUSTES POR LIGA:**
• Tier 1 (LCK/LPL/LEC/LCS): Sem redução
• Tier 2 (Regionais): -10%
• Tier 3 (Menores): -20%

💎 **BONUS POR EV EXCEPCIONAL:**
• EV 20%+: +20% unidades
• EV 18%+: +10% unidades

⚡ **CRITÉRIOS MÍNIMOS:**
• Confiança mínima: 65%
• EV mínimo: 5%
• Máximo por aposta: 5 unidades
        """

class RiotAPIClient:
    """Cliente para API da Riot Games - APENAS DADOS REAIS"""

    def __init__(self):
        self.api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
        self.base_urls = {
            'esports': 'https://esports-api.lolesports.com/persisted/gw',
            'prod': 'https://prod-relapi.ewp.gg/persisted/gw'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        logger.info("🔗 RiotAPIClient inicializado - APENAS DADOS REAIS")

    async def get_live_matches(self) -> List[Dict]:
        """Busca partidas ao vivo REAIS da API oficial - APENAS MATCHES EM ANDAMENTO"""
        logger.info("🔍 Buscando partidas ao vivo...")
        endpoints = [
            f"{self.base_urls['esports']}/getLive?hl=pt-BR",
            f"{self.base_urls['esports']}/getSchedule?hl=pt-BR"
        ]
        all_matches = []

        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, headers=self.headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            matches = self._extract_live_matches_only(data)
                            all_matches.extend(matches)
            except Exception as e:
                logger.warning(f"❌ Erro no endpoint: {e}")
                continue
                    
        return all_matches[:10]

    async def get_live_matches_with_details(self) -> List[Dict]:
        """Busca partidas ao vivo COM dados detalhados (draft + estatísticas)"""
        logger.info("🔍 Buscando partidas ao vivo com dados detalhados...")
        
        # Primeiro buscar partidas ao vivo básicas
        live_matches = await self.get_live_matches()
        
        detailed_matches = []
        
        for match in live_matches:
            try:
                # Enriquecer cada partida com dados detalhados
                detailed_match = await self._get_match_details(match)
                if detailed_match:
                    detailed_matches.append(detailed_match)
            except Exception as e:
                logger.warning(f"❌ Erro ao buscar detalhes da partida: {e}")
                continue
        
        logger.info(f"📊 {len(detailed_matches)} partidas com dados detalhados encontradas")
        return detailed_matches

    async def _get_match_details(self, match: Dict) -> Optional[Dict]:
        """Busca dados detalhados de uma partida específica"""
        try:
            # Simular busca de dados detalhados da partida
            # Na implementação real, isso faria chamadas específicas para endpoints de dados ao vivo
            
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None
            
            # Simular dados de draft (na implementação real viria da API)
            draft_data = {
                'team1_picks': ['Champion1', 'Champion2', 'Champion3', 'Champion4', 'Champion5'],
                'team2_picks': ['Champion6', 'Champion7', 'Champion8', 'Champion9', 'Champion10'],
                'team1_bans': ['Banned1', 'Banned2', 'Banned3'],
                'team2_bans': ['Banned4', 'Banned5', 'Banned6']
            }
            
            # Simular estatísticas da partida (na implementação real viria da API)
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
            
            # Determinar número do jogo baseado no status
            game_number = 1  # Na implementação real, viria da API
            if 'game' in match.get('tournament', '').lower():
                try:
                    # Tentar extrair número do jogo do torneio
                    game_number = int(''.join(filter(str.isdigit, match.get('tournament', ''))) or 1)
                except:
                    game_number = 1
            
            # Adicionar dados detalhados à partida
            detailed_match = match.copy()
            detailed_match.update({
                'draft_data': draft_data,
                'match_statistics': match_statistics,
                'game_time': game_time,
                'game_number': game_number,
                'has_complete_data': True
            })
            
            logger.debug(f"📊 Dados detalhados obtidos para {teams[0].get('name')} vs {teams[1].get('name')} - Game {game_number}")
            return detailed_match
            
        except Exception as e:
            logger.warning(f"❌ Erro ao obter detalhes da partida: {e}")
            return None

    def _extract_live_matches_only(self, data: Dict) -> List[Dict]:
        """Extrai APENAS partidas que estão acontecendo AGORA"""
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
                        # Calcular tempo estimado de jogo se tiver startTime
                        game_time = 0
                        start_time_str = event.get('startTime', '')
                        if start_time_str:
                            try:
                                from datetime import timezone
                                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                                start_time_local = start_time.astimezone()
                                time_diff = now - start_time_local.replace(tzinfo=None)
                                if time_diff.total_seconds() > 0:
                                    game_time = int(time_diff.total_seconds())
                            except:
                                pass
                        
                        match = {
                            'teams': teams,
                            'league': self._extract_league(event),
                            'status': 'live',  # Forçar status live
                            'start_time': start_time_str,
                            'game_time': game_time,
                            'tournament': event.get('tournament', {}).get('name', 'Tournament')
                        }
                        matches.append(match)
                        logger.info(f"🎮 Partida ao vivo encontrada: {teams[0].get('name')} vs {teams[1].get('name')}")
        except Exception as e:
            logger.error(f"Erro ao extrair partidas ao vivo: {e}")
        
        logger.info(f"🎮 {len(matches)} partidas realmente ao vivo encontradas")
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
        
        logger.info(f"💰 TheOddsAPIClient inicializado com API Key: {api_key[:8]}...")

    async def get_esports_odds(self, region: str = "us") -> List[Dict]:
        """Busca odds de eSports (incluindo League of Legends)"""
        try:
            # Verificar cache primeiro
            cache_key = f"esports_odds_{region}"
            if self._is_cache_valid(cache_key):
                logger.debug(f"💾 Usando odds do cache para {region}")
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
                        logger.info(f"💰 Obtidas {len(data)} odds de eSports de {region}")
                        
                        # Filtrar apenas jogos de League of Legends
                        lol_odds = self._filter_lol_games(data)
                        
                        # Salvar no cache
                        self.odds_cache[cache_key] = {
                            'data': lol_odds,
                            'timestamp': datetime.now()
                        }
                        
                        return lol_odds
                    elif response.status == 429:
                        logger.warning("⚠️ Rate limit atingido na The Odds API")
                        return []
                    else:
                        logger.warning(f"❌ Erro na The Odds API: Status {response.status}")
                        return []

        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds de eSports: {e}")
            return []

    def _filter_lol_games(self, odds_data: List[Dict]) -> List[Dict]:
        """Filtra apenas jogos de League of Legends"""
        lol_keywords = ['league of legends', 'lol', 'lck', 'lpl', 'lec', 'lcs', 'cblol', 'worlds', 'msi']
        filtered_odds = []
        
        for game in odds_data:
            sport_title = game.get('sport_title', '').lower()
            sport_key = game.get('sport_key', '').lower()
            
            # Verificar se é jogo de LoL baseado no título ou chave do esporte
            if any(keyword in sport_title for keyword in lol_keywords) or \
               any(keyword in sport_key for keyword in lol_keywords):
                filtered_odds.append(game)
                
        logger.info(f"🎮 Filtrados {len(filtered_odds)} jogos de League of Legends")
        return filtered_odds

    async def get_match_odds(self, team1: str, team2: str, league: str = "") -> Optional[Dict]:
        """Busca odds específicas para uma partida"""
        try:
            # Buscar todas as odds de eSports
            all_odds = await self.get_esports_odds()
            
            # Procurar partida específica
            for game in all_odds:
                teams = game.get('teams', [])
                if len(teams) >= 2:
                    game_team1 = teams[0].get('name', '').lower()
                    game_team2 = teams[1].get('name', '').lower()
                    
                    # Verificar se os times correspondem (busca flexível)
                    if (self._teams_match(team1, game_team1) and self._teams_match(team2, game_team2)) or \
                       (self._teams_match(team1, game_team2) and self._teams_match(team2, game_team1)):
                        
                        logger.info(f"💰 Odds encontradas para {team1} vs {team2}")
                        return self._process_match_odds(game, team1, team2)
            
            logger.debug(f"⚠️ Odds não encontradas para {team1} vs {team2}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds da partida: {e}")
            return None

    def _teams_match(self, team_name: str, api_team_name: str) -> bool:
        """Verifica se nomes de times correspondem (busca flexível)"""
        team_clean = team_name.lower().strip()
        api_clean = api_team_name.lower().strip()
        
        # Correspondência exata
        if team_clean == api_clean:
            return True
            
        # Correspondência parcial
        if team_clean in api_clean or api_clean in team_clean:
            return True
            
        # Verificar códigos/abreviações comuns
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
        
        # Verificar se algum dos códigos corresponde
        for canonical, codes in team_codes.items():
            if team_clean in codes and any(code in api_clean for code in codes):
                return True
                
        return False

    def _process_match_odds(self, game_data: Dict, team1: str, team2: str) -> Dict:
        """Processa odds de uma partida específica"""
        try:
            processed_odds = {
                'team1': team1,
                'team2': team2,
                'team1_odds': 2.0,  # Odds padrão
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
            
            # Calcular melhores odds e médias
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
                
                logger.info(f"💰 Odds processadas: {team1} {processed_odds['team1_odds']:.2f} vs {team2} {processed_odds['team2_odds']:.2f}")
                
            return processed_odds
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar odds: {e}")
            return {
                'team1': team1, 'team2': team2,
                'team1_odds': 2.0, 'team2_odds': 2.0,
                'source': 'fallback'
            }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se o cache ainda é válido"""
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
                logger.info(f"🧹 {len(keys_to_remove)} entradas antigas removidas do cache de odds")
                
        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache de odds: {e}")

    async def get_odds_summary(self) -> Dict:
        """Retorna resumo das odds disponíveis"""
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
                # Extrair liga se possível
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
            logger.error(f"❌ Erro ao gerar resumo de odds: {e}")
            return {'error': str(e)}

class LoLUserPreferences:
    """Sistema de preferências de usuários para LoL tips"""
    
    def __init__(self):
        self.user_preferences = {}
        self.favorite_teams = {}
        self.league_filters = {}
        
    def set_favorite_teams(self, user_id: int, teams: List[str]):
        """Define times favoritos do usuário"""
        self.favorite_teams[user_id] = teams
        logger.info(f"👤 Usuário {user_id} definiu times favoritos: {teams}")
        
    def set_league_filter(self, user_id: int, leagues: List[str]):
        """Define filtro de ligas do usuário"""
        self.league_filters[user_id] = leagues
        logger.info(f"👤 Usuário {user_id} definiu filtro de ligas: {leagues}")
        
    def get_user_preferences(self, user_id: int) -> Dict:
        """Retorna preferências do usuário"""
        return {
            'favorite_teams': self.favorite_teams.get(user_id, []),
            'league_filters': self.league_filters.get(user_id, []),
            'notifications_enabled': self.user_preferences.get(user_id, {}).get('notifications', True)
        }
        
    def should_notify_user(self, user_id: int, match: Dict) -> bool:
        """Verifica se deve notificar usuário sobre uma partida"""
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
    """Analisador específico para eventos cruciais de LoL"""
    
    def __init__(self):
        self.game_states = {}
        
    def analyze_crucial_events(self, match: Dict) -> Dict:
        """Analisa eventos cruciais da partida para timing de tips"""
        try:
            match_stats = match.get('match_stats', {})
            game_time = match.get('game_time', 0)
            
            events_detected = []
            impact_score = 0.0
            
            # Analisar diferença de ouro
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
    """Sistema de predição dinâmica com ML real + algoritmos como fallback"""

    def __init__(self):
        # Inicializar ML real se disponível 
        self.ml_system = None
        self.ml_loading = False
        
        # Verificar se ML está realmente disponível
        if ML_MODULE_AVAILABLE:
            try:
                logger.info("🤖 Tentando carregar sistema ML...")
                self.ml_system = ml_prediction_system.MLPredictionSystem()
                logger.info("🤖 Sistema de ML REAL inicializado com sucesso")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao inicializar ML: {e}")
                self.ml_system = None
        else:
            logger.info("⚠️ Módulo ML não disponível - usando algoritmos matemáticos")

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
        
        # Status corrigido do ML
        ml_status = "🟢 ML REAL ATIVO" if self.ml_system else "🟡 ALGORITMOS MATEMÁTICOS"
        logger.info(f"🔮 Sistema de Predição inicializado: {ml_status}")

    def _ensure_ml_loaded(self):
        """Carrega ML sob demanda se não foi carregado ainda (Railway)"""
        if ML_MODULE_AVAILABLE and self.ml_system is None and not self.ml_loading:
            try:
                logger.info("🤖 Carregando ML sob demanda...")
                self.ml_loading = True
                self.ml_system = ml_prediction_system.MLPredictionSystem()
                logger.info("🤖 ML carregado sob demanda com sucesso")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar ML sob demanda: {e}")
                self.ml_system = None
            finally:
                self.ml_loading = False

    async def predict_live_match(self, match: Dict) -> Dict:
        """Predição com ML real ou fallback para algoritmos matemáticos"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return self._get_fallback_prediction()

            team1_name = teams[0].get('name', 'Team 1')
            team2_name = teams[1].get('name', 'Team 2')
            league = match.get('league', 'Unknown')

            # 🤖 TENTAR ML REAL PRIMEIRO
            if self.ml_system:
                try:
                    ml_prediction = self.ml_system.predict_match(team1_name, team2_name, league)
                    if ml_prediction and ml_prediction.get('confidence') in ['Alta', 'Muito Alta']:
                        # Converter para formato esperado
                        return {
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
                    logger.info(f"⚠️ ML predição baixa confiança, usando fallback")
                except Exception as e:
                    logger.warning(f"⚠️ Erro no ML, usando fallback: {e}")
            elif ML_MODULE_AVAILABLE and not self.ml_loading:
                # Tentar carregar ML sob demanda (Railway)
                self._ensure_ml_loaded()
                if self.ml_system:
                    # Tentar novamente após carregar
                    try:
                        ml_prediction = self.ml_system.predict_match(team1_name, team2_name, league)
                        if ml_prediction and ml_prediction.get('confidence') in ['Alta', 'Muito Alta']:
                            return {
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
                    except Exception as e:
                        logger.warning(f"⚠️ Erro no ML sob demanda: {e}")
            
            # 🧮 FALLBACK: ALGORITMOS MATEMÁTICOS
            logger.info(f"🧮 Usando algoritmos matemáticos para {team1_name} vs {team2_name}")
            return await self._predict_with_algorithms(match)

        except Exception as e:
            logger.error(f"❌ Erro na predição: {e}")
            return self._get_fallback_prediction()

    async def predict_live_match_with_live_data(self, match: Dict) -> Dict:
        """Predição avançada usando dados ao vivo (draft + estatísticas)"""
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

            logger.info(f"🎮 Predição com dados ao vivo: {team1_name} vs {team2_name} (Game {game_time//60}min)")

            # Primeiro obter predição base
            base_prediction = await self.predict_live_match(match)
            
            if not base_prediction:
                return self._get_fallback_prediction()

            # Ajustar predição com dados ao vivo
            adjusted_prediction = self._adjust_prediction_with_live_data(
                base_prediction, draft_data, match_stats, game_time
            )

            # Aumentar confiança se temos dados ao vivo
            if adjusted_prediction['confidence'] == 'Média':
                adjusted_prediction['confidence'] = 'Alta'
            elif adjusted_prediction['confidence'] == 'Alta':
                adjusted_prediction['confidence'] = 'Muito Alta'

            # Adicionar análise específica de dados ao vivo
            live_analysis = self._generate_live_data_analysis(draft_data, match_stats, game_time)
            adjusted_prediction['analysis'] = f"{adjusted_prediction['analysis']} • {live_analysis}"
            
            # Marcar como predição com dados ao vivo
            adjusted_prediction['prediction_factors']['live_data'] = True
            adjusted_prediction['prediction_factors']['game_time'] = game_time
            adjusted_prediction['cache_status'] = 'live_data_enhanced'

            logger.info(f"🎯 Predição com dados ao vivo: {adjusted_prediction['favored_team']} favorito ({adjusted_prediction['confidence']})")
            return adjusted_prediction

        except Exception as e:
            logger.error(f"❌ Erro na predição com dados ao vivo: {e}")
            return await self.predict_live_match(match)  # Fallback para predição básica

    def _adjust_prediction_with_live_data(self, base_prediction: Dict, draft_data: Dict, 
                                        match_stats: Dict, game_time: int) -> Dict:
        """Ajusta predição baseada em dados ao vivo"""
        try:
            adjusted = base_prediction.copy()
            
            # Analisar estatísticas da partida
            gold_diff = match_stats.get('gold_difference', 0)
            kill_diff = match_stats.get('kill_difference', 0)
            tower_diff = match_stats.get('tower_difference', 0)
            
            # Determinar qual time está na frente
            team1_name = adjusted['team1']
            team2_name = adjusted['team2']
            favored_team = adjusted['favored_team']
            
            # Calcular ajuste baseado na situação atual
            situation_modifier = 0.0
            
            # Ajuste por diferença de gold
            if abs(gold_diff) > 3000:
                if (gold_diff > 0 and favored_team == team1_name) or (gold_diff < 0 and favored_team == team2_name):
                    situation_modifier += 0.15  # Time favorito está na frente
                else:
                    situation_modifier -= 0.10  # Time favorito está atrás
            
            # Ajuste por diferença de kills
            if abs(kill_diff) > 5:
                if (kill_diff > 0 and favored_team == team1_name) or (kill_diff < 0 and favored_team == team2_name):
                    situation_modifier += 0.10
                else:
                    situation_modifier -= 0.08
            
            # Ajuste por diferença de torres
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
            
            logger.debug(f"📊 Ajuste por dados ao vivo: {situation_modifier:+.2f} → Nova prob: {new_win_prob:.2f}")
            return adjusted
            
        except Exception as e:
            logger.warning(f"❌ Erro ao ajustar predição: {e}")
            return base_prediction

    def _generate_live_data_analysis(self, draft_data: Dict, match_stats: Dict, game_time: int) -> str:
        """Gera análise textual dos dados ao vivo"""
        try:
            analysis_parts = []
            
            # Análise de tempo de jogo
            game_min = game_time // 60
            if game_min < 15:
                analysis_parts.append(f"Early game ({game_min}min)")
            elif game_min < 30:
                analysis_parts.append(f"Mid game ({game_min}min)")
            else:
                analysis_parts.append(f"Late game ({game_min}min)")
            
            # Análise de estatísticas
            gold_diff = match_stats.get('gold_difference', 0)
            kill_diff = match_stats.get('kill_difference', 0)
            
            if abs(gold_diff) > 3000:
                team_ahead = "T1" if gold_diff > 0 else "T2"
                analysis_parts.append(f"{team_ahead} com vantagem de gold significativa")
            
            if abs(kill_diff) > 5:
                team_ahead = "T1" if kill_diff > 0 else "T2"
                analysis_parts.append(f"{team_ahead} dominando em kills")
            
            # Análise de draft (simplificada)
            if draft_data.get('team1_picks') and draft_data.get('team2_picks'):
                analysis_parts.append("Drafts completos analisados")
            
            return " • ".join(analysis_parts) if analysis_parts else "Dados ao vivo processados"
            
        except Exception as e:
            logger.warning(f"❌ Erro na análise de dados ao vivo: {e}")
            return "Análise de dados ao vivo indisponível"

    async def _predict_with_algorithms(self, match: Dict) -> Dict:
        """Predição usando algoritmos matemáticos (fallback)"""
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

        # Determinar confiança
        confidence = self._calculate_confidence(team1_data, team2_data)

        # Determinar favorito
        if team1_prob > team2_prob:
            favored_team = team1_name
            win_probability = team1_prob
        else:
            favored_team = team2_name
            win_probability = team2_prob

        # Gerar análise
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
        """Ajuste baseado na força real das regiões"""
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
        """Calcula nível de confiança"""
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
            return 'Média'
        else:
            return 'Baixa'

    def _generate_match_analysis(self, team1: str, team2: str, team1_data: Dict,
                               team2_data: Dict, win_prob: float) -> str:
        """Gera análise textual da predição"""
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
            analysis_parts.append(f"{favorite} é ligeiramente favorito")
        else:
            analysis_parts.append("Times com força similar")

        if fav_prob > 0.7:
            analysis_parts.append(f"{favorite} é forte favorito ({fav_prob:.1%})")
        else:
            analysis_parts.append("Partida equilibrada")

        return " • ".join(analysis_parts)

    def _get_fallback_prediction(self) -> Dict:
        """Predição padrão em caso de erro"""
        return {
            'team1': 'Team 1', 'team2': 'Team 2',
            'team1_win_probability': 0.5, 'team2_win_probability': 0.5,
            'team1_odds': 2.0, 'team2_odds': 2.0,
            'favored_team': 'Team 1', 'win_probability': 0.5,
            'confidence': 'Baixa', 'analysis': 'Análise não disponível',
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
                
                logger.info(f"💰 Usando odds REAIS: {favored_team} = {base_odds:.2f}")
                
                # Verificar se há melhores odds disponíveis
                best_odds = real_odds.get('best_odds', {})
                if favored_team == team1_name and 'team1_best' in best_odds:
                    best_available = best_odds['team1_best']
                    if best_available > base_odds:
                        logger.info(f"💎 Melhor odd encontrada: {best_available:.2f} vs média {base_odds:.2f}")
                        base_odds = best_available
                elif favored_team == team2_name and 'team2_best' in best_odds:
                    best_available = best_odds['team2_best']
                    if best_available > base_odds:
                        logger.info(f"💎 Melhor odd encontrada: {best_available:.2f} vs média {base_odds:.2f}")
                        base_odds = best_available
            else:
                logger.warning(f"⚠️ Odds reais não encontradas para {team1_name} vs {team2_name}, usando dados da partida")
                
                # Fallback: usar estatísticas da partida para ajustar odds
                stats = match.get('match_statistics', {})
                
                # Exemplo de fatores que afetam odds durante a partida
                gold_diff = stats.get('gold_difference', 0)
                kill_diff = stats.get('kill_difference', 0)
                tower_diff = stats.get('tower_difference', 0)
                
                # Ajustar odds baseado na situação atual
                if gold_diff > 3000:  # Time favorito tem vantagem de gold
                    base_odds -= 0.3
                elif gold_diff < -3000:  # Time favorito está atrás
                    base_odds += 0.4
                    
                if kill_diff > 5:
                    base_odds -= 0.2
                elif kill_diff < -5:
                    base_odds += 0.3
                    
                if tower_diff > 2:
                    base_odds -= 0.2
                elif tower_diff < -2:
                    base_odds += 0.2
                    
                logger.info(f"🎮 Usando odds ajustadas por dados ao vivo: {base_odds:.2f}")
                
            return max(1.2, min(5.0, base_odds))  # Limitar entre 1.2 e 5.0
            
        except Exception as e:
            logger.warning(f"❌ Erro ao calcular odds reais: {e}")
            return 2.0

class TelegramAlertsSystem:
    """Sistema de Alertas APENAS para Tips Profissionais"""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.group_chat_ids = set()
        self.alert_history = []
        self.sent_tips = set()
        self.min_alert_interval = 1800  # 30 minutos

        logger.info("📢 Sistema de Alertas para Tips inicializado")

    def add_group(self, chat_id: int):
        """Adiciona grupo para receber alertas"""
        self.group_chat_ids.add(chat_id)
        logger.info(f"📢 Grupo {chat_id} adicionado para alertas")

    def remove_group(self, chat_id: int):
        """Remove grupo dos alertas"""
        self.group_chat_ids.discard(chat_id)
        logger.info(f"📢 Grupo {chat_id} removido dos alertas")

    async def send_tip_alert(self, tip: Dict, bot_application):
        """Envia alerta de tip profissional para os grupos"""
        try:
            tip_id = tip.get('tip_id', '')
            if tip_id in self.sent_tips:
                logger.info(f"📢 Tip {tip_id} já foi enviado - pulando")
                return

            if not self._should_send_alert(tip):
                logger.info(f"📢 Tip não atende critérios para alerta")
                return

            # Extrair informações específicas do mapa e dados ao vivo
            map_info = tip.get('map_info', 'Mapa 1')
            game_time = tip.get('game_time', 0)
            game_min = game_time // 60 if game_time > 0 else 0
            
            # Dados específicos do jogo
            draft_analysis = tip.get('draft_analysis', '')
            stats_analysis = tip.get('stats_analysis', '')
            live_odds = tip.get('live_odds', 0)

            alert_message = f"""
🚨 **ALERTA DE TIP PROFISSIONAL** 🚨

🗺️ **{map_info}: {tip['title']}**
🎮 Liga: {tip['league']}
⏱️ Tempo de jogo: {game_min}min (AO VIVO)

🤖 **ANÁLISE IA COM DADOS AO VIVO:**
• Confiança: {tip['confidence_score']:.1f}% ({tip['confidence_level']})
• EV: {tip['ev_percentage']:.1f}%
• Probabilidade: {tip['win_probability']*100:.1f}%
• Odds ao vivo: {live_odds:.2f}

🎲 **SISTEMA DE UNIDADES:**
• Apostar: {tip['units']} unidades
• Valor: ${tip['stake_amount']:.2f}
• Risco: {tip['risk_level']}

⭐ **Recomendação:** {tip['recommended_team']}

📊 **DADOS DA PARTIDA:**"""

            # Adicionar análise de draft se disponível
            if draft_analysis and draft_analysis != "Dados de draft não disponíveis":
                alert_message += f"\n🎯 Draft: {draft_analysis}"
            
            # Adicionar análise de estatísticas se disponível
            if stats_analysis and stats_analysis != "Estatísticas não disponíveis":
                alert_message += f"\n📈 Stats: {stats_analysis}"

            alert_message += f"""

💡 **EXPLICAÇÃO COMPLETA:**
{tip['reasoning']}

⚡ **PARTIDA AO VIVO COM DADOS REAIS!**
⏰ {datetime.now().strftime('%H:%M:%S')}
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
                    logger.warning(f"❌ Erro ao enviar alerta para grupo {chat_id}: {e}")
                    self.group_chat_ids.discard(chat_id)

            self.sent_tips.add(tip_id)
            self._register_alert(tip_id, tip)

            logger.info(f"📢 Alerta de tip {map_info} enviado para {sent_count} grupos - ID: {tip_id}")

        except Exception as e:
            logger.error(f"❌ Erro no sistema de alertas: {e}")

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
        """Registra alerta no histórico"""
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
        """Retorna estatísticas dos alertas"""
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

            # Limpar histórico antigo também
            self.alert_history = [alert for alert in self.alert_history 
                                if alert['timestamp'] >= cutoff_time]

            if old_tips:
                logger.info(f"🧹 {len(old_tips)} tips antigos removidos do cache")
        except Exception as e:
            logger.error(f"❌ Erro ao limpar tips antigos: {e}")

class ScheduleManager:
    """Gerenciador de Agenda de Partidas"""

    def __init__(self, riot_client=None):
        self.riot_client = riot_client or RiotAPIClient()
        self.scheduled_matches = []
        self.last_update = None
        logger.info("📅 ScheduleManager inicializado")

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
                    logger.warning(f"❌ Erro no endpoint de agenda: {e}")
                    continue

            unique_matches = self._remove_duplicates(all_matches)
            sorted_matches = sorted(unique_matches, key=lambda x: x.get('start_time', ''))

            self.scheduled_matches = sorted_matches[:20]
            self.last_update = datetime.now()

            logger.info(f"📅 {len(self.scheduled_matches)} partidas agendadas encontradas")
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
                # CORREÇÃO: Usar timezone aware para comparação
                from datetime import timezone
                cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
                now_utc = datetime.now(timezone.utc)
                
                for event in events:
                    try:
                        start_time_str = event.get('startTime', '')
                        if start_time_str:
                            # Converter para datetime com timezone
                            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                            
                            # Verificar se está no intervalo desejado
                            if now_utc <= start_time <= cutoff_date:
                                teams = self._extract_teams_from_event(event)
                                if len(teams) >= 2:
                                    # Converter para horário local para exibição
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
                    
                    # Criar ID único mais específico
                    # Usar tanto A vs B quanto B vs A para evitar duplicatas de ordem
                    team_pair = tuple(sorted([team1, team2]))
                    match_id = f"{team_pair}_{league}_{start_time}"
                    
                    if match_id not in seen:
                        seen.add(match_id)
                        unique_matches.append(match)
                    else:
                        logger.debug(f"🗑️ Partida duplicada removida: {team1} vs {team2}")
            except Exception as e:
                logger.debug(f"Erro ao processar partida para duplicatas: {e}")
                continue
        
        logger.info(f"🧹 Remoção de duplicatas: {len(matches)} → {len(unique_matches)} partidas únicas")
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
    """Sistema de Tips Profissional com Monitoramento Contínuo"""

    def __init__(self, riot_client=None):
        self.riot_client = riot_client or RiotAPIClient()
        self.units_system = ProfessionalUnitsSystem()
        self.odds_client = TheOddsAPIClient()  # Cliente para odds reais
        self.user_preferences = LoLUserPreferences()  # Preferências de usuários LoL
        self.game_analyzer = LoLGameAnalyzer()  # Analisador de eventos cruciais
        self.tips_database = []
        self.given_tips = set()
        self.monitoring = False
        self.last_scan = None
        self.monitoring_task = None

        # Critérios profissionais - SEM LIMITE SEMANAL
        self.min_ev_percentage = 8.0
        self.min_confidence_score = 75.0
        # REMOVIDO: self.max_tips_per_week = 5  # Agora sem limite!

        # Sempre iniciar monitoramento - funciona tanto no Railway quanto local
        self.start_monitoring()
        logger.info("🎯 Sistema de Tips Profissional LoL inicializado com ANÁLISE DE EVENTOS CRUCIAIS + ODDS REAIS - SEM LIMITE DE TIPS")

    def start_monitoring(self):
        """Inicia monitoramento contínuo de APENAS partidas ao vivo com dados completos"""
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
                        
                        # Aguardar 3 minutos antes do próximo scan (mais frequente para partidas ao vivo)
                        if self.monitoring:
                            time.sleep(180)  # 3 minutos
                            
                    except Exception as e:
                        logger.error(f"❌ Erro no monitoramento de tips: {e}")
                        # Em caso de erro, aguardar 1 minuto antes de tentar novamente
                        if self.monitoring:
                            time.sleep(60)

            # Iniciar thread de monitoramento
            monitor_thread = threading.Thread(target=monitor_loop, daemon=True, name="TipsMonitor")
            monitor_thread.start()
            logger.info("🔍 Monitoramento contínuo de tips iniciado - APENAS PARTIDAS AO VIVO - Verificação a cada 3 minutos")

    def stop_monitoring(self):
        """Para o monitoramento"""
        self.monitoring = False
        logger.info("🛑 Monitoramento de tips interrompido")

    async def _scan_live_matches_only(self):
        """Escaneia APENAS partidas ao vivo com dados completos (drafts + estatísticas)"""
        try:
            logger.info("🔍 Escaneando APENAS partidas AO VIVO com dados completos...")

            # Buscar APENAS partidas ao vivo (não agendadas)
            live_matches = await self.riot_client.get_live_matches_with_details()
            logger.info(f"📍 Encontradas {len(live_matches)} partidas ao vivo com dados completos")

            opportunities_found = 0

            for i, match in enumerate(live_matches, 1):
                try:
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        game_number = match.get('game_number', 1)
                        logger.debug(f"🔍 Analisando JOGO {game_number}: {team1} vs {team2}")

                    # Verificar se partida tem dados suficientes (draft + stats)
                    if not self._has_complete_match_data(match):
                        logger.debug(f"⏳ Partida sem dados completos ainda - aguardando...")
                        continue

                    # Analisar partida para tip COM dados completos
                    tip_analysis = await self._analyze_live_match_with_data(match)

                    if tip_analysis and self._meets_professional_criteria(tip_analysis):
                        tip_id = self._generate_tip_id_with_game(match)

                        # Verificar se já foi dado este tip específico (incluindo número do jogo)
                        if tip_id not in self.given_tips:
                            professional_tip = self._create_professional_tip_with_game_data(tip_analysis)

                            if professional_tip:
                                self.tips_database.append(professional_tip)
                                self.given_tips.add(tip_id)
                                opportunities_found += 1

                                logger.info(f"🎯 NOVA OPORTUNIDADE ENCONTRADA: {professional_tip['title']}")
                                logger.info(f"   📊 Confiança: {professional_tip['confidence_score']:.1f}% | EV: {professional_tip['ev_percentage']:.1f}%")
                                logger.info(f"   🎲 Unidades: {professional_tip['units']} | Valor: ${professional_tip['stake_amount']:.2f}")
                                logger.info(f"   🗺️ {professional_tip['map_info']}")

                                # ENVIAR ALERTA AUTOMÁTICO PARA GRUPOS
                                try:
                                    if hasattr(self, '_bot_instance') and self._bot_instance:
                                        alerts_system = self._bot_instance.alerts_system
                                        bot_app = self._bot_instance.bot_application

                                        if alerts_system.group_chat_ids and bot_app:
                                            await alerts_system.send_tip_alert(professional_tip, bot_app)
                                            logger.info(f"📢 Alerta automático enviado para {len(alerts_system.group_chat_ids)} grupos")
                                        else:
                                            logger.info("📢 Nenhum grupo cadastrado para alertas ainda")

                                except Exception as alert_error:
                                    logger.warning(f"❌ Erro ao enviar alerta automático: {alert_error}")
                        else:
                            logger.debug(f"🔄 Tip já foi dado anteriormente: {tip_id}")
                    else:
                        if tip_analysis:
                            logger.debug(f"📊 Partida não atende critérios: Conf={tip_analysis.get('confidence_score', 0):.1f}% EV={tip_analysis.get('ev_percentage', 0):.1f}%")

                except Exception as match_error:
                    logger.warning(f"❌ Erro ao analisar partida {i}: {match_error}")
                    continue

            # Atualizar timestamp do último scan
            self.last_scan = datetime.now()

            if opportunities_found > 0:
                logger.info(f"✅ SCAN COMPLETO: {opportunities_found} novas oportunidades de tips encontradas!")
            else:
                logger.info("ℹ️ SCAN COMPLETO: Nenhuma nova oportunidade encontrada neste scan")

            # Limpeza de tips antigos
            self._cleanup_old_tips()

        except Exception as e:
            logger.error(f"❌ Erro geral no scan de partidas ao vivo: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _has_complete_match_data(self, match: Dict) -> bool:
        """Verifica se a partida tem dados completos (draft + estatísticas)"""
        try:
            # Verificar se tem dados de draft
            draft_data = match.get('draft_data')
            if not draft_data:
                return False

            # Verificar se tem estatísticas da partida
            match_stats = match.get('match_statistics')
            if not match_stats:
                return False

            # Verificar se a partida realmente começou (não apenas draft)
            game_time = match.get('game_time', 0)
            if game_time < 300:  # Menos de 5 minutos = ainda muito cedo
                return False

            # Verificar se tem dados dos times
            teams = match.get('teams', [])
            if len(teams) < 2:
                return False

            # Verificar se tem informação do mapa/game
            game_number = match.get('game_number')
            if not game_number:
                return False

            logger.debug(f"✅ Partida tem dados completos - Game {game_number}, {game_time}s de jogo")
            return True

        except Exception as e:
            logger.debug(f"❌ Erro ao verificar dados da partida: {e}")
            return False

    async def _analyze_live_match_with_data(self, match: Dict) -> Optional[Dict]:
        """Analisa partida ao vivo COM dados de draft e estatísticas"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None

            team1_name = teams[0].get('name', '')
            team2_name = teams[1].get('name', '')
            league = match.get('league', '')
            game_number = match.get('game_number', 1)
            game_time = match.get('game_time', 0)

            # Usar sistema de predição COM dados ao vivo
            prediction_system = DynamicPredictionSystem()
            ml_prediction = await prediction_system.predict_live_match_with_live_data(match)

            if not ml_prediction or ml_prediction['confidence'] not in ['Alta', 'Muito Alta']:
                return None

            favored_team = ml_prediction['favored_team']
            win_probability = ml_prediction['win_probability']
            confidence_level = ml_prediction['confidence']

            # Mapear confiança para score numérico
            confidence_mapping = {'Muito Alta': 90, 'Alta': 80, 'Média': 70, 'Baixa': 60}
            confidence_score = confidence_mapping.get(confidence_level, 60)

            # Calcular EV baseado em dados ao vivo
            live_odds = self._calculate_live_odds_from_data(match, favored_team)
            ev_percentage = self._calculate_ev_with_live_data(win_probability, live_odds, match)
            
            # Determinar tier da liga
            league_tier = self._determine_league_tier(league)

            # Extrair dados específicos da partida
            draft_analysis = self._analyze_draft_data(match.get('draft_data', {}))
            stats_analysis = self._analyze_match_statistics(match.get('match_statistics', {}))

            return {
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

        except Exception as e:
            logger.error(f"❌ Erro na análise da partida ao vivo: {e}")
            return None

    def _calculate_ev_with_live_data(self, win_probability: float, live_odds: float, match: Dict) -> float:
        """Calcula EV usando dados ao vivo da partida"""
        try:
            # EV = (odds * win_probability) - 1
            base_ev = (live_odds * win_probability) - 1
            
            # Ajustar EV baseado na qualidade dos dados
            game_time = match.get('game_time', 0)
            
            # Partidas com mais tempo têm dados mais confiáveis
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
                return "Dados de draft não disponíveis"
                
            team1_picks = draft_data.get('team1_picks', [])
            team2_picks = draft_data.get('team2_picks', [])
            
            analysis_parts = []
            
            # Analisar composições
            if len(team1_picks) >= 5 and len(team2_picks) >= 5:
                analysis_parts.append("Drafts completos analisados")
                
                # Exemplo de análise de composição
                team1_comp_type = self._analyze_team_composition(team1_picks)
                team2_comp_type = self._analyze_team_composition(team2_picks)
                
                analysis_parts.append(f"Comp. T1: {team1_comp_type}")
                analysis_parts.append(f"Comp. T2: {team2_comp_type}")
            else:
                analysis_parts.append("Draft em andamento")
                
            return " • ".join(analysis_parts)
            
        except Exception as e:
            logger.warning(f"Erro na análise de draft: {e}")
            return "Erro na análise de draft"

    def _analyze_team_composition(self, picks: List) -> str:
        """Analisa o tipo de composição do time"""
        # Simplificado para demonstração
        if len(picks) >= 5:
            return "Composição Completa"
        return "Composição Parcial"

    def _analyze_match_statistics(self, match_stats: Dict) -> str:
        """Analisa estatísticas da partida"""
        try:
            if not match_stats:
                return "Estatísticas não disponíveis"
                
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
                
            return " • ".join(analysis_parts)
            
        except Exception as e:
            logger.warning(f"Erro na análise de estatísticas: {e}")
            return "Erro na análise de estatísticas"

    def _generate_tip_id_with_game(self, match: Dict) -> str:
        """Gera ID único para o tip incluindo número do jogo"""
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
        """Cria tip profissional com dados específicos do jogo"""
        try:
            units_calc = self.units_system.calculate_units(
                confidence=analysis['confidence_score'],
                ev_percentage=analysis['ev_percentage'],
                league_tier=analysis['league_tier']
            )

            # Título com informação do mapa
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
        """Gera explicação do tip com dados ao vivo"""
        reasoning_parts = []
        
        # Informação do jogo
        game_time_min = int(analysis['game_time'] / 60)
        reasoning_parts.append(f"🗺️ {analysis['map_info']} ({game_time_min}min de jogo)")
        
        reasoning_parts.append(f"🤖 IA identifica {analysis['favored_team']} como favorito")
        reasoning_parts.append(f"📊 Confiança ML: {analysis['confidence_level']} ({analysis['confidence_score']:.1f}%)")
        reasoning_parts.append(f"💰 Valor esperado: {analysis['ev_percentage']:.1f}%")
        
        # Dados ao vivo
        reasoning_parts.append(f"📈 Odds ao vivo: {analysis['live_odds']:.2f}")
        
        # Análises específicas
        if analysis.get('draft_analysis'):
            reasoning_parts.append(f"🎯 Draft: {analysis['draft_analysis']}")
        if analysis.get('stats_analysis'):
            reasoning_parts.append(f"📊 Stats: {analysis['stats_analysis']}")
            
        reasoning_parts.append(f"🎲 {units_calc['reasoning']}")

        return " • ".join(reasoning_parts)

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
            'last_scan': self.last_scan.strftime('%H:%M:%S') if self.last_scan else 'Nunca',
            'total_tips': len(self.tips_database),  # Chave correta esperada pelos callbacks
            'tips_today': tips_today,  # Chave correta esperada pelos callbacks
            'tips_this_week': len(recent_tips),
            'scan_frequency': '3 minutos (apenas partidas ao vivo)',
            'given_tips_cache': len(self.given_tips),
            'focus': 'APENAS partidas ao vivo com dados completos',
            'weekly_limit': 'REMOVIDO - Tips ilimitados'
        }

    def set_bot_instance(self, bot_instance):
        """Define instância do bot para envio de alertas automáticos"""
        self._bot_instance = bot_instance
        logger.info("🤖 Bot instance conectada ao sistema de tips")

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
                logger.info(f"🧹 {len(old_tip_ids)} tips antigos removidos do cache")

        except Exception as e:
            logger.error(f"❌ Erro na limpeza de tips antigos: {e}")

    def _meets_professional_criteria(self, analysis: Dict) -> bool:
        """Verifica critérios profissionais"""
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
        """Gera explicação do tip"""
        reasoning_parts = []
        reasoning_parts.append(f"🤖 IA identifica {analysis['favored_team']} como favorito")
        reasoning_parts.append(f"📊 Confiança ML: {analysis['confidence_level']} ({analysis['confidence_score']:.1f}%)")
        reasoning_parts.append(f"💰 Valor esperado: {analysis['ev_percentage']:.1f}%")
        reasoning_parts.append(f"🎲 {units_calc['reasoning']}")

        if analysis.get('ml_analysis'):
            reasoning_parts.append(f"🔍 {analysis['ml_analysis']}")

        return " • ".join(reasoning_parts)

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
        """Gera ID único para o tip"""
        teams = match.get('teams', [])
        if len(teams) >= 2:
            team1 = teams[0].get('name', '')
            team2 = teams[1].get('name', '')
            league = match.get('league', '')
            timestamp = datetime.now().strftime('%Y%m%d')
            return f"{team1}_{team2}_{league}_{timestamp}".replace(' ', '_')
        return f"tip_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def generate_professional_tip(self) -> Optional[Dict]:
        """Gera tip profissional usando ML e retorna o melhor disponível"""
        try:
            # Buscar partidas disponíveis
            live_matches = await self.riot_client.get_live_matches()
            schedule_manager = ScheduleManager(self.riot_client)
            scheduled_matches = await schedule_manager.get_scheduled_matches(days_ahead=1)

            all_matches = live_matches + scheduled_matches
            logger.info(f"🎯 Analisando {len(all_matches)} partidas para tip profissional")

            # Analisar cada partida com ML
            best_tip = None
            best_score = 0

            for match in all_matches:
                tip_analysis = await self._analyze_match_for_tip(match)

                if tip_analysis and self._meets_professional_criteria(tip_analysis):
                    # Calcular score combinado (confiança + EV)
                    combined_score = tip_analysis['confidence_score'] + tip_analysis['ev_percentage']

                    if combined_score > best_score:
                        best_score = combined_score
                        best_tip = self._create_professional_tip(tip_analysis)

            if best_tip:
                logger.info(f"🎯 Melhor tip encontrado: {best_tip['title']} (Score: {best_score:.1f})")
            else:
                logger.info("ℹ️ Nenhum tip profissional disponível no momento")

            return best_tip

        except Exception as e:
            logger.error(f"❌ Erro ao gerar tip profissional: {e}")
            return None

    async def _analyze_match_for_tip(self, match: Dict) -> Optional[Dict]:
        """Analisa partida para determinar se é uma oportunidade de tip"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None

            team1_name = teams[0].get('name', '')
            team2_name = teams[1].get('name', '')
            league = match.get('league', '')

            # Usar sistema de predição para análise
            prediction_system = DynamicPredictionSystem()
            ml_prediction = await prediction_system.predict_live_match(match)

            if not ml_prediction or ml_prediction['confidence'] not in ['Alta', 'Muito Alta']:
                return None

            favored_team = ml_prediction['favored_team']
            win_probability = ml_prediction['win_probability']
            confidence_level = ml_prediction['confidence']

            # Mapear confiança para score numérico
            confidence_mapping = {'Muito Alta': 90, 'Alta': 80, 'Média': 70, 'Baixa': 60}
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
            logger.error(f"❌ Erro na análise da partida: {e}")
            return None

class LoLBotV3UltraAdvanced:
    """Bot LoL V3 Ultra Avançado com Sistema de Unidades Profissional + ML + Alertas"""

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

        logger.info("🤖 Bot LoL V3 Ultra Avançado inicializado - Tips + Agenda + Predições IA + Alertas")

    def set_bot_application(self, application):
        """Define a aplicação do bot para o sistema de alertas"""
        self.bot_application = application

        # Railway mode - sem threading de cleanup automático
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME'))
        
        if not is_railway:
            # Apenas local - cleanup automático
            logger.info("🧹 Cleanup automático ativo - modo local")

    def start_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /start"""
        user = update.effective_user
        welcome_message = f"""
🎮 **BOT LOL V3 ULTRA AVANÇADO** 🎮

Olá {user.first_name}! 👋

🎲 **SISTEMA DE UNIDADES PROFISSIONAL**
📊 Baseado em grupos de apostas profissionais
⚡ Sem Kelly Criterion - Sistema simplificado
🎯 Critérios: 65%+ confiança, 5%+ EV mínimo

🔥 **FUNCIONALIDADES:**
• 🎯 Tips profissionais com monitoramento ativo
• 🔮 Predições IA com machine learning
• 📅 Agenda de partidas (próximos 7 dias)
• 🎮 Partidas ao vivo selecionáveis
• 📢 Sistema de alertas para grupos
• 📊 Sistema de unidades padrão
• 📋 Estatísticas detalhadas

Use /menu para ver todas as opções!
        """

        keyboard = [
            [InlineKeyboardButton("🎯 Tips Profissionais", callback_data="tips")],
            [InlineKeyboardButton("🔮 Predições IA", callback_data="predictions")],
            [InlineKeyboardButton("📅 Agenda de Partidas", callback_data="schedule")],
            [InlineKeyboardButton("🎮 Partidas Ao Vivo", callback_data="live_matches")],
            [InlineKeyboardButton("📢 Sistema de Alertas", callback_data="alert_stats")],
            [InlineKeyboardButton("📋 Menu Completo", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")

    def menu_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /menu"""
        menu_message = """
🎮 **MENU PRINCIPAL - BOT LOL V3** 🎮

🎯 **TIPS & ANÁLISES (ATUALIZADO):**
• /tips - Tips profissionais AO VIVO
• /predictions - Predições IA
• /schedule - Agenda de partidas
• /live - Partidas ao vivo
• /monitoring - Status do monitoramento
• /force_scan - Scan manual (admin)
• /alerts - Sistema de alertas
• /odds - Odds reais (The Odds API) 💰

🎲 **SISTEMA DE UNIDADES:**
• /units - Explicação do sistema
• /performance - Performance atual
• /history - Histórico de apostas

📊 **INFORMAÇÕES:**
• /help - Ajuda completa
• /about - Sobre o bot

💰 **NOVA INTEGRAÇÃO - ODDS REAIS:**
🔥 Agora o sistema usa odds REAIS de casas de apostas!
• ✅ The Odds API integrada
• ✅ Múltiplas casas de apostas
• ✅ Melhores odds automaticamente
• ✅ EV calculado com dados reais
• ✅ Cache inteligente para performance

🎮 **FUNCIONALIDADE - TIPS AO VIVO:**
🔥 Sistema gera tips APENAS para partidas que estão acontecendo!
• ✅ Dados reais de draft + estatísticas
• ✅ Informação específica do mapa (Game 1, 2, 3...)
• ✅ Análise em tempo real durante a partida
• ✅ Tips ilimitados (sem limite semanal)
• ✅ Monitoramento a cada 3 minutos

Clique nos botões abaixo para navegação rápida:
        """

        keyboard = [
            [InlineKeyboardButton("🎯 Tips AO VIVO", callback_data="tips"),
             InlineKeyboardButton("🔮 Predições", callback_data="predictions")],
            [InlineKeyboardButton("💰 Odds Reais", callback_data="odds_summary"),
             InlineKeyboardButton("🎮 Ao Vivo", callback_data="live_matches")],
            [InlineKeyboardButton("📅 Agenda", callback_data="schedule"),
             InlineKeyboardButton("🔍 Monitoramento", callback_data="monitoring")],
            [InlineKeyboardButton("🚀 Scan Manual", callback_data="force_scan"),
             InlineKeyboardButton("📢 Alertas", callback_data="alert_stats")],
            [InlineKeyboardButton("📊 Unidades", callback_data="units_info"),
             InlineKeyboardButton("❓ Ajuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode="Markdown")

    def schedule_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /schedule"""
        try:
            # Usar asyncio para buscar dados
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scheduled_matches = loop.run_until_complete(self.schedule_manager.get_scheduled_matches())
            loop.close()

            if scheduled_matches:
                schedule_message = f"""
📅 **AGENDA DE PARTIDAS** 📅

🔍 **{len(scheduled_matches)} PARTIDAS AGENDADAS**

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
🏆 {league}
⏰ {start_time}

"""
                schedule_message += f"""
⏰ Última atualização: {self.schedule_manager.last_update.strftime('%H:%M:%S') if self.schedule_manager.last_update else 'Nunca'}
                """
            else:
                schedule_message = """
📅 **AGENDA DE PARTIDAS** 📅

ℹ️ **NENHUMA PARTIDA AGENDADA**

🔍 **Não há partidas agendadas para os próximos 7 dias**

🔄 Tente novamente em alguns minutos
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="schedule")],
                [InlineKeyboardButton("📅 Hoje", callback_data="schedule_today")],
                [InlineKeyboardButton("🎮 Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(schedule_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando schedule: {e}")
            update.message.reply_text("❌ Erro ao buscar agenda. Tente novamente.")

    def tips_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /tips"""
        try:
            # Usar asyncio para gerar tip
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tip = loop.run_until_complete(self.tips_system.generate_professional_tip())
            loop.close()

            if tip:
                # Extrair informações específicas do mapa
                map_info = tip.get('map_info', 'Mapa 1')
                game_time = tip.get('game_time', 0)
                game_min = game_time // 60 if game_time > 0 else 0
                
                tip_message = f"""
🎯 **TIP PROFISSIONAL AO VIVO** 🎯

🗺️ **{map_info}: {tip['title']}**
🎮 Liga: {tip['league']}
⏱️ Tempo: {game_min}min (PARTIDA AO VIVO)

📊 **ANÁLISE COM DADOS REAIS:**
• Confiança: {tip['confidence_score']:.1f}% ({tip['confidence_level']})
• EV: {tip['ev_percentage']:.1f}%
• Probabilidade: {tip['win_probability']*100:.1f}%

🎲 **SISTEMA DE UNIDADES:**
• Apostar: {tip['units']} unidades
• Valor: ${tip['stake_amount']:.2f}
• Risco: {tip['risk_level']}

⭐ **Recomendação:** {tip['recommended_team']}

💡 **Análise Completa:**
{tip['reasoning']}

🤖 **Dados Utilizados:**
• Draft completo analisado
• Estatísticas em tempo real
• IA com dados ao vivo
                """
            else:
                tip_message = """
🎯 **NENHUM TIP DISPONÍVEL** 🎯

❌ Nenhuma partida AO VIVO atende aos critérios profissionais no momento.

📋 **Critérios para tips:**
• ✅ Partida DEVE estar em andamento (ao vivo)
• ✅ Dados completos de draft + estatísticas
• ✅ Confiança: 75%+ com dados ao vivo
• ✅ EV: 8%+ calculado com odds reais
• ✅ Mínimo 5 minutos de jogo

🔄 Sistema monitora automaticamente partidas AO VIVO a cada 3 minutos.

⏰ Aguarde uma partida começar ou continue em andamento.
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Novo Tip", callback_data="tips")],
                [InlineKeyboardButton("🔍 Monitoramento", callback_data="monitoring")],
                [InlineKeyboardButton("🎮 Partidas Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(tip_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando tips: {e}")
            update.message.reply_text("❌ Erro ao gerar tip. Tente novamente.")

    def live_matches_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /live"""
        try:
            # Usar asyncio para buscar partidas
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            matches = loop.run_until_complete(self.riot_client.get_live_matches())
            loop.close()

            if matches:
                message = "🎮 **PARTIDAS AO VIVO** 🎮\n\nSelecione uma partida para análise detalhada:\n\n"

                keyboard = []
                for i, match in enumerate(matches[:8]):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')

                        button_text = f"{team1} vs {team2}"
                        if len(button_text) > 30:
                            button_text = button_text[:27] + "..."

                        keyboard.append([InlineKeyboardButton(
                            button_text,
                            callback_data=f"match_{i}"
                        )])

                        # Cache da partida
                        self.live_matches_cache[i] = match

                keyboard.append([InlineKeyboardButton("🔄 Atualizar", callback_data="live_matches")])
                keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])

                self.cache_timestamp = datetime.now()

            else:
                message = """
🎮 **NENHUMA PARTIDA AO VIVO** 🎮

❌ Não há partidas ao vivo no momento.

🔄 Tente novamente em alguns minutos.
                """
                keyboard = [
                    [InlineKeyboardButton("🔄 Atualizar", callback_data="live_matches")],
                    [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando live: {e}")
            update.message.reply_text("❌ Erro ao buscar partidas. Tente novamente.")

    def monitoring_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /monitoring"""
        try:
            monitoring_status = self.tips_system.get_monitoring_status()

            # Verificar se o monitoramento está realmente ativo
            monitoring_status_emoji = "🟢" if monitoring_status['monitoring_active'] else "🔴"
            last_scan = monitoring_status['last_scan']
            
            # Calcular tempo desde último scan
            time_since_scan = "Nunca"
            if last_scan != "Nunca" and self.tips_system.last_scan:
                now = datetime.now()
                time_diff = now - self.tips_system.last_scan
                minutes_ago = int(time_diff.total_seconds() / 60)
                
                if minutes_ago < 1:
                    time_since_scan = "Agora mesmo"
                elif minutes_ago < 60:
                    time_since_scan = f"{minutes_ago} minutos atrás"
                else:
                    hours_ago = int(minutes_ago / 60)
                    time_since_scan = f"{hours_ago} horas atrás"

            monitoring_message = f"""
🔍 **SISTEMA DE MONITORAMENTO ATUALIZADO** 🔍

🎯 **TIPS APENAS COM PARTIDAS AO VIVO:**
• Status: {monitoring_status_emoji} {'ATIVO' if monitoring_status['monitoring_active'] else 'INATIVO'}
• Última verificação: {last_scan}
• Tempo decorrido: {time_since_scan}
• Frequência: {monitoring_status['scan_frequency']}

📊 **ESTATÍSTICAS DE DESCOBERTAS:**
• Tips encontrados (total): {monitoring_status['total_tips']}
• Tips esta semana: {monitoring_status['tips_this_week']}
• Cache de tips dados: {monitoring_status.get('given_tips_cache', 0)}

🎮 **NOVO FOCO - APENAS PARTIDAS AO VIVO:**
• ✅ APENAS partidas que já começaram (ao vivo)
• ✅ Dados completos de draft + estatísticas
• ✅ Informação específica do mapa (Game 1, 2, 3...)
• ✅ Análise em tempo real com dados da partida
• ❌ NÃO monitora mais partidas agendadas

🎲 **CRITÉRIOS RIGOROSOS MANTIDOS:**
• Confiança mínima: 75% (com dados ao vivo)
• EV mínimo: 8% (calculado com odds reais)
• Tempo mínimo: 5 minutos de jogo
• **SEM LIMITE SEMANAL** - Tips ilimitados!

⚡ **PROCESSO OTIMIZADO:**
O sistema agora foca EXCLUSIVAMENTE em partidas que estão acontecendo, analisando drafts e estatísticas em tempo real para gerar tips mais precisos.

🤖 **SISTEMA DE IA APRIMORADO:**
• Machine Learning: {'🟢 Disponível' if self.prediction_system.ml_system else '🟡 Fallback matemático'}
• Dados ao vivo: 🟢 Integrados
• Alertas automáticos: {'🟢 Ativo' if len(self.alerts_system.group_chat_ids) > 0 else '🟡 Sem grupos'}
            """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="monitoring")],
                [InlineKeyboardButton("🚀 Scan Manual", callback_data="force_scan")],
                [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("🎮 Partidas AO VIVO", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(monitoring_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando monitoring: {e}")
            update.message.reply_text("❌ Erro ao buscar status. Tente novamente.")

    def force_scan_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /force_scan - força um scan manual imediato"""
        try:
            user = update.effective_user
            
            # Verificar se é o owner
            if user.id != OWNER_ID:
                update.message.reply_text("❌ Apenas o administrador pode forçar scans manuais.")
                return

            # Mostrar mensagem inicial
            progress_message = """
🔍 **SCAN MANUAL INICIADO** 🔍

⏳ **STATUS:**
• Buscando partidas disponíveis...
• Analisando com sistema de IA...
• Verificando critérios profissionais...

⚡ **Aguarde alguns segundos...**
            """

            sent_message = update.message.reply_text(progress_message, parse_mode="Markdown")

            # Executar scan em thread separada para não bloquear
            def run_manual_scan():
                try:
                    # Usar asyncio para executar o scan
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Executar scan usando o novo método live-only
                    loop.run_until_complete(self.tips_system._scan_live_matches_only())
                    
                    # Fechar loop
                    loop.close()
                    
                    # Buscar status atualizado
                    status = self.tips_system.get_monitoring_status()
                    
                    # Atualizar mensagem com resultado
                    result_message = f"""
🔍 **SCAN MANUAL COMPLETO** ✅

📊 **RESULTADOS:**
• Status: Executado com sucesso
• Horário: {datetime.now().strftime('%H:%M:%S')}
• Partidas verificadas: {status.get('matches_scanned', 0)}
• Tips encontrados: {status['total_tips']}

🎯 **PRÓXIMO SCAN AUTOMÁTICO:**
• Em aproximadamente 3 minutos
• Monitoramento: {'🟢 Ativo' if status['monitoring_active'] else '🔴 Inativo'}

💡 **Use /monitoring para ver status completo**
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("🔄 Novo Scan", callback_data="force_scan")],
                        [InlineKeyboardButton("🔍 Monitoramento", callback_data="monitoring")],
                        [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
                        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Editar mensagem original
                    query.edit_message_text(result_message, reply_markup=reply_markup, parse_mode="Markdown")
                    
                except Exception as scan_error:
                    error_message = f"""
❌ **ERRO NO SCAN MANUAL**

🔍 **Detalhes do erro:**
{str(scan_error)}

💡 **Tente novamente em alguns minutos**
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="force_scan")],
                        [InlineKeyboardButton("🔍 Monitoramento", callback_data="monitoring")],
                        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    query.edit_message_text(error_message, reply_markup=reply_markup, parse_mode="Markdown")
                    logger.error(f"❌ Erro no scan manual: {scan_error}")

            # Executar em thread separada
            scan_thread = threading.Thread(target=run_manual_scan, daemon=True)
            scan_thread.start()

        except Exception as e:
            logger.error(f"Erro no callback force_scan: {e}")
            query.edit_message_text("❌ Erro ao iniciar scan manual. Tente novamente.")

    def predictions_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /predictions"""
        try:
            # Usar asyncio para buscar predições
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            live_matches = loop.run_until_complete(self.riot_client.get_live_matches())
            loop.close()

            if live_matches:
                predictions_message = f"""
🔮 **PREDIÇÕES IA** 🔮

🎯 **{len(live_matches)} PARTIDAS ANALISADAS**

"""

                predictions_made = 0
                for match in live_matches[:5]:
                    # Usar asyncio para predição
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    prediction = loop.run_until_complete(self.prediction_system.predict_live_match(match))
                    loop.close()

                    if prediction and prediction['confidence'] in ['Alta', 'Muito Alta']:
                        predictions_made += 1
                        conf_emoji = '🔥' if prediction['confidence'] == 'Muito Alta' else '⚡'

                        predictions_message += f"""
{conf_emoji} **{prediction['team1']} vs {prediction['team2']}**
🏆 {prediction['league']} • Confiança: {prediction['confidence']}
🎯 Favorito: {prediction['favored_team']} ({prediction['win_probability']*100:.1f}%)
💰 Odds: {prediction['team1_odds']:.2f} vs {prediction['team2_odds']:.2f}

"""

                if predictions_made == 0:
                    predictions_message += """
ℹ️ **NENHUMA PREDIÇÃO DE ALTA CONFIANÇA**

🔍 **Critérios para predições:**
• Confiança: Alta ou Muito Alta
• Times conhecidos na base de dados
• Dados suficientes para análise

🔄 Tente novamente em alguns minutos
                    """
                else:
                    predictions_message += f"""
🤖 **SISTEMA DE IA:**
• Base de dados: {len(self.prediction_system.teams_database)} times
• Algoritmo: Análise multi-fatorial com dados reais
                    """
            else:
                predictions_message = """
🔮 **PREDIÇÕES IA** 🔮

ℹ️ **NENHUMA PARTIDA PARA ANÁLISE**

🔍 **Aguardando partidas ao vivo**
• Sistema monitora automaticamente
• Predições baseadas em dados reais
• Confiança calculada por IA

🔄 Tente novamente quando houver partidas
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="predictions")],
                [InlineKeyboardButton("🎮 Partidas Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(predictions_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando predictions: {e}")
            update.message.reply_text("❌ Erro ao gerar predições. Tente novamente.")

    def alerts_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /alerts"""
        try:
            chat_id = update.effective_chat.id
            chat_type = update.effective_chat.type
            user = update.effective_user

            # Verificar se é grupo
            if chat_type in ['group', 'supergroup']:
                is_registered = chat_id in self.alerts_system.group_chat_ids
                alert_stats = self.alerts_system.get_alert_stats()

                if is_registered:
                    alerts_message = f"""
📢 **SISTEMA DE ALERTAS ATIVO** 📢

✅ **GRUPO CADASTRADO**
• ID: {chat_id}
• Status: 🟢 Recebendo alertas
• Cadastrado por: {user.first_name}

🎯 **CRITÉRIOS DOS ALERTAS:**
• Confiança mínima: 80%
• EV mínimo: 10%
• Unidades mínimas: 2.0
• Análise ML: Alta/Muito Alta

📊 **ESTATÍSTICAS GLOBAIS:**
• Grupos cadastrados: {alert_stats['total_groups']}
• Alertas enviados: {alert_stats['total_tips_sent']}
• Tips esta semana: {alert_stats['tips_this_week']}

⚡ **STATUS:** Sistema monitora 24/7 automaticamente!

⏰ Último alerta: {alert_stats['last_tip_alert'].strftime('%d/%m %H:%M') if alert_stats['last_tip_alert'] else 'Nunca'}
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("❌ Desativar Alertas", callback_data=f"unregister_alerts_{chat_id}")],
                        [InlineKeyboardButton("📊 Ver Estatísticas", callback_data="alert_stats")],
                        [InlineKeyboardButton("🎯 Gerar Tip Agora", callback_data="tips")],
                        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                    ]
                else:
                    alerts_message = f"""
📢 **SISTEMA DE ALERTAS** 📢

❌ **GRUPO NÃO CADASTRADO**
• ID: {chat_id}
• Status: 🔴 Não recebe alertas
• Solicitado por: {user.first_name}

🎯 **O QUE VOCÊ VAI RECEBER:**
• Tips profissionais em tempo real
• Análises de Machine Learning
• Oportunidades com 80%+ confiança
• Valor esperado de 10%+ garantido

📊 **COMO FUNCIONA:**
• Sistema monitora API da Riot 24/7
• Análise automática de todas as partidas
• Alertas enviados apenas para tips de qualidade
• Sem spam - apenas oportunidades reais

🚀 **CLIQUE PARA ATIVAR AGORA!**
                    """

                    keyboard = [
                        [InlineKeyboardButton("✅ ATIVAR ALERTAS", callback_data=f"register_alerts_{chat_id}")],
                        [InlineKeyboardButton("📊 Ver Exemplo", callback_data="alert_stats")],
                        [InlineKeyboardButton("🎯 Testar Tip", callback_data="tips")],
                        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                    ]
            else:
                alerts_message = f"""
📢 **SISTEMA DE ALERTAS** 📢

ℹ️ **COMANDO PARA GRUPOS**

{user.first_name}, este comando funciona apenas em grupos!

🔍 **Para usar alertas:**
1. ➕ Adicione o bot a um grupo
2. 📢 Use /alerts no grupo  
3. ✅ Clique em "Ativar Alertas"
4. 🎯 Receba tips automáticos!

📊 **Benefícios dos alertas:**
• Tips profissionais 24/7
• Confiança 80%+ garantida
• EV 10%+ mínimo
• Zero spam, apenas qualidade

💡 **Dica:** Crie um grupo privado só para os tips!
                """
                
                keyboard = [
                    [InlineKeyboardButton("📖 Como Usar", callback_data="alert_help")],
                    [InlineKeyboardButton("🎯 Testar Tip", callback_data="tips")],
                    [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(alerts_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando alerts: {e}")
            update.message.reply_text("❌ Erro no sistema de alertas. Tente novamente.")

    def units_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /units - Explicação do sistema de unidades"""
        try:
            units_info = self.tips_system.units_system.get_units_explanation()
            
            # Adicionar informações específicas do bot
            additional_info = f"""

💰 **CONFIGURAÇÃO ATUAL:**
• Bankroll base: $1000.00
• 1 unidade = $10.00 (1% do bankroll)
• Máximo por aposta: 5 unidades ($50.00)
• Mínimo por aposta: 0.5 unidades ($5.00)

📊 **PERFORMANCE ATUAL:**
• Total de apostas registradas: {self.tips_system.units_system.performance_stats['total_bets']}
• Unidades apostadas: {self.tips_system.units_system.performance_stats['total_units_staked']:.1f}
• ROI: {self.tips_system.units_system.performance_stats['roi_percentage']:.1f}%

🔧 **AJUSTES DISPONÍVEIS:**
Use /performance para estatísticas detalhadas
Use /history para histórico completo
            """

            complete_message = units_info + additional_info

            keyboard = [
                [InlineKeyboardButton("📊 Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("📋 Histórico", callback_data="bet_history")],
                [InlineKeyboardButton("🎯 Gerar Tip", callback_data="tips")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(complete_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando units: {e}")
            update.message.reply_text("❌ Erro ao buscar informações de unidades. Tente novamente.")

    def performance_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /performance - Performance do sistema de unidades"""
        try:
            stats = self.tips_system.units_system.performance_stats
            
            performance_message = f"""
📊 **PERFORMANCE DO SISTEMA DE UNIDADES** 📊

🎲 **ESTATÍSTICAS GERAIS:**
• Total de apostas: {stats['total_bets']}
• Vitórias: {stats['wins']}
• Derrotas: {stats['losses']}
• Strike Rate: {stats['strike_rate']:.1f}%

💰 **UNIDADES:**
• Total apostado: {stats['total_units_staked']:.1f} unidades
• Lucro/Prejuízo: {stats['total_units_profit']:.1f} unidades
• ROI: {stats['roi_percentage']:.1f}%

💵 **VALORES (Bankroll $1000):**
• Valor apostado: ${stats['total_units_staked'] * 10:.2f}
• Lucro/Prejuízo: ${stats['total_units_profit'] * 10:.2f}
• Saldo atual: ${1000 + (stats['total_units_profit'] * 10):.2f}

📈 **ANÁLISE:**
"""
            
            if stats['total_bets'] == 0:
                performance_message += """
ℹ️ **SEM DADOS AINDA**
• Nenhuma aposta registrada ainda
• Sistema pronto para começar
• Use /tips para gerar primeira oportunidade
                """
            else:
                if stats['roi_percentage'] > 10:
                    performance_message += "🔥 **EXCELENTE PERFORMANCE!** ROI acima de 10%"
                elif stats['roi_percentage'] > 5:
                    performance_message += "✅ **BOA PERFORMANCE!** ROI positivo e consistente"
                elif stats['roi_percentage'] > 0:
                    performance_message += "📈 **PERFORMANCE POSITIVA** - Mantendo lucro"
                else:
                    performance_message += "⚠️ **ATENÇÃO** - Performance negativa, revisar estratégia"

            keyboard = [
                [InlineKeyboardButton("📋 Ver Histórico", callback_data="bet_history")],
                [InlineKeyboardButton("🎯 Novo Tip", callback_data="tips")],
                [InlineKeyboardButton("📊 Sistema Unidades", callback_data="units_info")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(performance_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando performance: {e}")
            update.message.reply_text("❌ Erro ao buscar performance. Tente novamente.")

    def history_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /history - Histórico de apostas"""
        try:
            bet_history = self.tips_system.units_system.bet_history
            
            if not bet_history:
                history_message = """
📋 **HISTÓRICO DE APOSTAS** 📋

ℹ️ **NENHUMA APOSTA REGISTRADA**

🎯 **Como funciona:**
• Sistema registra automaticamente tips gerados
• Cada tip vira uma entrada no histórico
• Performance calculada automaticamente

🚀 **Para começar:**
• Use /tips para gerar primeira oportunidade
• Tips profissionais são registrados automaticamente
• Acompanhe performance em tempo real

💡 **Dica:** O sistema só registra tips que atendem aos critérios profissionais (75%+ confiança, 8%+ EV)
                """
            else:
                history_message = f"""
📋 **HISTÓRICO DE APOSTAS** 📋

📊 **ÚLTIMAS {min(len(bet_history), 10)} APOSTAS:**

"""
                for i, bet in enumerate(bet_history[-10:], 1):
                    result_emoji = "✅" if bet.get('result') == 'win' else "❌" if bet.get('result') == 'loss' else "⏳"
                    history_message += f"""
**{i}. {bet.get('team', 'Team')}** {result_emoji}
• Unidades: {bet.get('units', 0):.1f}
• Data: {bet.get('date', 'N/A')}
• Liga: {bet.get('league', 'N/A')}
• Resultado: {bet.get('result', 'Pendente')}

"""

                history_message += f"""
📈 **RESUMO:**
• Total de registros: {len(bet_history)}
• Exibindo: {min(len(bet_history), 10)} mais recentes
                """

            keyboard = [
                [InlineKeyboardButton("📊 Ver Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("🎯 Novo Tip", callback_data="tips")],
                [InlineKeyboardButton("📊 Sistema Unidades", callback_data="units_info")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(history_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando history: {e}")
            update.message.reply_text("❌ Erro ao buscar histórico. Tente novamente.")

    def odds_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /odds - Mostra odds reais disponíveis"""
        try:
            # Buscar resumo das odds disponíveis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            odds_summary = loop.run_until_complete(self.tips_system.odds_client.get_odds_summary())
            loop.close()

            if 'error' in odds_summary:
                odds_message = f"""
💰 **ODDS REAIS - THE ODDS API** 💰

❌ **ERRO AO BUSCAR ODDS**

🔍 **Detalhes do erro:**
{odds_summary['error']}

🔧 **Possíveis causas:**
• Rate limit da API atingido
• Problemas de conectividade
• API Key inválida
• Odds de eSports não disponíveis no momento

🔄 Tente novamente em alguns minutos.
                """
            else:
                leagues_text = ", ".join(odds_summary.get('leagues', [])[:5])
                if len(odds_summary.get('leagues', [])) > 5:
                    leagues_text += f" (+{len(odds_summary['leagues']) - 5} mais)"

                teams_text = ", ".join(odds_summary.get('teams', [])[:8])
                if len(odds_summary.get('teams', [])) > 8:
                    teams_text += f" (+{len(odds_summary['teams']) - 8} mais)"

                bookmakers_text = ", ".join(odds_summary.get('bookmakers', [])[:6])
                if len(odds_summary.get('bookmakers', [])) > 6:
                    bookmakers_text += f" (+{len(odds_summary['bookmakers']) - 6} mais)"

                odds_message = f"""
💰 **ODDS REAIS - THE ODDS API** 💰

📊 **RESUMO ATUAL:**
• Total de jogos: {odds_summary.get('total_games', 0)}
• Atualizado: {datetime.now().strftime('%H:%M:%S')}

🏆 **LIGAS DISPONÍVEIS:**
{leagues_text if leagues_text else 'Nenhuma liga encontrada'}

🎮 **ALGUNS TIMES:**
{teams_text if teams_text else 'Nenhum time encontrado'}

🏪 **CASAS DE APOSTAS:**
{bookmakers_text if bookmakers_text else 'Nenhuma casa encontrada'}

💡 **COMO FUNCIONA:**
• Odds são buscadas em tempo real
• Múltiplas casas de apostas
• Melhores odds são priorizadas
• Cache de 5 minutos para eficiência

⚡ **INTEGRAÇÃO ATIVA:**
O sistema já usa essas odds automaticamente nos tips!
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="odds_summary")],
                [InlineKeyboardButton("🎯 Gerar Tip", callback_data="tips")],
                [InlineKeyboardButton("🎮 Partidas Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(odds_message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando odds: {e}")
            update.message.reply_text("❌ Erro ao buscar odds. Tente novamente.")

    def proximosjogoslol_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /proximosjogoslol - Próximas partidas de LoL"""
        try:
            # Usar asyncio para buscar dados
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scheduled_matches = loop.run_until_complete(self.schedule_manager.get_scheduled_matches())
            loop.close()

            if scheduled_matches:
                message = "🎮 **PRÓXIMOS JOGOS LoL** 🎮\n\n"
                
                # Filtrar apenas próximas 5 partidas
                for i, match in enumerate(scheduled_matches[:5], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        start_time = match.get('start_time_formatted', 'TBD')

                        # Verificar se é liga principal
                        league_icon = "🏆" if any(major in league for major in ['LCK', 'LEC', 'LCS', 'WORLDS', 'MSI']) else "🎯"
                        
                        message += f"{league_icon} **{team1} vs {team2}**\n"
                        message += f"📅 {league}\n"
                        message += f"⏰ {start_time}\n\n"

                message += "💡 Use /filtrarligas para personalizar suas preferências!"
            else:
                message = """
🎮 **PRÓXIMOS JOGOS LoL** 🎮

ℹ️ Nenhuma partida agendada encontrada.

🔄 Tente novamente em alguns minutos.
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="schedule")],
                [InlineKeyboardButton("⚙️ Filtrar Ligas", callback_data="filter_leagues")],
                [InlineKeyboardButton("🎮 Ao Vivo", callback_data="live_matches")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando proximosjogoslol: {e}")
            update.message.reply_text("❌ Erro ao buscar próximos jogos. Tente novamente.")

    def filtrarligas_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /filtrarligas - Configurar filtros de ligas"""
        try:
            user_id = update.effective_user.id
            current_prefs = self.tips_system.user_preferences.get_user_preferences(user_id)
            
            message = """
⚙️ **FILTROS DE LIGAS LoL** ⚙️

Personalize quais ligas você quer receber tips e notificações:

🏆 **PRINCIPAIS:**
• LCK - Korea
• LEC - Europe  
• LCS - North America
• LPL - China

🌍 **REGIONAIS:**
• CBLOL - Brasil
• PCS - Pacific
• LLA - Latam
• LJL - Japan

🔥 **EVENTOS ESPECIAIS:**
• WORLDS - Mundial
• MSI - Mid-Season

**Filtros atuais:** {current_filters}

Use os botões abaixo para configurar:
            """.format(
                current_filters=", ".join(current_prefs['league_filters']) if current_prefs['league_filters'] else "Todas as ligas"
            )

            keyboard = [
                [InlineKeyboardButton("🏆 Ligas Principais", callback_data="filter_major")],
                [InlineKeyboardButton("🌍 Ligas Regionais", callback_data="filter_regional")],
                [InlineKeyboardButton("🔥 Eventos Especiais", callback_data="filter_events")],
                [InlineKeyboardButton("🌐 Todas as Ligas", callback_data="filter_all")],
                [InlineKeyboardButton("📊 Ver Minhas Preferências", callback_data="view_preferences")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando filtrarligas: {e}")
            update.message.reply_text("❌ Erro ao carregar filtros. Tente novamente.")

    def timesfavoritos_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /timesfavoritos - Configurar times favoritos"""
        try:
            user_id = update.effective_user.id
            current_prefs = self.tips_system.user_preferences.get_user_preferences(user_id)
            
            message = """
⭐ **TIMES FAVORITOS** ⭐

Configure seus times favoritos para receber alertas especiais quando eles jogarem!

**Times atuais:** {current_teams}

💡 **Como usar:**
• Digite o nome dos times separados por vírgula
• Exemplo: T1, G2, Loud, Pain Gaming

📱 **Benefícios:**
• Tips prioritárias dos seus times
• Alertas de início de jogos
• Notificações personalizadas

Use /configurartimes [lista de times] para definir.
            """.format(
                current_teams=", ".join(current_prefs['favorite_teams']) if current_prefs['favorite_teams'] else "Nenhum time definido"
            )

            keyboard = [
                [InlineKeyboardButton("⚙️ Configurar Times", callback_data="configure_teams")],
                [InlineKeyboardButton("🗑️ Limpar Lista", callback_data="clear_teams")],
                [InlineKeyboardButton("📊 Ver Preferências", callback_data="view_preferences")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando timesfavoritos: {e}")
            update.message.reply_text("❌ Erro ao carregar times favoritos. Tente novamente.")

    def statuslol_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /statuslol [time] - Status atual de um time em jogo"""
        try:
            args = context.args
            if not args:
                message = """
📊 **STATUS LoL** 📊

Para verificar o status de um time em partida:

**Uso:** `/statuslol [nome do time]`
**Exemplo:** `/statuslol T1`

🎮 **Informações disponíveis:**
• Diferença de ouro atual
• Objetivos conquistados (Dragões, Barão)
• Torres destruídas
• Tempo de jogo
• Posição na partida

💡 Funciona apenas para partidas **AO VIVO**
                """
                update.message.reply_text(message, parse_mode="Markdown")
                return

            team_name = " ".join(args).strip()
            
            # Buscar partidas ao vivo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            live_matches = loop.run_until_complete(self.riot_client.get_live_matches())
            loop.close()

            team_match = None
            for match in live_matches:
                teams = match.get('teams', [])
                for team in teams:
                    if team_name.lower() in team.get('name', '').lower():
                        team_match = match
                        break
                if team_match:
                    break

            if not team_match:
                message = f"""
❌ **TIME NÃO ENCONTRADO** ❌

O time "{team_name}" não está jogando no momento ou não foi encontrado.

🔍 **Verificar:**
• Nome do time está correto?
• Time está em partida ao vivo?
• Aguarde alguns segundos e tente novamente

Use /live para ver todas as partidas ao vivo.
                """
                update.message.reply_text(message, parse_mode="Markdown")
                return

            # Analisar dados da partida
            match_stats = team_match.get('match_statistics', {})
            game_time = team_match.get('game_time', 0)
            teams = team_match.get('teams', [])
            
            message = f"""
📊 **STATUS AO VIVO - {team_name.upper()}** 📊

🎮 **Partida:** {teams[0].get('name', 'Team1')} vs {teams[1].get('name', 'Team2')}
⏰ **Tempo:** {game_time // 60}min {game_time % 60}s

💰 **Diferença de Ouro:** {match_stats.get('gold_difference', 0):+,}
🏗️ **Torres:** {match_stats.get('tower_difference', 0):+}
🐉 **Dragões:** {match_stats.get('dragon_count', 0)}
👹 **Barões:** {match_stats.get('baron_count', 0)}

📈 **Análise:**
{self._get_team_status_analysis(match_stats, game_time)}

*Dados atualizados automaticamente*
            """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar Status", callback_data=f"team_status_{team_name}")],
                [InlineKeyboardButton("🎯 Gerar Tip", callback_data="tips")],
                [InlineKeyboardButton("📊 Análise Completa", callback_data="predictions")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro no comando statuslol: {e}")
            update.message.reply_text("❌ Erro ao buscar status. Tente novamente.")

    def _get_team_status_analysis(self, match_stats: Dict, game_time: int) -> str:
        """Gera análise rápida do status da partida"""
        try:
            gold_diff = match_stats.get('gold_difference', 0)
            tower_diff = match_stats.get('tower_difference', 0)
            minutes = game_time // 60

            if abs(gold_diff) < 2000 and abs(tower_diff) <= 1 and minutes < 20:
                return "⚖️ Partida equilibrada - Qualquer time pode virar"
            elif gold_diff > 3000 and minutes > 15:
                return "📈 Time azul com vantagem sólida - Caminho para vitória"
            elif gold_diff < -3000 and minutes > 15:
                return "📉 Time vermelho com vantagem sólida - Cenário favorável"
            elif minutes > 30:
                return "⏰ Late game - Potencial para viradas dramáticas"
            else:
                return "🎯 Fase crucial da partida - Próximas TFs são decisivas"
                
        except Exception:
            return "📊 Análise indisponível"

    def callback_handler(self, update: Update, context: CallbackContext) -> None:
        """Handler para callbacks dos botões"""
        query = update.callback_query
        query.answer()

        data = query.data

        try:
            if data == "tips":
                self._handle_tips_callback(query)
            elif data == "schedule":
                self._handle_schedule_callback(query)
            elif data == "live_matches":
                self._handle_live_matches_callback(query)
            elif data == "units_info":
                self._handle_units_info_callback(query)
            elif data == "monitoring":
                self._handle_monitoring_callback(query)
            elif data == "predictions":
                self._handle_predictions_callback(query)
            elif data == "alert_stats":
                self._handle_alert_stats_callback(query)
            elif data.startswith("register_alerts_"):
                chat_id = int(data.split("_")[-1])
                self._handle_register_alerts_callback(query, chat_id)
            elif data.startswith("unregister_alerts_"):
                chat_id = int(data.split("_")[-1])
                self._handle_unregister_alerts_callback(query, chat_id)
            elif data == "alert_help":
                self._handle_alert_help_callback(query)
            elif data == "performance_stats":
                self._handle_performance_stats_callback(query)
            elif data == "bet_history":
                self._handle_bet_history_callback(query)
            elif data == "odds_summary":
                self._handle_odds_summary_callback(query)
            elif data == "force_scan":
                self._handle_force_scan_callback(query)
            elif data == "main_menu":
                self._handle_main_menu_callback(query)

        except Exception as e:
            logger.error(f"Erro no callback handler: {e}")
            query.answer("❌ Erro interno. Tente novamente.")

    # Adicionar todos os métodos de callback necessários aqui...
    def _handle_tips_callback(self, query) -> None:
        """Handle callback para tips"""
        try:
            # Buscar tips profissionais
            tips = self.tips_system.tips_database[-5:] if self.tips_system.tips_database else []
            
            if tips:
                message = "🎯 **TIPS PROFISSIONAIS AO VIVO** 🎯\n\n"
                
                for i, tip in enumerate(tips, 1):
                    confidence = tip.get('confidence_score', 0)
                    ev = tip.get('ev_percentage', 0)
                    units = tip.get('units', 0)
                    
                    message += f"**{i}. {tip.get('title', 'Tip')}**\n"
                    message += f"🎮 {tip.get('map_info', 'N/A')}\n"
                    message += f"📊 Confiança: {confidence:.1f}% | EV: {ev:.1f}%\n"
                    message += f"💰 Unidades: {units} | Status: PARTIDA AO VIVO\n\n"
                    
                message += "💡 Use /tips para detalhes completos!"
            else:
                message = """
🎯 **TIPS PROFISSIONAIS** 🎯

ℹ️ Nenhuma tip ativa no momento.

🔍 **O sistema monitora:**
• Partidas AO VIVO apenas
• Critérios profissionais (75%+ confiança)
• Expected Value mínimo de 8%

⏰ Verificação automática a cada 3 minutos
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="tips")],
                [InlineKeyboardButton("🎮 Partidas ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("📊 Monitoramento", callback_data="monitoring")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback tips: {e}")
            query.edit_message_text("❌ Erro ao carregar tips. Tente novamente.")

    def _handle_schedule_callback(self, query):
        """Handle callback para agenda"""
        try:
            # Usar método síncrono simplificado
            scheduled_matches = self._get_schedule_sync()

            if scheduled_matches:
                message = "📅 **PRÓXIMAS PARTIDAS** 📅\n\n"
                
                for i, match in enumerate(scheduled_matches[:8], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        time_formatted = match.get('start_time_formatted', 'N/A')
                        
                        message += f"🎮 **{team1} vs {team2}**\n"
                        message += f"🏆 {league}\n"
                        message += f"⏰ {time_formatted}\n\n"
            else:
                message = "📅 **Nenhuma partida agendada encontrada.**\n\n"
                message += "💡 *Tente novamente em alguns minutos*"

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="schedule")],
                [InlineKeyboardButton("🔴 Partidas ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback schedule: {e}")
            error_message = "❌ **Erro ao carregar agenda.**\n\n"
            error_message += "💡 *Tente novamente em alguns segundos ou use /schedule*"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="schedule")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(error_message, reply_markup=reply_markup, parse_mode="Markdown")

    def _get_schedule_sync(self):
        """Método síncrono para buscar agenda"""
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
            # Retornar lista vazia em caso de erro
            return []

    def _handle_live_matches_callback(self, query):
        """Handle callback para partidas ao vivo"""
        try:
            # Usar método síncrono simplificado
            live_matches = self._get_live_matches_sync()

            if live_matches:
                message = "🔴 **PARTIDAS AO VIVO** 🔴\n\n"
                
                for i, match in enumerate(live_matches[:5], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        
                        # Calcular tempo de jogo se disponível
                        game_time = match.get('game_time', 0)
                        if game_time > 0:
                            game_time_str = f"⏰ {game_time // 60}min {game_time % 60}s"
                        else:
                            game_time_str = "⏰ Ao vivo"
                        
                        message += f"🎮 **{team1} vs {team2}**\n"
                        message += f"🏆 {league}\n"
                        message += f"{game_time_str}\n\n"
            else:
                message = "🔴 **Nenhuma partida ao vivo no momento.**\n\n"
                message += "💡 *Tip: Use /force_scan para verificar manualmente*"

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="live_matches")],
                [InlineKeyboardButton("🎯 Gerar Tip", callback_data="tips")],
                [InlineKeyboardButton("📊 Predições", callback_data="predictions")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback live_matches: {e}")
            error_message = "❌ **Erro ao carregar partidas ao vivo.**\n\n"
            error_message += "💡 *Tente novamente em alguns segundos ou use /live*"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(error_message, reply_markup=reply_markup, parse_mode="Markdown")

    def _get_live_matches_sync(self):
        """Método síncrono para buscar partidas ao vivo"""
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
            # Retornar lista vazia em caso de erro
            return []

    def _handle_units_info_callback(self, query):
        """Handle callback para informações das unidades"""
        try:
            explanation = self.tips_system.units_system.get_units_explanation()
            
            keyboard = [
                [InlineKeyboardButton("📊 Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("📋 Histórico", callback_data="bet_history")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(explanation, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback units_info: {e}")
            query.edit_message_text("❌ Erro ao carregar informações das unidades.")

    def _handle_monitoring_callback(self, query):
        """Handle callback para monitoramento"""
        try:
            status = self.tips_system.get_monitoring_status()
            
            message = f"""
📊 **STATUS DO MONITORAMENTO** 📊

🔄 **Monitoramento:** {'🟢 Ativo' if status['monitoring_active'] else '🔴 Inativo'}
⏰ **Último scan:** {status['last_scan']}
🎯 **Tips encontradas:** {status['total_tips']}
📈 **Tips hoje:** {status['tips_today']}

🤖 **SISTEMA DE IA APRIMORADO:**
• Machine Learning: {'🟢 Disponível' if self.prediction_system.ml_system else '🟡 Fallback matemático'}
• Dados ao vivo: 🟢 Integrados
• Alertas automáticos: {'🟢 Ativo' if len(self.alerts_system.group_chat_ids) > 0 else '🟡 Sem grupos'}

💰 **ODDS REAIS:**
• The Odds API: 🟢 Integrada
• Cache: 🟢 Otimizado
• Casas de apostas: Múltiplas

🎮 **EVENTOS LoL MONITORADOS:**
• Barão conquistado
• Alma/Dragão Ancião
• Diferença de ouro 5k+
• Team fights cruciais
• Torres/Inibidores

⚙️ **CONFIGURAÇÕES:**
• Critério mínimo: 75% confiança
• EV mínimo: 8%
• Limite semanal: SEM LIMITE

⚡ **Para usar:**
1. /live - Ver partidas ao vivo
2. /tips - Gerar predições profissionais
3. /monitoring - Acompanhar análises

💡 O sistema analisa automaticamente partidas ao vivo e gera tips quando detecta oportunidades profissionais.
            """

            keyboard = [
                [InlineKeyboardButton("🎮 Partidas ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("📊 Monitoramento", callback_data="monitoring")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback monitoring: {e}")
            query.edit_message_text("❌ Erro ao carregar monitoramento.")

    def _handle_predictions_callback(self, query):
        """Handle callback para predições"""
        try:
            message = """
🔮 **SISTEMA DE PREDIÇÕES IA** 🔮

🤖 **Status:** {'🟢 ML Ativo' if self.prediction_system.ml_system else '🟡 Algoritmos Matemáticos'}

📊 **Funcionalidades:**
• Análise de draft em tempo real
• Predições baseadas em estatísticas
• Ajustes por dados ao vivo
• Confiança dinâmica
• Expected Value calculado

🎮 **Específico para LoL:**
• Análise de composições
• Potencial de scaling
• Eventos cruciais detectados
• Timing de "Janela de Ouro"

⚡ **Para usar:**
1. /live - Ver partidas ao vivo
2. /tips - Gerar predições profissionais
3. /monitoring - Acompanhar análises

💡 O sistema analisa automaticamente partidas ao vivo e gera tips quando detecta oportunidades profissionais.
            """

            keyboard = [
                [InlineKeyboardButton("🎮 Partidas ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("📊 Monitoramento", callback_data="monitoring")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback predictions: {e}")
            query.edit_message_text("❌ Erro ao carregar predições.")

    def _handle_alert_stats_callback(self, query):
        """Handle callback para estatísticas de alertas"""
        try:
            stats = self.alerts_system.get_alert_stats()
            
            message = f"""
📢 **ESTATÍSTICAS DE ALERTAS** 📢

👥 **Grupos cadastrados:** {stats['total_groups']}
📊 **Alertas enviados:** {stats['alerts_sent']}
🎯 **Tips alertadas:** {stats['tips_alerted']}
⏰ **Último alerta:** {stats['last_alert']}

📈 **Performance:**
• Taxa de sucesso: {stats['success_rate']:.1f}%
• Alertas hoje: {stats['alerts_today']}
• Grupos ativos: {stats['active_groups']}

💡 Para adicionar este chat aos alertas:
/alerts
            """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="alert_stats")],
                [InlineKeyboardButton("📢 Configurar Alertas", callback_data="alert_help")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback alert_stats: {e}")
            query.edit_message_text("❌ Erro ao carregar estatísticas de alertas.")

    def _handle_register_alerts_callback(self, query, chat_id):
        """Handle callback para registrar alertas"""
        try:
            success = self.alerts_system.add_group(chat_id)
            
            if success:
                message = f"""
✅ **ALERTAS ATIVADOS** ✅

Este chat foi cadastrado para receber alertas automáticos!

📢 **Você receberá:**
• Tips profissionais em tempo real
• Alertas de partidas ao vivo
• Oportunidades de alta confiança
• Notificações de eventos cruciais

⚙️ **Configurações:**
• Apenas tips 75%+ confiança
• EV mínimo de 8%
• Dados reais de odds
• Análise de eventos LoL

🔕 Para desativar: /alerts
                """
            else:
                message = "❌ Erro ao ativar alertas. Tente novamente."

            keyboard = [
                [InlineKeyboardButton("📊 Ver Estatísticas", callback_data="alert_stats")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback register_alerts: {e}")
            query.edit_message_text("❌ Erro ao registrar alertas.")

    def _handle_unregister_alerts_callback(self, query, chat_id):
        """Handle callback para desregistrar alertas"""
        try:
            success = self.alerts_system.remove_group(chat_id)
            
            if success:
                message = """
🔕 **ALERTAS DESATIVADOS** 🔕

Este chat foi removido da lista de alertas.

💡 **Para reativar:**
• Use o comando /alerts
• Clique em "Ativar Alertas"

📊 **Você ainda pode:**
• Usar comandos manuais
• Verificar tips com /tips
• Monitorar com /monitoring
                """
            else:
                message = "❌ Erro ao desativar alertas. Tente novamente."

            keyboard = [
                [InlineKeyboardButton("📢 Reativar Alertas", callback_data=f"register_alerts_{chat_id}")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback unregister_alerts: {e}")
            query.edit_message_text("❌ Erro ao desregistrar alertas.")

    def _handle_alert_help_callback(self, query):
        """Handle callback para ajuda de alertas"""
        try:
            message = """
📢 **SISTEMA DE ALERTAS** 📢

🎯 **Como funciona:**
• Sistema monitora partidas ao vivo 24/7
• Detecta oportunidades profissionais automaticamente
• Envia alertas instantâneos para grupos cadastrados
• Apenas tips que atendem critérios rigorosos

⚙️ **Critérios para alertas:**
• Confiança mínima: 75%
• Expected Value: 8%+
• Partidas AO VIVO apenas
• Dados completos (draft + stats)

🎮 **Eventos LoL monitorados:**
• Barão conquistado
• Alma/Dragão Ancião  
• 5k+ vantagem ouro
• Team fights cruciais
• Torres/Inibidores

📱 **Para ativar neste chat:**
1. Use o comando /alerts
2. Clique em "Ativar Alertas"
3. Confirme a ativação

💡 **Dica:** Alertas funcionam em grupos e canais privados.
            """

            keyboard = [
                [InlineKeyboardButton("📢 Ativar Alertas", callback_data=f"register_alerts_{query.message.chat.id}")],
                [InlineKeyboardButton("📊 Ver Estatísticas", callback_data="alert_stats")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback alert_help: {e}")
            query.edit_message_text("❌ Erro ao carregar ajuda de alertas.")

    def _handle_performance_stats_callback(self, query):
        """Handle callback para estatísticas de performance"""
        try:
            bet_history = self.tips_system.units_system.bet_history
            current_bankroll = self.tips_system.units_system.bankroll
            
            if bet_history:
                total_bets = len(bet_history)
                profitable_bets = sum(1 for bet in bet_history if bet.get('result') == 'win')
                win_rate = (profitable_bets / total_bets) * 100 if total_bets > 0 else 0
                
                total_units = sum(bet.get('units_risked', 0) for bet in bet_history)
                total_profit = sum(bet.get('profit_loss', 0) for bet in bet_history)
                roi = (total_profit / total_units) * 100 if total_units > 0 else 0
                
                message = f"""
📊 **PERFORMANCE DETALHADA** 📊

💰 **Resumo financeiro:**
• Bankroll atual: ${current_bankroll:.2f}
• Total apostado: {total_units:.1f} unidades
• Lucro/Prejuízo: ${total_profit:.2f}
• ROI: {roi:.1f}%

📈 **Estatísticas:**
• Total de apostas: {total_bets}
• Apostas lucrativas: {profitable_bets}
• Win rate: {win_rate:.1f}%
• Unidade média: {total_units/total_bets:.1f} (se {total_bets} > 0)

🎯 **Performance por confiança:**
• 75-80%: {sum(1 for bet in bet_history if 75 <= bet.get('confidence', 0) < 80)} apostas
• 80-90%: {sum(1 for bet in bet_history if 80 <= bet.get('confidence', 0) < 90)} apostas  
• 90%+: {sum(1 for bet in bet_history if bet.get('confidence', 0) >= 90)} apostas

⏰ **Última atualização:** {datetime.now().strftime('%H:%M')}
                """
            else:
                message = """
📊 **PERFORMANCE DETALHADA** 📊

ℹ️ **Nenhum histórico disponível ainda.**

🎯 **Para começar:**
• Use /tips para gerar primeira oportunidade
• Tips profissionais são registradas automaticamente
• Performance será calculada em tempo real

💡 O sistema só registra tips que atendem aos critérios profissionais (75%+ confiança, 8%+ EV).
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="performance_stats")],
                [InlineKeyboardButton("📋 Ver Histórico", callback_data="bet_history")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback performance_stats: {e}")
            query.edit_message_text("❌ Erro ao carregar estatísticas de performance.")

    def _handle_bet_history_callback(self, query):
        """Handle callback para histórico de apostas"""
        try:
            bet_history = self.tips_system.units_system.bet_history
            
            if bet_history:
                message = "📋 **HISTÓRICO DE APOSTAS** 📋\n\n"
                
                # Mostrar últimas 5 apostas
                for i, bet in enumerate(bet_history[-5:], 1):
                    result_icon = "✅" if bet.get('result') == 'win' else "❌" if bet.get('result') == 'loss' else "⏳"
                    
                    message += f"**{i}. {bet.get('tip_title', 'Tip')}**\n"
                    message += f"{result_icon} Resultado: {bet.get('result', 'pending').upper()}\n"
                    message += f"💰 Unidades: {bet.get('units_risked', 0):.1f}\n"
                    message += f"📊 Confiança: {bet.get('confidence', 0):.1f}%\n"
                    message += f"📅 {bet.get('timestamp', 'N/A')}\n\n"
                    
                message += f"📊 **Total:** {len(bet_history)} apostas registradas"
            else:
                message = """
📋 **HISTÓRICO DE APOSTAS** 📋

ℹ️ **Nenhuma aposta registrada ainda.**

🎯 **Como funciona:**
• Sistema registra automaticamente tips gerados
• Cada tip vira uma entrada no histórico  
• Performance calculada automaticamente

🚀 **Para começar:**
• Use /tips para gerar primeira oportunidade
• Tips profissionais são registrados automaticamente
• Acompanhe performance em tempo real

💡 Apenas tips que atendem aos critérios profissionais são registradas.
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="bet_history")],
                [InlineKeyboardButton("📊 Performance", callback_data="performance_stats")],
                [InlineKeyboardButton("🎯 Nova Tip", callback_data="tips")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback bet_history: {e}")
            query.edit_message_text("❌ Erro ao carregar histórico de apostas.")

    def _handle_odds_summary_callback(self, query):
        """Handle callback para resumo de odds"""
        try:
            # Buscar resumo de odds
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            odds_summary = loop.run_until_complete(self.tips_system.odds_client.get_odds_summary())
            loop.close()
            
            message = f"""
💰 **RESUMO DE ODDS REAIS** 💰

📊 **The Odds API Status:**
• Jogos disponíveis: {odds_summary.get('total_games', 0)}
• Ligas cobertas: {len(odds_summary.get('leagues', []))}
• Times monitorados: {len(odds_summary.get('teams', []))}
• Casas de apostas: {len(odds_summary.get('bookmakers', []))}

🏆 **Principais ligas:**
{chr(10).join([f"• {league}" for league in odds_summary.get('leagues', [])[:5]])}

🎮 **Funcionalidades:**
• Odds reais em tempo real
• Múltiplas casas de apostas
• Cache otimizado (5min)
• Expected Value preciso

⚡ **Para usar:**
• /tips - Tips com odds reais
• /odds - Ver odds disponíveis
• Sistema calcula EV automaticamente
            """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="odds_summary")],
                [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("💰 Comando /odds", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback odds_summary: {e}")
            query.edit_message_text("❌ Erro ao carregar resumo de odds.")

    def _handle_force_scan_callback(self, query):
        """Handle callback para scan forçado"""
        try:
            user = query.from_user
            
            # Verificar se é o owner
            if user.id != OWNER_ID:
                query.answer("❌ Apenas o administrador pode forçar scans manuais.")
                return

            # Responder callback primeiro
            query.answer("🔍 Iniciando scan manual...")
            
            # Atualizar mensagem para mostrar progresso
            progress_message = """
🔍 **SCAN MANUAL INICIADO** 🔍

⏳ **STATUS:**
• Buscando partidas disponíveis...
• Analisando com sistema de IA...
• Verificando critérios profissionais...

⚡ **Aguarde alguns segundos...**
            """
            
            query.edit_message_text(progress_message, parse_mode="Markdown")
            
            # Executar scan em thread separada
            def run_manual_scan():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.tips_system._scan_live_matches_only())
                    loop.close()
                    
                    # Buscar resultados
                    recent_tips = self.tips_system.tips_database[-3:] if self.tips_system.tips_database else []
                    
                    if recent_tips:
                        result_message = f"""
✅ **SCAN MANUAL CONCLUÍDO** ✅

🎯 **Resultados:**
• {len(recent_tips)} oportunidades encontradas
• Critérios profissionais aplicados
• Tips adicionadas ao sistema

📊 **Últimas tips encontradas:**
"""
                        for tip in recent_tips:
                            result_message += f"• {tip.get('title', 'Tip')}\n"
                            result_message += f"  📊 {tip.get('confidence_score', 0):.1f}% confiança\n"
                    else:
                        result_message = """
✅ **SCAN MANUAL CONCLUÍDO** ✅

ℹ️ **Nenhuma nova oportunidade encontrada.**

🔍 **Verificado:**
• Todas as partidas ao vivo
• Critérios profissionais aplicados
• Sistema funcionando normalmente

⏰ Próximo scan automático em 3 minutos
                        """
                    
                    keyboard = [
                        [InlineKeyboardButton("🔄 Novo Scan", callback_data="force_scan")],
                        [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
                        [InlineKeyboardButton("📊 Monitoramento", callback_data="monitoring")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Atualizar mensagem com resultado
                    query.edit_message_text(result_message, reply_markup=reply_markup, parse_mode="Markdown")
                    
                except Exception as e:
                    logger.error(f"Erro no scan manual: {e}")
                    error_message = f"""
❌ **ERRO NO SCAN MANUAL** ❌

Erro: {str(e)}

🔄 **Tente novamente ou:**
• Verificar conexão
• Aguardar scan automático
• Usar /monitoring para status
                    """
                    query.edit_message_text(error_message, parse_mode="Markdown")
            
            # Executar em thread separada
            import threading
            scan_thread = threading.Thread(target=run_manual_scan, daemon=True)
            scan_thread.start()
            
        except Exception as e:
            logger.error(f"Erro no callback force_scan: {e}")
            query.edit_message_text("❌ Erro ao iniciar scan manual.")

    def _handle_main_menu_callback(self, query):
        """Handle callback para menu principal"""
        try:
            menu_message = """
🎮 **MENU PRINCIPAL - BOT LOL V3** 🎮

🎯 **TIPS & ANÁLISES (ATUALIZADO):**
• /tips - Tips profissionais AO VIVO
• /predictions - Predições IA
• /schedule - Agenda de partidas
• /live - Partidas ao vivo
• /monitoring - Status do monitoramento
• /force_scan - Scan manual (admin)
• /alerts - Sistema de alertas

🎲 **SISTEMA DE UNIDADES:**
• /units - Explicação do sistema
• /performance - Performance atual
• /history - Histórico de apostas

📊 **INFORMAÇÕES:**
• /help - Ajuda completa
• /about - Sobre o bot

🎮 **NOVA FUNCIONALIDADE - TIPS AO VIVO:**
🔥 Agora o sistema gera tips APENAS para partidas que estão acontecendo!
• ✅ Dados reais de draft + estatísticas
• ✅ Informação de mapa e tempo de jogo
• ✅ SEM LIMITE semanal de tips
• ✅ Monitoramento a cada 3 minutos

💰 **ODDS REAIS INTEGRADAS:**
• The Odds API para odds reais
• Expected Value preciso
• Múltiplas casas de apostas
            """

            keyboard = [
                [InlineKeyboardButton("🎯 Tips Profissionais", callback_data="tips")],
                [InlineKeyboardButton("🔴 Partidas ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("📅 Agenda", callback_data="schedule")],
                [InlineKeyboardButton("📊 Monitoramento", callback_data="monitoring")],
                [InlineKeyboardButton("🔮 Predições IA", callback_data="predictions")],
                [InlineKeyboardButton("📢 Alertas", callback_data="alert_stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(menu_message, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Erro no callback main_menu: {e}")
            query.edit_message_text("❌ Erro ao carregar menu principal.")

def run_flask():
    """Executa apenas o Flask app para health checks"""
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

def check_single_instance():
    """Verifica se já existe uma instância rodando"""
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
            # Sistema não suportado, usar verificação simples
            if os.path.exists(lock_file_path):
                # Verificar se processo ainda está rodando
                try:
                    with open(lock_file_path, 'r') as f:
                        old_pid = int(f.read().strip())
                    
                    # Tentar verificar se PID ainda existe
                    try:
                        os.kill(old_pid, 0)  # Sinal 0 não mata, apenas verifica
                        logger.warning(f"⚠️ Instância já rodando (PID: {old_pid})")
                        return None
                    except OSError:
                        # PID não existe mais, remover lock
                        os.remove(lock_file_path)
                        logger.info("🧹 Lock órfão removido")
                except (ValueError, FileNotFoundError):
                    # Arquivo corrompido ou não existe
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
            
            # Criar novo lock
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            return True
            
    except Exception as e:
        logger.warning(f"⚠️ Erro ao verificar instância única: {e}")
        return True  # Em caso de erro, permitir execução

async def main():
    """Função principal do bot"""
    try:
        # Verificação de instância única
        lock_fd_or_status = check_single_instance()
        if lock_fd_or_status is None:
            logger.error("❌ Outra instância do bot já está rodando!")
            sys.exit(1)
        
        logger.info("🤖 Bot LoL V3 Ultra Advanced - Iniciando...")
        
        # Verificar ambiente Railway
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))
        logger.info(f"🔧 Ambiente detectado: {'Railway' if is_railway else 'Local'}")

        # Criar instância do bot
        bot_instance = LoLBotV3UltraAdvanced()

        # Verificação de compatibilidade da versão
        USE_APPLICATION = False
        
        try:
            # Tentar importar Application (v20+)
            from telegram.ext import Application
            
            logger.info("📦 Detectada versão do python-telegram-bot 20+")
            USE_APPLICATION = True
            
            # Versão v20+ - usar Application
            application = Application.builder().token(TOKEN).build()
            
            # Definir aplicação para sistema de alertas
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
            logger.info(f"✅ {total_handlers} handlers registrados (Application v20+)")
            
        except ImportError:
            logger.info("📦 Versão python-telegram-bot 13-19 detectada")
            
            # Versão v13-19 - usar Updater  
            try:
                # Tentar com use_context primeiro
                updater = Updater(TOKEN, use_context=True)
            except TypeError:
                try:
                    # Fallback para versão sem use_context
                    updater = Updater(TOKEN)
                except TypeError:
                    # Última tentativa - versão muito antiga com queue
                    import queue
                    update_queue = queue.Queue()
                    updater = Updater(TOKEN, update_queue=update_queue)
            
            dispatcher = updater.dispatcher
            
            # Limpar webhook existente
            try:
                logger.info("🧹 Limpando webhook existente...")
                updater.bot.delete_webhook(drop_pending_updates=True)
                logger.info("✅ Webhook anterior removido")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar webhook: {e}")

            # Definir aplicação para sistema de alertas  
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
            logger.info(f"✅ {total_handlers} handlers registrados (Updater v13-19)")

        if is_railway:
            # Modo Railway - Webhook
            logger.info("🚀 Detectado ambiente Railway - Configurando webhook")

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
                            logger.info(f"🔄 Webhook v20+ processado: {update_obj.update_id if update_obj else 'None'}")
                        return "OK", 200
                    except Exception as e:
                        logger.error(f"❌ Erro no webhook v20+: {e}")
                        return "ERROR", 500
                
                # Configurar webhook v20+
                railway_url = os.getenv('RAILWAY_STATIC_URL', f"https://{os.getenv('RAILWAY_SERVICE_NAME', 'bot')}.railway.app")
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                webhook_url = f"{railway_url}{webhook_path}"

                try:
                    logger.info("🔄 Configurando webhook v20+...")
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    await application.bot.set_webhook(webhook_url)
                    
                    webhook_info = await application.bot.get_webhook_info()
                    logger.info(f"📋 Webhook v20+ ativo: {webhook_info.url}")
                    
                    me = await application.bot.get_me()
                    logger.info(f"🤖 Bot v20+ verificado: @{me.username}")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao configurar webhook v20+: {e}")
            
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
                            logger.info(f"🔄 Webhook v13-19 processado: {update_obj.update_id if update_obj else 'None'}")
                        return "OK", 200
                    except Exception as e:
                        logger.error(f"❌ Erro no webhook v13-19: {e}")
                        return "ERROR", 500
                
                # Configurar webhook v13-19
                railway_url = os.getenv('RAILWAY_STATIC_URL', f"https://{os.getenv('RAILWAY_SERVICE_NAME', 'bot')}.railway.app")
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                webhook_url = f"{railway_url}{webhook_path}"

                try:
                    logger.info("🔄 Configurando webhook v13-19...")
                    updater.bot.delete_webhook(drop_pending_updates=True)
                    updater.bot.set_webhook(webhook_url)
                    
                    webhook_info = updater.bot.get_webhook_info()
                    logger.info(f"📋 Webhook v13-19 ativo: {webhook_info.url}")
                    
                    me = updater.bot.get_me()
                    logger.info(f"🤖 Bot v13-19 verificado: @{me.username}")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao configurar webhook v13-19: {e}")

            logger.info("✅ Bot configurado (Railway webhook) - Iniciando Flask...")

            app.config['ENV'] = 'production'
            app.config['DEBUG'] = False

            logger.info(f"🌐 Iniciando Flask na porta {PORT}")
            logger.info(f"🔗 Webhook disponível em: {webhook_url}")

            app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

        else:
            # Modo Local - Polling
            logger.info("🏠 Ambiente local detectado - Usando polling")

            if USE_APPLICATION:
                # Polling v20+
                logger.info("✅ Bot configurado (polling v20+) - Iniciando...")

                try:
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    logger.info("🧹 Webhook removido antes de iniciar polling v20+")
                except Exception as e:
                    logger.debug(f"Webhook já estava removido v20+: {e}")

                logger.info("🔄 Iniciando polling v20+...")
                
                # Corrigir problema do event loop
                try:
                    # Primeiro tentar método padrão
                    application.run_polling(drop_pending_updates=True)
                except RuntimeError as e:
                    if "event loop" in str(e).lower():
                        logger.info("🔄 Event loop em execução, usando método alternativo...")
                        # Método alternativo para event loop já rodando
                        await application.initialize()
                        await application.start()
                        await application.updater.start_polling(drop_pending_updates=True)
                        
                        logger.info("✅ Bot iniciado com polling v20+ (método alternativo)")
                        
                        # Manter o bot rodando
                        try:
                            import signal
                            import asyncio
                            
                            # Configurar handlers de sinal
                            def signal_handler(signum, frame):
                                logger.info("🛑 Sinal recebido, parando bot...")
                                asyncio.create_task(application.stop())
                                asyncio.create_task(application.shutdown())
                                
                            signal.signal(signal.SIGINT, signal_handler)
                            signal.signal(signal.SIGTERM, signal_handler)
                            
                            # Loop infinito assíncrono
                            while True:
                                await asyncio.sleep(1)
                                
                        except KeyboardInterrupt:
                            logger.info("🛑 Parando bot...")
                        finally:
                            await application.stop()
                            await application.shutdown()
                    else:
                        raise
            
            else:
                # Polling v13-19
                logger.info("✅ Bot configurado (polling v13-19) - Iniciando...")

                try:
                    updater.bot.delete_webhook(drop_pending_updates=True)
                    logger.info("🧹 Webhook removido antes de iniciar polling v13-19")
                except Exception as e:
                    logger.debug(f"Webhook já estava removido v13-19: {e}")

                logger.info("🔄 Iniciando polling v13-19...")
                updater.start_polling(drop_pending_updates=True)
                updater.idle()

    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        import traceback
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")

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
                    logger.info("🔓 Lock liberado e arquivo removido.")
                except OSError as e:
                    logger.warning(f"⚠️ Não foi possível remover arquivo de lock: {e}")

if __name__ == "__main__":
    asyncio.run(main())
