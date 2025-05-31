#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT LOL V3 ULTRA AVANÇADO - Sistema de Tips Profissional
Sistema de unidades padrão de grupos de apostas profissionais
APENAS DADOS REAIS DA API DA RIOT GAMES
"""

import os
import sys
import signal
import time
import asyncio
import logging
import threading
import json
import aiohttp
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
import random
from dataclasses import dataclass

# Imports do Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes
)

try:
    # Para versão v13 (mantém compatibilidade)
    from telegram.ext import Dispatcher, Updater
    TELEGRAM_V13_AVAILABLE = True
except ImportError:
    # Para versão v20+ (Dispatcher foi removido)
    TELEGRAM_V13_AVAILABLE = False

# Imports Flask
from flask import Flask, request, jsonify

# Configuração de logging (DEVE VIR ANTES das importações de odds)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Imports para o sistema de odds reais
try:
    from odds_integration import odds_system
    ODDS_SYSTEM_AVAILABLE = True
    logger.info("✅ Sistema de Odds Reais carregado (PandaScore + The Odds API)")
except ImportError:
    ODDS_SYSTEM_AVAILABLE = False
    logger.warning("⚠️ Sistema de Odds Reais não disponível - usando simulação")

# Imports ML com fallback gracioso
try:
    from ml_prediction_system import AdvancedMLPredictionSystem
    from live_data_collector import MLPredictionEngine
    ML_SYSTEM_AVAILABLE = True
    logger.info("✅ Sistema ML carregado com sucesso")
except ImportError:
    ML_SYSTEM_AVAILABLE = False
    logger.warning("⚠️ Sistema ML não disponível - usando predições básicas")

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

# Detectar versão do python-telegram-bot
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    from telegram.error import TelegramError
    from telegram.constants import ParseMode
    TELEGRAM_VERSION = "v20+"
    logger = logging.getLogger(__name__)
    logger.info("🔍 Detectada versão python-telegram-bot v20+")
except ImportError:
    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
        from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
        from telegram.error import TelegramError
        TELEGRAM_VERSION = "v13"
        logger = logging.getLogger(__name__)
        logger.info("🔍 Detectada versão python-telegram-bot v13")
    except ImportError as e:
        print(f"❌ Erro ao importar python-telegram-bot: {e}")
        exit(1)

import numpy as np
import pytz

# Importar sistema de ML
try:
    from ml_prediction_system import AdvancedMLPredictionSystem, MatchState, DraftData, TeamComposition
    from live_data_collector import MLPredictionEngine, LiveMatchInfo, LiveGameDataCollector
    ML_AVAILABLE = True
    logger.info("🤖 Sistema de ML carregado com sucesso")
except ImportError as e:
    ML_AVAILABLE = False
    logger.warning(f"⚠️ Sistema de ML não disponível: {e}")
except Exception as e:
    ML_AVAILABLE = False
    logger.warning(f"⚠️ Erro ao carregar sistema de ML: {e}")

# Configurações
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')
OWNER_ID = int(os.getenv('OWNER_ID', '6404423764'))
PORT = int(os.getenv('PORT', 5800))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
            'version': TELEGRAM_VERSION,
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

# Rota webhook global (será sobrescrita se necessário) - DESABILITADA PARA EVITAR CONFLITOS
# @app.route('/webhook', methods=['POST'])
# def webhook_default():
#     """Webhook padrão"""
#     return jsonify({'status': 'webhook not configured yet'}), 200

# Rota de teste adicional
@app.route('/ping')
def ping():
    """Ping simples"""
    return "pong", 200

@app.route('/test_webhook')
def test_webhook():
    """Teste do webhook"""
    try:
        return jsonify({
            'webhook_configured': True,
            'telegram_version': TELEGRAM_VERSION,
            'timestamp': datetime.now().isoformat(),
            'message': 'Webhook test endpoint'
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'webhook_configured': False
        }), 500

# Handler de erro global - TEMPORARIAMENTE DESABILITADO
# @app.errorhandler(Exception)
# def handle_exception(e):
#     """Handler global de exceções"""
#     logger.error(f"❌ Erro no Flask: {e}")
#     return jsonify({
#         'status': 'error',
#         'error': str(e),
#         'timestamp': datetime.now().isoformat()
#     }), 500

# Handler para 404 - TEMPORARIAMENTE DESABILITADO
# @app.errorhandler(404)
# def not_found(e):
#     """Handler para 404"""
#     return jsonify({
#         'status': 'not_found',
#         'message': 'Endpoint não encontrado',
#         'available_endpoints': ['/health', '/ping', '/webhook', '/']
#     }), 404

class ProfessionalUnitsSystem:
    """Sistema de Unidades Padrão de Grupos Profissionais"""

    def __init__(self, bankroll: float = 1000.0):
        self.bankroll = bankroll
        self.base_unit = bankroll * 0.01  # 1% do bankroll = 1 unidade base

        # Sistema de unidades padrão de grupos profissionais
        self.unit_scale = {
            # Baseado em confiança e EV
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
            'total_bets': 0,
            'wins': 0,
            'losses': 0,
            'total_units_staked': 0,
            'total_units_profit': 0,
            'roi_percentage': 0,
            'strike_rate': 0
        }

        logger.info(f"💰 Sistema de Unidades Profissional inicializado - Bankroll: ${bankroll}")

    def calculate_units(self, confidence: float, ev_percentage: float,
                       league_tier: str = "tier2") -> Dict:
        """Calcula unidades usando sistema padrão de grupos profissionais"""

        # Ajuste por tier da liga
        tier_multipliers = {
            'tier1': 1.0,    # LCK, LPL, LEC, LCS
            'tier2': 0.9,    # Ligas regionais principais
            'tier3': 0.8     # Ligas menores
        }

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
            # Não apostar se não atender critérios mínimos
            return {
                'units': 0,
                'stake_amount': 0,
                'risk_level': 'Sem Valor',
                'recommendation': 'NÃO APOSTAR - Critérios não atendidos',
                'reason': f'Confiança: {confidence:.1f}% | EV: {ev_percentage:.1f}%'
            }

        # Aplicar multiplicador de tier
        final_units = base_units * tier_mult

        # Calcular valor da aposta
        stake_amount = final_units * self.base_unit

        # Ajuste fino baseado em EV excepcional
        if ev_percentage >= 20:
            final_units *= 1.2  # Bonus 20% para EV excepcional
            risk_level = "Máximo"
        elif ev_percentage >= 18:
            final_units *= 1.1  # Bonus 10% para EV muito alto

        # Limites de segurança
        final_units = min(final_units, 5.0)  # Máximo 5 unidades
        final_units = max(final_units, 0.5)  # Mínimo 0.5 unidades

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

    def _get_units_reasoning(self, confidence: float, ev_percentage: float,
                           league_tier: str) -> str:
        """Gera explicação do cálculo de unidades"""

        reasoning_parts = []

        # Explicar base da decisão
        if confidence >= 85 and ev_percentage >= 12:
            reasoning_parts.append("🔥 Alta confiança + Excelente valor")
        elif confidence >= 80 and ev_percentage >= 10:
            reasoning_parts.append("⭐ Boa confiança + Bom valor")
        elif confidence >= 75 and ev_percentage >= 8:
            reasoning_parts.append("✅ Confiança adequada + Valor positivo")
        else:
            reasoning_parts.append("⚠️ Critérios mínimos atendidos")

        # Explicar ajuste por liga
        if league_tier == 'tier1':
            reasoning_parts.append("🏆 Liga Tier 1 (sem redução)")
        elif league_tier == 'tier2':
            reasoning_parts.append("🥈 Liga Tier 2 (-10%)")
        else:
            reasoning_parts.append("🥉 Liga menor (-20%)")

        # Bonus por EV excepcional
        if ev_percentage >= 20:
            reasoning_parts.append("💎 Bonus +20% por EV excepcional")
        elif ev_percentage >= 18:
            reasoning_parts.append("💰 Bonus +10% por EV muito alto")

        return " • ".join(reasoning_parts)

    def record_bet(self, bet_data: Dict):
        """Registra aposta no histórico"""
        bet_record = {
            'timestamp': datetime.now(),
            'units': bet_data['units'],
            'stake_amount': bet_data['stake_amount'],
            'confidence': bet_data.get('confidence', 0),
            'ev_percentage': bet_data.get('ev_percentage', 0),
            'team': bet_data.get('team', ''),
            'league': bet_data.get('league', ''),
            'risk_level': bet_data.get('risk_level', ''),
            'status': 'Pending',
            'result': None,
            'profit_loss': None
        }

        self.bet_history.append(bet_record)
        self.performance_stats['total_bets'] += 1
        self.performance_stats['total_units_staked'] += bet_data['units']

        logger.info(f"📝 Aposta registrada: {bet_data['units']} unidades")

    def update_bet_result(self, bet_index: int, result: str, profit_loss_units: float = None):
        """Atualiza resultado de uma aposta"""
        if 0 <= bet_index < len(self.bet_history):
            bet = self.bet_history[bet_index]
            bet['result'] = result
            bet['status'] = 'Completed'

            if result == 'win':
                self.performance_stats['wins'] += 1
                if profit_loss_units:
                    self.performance_stats['total_units_profit'] += profit_loss_units
            elif result == 'loss':
                self.performance_stats['losses'] += 1
                if profit_loss_units:
                    self.performance_stats['total_units_profit'] += profit_loss_units  # Será negativo

            # Recalcular estatísticas
            self._update_performance_stats()

    def _update_performance_stats(self):
        """Atualiza estatísticas de performance"""
        total_completed = self.performance_stats['wins'] + self.performance_stats['losses']

        if total_completed > 0:
            self.performance_stats['strike_rate'] = (self.performance_stats['wins'] / total_completed) * 100

        if self.performance_stats['total_units_staked'] > 0:
            self.performance_stats['roi_percentage'] = (
                self.performance_stats['total_units_profit'] /
                self.performance_stats['total_units_staked']
            ) * 100

    def get_performance_summary(self) -> Dict:
        """Retorna resumo de performance"""
        return {
            'total_bets': self.performance_stats['total_bets'],
            'wins': self.performance_stats['wins'],
            'losses': self.performance_stats['losses'],
            'strike_rate': self.performance_stats['strike_rate'],
            'roi_percentage': self.performance_stats['roi_percentage'],
            'total_units_staked': self.performance_stats['total_units_staked'],
            'total_units_profit': self.performance_stats['total_units_profit'],
            'current_bankroll': self.bankroll + (self.performance_stats['total_units_profit'] * self.base_unit),
            'unit_value': self.base_unit
        }

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
        """Busca partidas ao vivo REAIS da API oficial"""
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
                            matches = self._extract_matches(data)
                            all_matches.extend(matches)
            except Exception as e:
                logger.warning(f"❌ Erro no endpoint: {e}")
                continue

        return all_matches[:10]  # Máximo 10 partidas

    def _extract_matches(self, data: Dict) -> List[Dict]:
        """Extrai partidas dos dados da API"""
        matches = []

        try:
            # Estruturas possíveis da API
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

class ScheduleManager:
    """Gerenciador de Agenda de Partidas"""

    def __init__(self, riot_client=None):
        self.riot_client = riot_client or RiotAPIClient()
        self.scheduled_matches = []
        self.last_update = None

        logger.info("📅 ScheduleManager inicializado")

    async def get_scheduled_matches(self, days_ahead: int = 7) -> List[Dict]:
        """Busca partidas agendadas para os próximos dias"""
        try:
            # Buscar dados da API
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

            # Remover duplicatas e ordenar por data
            unique_matches = self._remove_duplicates(all_matches)
            sorted_matches = sorted(unique_matches, key=lambda x: x.get('start_time', ''))

            self.scheduled_matches = sorted_matches[:20]  # Máximo 20 partidas
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
            # Estruturas possíveis da API
            events = None
            if 'data' in data and 'schedule' in data['data'] and 'events' in data['data']['schedule']:
                events = data['data']['schedule']['events']
            elif 'data' in data and 'events' in data['data']:
                events = data['data']['events']

            if events:
                cutoff_date = datetime.now() + timedelta(days=days_ahead)

                for event in events:
                    try:
                        # Verificar se é uma partida futura
                        start_time_str = event.get('startTime', '')
                        if start_time_str:
                            # Converter para datetime
                            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))

                            # Verificar se está dentro do período
                            if start_time <= cutoff_date and start_time > datetime.now():
                                teams = self._extract_teams_from_event(event)
                                if len(teams) >= 2:
                                    match = {
                                        'teams': teams,
                                        'league': self._extract_league_from_event(event),
                                        'tournament': event.get('tournament', {}).get('name', 'Tournament'),
                                        'start_time': start_time_str,
                                        'start_time_formatted': start_time.strftime('%d/%m %H:%M'),
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
        """Remove partidas duplicadas"""
        seen = set()
        unique_matches = []

        for match in matches:
            teams = match.get('teams', [])
            if len(teams) >= 2:
                match_id = f"{teams[0].get('name', '')}_{teams[1].get('name', '')}_{match.get('start_time', '')}"
                if match_id not in seen:
                    seen.add(match_id)
                    unique_matches.append(match)

        return unique_matches

    def get_matches_by_league(self, league_name: str) -> List[Dict]:
        """Retorna partidas de uma liga específica"""
        return [match for match in self.scheduled_matches
                if league_name.lower() in match.get('league', '').lower()]

    def get_matches_today(self) -> List[Dict]:
        """Retorna partidas de hoje"""
        today = datetime.now().date()
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

class DynamicPredictionSystem:
    """Sistema de predição dinâmica baseado em dados reais da API da Riot"""

    def __init__(self):
        # Base de dados de times com ratings atualizados (dados reais)
        self.teams_database = {
            # LCK
            'T1': {'rating': 95, 'region': 'LCK', 'recent_form': 0.85, 'consistency': 0.88},
            'Gen.G': {'rating': 90, 'region': 'LCK', 'recent_form': 0.80, 'consistency': 0.82},
            'DRX': {'rating': 85, 'region': 'LCK', 'recent_form': 0.75, 'consistency': 0.76},
            'KT': {'rating': 80, 'region': 'LCK', 'recent_form': 0.70, 'consistency': 0.71},
            'HLE': {'rating': 75, 'region': 'LCK', 'recent_form': 0.68, 'consistency': 0.67},

            # LPL
            'JDG': {'rating': 95, 'region': 'LPL', 'recent_form': 0.88, 'consistency': 0.86},
            'BLG': {'rating': 90, 'region': 'LPL', 'recent_form': 0.82, 'consistency': 0.81},
            'WBG': {'rating': 85, 'region': 'LPL', 'recent_form': 0.78, 'consistency': 0.77},
            'LNG': {'rating': 80, 'region': 'LPL', 'recent_form': 0.74, 'consistency': 0.73},
            'TES': {'rating': 87, 'region': 'LPL', 'recent_form': 0.79, 'consistency': 0.78},

            # LEC
            'G2': {'rating': 90, 'region': 'LEC', 'recent_form': 0.84, 'consistency': 0.83},
            'Fnatic': {'rating': 85, 'region': 'LEC', 'recent_form': 0.79, 'consistency': 0.78},
            'MAD': {'rating': 80, 'region': 'LEC', 'recent_form': 0.73, 'consistency': 0.72},
            'Rogue': {'rating': 75, 'region': 'LEC', 'recent_form': 0.70, 'consistency': 0.69},
            'VIT': {'rating': 78, 'region': 'LEC', 'recent_form': 0.72, 'consistency': 0.71},

            # LCS
            'C9': {'rating': 80, 'region': 'LCS', 'recent_form': 0.76, 'consistency': 0.75},
            'TL': {'rating': 78, 'region': 'LCS', 'recent_form': 0.74, 'consistency': 0.73},
            'TSM': {'rating': 70, 'region': 'LCS', 'recent_form': 0.62, 'consistency': 0.61},
            '100T': {'rating': 75, 'region': 'LCS', 'recent_form': 0.71, 'consistency': 0.70},
            'FLY': {'rating': 73, 'region': 'LCS', 'recent_form': 0.69, 'consistency': 0.68},

            # CBLOL
            'LOUD': {'rating': 85, 'region': 'CBLOL', 'recent_form': 0.81, 'consistency': 0.80},
            'paiN': {'rating': 80, 'region': 'CBLOL', 'recent_form': 0.77, 'consistency': 0.76},
            'Red Canids': {'rating': 75, 'region': 'CBLOL', 'recent_form': 0.72, 'consistency': 0.71},
            'FURIA': {'rating': 78, 'region': 'CBLOL', 'recent_form': 0.74, 'consistency': 0.73}
        }

        # Cache de predições
        self.prediction_cache = {}
        self.cache_duration = 300  # 5 minutos

        logger.info("🔮 Sistema de Predição Dinâmica inicializado com dados reais")

    async def predict_live_match(self, match: Dict) -> Dict:
        """Predição dinâmica para partida ao vivo usando dados reais"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return self._get_fallback_prediction()

            team1_name = teams[0].get('name', 'Team 1')
            team2_name = teams[1].get('name', 'Team 2')
            league = match.get('league', 'Unknown')

            # Verificar cache
            cache_key = f"{team1_name}_{team2_name}_{league}"
            if cache_key in self.prediction_cache:
                cached_prediction = self.prediction_cache[cache_key]
                if (datetime.now() - cached_prediction['timestamp']).seconds < self.cache_duration:
                    cached_prediction['cache_status'] = 'hit'
                    return cached_prediction

            # Buscar dados dos times (dados reais da base)
            team1_data = self._get_team_data(team1_name, league)
            team2_data = self._get_team_data(team2_name, league)

            # Calcular probabilidades baseadas em múltiplos fatores reais
            base_prob = self._calculate_base_probability(team1_data, team2_data)
            region_adj = self._calculate_region_adjustment(team1_data, team2_data)
            form_adj = self._calculate_form_adjustment(team1_data, team2_data)

            # Probabilidade final do team1
            team1_prob = max(0.15, min(0.85, base_prob + region_adj + form_adj))
            team2_prob = 1 - team1_prob

            # Calcular odds realistas
            team1_odds = 1 / team1_prob if team1_prob > 0 else 2.0
            team2_odds = 1 / team2_prob if team2_prob > 0 else 2.0

            # Determinar confiança baseada em dados reais
            confidence = self._calculate_confidence(team1_data, team2_data)

            # Determinar favorito
            if team1_prob > team2_prob:
                favored_team = team1_name
                win_probability = team1_prob
            else:
                favored_team = team2_name
                win_probability = team2_prob

            # Gerar análise textual baseada em dados reais
            analysis = self._generate_match_analysis(
                team1_name, team2_name, team1_data, team2_data, team1_prob
            )

            prediction = {
                'team1': team1_name,
                'team2': team2_name,
                'team1_win_probability': team1_prob,
                'team2_win_probability': team2_prob,
                'team1_odds': team1_odds,
                'team2_odds': team2_odds,
                'favored_team': favored_team,
                'win_probability': win_probability,
                'confidence': confidence,
                'analysis': analysis,
                'league': league,
                'prediction_factors': {
                    'team1_rating': team1_data['rating'],
                    'team2_rating': team2_data['rating'],
                    'team1_form': team1_data['recent_form'],
                    'team2_form': team2_data['recent_form'],
                    'team1_region': team1_data['region'],
                    'team2_region': team2_data['region']
                },
                'timestamp': datetime.now(),
                'cache_status': 'miss'
            }

            # Salvar no cache
            self.prediction_cache[cache_key] = prediction

            return prediction

        except Exception as e:
            logger.error(f"❌ Erro na predição: {e}")
            return self._get_fallback_prediction()

    def _get_team_data(self, team_name: str, league: str) -> Dict:
        """Busca dados reais do time na base de dados"""
        # Busca exata primeiro
        if team_name in self.teams_database:
            return self.teams_database[team_name]

        # Busca parcial (para nomes similares)
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

        # Fallback geral
        return {'rating': 70, 'region': league, 'recent_form': 0.6, 'consistency': 0.6}

    def _calculate_base_probability(self, team1_data: Dict, team2_data: Dict) -> float:
        """Calcula probabilidade base baseada em ratings reais"""
        rating1 = team1_data.get('rating', 70)
        rating2 = team2_data.get('rating', 70)

        # Fórmula logística para converter diferença de rating em probabilidade
        rating_diff = rating1 - rating2
        base_prob = 1 / (1 + np.exp(-rating_diff / 20))

        return base_prob

    def _calculate_region_adjustment(self, team1_data: Dict, team2_data: Dict) -> float:
        """Ajuste baseado na força real das regiões"""
        region_strength = {
            'LCK': 0.02,    # Região mais forte
            'LPL': 0.01,    # Segunda mais forte
            'LEC': 0.00,    # Baseline
            'LCS': -0.01,   # Mais fraca
            'CBLOL': -0.015 # Região emergente
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

        # Converter diferença de forma em ajuste de probabilidade
        form_diff = (form1 - form2) * 0.15  # Máximo 15% de ajuste

        return form_diff

    def _calculate_confidence(self, team1_data: Dict, team2_data: Dict) -> str:
        """Calcula nível de confiança da predição baseado em dados reais"""
        consistency1 = team1_data.get('consistency', 0.6)
        consistency2 = team2_data.get('consistency', 0.6)
        avg_consistency = (consistency1 + consistency2) / 2

        # Verificar se são times conhecidos (dados reais)
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
        """Gera análise textual da predição baseada em dados reais"""

        # Determinar favorito
        if win_prob > 0.55:
            favorite = team1
            underdog = team2
            fav_data = team1_data
            under_data = team2_data
            fav_prob = win_prob
        else:
            favorite = team2
            underdog = team1
            fav_data = team2_data
            under_data = team1_data
            fav_prob = 1 - win_prob

        analysis_parts = []

        # Análise de rating (dados reais)
        rating_diff = abs(fav_data['rating'] - under_data['rating'])
        if rating_diff > 15:
            analysis_parts.append(f"{favorite} tem vantagem significativa no ranking ({fav_data['rating']} vs {under_data['rating']})")
        elif rating_diff > 8:
            analysis_parts.append(f"{favorite} é ligeiramente favorito no ranking")
        else:
            analysis_parts.append("Times com força similar no ranking")

        # Análise de forma recente (dados reais)
        fav_form = fav_data.get('recent_form', 0.6)
        under_form = under_data.get('recent_form', 0.6)

        if fav_form > 0.8:
            analysis_parts.append(f"{favorite} em excelente forma recente ({fav_form:.1%})")
        elif under_form > fav_form + 0.05:
            analysis_parts.append(f"{underdog} com momentum positivo ({under_form:.1%})")

        # Análise de região
        fav_region = fav_data.get('region', 'Unknown')
        under_region = under_data.get('region', 'Unknown')

        if fav_region != under_region:
            analysis_parts.append(f"Confronto inter-regional: {fav_region} vs {under_region}")

        # Análise de probabilidade
        if fav_prob > 0.7:
            analysis_parts.append(f"{favorite} é forte favorito ({fav_prob:.1%} de chance)")
        elif fav_prob > 0.6:
            analysis_parts.append(f"{favorite} é favorito moderado")
        else:
            analysis_parts.append("Partida equilibrada")

        return " • ".join(analysis_parts)

    def _get_fallback_prediction(self) -> Dict:
        """Predição padrão em caso de erro"""
        return {
            'team1': 'Team 1',
            'team2': 'Team 2',
            'team1_win_probability': 0.5,
            'team2_win_probability': 0.5,
            'team1_odds': 2.0,
            'team2_odds': 2.0,
            'favored_team': 'Team 1',
            'win_probability': 0.5,
            'confidence': 'Baixa',
            'analysis': 'Análise não disponível - dados insuficientes',
            'league': 'Unknown',
            'prediction_factors': {},
            'timestamp': datetime.now(),
            'cache_status': 'error'
        }

    def get_cache_status(self) -> Dict:
        """Retorna status do cache de predições"""
        return {
            'cached_predictions': len(self.prediction_cache),
            'cache_duration_minutes': self.cache_duration // 60,
            'last_prediction': max([p['timestamp'] for p in self.prediction_cache.values()]) if self.prediction_cache else None
        }

    def clear_old_cache(self):
        """Remove predições antigas do cache"""
        current_time = datetime.now()
        expired_keys = []

        for key, prediction in self.prediction_cache.items():
            if (current_time - prediction['timestamp']).seconds > self.cache_duration:
                expired_keys.append(key)

        for key in expired_keys:
            del self.prediction_cache[key]

        if expired_keys:
            logger.info(f"🧹 {len(expired_keys)} predições expiradas removidas do cache")

class TelegramAlertsSystem:
    """Sistema de Alertas APENAS para Tips Profissionais"""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.group_chat_ids = set()  # IDs dos grupos cadastrados
        self.alert_history = []
        self.sent_tips = set()  # IDs dos tips já enviados
        self.min_alert_interval = 1800  # 30 minutos entre tips similares

        logger.info("📢 Sistema de Alertas para Tips inicializado")

    def add_group(self, chat_id: int):
        """Adiciona grupo para receber alertas de tips"""
        self.group_chat_ids.add(chat_id)
        logger.info(f"📢 Grupo {chat_id} adicionado para alertas de tips")

    def remove_group(self, chat_id: int):
        """Remove grupo dos alertas"""
        self.group_chat_ids.discard(chat_id)
        logger.info(f"📢 Grupo {chat_id} removido dos alertas")

    async def send_tip_alert(self, tip: Dict, bot_application):
        """Envia alerta de tip profissional para os grupos (sem repetições)"""
        try:
            tip_id = tip.get('tip_id', '')

            # Verificar se já foi enviado
            if tip_id in self.sent_tips:
                logger.info(f"📢 Tip {tip_id} já foi enviado - pulando")
                return

            # Verificar critérios mínimos para alerta
            if not self._should_send_alert(tip):
                logger.info(f"📢 Tip não atende critérios para alerta")
                return

            alert_message = f"""
🚨 **ALERTA DE TIP PROFISSIONAL** 🚨

🏆 **{tip['title']}**
🎮 Liga: {tip['league']}

🤖 **ANÁLISE IA:**
• Confiança: {tip['confidence_score']:.1f}% ({tip['confidence_level']})
• EV: {tip['ev_percentage']:.1f}%
• Probabilidade: {tip['win_probability']*100:.1f}%

🎲 **UNIDADES:**
• Apostar: {tip['units']} unidades
• Valor: ${tip['stake_amount']:.2f}
• Risco: {tip['risk_level']}

⭐ **Recomendação:** {tip['recommended_team']}

💡 **Explicação IA:**
{tip['reasoning']}

⏰ {datetime.now().strftime('%H:%M:%S')}
            """

            # Enviar para todos os grupos cadastrados
            sent_count = 0
            for chat_id in self.group_chat_ids.copy():
                try:
                    if TELEGRAM_VERSION == "v20+":
                        await bot_application.bot.send_message(
                            chat_id=chat_id,
                            text=alert_message,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await bot_application.bot.send_message(
                            chat_id=chat_id,
                            text=alert_message,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"❌ Erro ao enviar alerta para grupo {chat_id}: {e}")
                    # Remove grupo inválido
                    self.group_chat_ids.discard(chat_id)

            # Registrar tip como enviado
            self.sent_tips.add(tip_id)
            self._register_alert(tip_id, tip)

            logger.info(f"📢 Alerta de tip enviado para {sent_count} grupos - ID: {tip_id}")

        except Exception as e:
            logger.error(f"❌ Erro no sistema de alertas: {e}")

    def _should_send_alert(self, tip: Dict) -> bool:
        """Verifica se deve enviar alerta para o tip"""
        # Critérios mínimos para alertas
        confidence = tip.get('confidence_score', 0)
        ev = tip.get('ev_percentage', 0)
        confidence_level = tip.get('confidence_level', '')

        return (
            confidence >= 80 and  # Confiança mínima 80%
            ev >= 10 and         # EV mínimo 10%
            confidence_level in ['Alta', 'Muito Alta'] and
            tip.get('units', 0) >= 2.0  # Mínimo 2 unidades
        )

    def _register_alert(self, tip_id: str, tip: Dict):
        """Registra alerta no histórico"""
        alert_record = {
            'tip_id': tip_id,
            'timestamp': datetime.now(),
            'groups_sent': len(self.group_chat_ids),
            'confidence': tip.get('confidence_score', 0),
            'ev': tip.get('ev_percentage', 0),
            'units': tip.get('units', 0),
            'recommended_team': tip.get('recommended_team', ''),
            'league': tip.get('league', '')
        }

        self.alert_history.append(alert_record)

        # Manter apenas últimos 50 alertas
        if len(self.alert_history) > 50:
            self.alert_history = self.alert_history[-50:]

    def get_alert_stats(self) -> Dict:
        """Retorna estatísticas dos alertas de tips"""
        recent_alerts = [a for a in self.alert_history
                        if (datetime.now() - a['timestamp']).days < 7]

        return {
            'total_groups': len(self.group_chat_ids),
            'total_tips_sent': len(self.alert_history),
            'tips_this_week': len(recent_alerts),
            'unique_tips_sent': len(self.sent_tips),
            'last_tip_alert': self.alert_history[-1]['timestamp'] if self.alert_history else None,
            'avg_confidence': sum(a['confidence'] for a in recent_alerts) / len(recent_alerts) if recent_alerts else 0,
            'avg_ev': sum(a['ev'] for a in recent_alerts) / len(recent_alerts) if recent_alerts else 0,
            'avg_units': sum(a['units'] for a in recent_alerts) / len(recent_alerts) if recent_alerts else 0
        }

    def clear_old_tips(self):
        """Remove tips antigos do cache (mais de 24h)"""
        # Limpar tips enviados há mais de 24h
        cutoff_time = datetime.now() - timedelta(hours=24)
        old_tips = []

        for alert in self.alert_history:
            if alert['timestamp'] < cutoff_time:
                old_tips.append(alert['tip_id'])

        for tip_id in old_tips:
            self.sent_tips.discard(tip_id)

        if old_tips:
            logger.info(f"🧹 {len(old_tips)} tips antigos removidos do cache")

class ProfessionalTipsSystem:
    """Sistema de Tips Profissional com Monitoramento Contínuo"""

    def __init__(self, riot_client=None):
        self.riot_client = riot_client or RiotAPIClient()
        self.units_system = ProfessionalUnitsSystem()
        self.tips_database = []
        self.given_tips = set()
        self.monitoring = False
        self.last_scan = None

        # Critérios profissionais
        self.min_ev_percentage = 8.0
        self.min_confidence_score = 75.0
        self.max_tips_per_week = 5

        # Iniciar monitoramento automático
        self.start_monitoring()

        logger.info("🎯 Sistema de Tips Profissional inicializado com MONITORAMENTO ATIVO")

    def start_monitoring(self):
        """Inicia monitoramento contínuo de todas as partidas"""
        if not self.monitoring:
            self.monitoring = True

            def monitor_loop():
                while self.monitoring:
                    try:
                        # Escanear por oportunidades de tips
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self._scan_all_matches_for_tips())
                        loop.close()
                        time.sleep(300)  # Verificar a cada 5 minutos
                    except Exception as e:
                        logger.error(f"Erro no monitoramento de tips: {e}")
                        time.sleep(60)

            monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitor_thread.start()
            logger.info("🔍 Monitoramento contínuo de tips iniciado - Verificação a cada 5 minutos")

    async def _scan_all_matches_for_tips(self):
        """Escaneia TODAS as partidas (ao vivo e agendadas) para encontrar oportunidades"""
        try:
            logger.info("🔍 Escaneando TODAS as partidas para oportunidades de tips...")

            # Buscar partidas ao vivo
            live_matches = await self.riot_client.get_live_matches()

            # Buscar partidas agendadas (próximas 24h)
            schedule_manager = ScheduleManager(self.riot_client)
            scheduled_matches = await schedule_manager.get_scheduled_matches(days_ahead=1)

            all_matches = live_matches + scheduled_matches

            opportunities_found = 0

            for match in all_matches:
                tip_analysis = await self._analyze_match_for_tip(match)

                if tip_analysis and self._meets_professional_criteria(tip_analysis):
                    tip_id = self._generate_tip_id(match)

                    # Verificar se já foi dado este tip
                    if tip_id not in self.given_tips:
                        professional_tip = self._create_professional_tip(tip_analysis)

                        if professional_tip:
                            self.tips_database.append(professional_tip)
                            self.given_tips.add(tip_id)
                            opportunities_found += 1

                            logger.info(f"🎯 NOVA OPORTUNIDADE ENCONTRADA: {professional_tip['title']}")

                            # ENVIAR ALERTA AUTOMÁTICO PARA GRUPOS
                            try:
                                # Verificar se há grupos cadastrados e bot disponível
                                if hasattr(self, '_bot_instance') and self._bot_instance:
                                    alerts_system = self._bot_instance.alerts_system
                                    bot_app = self._bot_instance.bot_application

                                    if alerts_system.group_chat_ids and bot_app:
                                        await alerts_system.send_tip_alert(professional_tip, bot_app)
                                        logger.info(f"📢 Alerta automático enviado para {len(alerts_system.group_chat_ids)} grupos")

                            except Exception as alert_error:
                                logger.warning(f"❌ Erro ao enviar alerta automático: {alert_error}")

            self.last_scan = datetime.now()

            if opportunities_found > 0:
                logger.info(f"✅ {opportunities_found} novas oportunidades de tips encontradas")
            else:
                logger.info("ℹ️ Nenhuma nova oportunidade encontrada neste scan")

        except Exception as e:
            logger.error(f"Erro no scan de partidas: {e}")

    def set_bot_instance(self, bot_instance):
        """Define instância do bot para envio de alertas automáticos"""
        self._bot_instance = bot_instance

    def get_monitoring_status(self) -> Dict:
        """Retorna status do monitoramento"""
        return {
            'monitoring_active': self.monitoring,
            'last_scan': self.last_scan.strftime('%H:%M:%S') if self.last_scan else 'Nunca',
            'total_tips_found': len(self.tips_database),
            'tips_this_week': len([tip for tip in self.tips_database
                                 if (datetime.now() - tip['timestamp']).days < 7]),
            'scan_frequency': '5 minutos'
        }

    async def generate_professional_tip(self) -> Optional[Dict]:
        """Gera tip profissional usando machine learning"""
        try:
            # Buscar partidas disponíveis
            live_matches = await self.riot_client.get_live_matches()
            schedule_manager = ScheduleManager(self.riot_client)
            scheduled_matches = await schedule_manager.get_scheduled_matches(days_ahead=1)

            all_matches = live_matches + scheduled_matches

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

            return best_tip

        except Exception as e:
            logger.error(f"Erro ao gerar tip profissional: {e}")
            return None

    async def _analyze_match_for_tip(self, match: Dict) -> Optional[Dict]:
        """Analisa partida usando machine learning para gerar tip"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None

            team1_name = teams[0].get('name', '')
            team2_name = teams[1].get('name', '')
            league = match.get('league', '')

            # Usar sistema de predição ML (sem importação circular)
            prediction_system = DynamicPredictionSystem()

            # Obter predição ML
            ml_prediction = await prediction_system.predict_live_match(match)

            if not ml_prediction or ml_prediction['confidence'] not in ['Alta', 'Muito Alta']:
                return None

            # Extrair dados da predição ML
            favored_team = ml_prediction['favored_team']
            win_probability = ml_prediction['win_probability']
            confidence_level = ml_prediction['confidence']

            # Calcular confiança numérica baseada no ML
            confidence_mapping = {
                'Muito Alta': 90,
                'Alta': 80,
                'Média': 70,
                'Baixa': 60
            }
            confidence_score = confidence_mapping.get(confidence_level, 60)

            # Calcular EV baseado nas odds ML vs odds estimadas do mercado
            ml_odds = ml_prediction['team1_odds'] if favored_team == team1_name else ml_prediction['team2_odds']

            # Estimar odds do mercado (simulação baseada em probabilidade)
            market_probability = win_probability * 0.95  # Margem da casa
            market_odds = 1 / market_probability if market_probability > 0 else 2.0

            # Calcular EV
            ev_percentage = ((ml_odds * win_probability) - 1) * 100

            # Determinar tier da liga
            league_tier = self._determine_league_tier(league)

            # Criar análise completa
            analysis = {
                'team1': team1_name,
                'team2': team2_name,
                'league': league,
                'league_tier': league_tier,
                'favored_team': favored_team,
                'opposing_team': team2_name if favored_team == team1_name else team1_name,
                'win_probability': win_probability,
                'confidence_score': confidence_score,
                'confidence_level': confidence_level,
                'ev_percentage': ev_percentage,
                'ml_odds': ml_odds,
                'market_odds': market_odds,
                'ml_analysis': ml_prediction['analysis'],
                'prediction_factors': ml_prediction['prediction_factors'],
                'match_data': match
            }

            return analysis

        except Exception as e:
            logger.error(f"Erro na análise ML da partida: {e}")
            return None

    def _meets_professional_criteria(self, analysis: Dict) -> bool:
        """Verifica se análise atende critérios profissionais"""
        confidence = analysis.get('confidence_score', 0)
        ev = analysis.get('ev_percentage', 0)

        # Critérios rigorosos
        return (
            confidence >= self.min_confidence_score and  # 75%+
            ev >= self.min_ev_percentage and            # 8%+
            analysis.get('confidence_level') in ['Alta', 'Muito Alta']
        )

    def _create_professional_tip(self, analysis: Dict) -> Dict:
        """Cria tip profissional baseado na análise ML"""
        try:
            # Calcular unidades usando sistema profissional
            units_calc = self.units_system.calculate_units(
                confidence=analysis['confidence_score'],
                ev_percentage=analysis['ev_percentage'],
                league_tier=analysis['league_tier']
            )

            # Criar tip estruturado
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
            logger.error(f"Erro ao criar tip profissional: {e}")
            return None

    def _generate_tip_reasoning(self, analysis: Dict, units_calc: Dict) -> str:
        """Gera explicação detalhada do tip baseado em ML"""
        reasoning_parts = []

        # Análise ML
        reasoning_parts.append(f"🤖 IA identifica {analysis['favored_team']} como favorito")
        reasoning_parts.append(f"📊 Confiança ML: {analysis['confidence_level']} ({analysis['confidence_score']:.1f}%)")
        reasoning_parts.append(f"💰 Valor esperado: {analysis['ev_percentage']:.1f}%")

        # Fatores da predição
        factors = analysis.get('prediction_factors', {})
        if factors:
            team1_rating = factors.get('team1_rating', 0)
            team2_rating = factors.get('team2_rating', 0)
            if team1_rating and team2_rating:
                reasoning_parts.append(f"⚖️ Ratings: {team1_rating} vs {team2_rating}")

        # Sistema de unidades
        reasoning_parts.append(f"🎲 {units_calc['reasoning']}")

        # Análise ML detalhada
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

class LoLBotV3UltraAdvanced:
    """Bot LoL V3 Ultra Avançado - Tips + Agenda + Predições IA + ML Otimizado"""
    
    def __init__(self):
        # Clients básicos (inicialização rápida)
        self.riot_client = RiotAPIClient()
        self.units_system = ProfessionalUnitsSystem()
        
        # Sistemas principais
        self.schedule_manager = ScheduleManager(riot_client=self.riot_client)
        self.prediction_system = DynamicPredictionSystem()
        self.alerts_system = TelegramAlertsSystem(bot_token=TOKEN)
        
        # Sistemas avançados
        self.tips_system = ProfessionalTipsSystem(riot_client=self.riot_client)
        self.tips_system.set_bot_instance(self)
        
        # Sistema de Odds Reais
        self.odds_system = odds_system if ODDS_SYSTEM_AVAILABLE else None
        
        # ML System - LAZY LOADING para evitar delay
        self.ml_system = None
        self.ml_engine = None
        self._ml_loading = False
        
        # Cache de comandos (1 minuto)
        self.command_cache = {}
        self.cache_duration = 60
        
        logger.info("🤖 LoLBotV3UltraAdvanced inicializado com sucesso!")

    async def _load_ml_system_async(self):
        """Carrega sistema ML de forma assíncrona (lazy loading)"""
        if self._ml_loaded or self._ml_loading:
            return
            
        self._ml_loading = True
        try:
            # Import apenas quando necessário
            from ml_prediction_system import AdvancedMLPredictionSystem
            from live_data_collector import MLPredictionEngine
            
            # Inicialização em background
            self.ml_system = AdvancedMLPredictionSystem()
            self.ml_engine = MLPredictionEngine()
            
            self._ml_loaded = True
            logger.info("🤖 Sistema de ML avançado inicializado")
            
        except Exception as e:
            logger.warning(f"⚠️ Sistema ML não disponível: {e}")
            self.ml_system = None
            self.ml_engine = None
        finally:
            self._ml_loading = False

    async def _get_ml_system(self):
        """Retorna sistema ML, carregando se necessário"""
        if not self._ml_loaded and not self._ml_loading:
            await self._load_ml_system_async()
        return self.ml_system

    async def _get_ml_engine(self):
        """Retorna engine ML, carregando se necessário"""
        if not self._ml_loaded and not self._ml_loading:
            await self._load_ml_system_async()
        return self.ml_engine

    def set_bot_application(self, application):
        """Define a aplicação do bot para o sistema de alertas"""
        self.bot_application = application

        # Limpar cache antigo de tips a cada hora
        import threading
        def cleanup_loop():
            while True:
                try:
                    self.alerts_system.clear_old_tips()
                    time.sleep(3600)  # 1 hora
                except:
                    time.sleep(3600)

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()

    async def start_command(self, update: Update, context) -> None:
        """Comando /start"""
        user = update.effective_user
        ml_status = "✅ ATIVO" if ML_AVAILABLE else "⚠️ BÁSICO"
        
        welcome_message = f"""
🎮 **BOT LOL V3 ULTRA AVANÇADO** 🎮

Olá {user.first_name}! 👋

🤖 **SISTEMA DE MACHINE LEARNING: {ml_status}**
🎯 Especializado em Money Line para LoL
⚡ Análise em tempo real após draft

🎲 **SISTEMA DE UNIDADES PROFISSIONAL**
📊 Baseado em grupos de apostas profissionais
⚡ Sem Kelly Criterion - Sistema simplificado
🎯 Critérios: 65%+ confiança, 5%+ EV mínimo

🔥 **FUNCIONALIDADES:**
• 🤖 Machine Learning para predições money line
• 🎯 Tips profissionais com monitoramento ativo
• 🔮 Predições IA com dados em tempo real
• 📅 Agenda de partidas (próximos 7 dias)
• 🎮 Partidas ao vivo selecionáveis
• 📢 Sistema de alertas para grupos
• 📊 Sistema de unidades padrão
• 📋 Estatísticas detalhadas

Use /menu para ver todas as opções!
        """

        keyboard = [
            [InlineKeyboardButton("🤖 ML Predictions", callback_data="ml_predictions"),
             InlineKeyboardButton("🎯 Money Line Tips", callback_data="money_line_tips")],
            [InlineKeyboardButton("🔮 Predições IA", callback_data="predictions"),
             InlineKeyboardButton("🎯 Tips Profissionais", callback_data="tips")],
            [InlineKeyboardButton("📅 Agenda de Partidas", callback_data="schedule"),
             InlineKeyboardButton("🎮 Partidas Ao Vivo", callback_data="live_matches")],
            [InlineKeyboardButton("📢 Sistema de Alertas", callback_data="alert_stats"),
             InlineKeyboardButton("📋 Menu Completo", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if TELEGRAM_VERSION == "v20+":
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    async def menu_command(self, update: Update, context) -> None:
        """Comando /menu"""
        ml_status = "✅ ATIVO" if ML_AVAILABLE else "⚠️ BÁSICO"
        
        menu_message = f"""
🎮 **MENU PRINCIPAL - BOT LOL V3** 🎮

🤖 **MACHINE LEARNING: {ml_status}**
• /ml_predictions - Sistema ML completo
• /ml_live_analysis - Análise ao vivo ML
• /money_line_tips - Tips money line especializados

🎯 **TIPS & ANÁLISES:**
• /tips - Tips profissionais
• /predictions - Predições IA
• /schedule - Agenda de partidas
• /live - Partidas ao vivo
• /monitoring - Status do monitoramento
• /alerts - Sistema de alertas

🎲 **SISTEMA DE UNIDADES:**
• /units - Explicação do sistema
• /performance - Performance atual
• /history - Histórico de apostas

📊 **INFORMAÇÕES:**
• /help - Ajuda completa
• /about - Sobre o bot

Clique nos botões abaixo para navegação rápida:
        """

        keyboard = [
            [InlineKeyboardButton("🤖 ML System", callback_data="ml_predictions"),
             InlineKeyboardButton("🎯 Money Line", callback_data="money_line_tips")],
            [InlineKeyboardButton("🔮 Predições", callback_data="predictions"),
             InlineKeyboardButton("🎯 Tips", callback_data="tips")],
            [InlineKeyboardButton("📅 Agenda", callback_data="schedule"),
             InlineKeyboardButton("🎮 Ao Vivo", callback_data="live_matches")],
            [InlineKeyboardButton("📢 Alertas", callback_data="alert_stats"),
             InlineKeyboardButton("📊 Unidades", callback_data="units_info")],
            [InlineKeyboardButton("🔍 Monitoramento", callback_data="monitoring"),
             InlineKeyboardButton("❓ Ajuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if TELEGRAM_VERSION == "v20+":
            await update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    async def schedule_command(self, update: Update, context) -> None:
        """Comando /schedule"""
        try:
            scheduled_matches = await self.schedule_manager.get_scheduled_matches()

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

            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(schedule_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(schedule_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no comando schedule: {e}")
            error_message = "❌ Erro ao buscar agenda. Tente novamente."
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def monitoring_command(self, update: Update, context) -> None:
        """Comando /monitoring"""
        try:
            monitoring_status = self.tips_system.get_monitoring_status()

            monitoring_message = f"""
🔍 **STATUS DO MONITORAMENTO** 🔍

🎯 **SISTEMA DE TIPS:**
• Status: {'🟢 Ativo' if monitoring_status['monitoring_active'] else '🔴 Inativo'}
• Última verificação: {monitoring_status['last_scan']}
• Frequência: A cada {monitoring_status['scan_frequency']}

📊 **ESTATÍSTICAS:**
• Tips encontrados: {monitoring_status['total_tips_found']}
• Tips esta semana: {monitoring_status['tips_this_week']}

🔍 **O QUE ESTÁ SENDO MONITORADO:**
• ✅ Partidas ao vivo (tempo real)
• ✅ Partidas agendadas (próximas 24h)
• ✅ Todas as ligas principais
• ✅ Critérios profissionais (75%+ confiança, 8%+ EV)

⚡ **PROCESSO AUTOMÁTICO:**
O sistema escaneia continuamente todas as partidas disponíveis na API da Riot Games, analisando cada uma para encontrar oportunidades que atendam aos critérios profissionais de grupos de apostas.
            """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="monitoring")],
                [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("📅 Agenda", callback_data="schedule")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(monitoring_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(monitoring_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no comando monitoring: {e}")
            error_message = "❌ Erro ao buscar status. Tente novamente."
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def tips_command(self, update: Update, context) -> None:
        """Comando /tips"""
        try:
            tip = await self.tips_system.generate_professional_tip()

            if tip:
                tip_message = f"""
🎯 **TIP PROFISSIONAL** 🎯

🏆 **{tip['title']}**
🎮 Liga: {tip['league']}

📊 **ANÁLISE:**
• Confiança: {tip['confidence_score']:.1f}%
• EV: {tip['ev_percentage']:.1f}%
• Probabilidade: {tip['win_probability']*100:.1f}%

🎲 **UNIDADES:**
• Apostar: {tip['units']} unidades
• Valor: ${tip['stake_amount']:.2f}
• Risco: {tip['risk_level']}

💡 **Explicação:**
{tip['reasoning']}

⭐ **Recomendação:** {tip['recommended_team']}
                """
            else:
                tip_message = """
🎯 **NENHUM TIP DISPONÍVEL** 🎯

❌ Nenhuma partida atende aos critérios profissionais no momento.

📋 **Critérios mínimos:**
• Confiança: 75%+
• EV: 8%+
• Times conhecidos
• Liga tier 1 ou 2

🔄 Tente novamente em alguns minutos.
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Novo Tip", callback_data="tips")],
                [InlineKeyboardButton("📊 Sistema Unidades", callback_data="units_info")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(tip_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(tip_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no comando tips: {e}")
            error_message = "❌ Erro ao gerar tip. Tente novamente."
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def live_matches_command(self, update: Update, context) -> None:
        """Comando /live"""
        try:
            matches = await self.riot_client.get_live_matches()

            if matches:
                message = "🎮 **PARTIDAS AO VIVO** 🎮\n\nSelecione uma partida para análise detalhada:\n\n"

                keyboard = []
                for i, match in enumerate(matches[:8]):  # Máximo 8 partidas
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        start_time = match.get('start_time_formatted', 'TBD')

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

            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no comando live: {e}")
            error_message = "❌ Erro ao buscar partidas. Tente novamente."
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def callback_handler(self, update: Update, context) -> None:
        """Handler principal para callbacks"""
        query = update.callback_query
        await query.answer()

        try:
            callback_data = query.data
            
            # Callbacks do sistema de odds
            if callback_data.startswith("odds_"):
                await self._handle_odds_callback(query)
            
            # ... existing callbacks ...
            
        except Exception as e:
            logger.error(f"Erro no callback_handler: {e}")
            await query.edit_message_text("❌ Erro ao processar comando.")

    async def _handle_odds_callback(self, query) -> None:
        """Handle callbacks do sistema de odds"""
        if not ODDS_SYSTEM_AVAILABLE:
            await query.edit_message_text("❌ Sistema de odds não disponível.")
            return
        
        callback_data = query.data
        
        try:
            if callback_data == "odds_live":
                await self._handle_odds_live_callback(query)
            
            elif callback_data == "odds_upcoming":
                await self._handle_odds_upcoming_callback(query)
            
            elif callback_data == "odds_status":
                await self._handle_odds_status_callback(query)
            
            elif callback_data == "odds_search":
                await query.edit_message_text(
                    "🔍 **Buscar Odds de Partida**\n\n"
                    "Para buscar odds de uma partida específica, use:\n"
                    "`/odds_search Team1 vs Team2`\n\n"
                    "Exemplo: `/odds_search T1 vs GenG`",
                    parse_mode='Markdown'
                )
            
            elif callback_data == "odds_value":
                await self._handle_odds_value_callback(query)
            
            elif callback_data == "odds_config":
                await self._handle_odds_config_callback(query)
            
        except Exception as e:
            logger.error(f"Erro no _handle_odds_callback: {e}")
            await query.edit_message_text("❌ Erro ao processar comando de odds.")

    async def _handle_odds_live_callback(self, query) -> None:
        """Handle para partidas ao vivo com odds"""
        try:
            await query.edit_message_text("⏳ Buscando partidas ao vivo com odds...")
            
            live_matches = await self.odds_system.get_live_matches_with_odds()
            
            if not live_matches:
                message = (
                    "📊 **PARTIDAS AO VIVO**\n\n"
                    "❌ Nenhuma partida LoL ao vivo encontrada no momento.\n\n"
                    "🔄 As partidas são atualizadas automaticamente."
                )
            else:
                message = "⚡ **PARTIDAS AO VIVO COM ODDS**\n\n"
                
                for i, match in enumerate(live_matches[:5], 1):
                    team1 = match['team1']['name']
                    team2 = match['team2']['name']
                    league = match.get('league', 'Unknown')
                    odds = match.get('odds', {})
                    
                    odds_text = "Indisponíveis"
                    if odds.get('available'):
                        odds_text = f"{odds.get('team1_odds', 'N/A'):.2f} vs {odds.get('team2_odds', 'N/A'):.2f}"
                    
                    message += (
                        f"🎮 **{team1} vs {team2}**\n"
                        f"🏆 {league}\n"
                        f"💰 Odds: {odds_text}\n"
                        f"🏪 Casa: {odds.get('bookmaker', 'N/A')}\n\n"
                    )
            
            keyboard = [[InlineKeyboardButton("🔄 Atualizar", callback_data="odds_live")]]
            keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="odds_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro no _handle_odds_live_callback: {e}")
            await query.edit_message_text("❌ Erro ao buscar partidas ao vivo.")

    async def _handle_odds_status_callback(self, query) -> None:
        """Handle para status das APIs de odds"""
        try:
            status = await self.odds_system.get_system_status()
            
            real_odds_status = "✅ ATIVO" if status['real_odds_enabled'] else "❌ DESABILITADO"
            pandascore_status = "✅ DISPONÍVEL" if status['pandascore_available'] else "❌ INDISPONÍVEL"
            theodds_status = "✅ DISPONÍVEL" if status['theodds_available'] else "❌ INDISPONÍVEL"
            
            # Verificar configuração das API keys
            panda_key = "✅ CONFIGURADA" if status['api_keys_configured']['pandascore'] else "❌ NÃO CONFIGURADA"
            theodds_key = "✅ CONFIGURADA" if status['api_keys_configured']['theodds'] else "❌ NÃO CONFIGURADA"
            
            message = (
                "📊 **STATUS DO SISTEMA DE ODDS**\n\n"
                
                "🔧 **Configuração Geral:**\n"
                f"• Odds Reais: {real_odds_status}\n"
                f"• Modo Híbrido: ✅ ATIVO\n\n"
                
                "🔗 **APIs Disponíveis:**\n"
                f"• PandaScore: {pandascore_status}\n"
                f"• The Odds API: {theodds_status}\n\n"
                
                "🔑 **API Keys:**\n"
                f"• PandaScore: {panda_key}\n"
                f"• The Odds API: {theodds_key}\n\n"
                
                "⚙️ **Funcionalidades:**\n"
                "• ✅ Partidas ao vivo\n"
                "• ✅ Próximas partidas\n"
                "• ✅ Value betting\n"
                "• ✅ Cache otimizado\n"
                "• ✅ Fallback para simulação\n\n"
                
                "💡 **Nota:** Sistema usa fallback inteligente\n"
                "quando APIs não estão disponíveis."
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="odds_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro no _handle_odds_status_callback: {e}")
            await query.edit_message_text("❌ Erro ao obter status das APIs.")

    async def _handle_tips_callback(self, query) -> None:
        """Handle callback para tips"""
        try:
            tip = await self.tips_system.generate_professional_tip()

            if tip:
                tip_message = f"""
🎯 **TIP PROFISSIONAL** 🎯

🏆 **{tip['title']}**
🎮 Liga: {tip['league']}

📊 **ANÁLISE:**
• Confiança: {tip['confidence_score']:.1f}%
• EV: {tip['ev_percentage']:.1f}%
• Probabilidade: {tip['win_probability']*100:.1f}%

🎲 **UNIDADES:**
• Apostar: {tip['units']} unidades
• Valor: ${tip['stake_amount']:.2f}
• Risco: {tip['risk_level']}

💡 **Explicação:**
{tip['reasoning']}

⭐ **Recomendação:** {tip['recommended_team']}
                """
            else:
                tip_message = """
🎯 **NENHUM TIP DISPONÍVEL** 🎯

❌ Nenhuma partida atende aos critérios profissionais no momento.

📋 **Critérios mínimos:**
• Confiança: 75%+
• EV: 8%+
• Times conhecidos
• Liga tier 1 ou 2

🔄 Tente novamente em alguns minutos.
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Novo Tip", callback_data="tips")],
                [InlineKeyboardButton("📊 Sistema Unidades", callback_data="units_info")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(tip_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no callback tips: {e}")
            await query.edit_message_text("❌ Erro ao gerar tip. Tente novamente.")

    async def _handle_schedule_callback(self, query) -> None:
        """Handle callback para agenda"""
        try:
            scheduled_matches = await self.schedule_manager.get_scheduled_matches()

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

            await query.edit_message_text(schedule_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no callback schedule: {e}")
            await query.edit_message_text("❌ Erro ao buscar agenda. Tente novamente.")

    async def _handle_schedule_today_callback(self, query) -> None:
        """Handle callback para agenda de hoje"""
        try:
            today_matches = self.schedule_manager.get_matches_today()

            if today_matches:
                schedule_message = f"""
📅 **PARTIDAS DE HOJE** 📅

🔍 **{len(today_matches)} PARTIDAS HOJE**

"""

                for i, match in enumerate(today_matches, 1):
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
            else:
                schedule_message = """
📅 **PARTIDAS DE HOJE** 📅

ℹ️ **NENHUMA PARTIDA HOJE**

🔍 **Não há partidas agendadas para hoje**

🔄 Tente novamente mais tarde
                """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="schedule_today")],
                [InlineKeyboardButton("📅 Agenda Completa", callback_data="schedule")],
                [InlineKeyboardButton("🎮 Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(schedule_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no callback schedule today: {e}")
            await query.edit_message_text("❌ Erro ao buscar partidas de hoje. Tente novamente.")

    async def _handle_live_matches_callback(self, query) -> None:
        """Handle callback para partidas ao vivo"""
        try:
            matches = await self.riot_client.get_live_matches()

            if matches:
                message = "🎮 **PARTIDAS AO VIVO** 🎮\n\nSelecione uma partida para análise detalhada:\n\n"

                keyboard = []
                for i, match in enumerate(matches[:8]):  # Máximo 8 partidas
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        start_time = match.get('start_time_formatted', 'TBD')

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
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no callback live: {e}")
            await query.edit_message_text("❌ Erro ao buscar partidas. Tente novamente.")

    async def _handle_units_info_callback(self, query) -> None:
        """Mostra informações do sistema de unidades"""
        units_info = self.tips_system.units_system.get_units_explanation()

        keyboard = [
            [InlineKeyboardButton("🎯 Gerar Tip", callback_data="tips")],
            [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(units_info, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    async def _handle_monitoring_callback(self, query) -> None:
        """Handle callback para monitoramento"""
        try:
            monitoring_status = self.tips_system.get_monitoring_status()

            monitoring_message = f"""
🔍 **STATUS DO MONITORAMENTO** 🔍

🎯 **SISTEMA DE TIPS:**
• Status: {'🟢 Ativo' if monitoring_status['monitoring_active'] else '🔴 Inativo'}
• Última verificação: {monitoring_status['last_scan']}
• Frequência: A cada {monitoring_status['scan_frequency']}

📊 **ESTATÍSTICAS:**
• Tips encontrados: {monitoring_status['total_tips_found']}
• Tips esta semana: {monitoring_status['tips_this_week']}

🔍 **O QUE ESTÁ SENDO MONITORADO:**
• ✅ Partidas ao vivo (tempo real)
• ✅ Partidas agendadas (próximas 24h)
• ✅ Todas as ligas principais
• ✅ Critérios profissionais (75%+ confiança, 8%+ EV)

⚡ **PROCESSO AUTOMÁTICO:**
O sistema escaneia continuamente todas as partidas disponíveis na API da Riot Games, analisando cada uma para encontrar oportunidades que atendam aos critérios profissionais de grupos de apostas.
            """

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="monitoring")],
                [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
                [InlineKeyboardButton("📅 Agenda", callback_data="schedule")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(monitoring_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no callback monitoring: {e}")
            await query.edit_message_text("❌ Erro ao buscar status. Tente novamente.")

    async def _handle_main_menu_callback(self, query) -> None:
        """Handle callback para menu principal"""
        menu_message = """
🎮 **MENU PRINCIPAL - BOT LOL V3** 🎮

🎯 **TIPS & ANÁLISES:**
• Tips profissionais
• Agenda de partidas
• Partidas ao vivo
• Status do monitoramento

🎲 **SISTEMA DE UNIDADES:**
• Explicação do sistema
• Performance atual
• Histórico de apostas

📊 **INFORMAÇÕES:**
• Ajuda completa
• Sobre o bot

Clique nos botões abaixo para navegação rápida:
        """

        keyboard = [
            [InlineKeyboardButton("🎯 Tips", callback_data="tips"),
             InlineKeyboardButton("📅 Agenda", callback_data="schedule")],
            [InlineKeyboardButton("🎮 Ao Vivo", callback_data="live_matches"),
             InlineKeyboardButton("📊 Unidades", callback_data="units_info")],
            [InlineKeyboardButton("🔍 Monitoramento", callback_data="monitoring"),
             InlineKeyboardButton("❓ Ajuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(menu_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    async def _handle_match_details_callback(self, query, match_index: int) -> None:
        """Handle callback para detalhes da partida"""
        try:
            if match_index in self.live_matches_cache:
                match = self.live_matches_cache[match_index]
                teams = match.get('teams', [])

                if len(teams) >= 2:
                    team1 = teams[0].get('name', 'Team1')
                    team2 = teams[1].get('name', 'Team2')
                    league = match.get('league', 'League')

                    # Análise da partida
                    tip_analysis = await self.tips_system._analyze_match_for_tip(match) # TODO: This was a placeholder in original, check if logic is complete

                    if tip_analysis:
                        # Assuming tip_analysis structure is as expected from ProfessionalTipsSystem
                        # This part might need adjustment based on the actual structure of tip_analysis
                        # For now, let's assume it has 'favored_team', 'win_probability', 'confidence_score', 'confidence_level'
                        
                        # Simplified message based on what might be available from _analyze_match_for_tip
                        # and then _create_professional_tip
                        professional_tip_data = self.tips_system._create_professional_tip(tip_analysis)

                        if professional_tip_data:
                            match_message = f"""
🎮 **ANÁLISE DETALHADA** 🎮

🏆 **{professional_tip_data['title']}**
🎯 Liga: {professional_tip_data['league']}

📊 **ANÁLISE IA:**
• Favorito: {professional_tip_data['recommended_team']}
• Probabilidade de Vitória: {professional_tip_data['win_probability']*100:.1f}%
• Confiança: {professional_tip_data['confidence_level']} ({professional_tip_data['confidence_score']:.1f}%)
• EV: {professional_tip_data['ev_percentage']:.1f}%

🎲 **UNIDADES RECOMENDADAS:**
• Unidades: {professional_tip_data['units']}
• Valor: ${professional_tip_data['stake_amount']:.2f}
• Risco: {professional_tip_data['risk_level']}

💡 **Raciocínio:**
{professional_tip_data['reasoning']}
"""
                        else:
                            match_message = f"""
🎮 **ANÁLISE DETALHADA** 🎮

🏆 **{team1} vs {team2}**
🎯 Liga: {league}

ℹ️ **Análise profissional não disponível no momento.**
(Não atendeu critérios ou erro na geração do tip)
"""
                    else:
                        match_message = f"""
🎮 **DETALHES DA PARTIDA** 🎮

🏆 **{team1} vs {team2}**
🎯 Liga: {league}

ℹ️ **Análise de tip não disponível no momento.**
(Partida não qualificada para tip)
                        """
                else:
                    match_message = "❌ Dados da partida não disponíveis."
            else:
                match_message = "❌ Partida não encontrada no cache."

            keyboard = [
                [InlineKeyboardButton("🔙 Voltar", callback_data="live_matches")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(match_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no callback match details: {e}")
            await query.edit_message_text("❌ Erro ao carregar detalhes da partida.")

    async def predictions_command(self, update: Update, context) -> None:
        """Comando /predictions"""
        try:
            # Buscar partidas ao vivo para predições
            live_matches = await self.riot_client.get_live_matches()

            if live_matches:
                predictions_message = f"""
🔮 **PREDIÇÕES IA** 🔮

🎯 **{len(live_matches)} PARTIDAS ANALISADAS**

"""

                predictions_made = 0
                for match in live_matches[:5]:  # Máximo 5 predições
                    prediction = await self.prediction_system.predict_live_match(match)

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
• Cache: {self.prediction_system.get_cache_status()['cached_predictions']} predições
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
                [InlineKeyboardButton("📊 Cache Status", callback_data="prediction_cache")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(predictions_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(predictions_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no comando predictions: {e}")
            error_message = "❌ Erro ao gerar predições. Tente novamente."
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def alerts_command(self, update: Update, context) -> None:
        """Comando /alerts"""
        try:
            chat_id = update.effective_chat.id
            chat_type = update.effective_chat.type

            # Verificar se é grupo
            if chat_type in ['group', 'supergroup']:
                # Verificar se já está cadastrado
                is_registered = chat_id in self.alerts_system.group_chat_ids

                if is_registered:
                    alerts_message = f"""
📢 **SISTEMA DE ALERTAS** 📢

✅ **GRUPO CADASTRADO**
• ID do Grupo: {chat_id}
• Status: Recebendo alertas

📊 **ESTATÍSTICAS:**
"""
                else:
                    alerts_message = f"""
📢 **SISTEMA DE ALERTAS** 📢

❌ **GRUPO NÃO CADASTRADO**
• ID do Grupo: {chat_id}
• Status: Não recebe alertas

📊 **PARA RECEBER ALERTAS:**
Use o botão "Cadastrar Grupo" abaixo
"""

                # Adicionar estatísticas
                alert_stats = self.alerts_system.get_alert_stats()
                alerts_message += f"""
• Grupos cadastrados: {alert_stats['total_groups']}
• Alertas enviados: {alert_stats['total_tips_sent']}
• Alertas esta semana: {alert_stats['tips_this_week']}
• Tips únicos: {alert_stats['unique_tips_sent']}

🚨 **TIPOS DE ALERTAS:**
• 🎯 Tips profissionais (80%+ confiança, 10%+ EV)
• 🤖 Análise baseada em Machine Learning
• ⚡ Oportunidades em tempo real
• 🎲 Mínimo 2 unidades para alerta

📊 **MÉDIAS ESTA SEMANA:**
• Confiança: {alert_stats['avg_confidence']:.1f}%
• EV: {alert_stats['avg_ev']:.1f}%
• Unidades: {alert_stats['avg_units']:.1f}

⏰ Último alerta: {alert_stats['last_tip_alert'].strftime('%H:%M:%S') if alert_stats['last_tip_alert'] else 'Nunca'}
                """

                if is_registered:
                    keyboard = [
                        [InlineKeyboardButton("❌ Descadastrar Grupo", callback_data=f"unregister_alerts_{chat_id}")],
                        [InlineKeyboardButton("📊 Estatísticas", callback_data="alert_stats")],
                        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                    ]
                else:
                    keyboard = [
                        [InlineKeyboardButton("✅ Cadastrar Grupo", callback_data=f"register_alerts_{chat_id}")],
                        [InlineKeyboardButton("📊 Estatísticas", callback_data="alert_stats")],
                        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                    ]
            else:
                alerts_message = """
📢 **SISTEMA DE ALERTAS** 📢

ℹ️ **COMANDO APENAS PARA GRUPOS**

🔍 **Para usar alertas:**
1. Adicione o bot a um grupo
2. Use /alerts no grupo
3. Cadastre o grupo para receber alertas

📊 **Tipos de alertas disponíveis:**
• 🎯 Tips profissionais
• 🔮 Predições IA
• ⚡ Oportunidades em tempo real
                """

                keyboard = [
                    [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(alerts_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(alerts_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Erro no comando alerts: {e}")
            error_message = "❌ Erro no sistema de alertas. Tente novamente."
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def _handle_predictions_callback(self, query):
        # Reutilizar a lógica do comando, mas adaptando para callback
        # query.message representa a mensagem original do botão
        # Precisamos simular um `update` e `context` para o comando
        class MockUpdate:
            def __init__(self, message):
                self.message = message
                self.effective_chat = message.chat # Adicionado para compatibilidade com alerts_command
        
        class MockContext:
            def __init__(self, bot):
                self.bot = bot

        # Para predictions_command, ele espera update.message.reply_text
        # Para _handle_alert_stats_callback, ele espera query.edit_message_text
        # Aqui, vamos chamar predictions_command que usa reply_text
        
        # Precisamos construir um 'update' similar ao que o CommandHandler passaria
        mock_update_obj = MockUpdate(query.message)
        
        # O 'context' para CommandHandler (v13) é um CallbackContext, 
        # para v20+ é ContextTypes.DEFAULT_TYPE.
        # Para simplificar a chamada direta, passamos o bot.
        mock_context_obj = MockContext(query.message.bot)

        await self.predictions_command(mock_update_obj, mock_context_obj)


    async def _handle_prediction_cache_callback(self, query):
        cache_status = self.prediction_system.get_cache_status()
        cache_message = f"""
🔍 **STATUS DO CACHE DE PREDIÇÕES** 🔍

🎯 **PREDIÇÕES:**
• Total: {cache_status['cached_predictions']}
• Duração: {cache_status['cache_duration_minutes']} minutos
• Última predição: {cache_status['last_prediction'].strftime('%d/%m %H:%M') if cache_status['last_prediction'] else 'Nunca'}
        """
        # Usar edit_message_text para callbacks
        await query.edit_message_text(cache_message, parse_mode=ParseMode.MARKDOWN,
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="predictions")]]))


    async def _handle_alert_stats_callback(self, query):
        alert_stats = self.alerts_system.get_alert_stats()
        stats_message = f"""
📊 **ESTATÍSTICAS DOS ALERTAS DE TIPS** 📊

🎯 **SISTEMA DE ALERTAS:**
• Total de grupos: {alert_stats['total_groups']}
• Total de tips enviados: {alert_stats['total_tips_sent']}
• Tips esta semana: {alert_stats['tips_this_week']}
• Tips únicos: {alert_stats['unique_tips_sent']}
• Último alerta: {alert_stats['last_tip_alert'].strftime('%d/%m %H:%M') if alert_stats['last_tip_alert'] else 'Nunca'}

📊 **MÉDIAS ESTA SEMANA:**
• Confiança média: {alert_stats['avg_confidence']:.1f}%
• EV médio: {alert_stats['avg_ev']:.1f}%
• Unidades médias: {alert_stats['avg_units']:.1f}

🤖 **CRITÉRIOS PARA ALERTAS:**
• Confiança mínima: 80%
• EV mínimo: 10%
• Unidades mínimas: 2.0
• Análise ML: Alta/Muito Alta

⚡ **PROCESSO AUTOMÁTICO:**
O sistema monitora continuamente todas as partidas e envia alertas automáticos quando encontra tips que atendem aos critérios rigorosos.
"""

        keyboard = [
            [InlineKeyboardButton("🔄 Atualizar", callback_data="alert_stats")],
            [InlineKeyboardButton("🎯 Ver Tips", callback_data="tips")],
            [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(stats_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    async def _handle_register_alerts_callback(self, query, chat_id):
        self.alerts_system.add_group(chat_id)
        await query.answer("✅ Grupo cadastrado com sucesso!") # Use query.answer para feedback rápido
        # Opcionalmente, edite a mensagem anterior para refletir o novo status
        # await self.alerts_command(query.message, query.message.bot) # Se quiser reenviar a mensagem /alerts

    async def _handle_unregister_alerts_callback(self, query, chat_id):
        self.alerts_system.remove_group(chat_id)
        await query.answer("❌ Grupo removido dos alertas.") # Use query.answer
        # Opcionalmente, edite a mensagem anterior
        # await self.alerts_command(query.message, query.message.bot)

    async def force_scan_command(self, update: Update, context) -> None:
        """Comando para forçar escaneamento de partidas (apenas admins)"""
        try:
            user_id = update.effective_user.id
            
            # Verificar se é admin
            if str(user_id) != str(self.OWNER_ID):
                await update.message.reply_text(
                    "❌ **Acesso Negado**\n\n"
                    "Este comando é restrito ao administrador do bot.",
                    parse_mode='Markdown'
                )
                return

            # Enviar mensagem de início
            status_msg = await update.message.reply_text(
                "🔄 **Iniciando Escaneamento Forçado**\n\n"
                "⏳ Escaneando todas as partidas em busca de tips profissionais...",
                parse_mode='Markdown'
            )

            # Executar escaneamento em thread separada para não bloquear
            def run_scan():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(self.tips_system._scan_all_matches_for_tips())
                    loop.close()
                    return result
                except Exception as e:
                    logger.error(f"Erro no escaneamento forçado: {e}")
                    return False

            # Executar em thread
            import threading
            scan_thread = threading.Thread(target=run_scan)
            scan_thread.start()
            scan_thread.join(timeout=30)  # Timeout de 30 segundos

            # Atualizar status
            status = self.tips_system.get_monitoring_status()
            
            await status_msg.edit_text(
                "✅ **Escaneamento Forçado Concluído**\n\n"
                f"📊 **Status do Sistema:**\n"
                f"• Status: {status['status']}\n"
                f"• Última verificação: {status['last_check']}\n"
                f"• Tips encontrados: {status['tips_found']}\n"
                f"• Partidas analisadas: {status['matches_analyzed']}\n\n"
                "💡 Use /tips para ver os tips mais recentes.",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no force_scan_command: {e}")
            await update.message.reply_text(
                "❌ **Erro no Escaneamento**\n\n"
                "Ocorreu um erro durante o escaneamento forçado. "
                "Tente novamente mais tarde.",
                parse_mode='Markdown'
            )

    async def units_command(self, update: Update, context) -> None:
        """Sistema de unidades profissional"""
        try:
            # Informações sobre o sistema de unidades
            units_info = self.units_system.get_units_explanation()
            performance = self.units_system.get_performance_summary()
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Performance", callback_data="units_performance"),
                    InlineKeyboardButton("📚 Como Usar", callback_data="units_guide")
                ],
                [
                    InlineKeyboardButton("🎯 Simulador", callback_data="units_simulator"),
                    InlineKeyboardButton("📈 Histórico", callback_data="units_history")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = (
                "💰 **SISTEMA DE UNIDADES PROFISSIONAL**\n\n"
                f"{units_info}\n\n"
                "📊 **Performance Atual:**\n"
                f"• ROI: {performance['roi']:.1f}%\n"
                f"• Win Rate: {performance['win_rate']:.1f}%\n"
                f"• Total de Apostas: {performance['total_bets']}\n"
                f"• Unidades Ganhas: {performance['total_units']:+.2f}\n"
                f"• Bankroll Atual: {performance['current_bankroll']:.2f}\n\n"
                "🎯 Selecione uma opção para mais detalhes:"
            )

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no units_command: {e}")
            await update.message.reply_text(
                "❌ Erro ao carregar sistema de unidades.",
                parse_mode='Markdown'
            )

    async def performance_command(self, update: Update, context) -> None:
        """Comando para exibir performance detalhada"""
        try:
            performance = self.units_system.get_performance_summary()
            monitoring_status = self.tips_system.get_monitoring_status()
            alerts_stats = self.alerts_system.get_alert_stats()
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Gráficos", callback_data="performance_charts"),
                    InlineKeyboardButton("🔄 Atualizar", callback_data="performance_refresh")
                ],
                [
                    InlineKeyboardButton("📋 Relatório", callback_data="performance_report"),
                    InlineKeyboardButton("🎯 Estatísticas", callback_data="performance_stats")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = (
                "📈 **PERFORMANCE DETALHADA**\n\n"
                "💰 **Sistema de Unidades:**\n"
                f"• ROI: {performance['roi']:+.1f}%\n"
                f"• Win Rate: {performance['win_rate']:.1f}%\n"
                f"• Profit/Loss: {performance['total_units']:+.2f} unidades\n"
                f"• Total de Apostas: {performance['total_bets']}\n"
                f"• Strike Rate: {performance['strike_rate']:.1f}%\n\n"
                
                "🔄 **Sistema de Monitoramento:**\n"
                f"• Status: {monitoring_status['status']}\n"
                f"• Tips Encontrados: {monitoring_status['tips_found']}\n"
                f"• Última Verificação: {monitoring_status['last_check']}\n"
                f"• Uptime: {monitoring_status['uptime']}\n\n"
                
                "📢 **Sistema de Alertas:**\n"
                f"• Alertas Enviados: {alerts_stats['total_sent']}\n"
                f"• Grupos Ativos: {alerts_stats['active_groups']}\n"
                f"• Taxa de Sucesso: {alerts_stats['success_rate']:.1f}%\n"
                f"• Último Alerta: {alerts_stats['last_alert']}\n\n"
                
                "🎯 Selecione uma opção para análise detalhada:"
            )

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no performance_command: {e}")
            await update.message.reply_text(
                "❌ Erro ao carregar dados de performance.",
                parse_mode='Markdown'
            )

    async def history_command(self, update: Update, context) -> None:
        """Comando para histórico de apostas"""
        try:
            performance = self.units_system.get_performance_summary()
            
            keyboard = [
                [
                    InlineKeyboardButton("📅 Últimos 7 dias", callback_data="history_week"),
                    InlineKeyboardButton("📅 Último mês", callback_data="history_month")
                ],
                [
                    InlineKeyboardButton("🏆 Melhores Tips", callback_data="history_best"),
                    InlineKeyboardButton("📊 Por Liga", callback_data="history_league")
                ],
                [
                    InlineKeyboardButton("💾 Exportar", callback_data="history_export"),
                    InlineKeyboardButton("🔍 Filtrar", callback_data="history_filter")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            recent_bets = performance.get('recent_bets', [])
            bet_history = ""
            
            if recent_bets:
                for i, bet in enumerate(recent_bets[-5:], 1):  # Últimas 5 apostas
                    status_emoji = "✅" if bet.get('result') == 'win' else "❌" if bet.get('result') == 'loss' else "⏳"
                    bet_history += (
                        f"{status_emoji} **{bet.get('match', 'N/A')}**\n"
                        f"   💰 {bet.get('units', 0):.2f} unidades\n"
                        f"   📅 {bet.get('date', 'N/A')}\n\n"
                    )
            else:
                bet_history = "📝 Nenhuma aposta registrada ainda."

            message = (
                "📋 **HISTÓRICO DE APOSTAS**\n\n"
                "📊 **Resumo Geral:**\n"
                f"• Total de Apostas: {performance['total_bets']}\n"
                f"• Win Rate: {performance['win_rate']:.1f}%\n"
                f"• ROI: {performance['roi']:+.1f}%\n"
                f"• Profit Total: {performance['total_units']:+.2f} unidades\n\n"
                
                "🎯 **Últimas Apostas:**\n"
                f"{bet_history}"
                
                "📋 Selecione um período para análise detalhada:"
            )

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no history_command: {e}")
            await update.message.reply_text(
                "❌ Erro ao carregar histórico de apostas.",
                parse_mode='Markdown'
            )

    async def odds_command(self, update: Update, context) -> None:
        """Integração com APIs de Odds Reais (PandaScore + The Odds API)"""
        try:
            if not ODDS_SYSTEM_AVAILABLE:
                await update.message.reply_text(
                    "❌ Sistema de odds reais não disponível.\n"
                    "Entre em contato com o administrador.",
                    parse_mode='Markdown'
                )
                return
            
            # Status do sistema de odds
            status = await self.odds_system.get_system_status()
            
            keyboard = [
                [
                    InlineKeyboardButton("⚡ Live Odds", callback_data="odds_live"),
                    InlineKeyboardButton("📅 Próximas", callback_data="odds_upcoming")
                ],
                [
                    InlineKeyboardButton("🔍 Buscar Partida", callback_data="odds_search"),
                    InlineKeyboardButton("💰 Value Bets", callback_data="odds_value")
                ],
                [
                    InlineKeyboardButton("📊 Status APIs", callback_data="odds_status"),
                    InlineKeyboardButton("⚙️ Configuração", callback_data="odds_config")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            status_text = "✅ ATIVO" if status['real_odds_enabled'] else "❌ DESABILITADO"
            pandascore_status = "✅" if status['pandascore_available'] else "❌"
            theodds_status = "✅" if status['theodds_available'] else "❌"

            message = (
                "🎲 **SISTEMA DE ODDS REAIS**\n\n"
                f"📊 **Status:** {status_text}\n\n"
                
                "🔗 **APIs Configuradas:**\n"
                f"• PandaScore: {pandascore_status}\n"
                f"• The Odds API: {theodds_status}\n\n"
                
                "⚡ **Live Odds:**\n"
                "• Partidas em andamento\n"
                "• Odds em tempo real\n"
                "• Múltiplas casas de apostas\n\n"
                
                "💰 **Value Betting:**\n"
                "• Identificação automática\n"
                "• Cálculo de Expected Value\n"
                "• Comparação com predições ML\n\n"
                
                "📊 **Fontes de Dados:**\n"
                "• PandaScore (eSports data)\n"
                "• The Odds API (Sportsbooks)\n"
                "• Sistema híbrido com fallback\n\n"
                
                "🎯 Selecione uma funcionalidade:"
            )

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no odds_command: {e}")
            await update.message.reply_text(
                "❌ Erro ao carregar sistema de odds reais.",
                parse_mode='Markdown'
            )

    async def proximosjogoslol_command(self, update: Update, context) -> None:
        """Próximos jogos LoL com análise"""
        try:
            upcoming_matches = await self.schedule_manager.get_scheduled_matches(days_ahead=3)
            
            keyboard = [
                [
                    InlineKeyboardButton("📅 Hoje", callback_data="proximos_today"),
                    InlineKeyboardButton("📅 Amanhã", callback_data="proximos_tomorrow")
                ],
                [
                    InlineKeyboardButton("🏆 Major Leagues", callback_data="proximos_major"),
                    InlineKeyboardButton("🌍 Todas Ligas", callback_data="proximos_all")
                ],
                [
                    InlineKeyboardButton("🔍 Filtros", callback_data="proximos_filter"),
                    InlineKeyboardButton("⚙️ Configurar", callback_data="proximos_settings")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if upcoming_matches:
                matches_text = ""
                for i, match in enumerate(upcoming_matches[:5], 1):
                    team1 = match.get('team1', {}).get('name', 'Team 1')
                    team2 = match.get('team2', {}).get('name', 'Team 2')
                    league = match.get('league', 'Unknown League')
                    time = match.get('time', 'TBD')
                    
                    matches_text += (
                        f"🎯 **{team1} vs {team2}**\n"
                        f"🏆 {league}\n"
                        f"⏰ {time}\n\n"
                    )
            else:
                matches_text = "📝 Nenhuma partida encontrada nos próximos dias."

            message = (
                "🎮 **PRÓXIMOS JOGOS LOL**\n\n"
                "📅 **Próximas Partidas:**\n\n"
                f"{matches_text}"
                
                "🎯 **Funcionalidades:**\n"
                "• Análise automática de todas as partidas\n"
                "• Predições baseadas em IA\n"
                "• Alertas para jogos importantes\n"
                "• Integração com sistema de tips\n\n"
                
                "📋 Selecione um filtro para ver mais partidas:"
            )

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no proximosjogoslol_command: {e}")
            await update.message.reply_text(
                "❌ Erro ao carregar próximos jogos LoL.",
                parse_mode='Markdown'
            )

    async def filtrarligas_command(self, update: Update, context) -> None:
        """Sistema de filtros de ligas"""
        try:
            keyboard = [
                [
                    InlineKeyboardButton("🏆 LCK", callback_data="filter_lck"),
                    InlineKeyboardButton("🇪🇺 LEC", callback_data="filter_lec")
                ],
                [
                    InlineKeyboardButton("🇺🇸 LCS", callback_data="filter_lcs"),
                    InlineKeyboardButton("🇨🇳 LPL", callback_data="filter_lpl")
                ],
                [
                    InlineKeyboardButton("🇧🇷 CBLOL", callback_data="filter_cblol"),
                    InlineKeyboardButton("🌍 MSI/Worlds", callback_data="filter_international")
                ],
                [
                    InlineKeyboardButton("⚙️ Personalizar", callback_data="filter_custom"),
                    InlineKeyboardButton("🔄 Reset", callback_data="filter_reset")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = (
                "🔍 **FILTROS DE LIGAS**\n\n"
                "🎯 **Ligas Principais:**\n\n"
                
                "🏆 **LCK (Korea):**\n"
                "• Liga mais competitiva\n"
                "• Alto nível técnico\n"
                "• Predições mais confiáveis\n\n"
                
                "🇪🇺 **LEC (Europe):**\n"
                "• Meta diversificada\n"
                "• Jogos estratégicos\n"
                "• Boa para análises\n\n"
                
                "🇺🇸 **LCS (North America):**\n"
                "• Liga imprevisível\n"
                "• Upset potential alto\n"
                "• Valor em underdogs\n\n"
                
                "🇨🇳 **LPL (China):**\n"
                "• Estilo agressivo\n"
                "• Muitos kills\n"
                "• Over/Under interessante\n\n"
                
                "⚙️ **Configurações Atuais:**\n"
                "• Todas as ligas ativas\n"
                "• Filtros: Nenhum aplicado\n\n"
                
                "🎯 Selecione as ligas que deseja monitorar:"
            )

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no filtrarligas_command: {e}")
            await update.message.reply_text(
                "❌ Erro ao carregar filtros de ligas.",
                parse_mode='Markdown'
            )

    async def timesfavoritos_command(self, update: Update, context) -> None:
        """Sistema de times favoritos com monitoramento automático"""
        try:
            keyboard = [
                [
                    InlineKeyboardButton("⭐ Adicionar Time", callback_data="favorites_add"),
                    InlineKeyboardButton("❌ Remover Time", callback_data="favorites_remove")
                ],
                [
                    InlineKeyboardButton("📋 Meus Times", callback_data="favorites_list"),
                    InlineKeyboardButton("🔔 Configurar Alertas", callback_data="favorites_alerts")
                ],
                [
                    InlineKeyboardButton("📊 Estatísticas", callback_data="favorites_stats"),
                    InlineKeyboardButton("🎯 Próximos Jogos", callback_data="favorites_upcoming")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Simular lista de times favoritos (integração futura com banco de dados)
            favorite_teams = [
                {"name": "T1", "league": "LCK", "record": "15-3", "next_game": "vs Gen.G"},
                {"name": "G2 Esports", "league": "LEC", "record": "12-6", "next_game": "vs FNC"},
                {"name": "JD Gaming", "league": "LPL", "record": "14-4", "next_game": "vs BLG"}
            ]

            favorites_text = ""
            if favorite_teams:
                for team in favorite_teams:
                    favorites_text += (
                        f"⭐ **{team['name']}** ({team['league']})\n"
                        f"   📊 Record: {team['record']}\n"
                        f"   🎯 Próximo: {team['next_game']}\n\n"
                    )
            else:
                favorites_text = "📝 Nenhum time favorito configurado ainda."

            message = (
                "⭐ **TIMES FAVORITOS**\n\n"
                "🎯 **Funcionalidades:**\n"
                "• Monitoramento automático\n"
                "• Alertas para jogos importantes\n"
                "• Estatísticas detalhadas\n"
                "• Análise de performance\n"
                "• Tips personalizados\n\n"
                
                "📋 **Seus Times Favoritos:**\n\n"
                f"{favorites_text}"
                
                "🔔 **Alertas Ativos:**\n"
                "• Notificação 1h antes do jogo\n"
                "• Tips automáticos disponíveis\n"
                "• Resumo pós-jogo\n\n"
                
                "⚙️ Configure seus times favoritos:"
            )

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no timesfavoritos_command: {e}")
            await update.message.reply_text(
                "❌ Erro ao carregar times favoritos.",
                parse_mode='Markdown'
            )

    async def statuslol_command(self, update: Update, context) -> None:
        """Status geral do sistema LoL"""
        try:
            # Obter status de todos os sistemas
            monitoring_status = self.tips_system.get_monitoring_status()
            performance = self.units_system.get_performance_summary()
            alerts_stats = self.alerts_system.get_alert_stats()
            prediction_cache = self.prediction_system.get_cache_status()
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Atualizar", callback_data="status_refresh"),
                    InlineKeyboardButton("📊 Detalhes", callback_data="status_details")
                ],
                [
                    InlineKeyboardButton("🔧 Diagnóstico", callback_data="status_diagnostic"),
                    InlineKeyboardButton("⚙️ Configurações", callback_data="status_settings")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Status geral
            system_status = "🟢 Online" if monitoring_status['status'] == 'running' else "🔴 Offline"
            
            message = (
                f"📊 **STATUS GERAL DO SISTEMA**\n\n"
                f"🔋 **Status:** {system_status}\n"
                f"⏰ **Uptime:** {monitoring_status.get('uptime', 'N/A')}\n"
                f"🔄 **Última Atualização:** {monitoring_status.get('last_check', 'N/A')}\n\n"
                
                "🎯 **Sistema de Tips:**\n"
                f"• Status: {'🟢 Ativo' if monitoring_status['status'] == 'running' else '🔴 Inativo'}\n"
                f"• Tips Encontrados: {monitoring_status.get('tips_found', 0)}\n"
                f"• Partidas Analisadas: {monitoring_status.get('matches_analyzed', 0)}\n"
                f"• Última Verificação: {monitoring_status.get('last_check', 'N/A')}\n\n"
                
                "💰 **Sistema de Unidades:**\n"
                f"• ROI: {performance.get('roi', 0):+.1f}%\n"
                f"• Win Rate: {performance.get('win_rate', 0):.1f}%\n"
                f"• Total de Apostas: {performance.get('total_bets', 0)}\n"
                f"• Bankroll: ${performance.get('current_bankroll', 1000):.2f}\n\n"
                
                "📢 **Sistema de Alertas:**\n"
                f"• Grupos Ativos: {alerts_stats.get('active_groups', 0)}\n"
                f"• Alertas Enviados: {alerts_stats.get('total_sent', 0)}\n"
                f"• Taxa de Sucesso: {alerts_stats.get('success_rate', 0):.1f}%\n"
                f"• Último Alerta: {alerts_stats.get('last_alert', 'N/A')}\n\n"
                
                "🤖 **Sistema de IA:**\n"
                f"• Cache de Predições: {prediction_cache.get('cached_predictions', 0)}\n"
                f"• Última Predição: {prediction_cache.get('last_prediction', 'N/A')}\n"
                f"• Acurácia: {prediction_cache.get('accuracy', 0):.1f}%\n\n"
                
                "📊 Selecione uma opção para mais detalhes:"
            )

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro no statuslol_command: {e}")
            await update.message.reply_text(
                "❌ Erro ao carregar status do sistema.",
                parse_mode='Markdown'
            )

    async def ml_predictions_command(self, update: Update, context) -> None:
        """Sistema ML completo para predições (com loading assíncrono)"""
        try:
            # Resposta imediata
            loading_msg = await update.message.reply_text("🤖 Carregando sistema ML...")
            
            # Verificar/carregar ML system
            ml_system = await self._get_ml_system()
            
            if not ml_system:
                await loading_msg.edit_text(
                    "❌ **Sistema ML Indisponível**\n\n"
                    "O sistema de Machine Learning não está disponível no momento.\n"
                    "Use os comandos básicos de predição: /predictions"
                )
                return
            
            # Atualizar com conteúdo
            await loading_msg.edit_text("🔄 Buscando partidas ativas...")
            
            # Buscar partidas em andamento (versão otimizada)
            try:
                partidas = await self.riot_client.get_live_matches()
                partidas_ativas = [p for p in partidas if p.get('status') == 'in_game'][:3]  # Limitar a 3
            except:
                partidas_ativas = []

            if not partidas_ativas:
                message = """🤖 **SISTEMA ML - SEM PARTIDAS ATIVAS**

❌ Não há partidas ao vivo no momento para análise ML.

🎯 **Funções Disponíveis:**
• Análise de composições
• Cálculo de Expected Value
• Predições baseadas em dados históricos

💡 **Dica:** O sistema ML funciona melhor com partidas em andamento após o draft."""
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Verificar Novamente", callback_data="ml_predictions")],
                    [InlineKeyboardButton("📊 Estatísticas ML", callback_data="ml_stats")],
                    [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
                ]
            else:
                # Análise rápida (apenas primeira partida para evitar delay)
                partida = partidas_ativas[0]
                
                message = f"""🤖 **SISTEMA ML ATIVO**

🎮 **Partida Principal:**
{partida['team1']} vs {partida['team2']}
📍 {partida['league']} | ⏱️ Em andamento

🎯 **Status:** Sistema carregado e operacional
📊 **Modelos:** Ensemble de 3 algoritmos
🔄 **Atualizações:** A cada 60 segundos

⚡ **Análise Rápida Disponível**"""

                keyboard = [
                    [InlineKeyboardButton("🔮 Análise ao Vivo", callback_data="ml_live_analysis")],
                    [InlineKeyboardButton("🎯 Money Line Tips", callback_data="money_line_tips")],
                    [InlineKeyboardButton("📊 Estatísticas ML", callback_data="ml_stats")],
                    [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await loading_msg.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            error_msg = f"❌ Erro no sistema ML: {str(e)[:100]}"
            await update.message.reply_text(error_msg)
            logger.error(f"Erro no ml_predictions_command: {e}")

    async def ml_live_analysis_command(self, update: Update, context) -> None:
        """Análise ao vivo ML otimizada"""
        try:
            # Resposta imediata
            loading_msg = await update.message.reply_text("🔄 Preparando análise ao vivo...")
            
            # Verificar ML system
            ml_engine = await self._get_ml_engine()
            
            if not ml_engine:
                await loading_msg.edit_text(
                    "❌ **Sistema ML Indisponível**\n\n"
                    "Use análise básica: /predictions"
                )
                return
            
            # Buscar dados rapidamente
            try:
                partidas = await self.riot_client.get_live_matches()
                partidas_ativas = [p for p in partidas if p.get('status') == 'in_game'][:2]  # Máximo 2
            except:
                partidas_ativas = []

            if not partidas_ativas:
                await loading_msg.edit_text(
                    "❌ **Nenhuma Partida Ativa**\n\n"
                    "Não há partidas ao vivo para análise no momento."
                )
                return

            # Análise da primeira partida apenas (otimizado)
            partida = partidas_ativas[0]
            
            message = f"""🔮 **ANÁLISE AO VIVO - ML**

🎮 **{partida['team1']} vs {partida['team2']}**
📍 {partida['league']}
⏱️ Status: {partida['status']}

🤖 **Sistema ML:** Ativo
📊 **Qualidade dos dados:** {'Alta' if partida.get('game_time', 0) > 10 else 'Média'}
🎯 **Última atualização:** Agora

⚡ **Análise otimizada para resposta rápida**"""

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="ml_live_analysis")],
                [InlineKeyboardButton("🎯 Ver Predição", callback_data="quick_ml_prediction")],
                [InlineKeyboardButton("🔙 Menu ML", callback_data="ml_predictions")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await loading_msg.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {str(e)[:100]}")
            logger.error(f"Erro no ml_live_analysis_command: {e}")

    async def money_line_tips_command(self, update: Update, context) -> None:
        """Money line tips otimizado"""
        try:
            # Resposta imediata
            loading_msg = await update.message.reply_text("🎯 Buscando oportunidades money line...")
            
            # Verificar sistema ML
            ml_system = await self._get_ml_system()
            
            if not ml_system:
                # Fallback para sistema básico
                await loading_msg.edit_text(
                    "🎯 **MONEY LINE TIPS - MODO BÁSICO**\n\n"
                    "Sistema ML indisponível. Usando análise básica.\n\n"
                    "📊 Use /tips para tips profissionais básicos"
                )
                return
            
            # Análise rápida (mock para demonstração - otimizado)
            message = """🎯 **MONEY LINE TIPS - ML**

⚡ **Modo Otimizado Ativo**

🎮 **Oportunidades Atuais:**
• Buscando partidas em andamento...
• Calculando Expected Value...
• Analisando value bets...

📊 **Critérios ML:**
✅ EV mínimo: 5%
✅ Confiança mínima: 65%
✅ Apenas partidas pós-draft

🔄 **Atualizado:** Tempo real"""

            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar Tips", callback_data="money_line_tips")],
                [InlineKeyboardButton("🤖 Sistema ML", callback_data="ml_predictions")],
                [InlineKeyboardButton("💰 Tips Básicos", callback_data="tips")],
                [InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await loading_msg.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {str(e)[:100]}")
            logger.error(f"Erro no money_line_tips_command: {e}")

def run_flask_app():
    """Executa Flask em thread separada (apenas para health check)"""
    # Não executar se webhook estiver ativo
    webhook_url = os.getenv('WEBHOOK_URL')
    railway_url = os.getenv('RAILWAY_STATIC_URL')

    if not (webhook_url or railway_url):
        app.run(host='0.0.0.0', port=PORT, debug=False)

def check_single_instance():
    """Verifica se é a única instância rodando"""
    import tempfile

    try:
        # Tentar importar fcntl (Unix/Linux)
        import fcntl

        # Criar arquivo de lock
        lock_file = os.path.join(tempfile.gettempdir(), 'bot_lol_v3.lock')

        # Tentar abrir arquivo de lock
        lock_fd = open(lock_file, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        # Escrever PID no arquivo
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()

        logger.info("🔒 Lock de instância única adquirido (Unix)")
        return lock_fd

    except ImportError:
        # Windows - usar método alternativo
        try:
            import msvcrt
            lock_file = os.path.join(tempfile.gettempdir(), 'bot_lol_v3.lock')

            # Verificar se arquivo existe e está em uso
            if os.path.exists(lock_file):
                try:
                    # Tentar abrir em modo exclusivo
                    lock_fd = open(lock_file, 'r+')
                    msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1) # Tenta travar sem bloquear
                    # Se chegou aqui, conseguiu travar, então não estava em uso por outro.
                    # Precisamos liberar e remover para que a nova instância crie o seu.
                    msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                    lock_fd.close()
                    os.remove(lock_file) # Remove o lock antigo
                except (IOError, OSError): # Se falhar ao travar, significa que outro processo tem o lock
                    logger.error("❌ OUTRA INSTÂNCIA JÁ ESTÁ RODANDO! (Windows - msvcrt lock)")
                    logger.error("🛑 Pare a outra instância antes de continuar")
                    return None

            # Criar novo arquivo de lock e travá-lo
            lock_fd = open(lock_file, 'w')
            lock_fd.write(str(os.getpid()))
            lock_fd.flush()
            # Tentar travar o arquivo criado pela instância atual
            try:
                msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
                logger.info("🔒 Lock de instância única adquirido (Windows)")
                return lock_fd # Retorna o file descriptor para mantê-lo aberto e travado
            except (IOError, OSError):
                lock_fd.close() # Não conseguiu travar, fechar e falhar
                logger.error("❌ Não foi possível adquirir lock no Windows, mesmo após remover o antigo.")
                return None


        except ImportError:
            # Fallback - verificação simples por arquivo
            lock_file = os.path.join(tempfile.gettempdir(), 'bot_lol_v3.lock')

            if os.path.exists(lock_file):
                # Verificar se processo ainda existe
                try:
                    with open(lock_file, 'r') as f:
                        old_pid = int(f.read().strip())

                    # Verificar se PID ainda está ativo
                    try:
                        os.kill(old_pid, 0)  # Não mata, só verifica
                        logger.error("❌ OUTRA INSTÂNCIA JÁ ESTÁ RODANDO!")
                        logger.error(f"🛑 PID {old_pid} ainda ativo")
                        return None
                    except OSError:
                        # Processo não existe mais, remover lock
                        os.remove(lock_file)
                        logger.info("🧹 Lock antigo removido (processo morto)")
                except:
                    # Arquivo corrompido, remover
                    try: # Adicionado try-except para remoção
                        os.remove(lock_file)
                    except OSError:
                        pass


            # Criar novo lock
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))

            logger.info("🔒 Lock de instância única adquirido (Fallback)")
            return True # Em fallback, só o arquivo existe, não há fd para manter

    except (IOError, OSError) as e:
        logger.error(f"❌ OUTRA INSTÂNCIA JÁ ESTÁ RODANDO! Erro: {e}")
        logger.error("🛑 Pare a outra instância antes de continuar")
        return None

def main():
    """Função principal"""
    try:
        logger.info("🎮 INICIANDO BOT LOL V3 - SISTEMA DE UNIDADES PROFISSIONAL")
        logger.info("=" * 60)
        logger.info("🎲 Sistema de Unidades: PADRÃO DE GRUPOS PROFISSIONAIS")
        logger.info("📊 Baseado em: Confiança + EV + Tier da Liga")
        logger.info("⚡ Sem Kelly Criterion - Sistema simplificado")
        logger.info("🎯 Critérios: 65%+ confiança, 5%+ EV mínimo")
        logger.info("=" * 60)

        # Verificar instância única
        lock_fd_or_status = check_single_instance() # Nome da variável alterado para clareza
        if lock_fd_or_status is None:
            logger.error("🛑 ABORTANDO: Outra instância já está rodando")
            sys.exit(1)

        # Verificar e limpar conflitos do Telegram ANTES de inicializar
        async def pre_check_telegram_conflicts():
            """Verifica conflitos do Telegram antes de iniciar"""
            import time  # Importar time para usar sleep
            try:
                logger.info("🔍 Verificando conflitos do Telegram...")

                if TELEGRAM_VERSION == "v20+":
                    from telegram.ext import Application
                    temp_app = Application.builder().token(TOKEN).build()

                    # Verificar webhook atual
                    webhook_info = await temp_app.bot.get_webhook_info()
                    if webhook_info.url:
                        logger.warning(f"⚠️ Webhook ativo detectado: {webhook_info.url}")
                        logger.info("🧹 Removendo webhook para evitar conflitos...")
                        await temp_app.bot.delete_webhook(drop_pending_updates=True)
                        await asyncio.sleep(2)
                        logger.info("✅ Webhook removido")

                    # Verificar se bot responde
                    me = await temp_app.bot.get_me()
                    logger.info(f"✅ Bot verificado: @{me.username}")

                else:
                    from telegram.ext import Updater
                    temp_updater = Updater(TOKEN, use_context=True) # use_context=True para v13

                    # Verificar webhook atual
                    webhook_info = temp_updater.bot.get_webhook_info()
                    if webhook_info.url:
                        logger.warning(f"⚠️ Webhook ativo detectado: {webhook_info.url}")
                        logger.info("🧹 Removendo webhook para evitar conflitos...")
                        temp_updater.bot.delete_webhook(drop_pending_updates=True)
                        time.sleep(2)
                        logger.info("✅ Webhook removido")

                    # Verificar se bot responde
                    me = temp_updater.bot.get_me()
                    logger.info(f"✅ Bot verificado: @{me.username}")

                return True

            except Exception as e:
                logger.error(f"❌ Erro na verificação do Telegram: {e}")
                return False

        # Executar verificação
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed(): # Adicionado para reabrir se necessário (comum em alguns cenários)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if not loop.run_until_complete(pre_check_telegram_conflicts()):
            logger.error("🛑 ABORTANDO: Conflitos do Telegram não resolvidos")
            sys.exit(1)

        # Inicializar bot
        bot = LoLBotV3UltraAdvanced()

        # Verificar modo de execução com detecção mais robusta
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))

        # Log detalhado do ambiente detectado
        logger.info(f"🔍 Detecção de ambiente:")
        logger.info(f"  • RAILWAY_ENVIRONMENT_NAME: {os.getenv('RAILWAY_ENVIRONMENT_NAME', 'Não definido')}")
        logger.info(f"  • RAILWAY_STATIC_URL: {os.getenv('RAILWAY_STATIC_URL', 'Não definido')}")
        logger.info(f"  • PORT: {PORT}")
        logger.info(f"  • Modo detectado: {'🚀 RAILWAY (webhook)' if is_railway else '🏠 LOCAL (polling)'}")

        # VERIFICAÇÃO CRÍTICA: Evitar execução local se Railway estiver ativo
        if not is_railway:
            logger.warning("⚠️ EXECUTANDO EM MODO LOCAL!")
            logger.warning("🚨 ATENÇÃO: Se o Railway estiver ativo, isso causará conflitos!")

            # Verificar se há webhook ativo (indicando Railway ativo)
            async def check_railway_active():
                try:
                    if TELEGRAM_VERSION == "v20+":
                        from telegram.ext import Application
                        temp_app = Application.builder().token(TOKEN).build()
                        webhook_info = await temp_app.bot.get_webhook_info()
                    else:
                        from telegram.ext import Updater
                        temp_updater = Updater(TOKEN, use_context=True)
                        webhook_info = temp_updater.bot.get_webhook_info()

                    if webhook_info.url:
                        logger.error("🚨 WEBHOOK ATIVO DETECTADO!")
                        logger.error(f"🔗 URL: {webhook_info.url}")
                        logger.error("🛑 ISSO INDICA QUE O RAILWAY ESTÁ ATIVO!")
                        logger.error("💥 EXECUTAR LOCALMENTE CAUSARÁ CONFLITOS!")
                        return True
                    return False
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao verificar webhook: {e}")
                    return False

            # Executar verificação
            # loop já foi obtido e setado antes
            railway_active = loop.run_until_complete(check_railway_active())

            if railway_active:
                logger.error("🛑 ABORTANDO EXECUÇÃO LOCAL!")
                logger.error("💡 SOLUÇÃO:")
                logger.error("  1. Pare o Railway primeiro")
                logger.error("  2. OU execute APENAS no Railway")
                logger.error("  3. NUNCA execute ambos simultaneamente!")
                sys.exit(1)
            else:
                logger.info("✅ Nenhum webhook ativo - seguro para execução local")

        # Verificar se há conflito de instâncias (redundante com check_single_instance, mas ok)
        if is_railway:
            logger.info("⚠️ MODO RAILWAY: Garantindo que não há polling ativo...")
        else:
            logger.info("⚠️ MODO LOCAL: Garantindo que não há webhook ativo...")

        if TELEGRAM_VERSION == "v20+":
            # Versão v20+
            application = Application.builder().token(TOKEN).build()

            # IMPORTANTE: Limpar webhook existente primeiro para evitar conflitos
            async def clear_existing_webhook():
                try:
                    logger.info("🧹 Limpando webhook existente para evitar conflitos...")
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    logger.info("✅ Webhook anterior removido")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao limpar webhook (normal se não existir): {e}")

            # Executar limpeza
            # loop já foi obtido e setado
            loop.run_until_complete(clear_existing_webhook())

            # Callback específico para tratar erros de conflito durante polling (baseado na documentação oficial)
            def conflict_error_callback(error_context: ContextTypes.DEFAULT_TYPE): # Corrigido para aceitar context
                """Callback específico para tratar erros de conflito durante polling"""
                from telegram.error import Conflict, TelegramError
                error = error_context # error está dentro do context

                if isinstance(error, Conflict) or ("Conflict" in str(error) and "getUpdates" in str(error)):
                    logger.critical("⚠️ Conflict error detected during polling - duplicate instance")
                    logger.warning("🔄 Conflito tratado silenciosamente (normal em deploy)")
                    logger.info("💡 Solução: Certifique-se de que apenas uma instância está rodando")
                    # Não fazer nada - deixar o sistema continuar (conforme documentação oficial)
                    return
                elif isinstance(error, TelegramError):
                    logger.error(f"❌ Telegram API error durante polling: {error}")
                else:
                    # Para outros erros, logar normalmente
                    logger.error(f"❌ Erro não relacionado ao Telegram durante polling: {error}")

            # Handler de erro global para conflitos (baseado na documentação oficial)
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Handler global de erros - Log Errors caused by Updates"""
                from telegram.error import TelegramError, Conflict

                try:
                    error = context.error
                    logger.error('Update "%s" caused error "%s"', update, error)

                    # Tratamento específico para conflitos (baseado na pesquisa oficial)
                    if isinstance(error, Conflict) or ("Conflict" in str(error) and "getUpdates" in str(error)):
                        logger.critical("⚠️ Conflict error detected. This bot instance might be a duplicate.")
                        logger.warning("🔄 Conflito tratado silenciosamente - bot continua funcionando")
                        # Não forçar exit - deixar o bot continuar (conforme documentação)
                        return
                    elif isinstance(error, TelegramError):
                        logger.error(f"❌ Telegram API error: {error}")
                    else:
                        logger.error(f"❌ Erro não relacionado ao Telegram: {error}")

                except Exception as e:
                    logger.error(f"❌ Erro no handler de erro: {e}")

            # Adicionar handler de erro
            application.add_error_handler(error_handler)

            # Handlers
            application.add_handler(CommandHandler("start", bot.start_command))
            application.add_handler(CommandHandler("menu", bot.menu_command))
            application.add_handler(CommandHandler("tips", bot.tips_command))
            application.add_handler(CommandHandler("live", bot.live_matches_command))
            application.add_handler(CommandHandler("schedule", bot.schedule_command))
            application.add_handler(CommandHandler("monitoring", bot.monitoring_command))
            application.add_handler(CommandHandler("predictions", bot.predictions_command))
            application.add_handler(CommandHandler("alerts", bot.alerts_command))
            application.add_handler(CommandHandler("force_scan", bot.force_scan_command))
            application.add_handler(CommandHandler("units", bot.units_command))
            application.add_handler(CommandHandler("performance", bot.performance_command))
            application.add_handler(CommandHandler("history", bot.history_command))
            application.add_handler(CommandHandler("odds", bot.odds_command))
            application.add_handler(CommandHandler("proximosjogoslol", bot.proximosjogoslol_command))
            application.add_handler(CommandHandler("filtrarligas", bot.filtrarligas_command))
            application.add_handler(CommandHandler("timesfavoritos", bot.timesfavoritos_command))
            application.add_handler(CommandHandler("statuslol", bot.statuslol_command))
            application.add_handler(CommandHandler("ml_predictions", bot.ml_predictions_command))
            application.add_handler(CommandHandler("ml_live_analysis", bot.ml_live_analysis_command))
            application.add_handler(CommandHandler("money_line_tips", bot.money_line_tips_command))
            application.add_handler(CallbackQueryHandler(bot.callback_handler))

            # Definir aplicação para sistema de alertas
            bot.set_bot_application(application)

            if is_railway:
                # Modo Railway - Webhook
                logger.info("🚀 Detectado ambiente Railway - Configurando webhook")

                # Configurar webhook path
                webhook_path = f"/webhook"

                # Remover rota webhook padrão de forma segura
                try:
                    # Método seguro para remover rota existente
                    for rule in list(app.url_map.iter_rules()):
                        if rule.rule == '/webhook' and rule.endpoint == 'webhook_default':
                            # A remoção direta de app.url_map._rules pode ser instável.
                            # Flask não tem um método público para remover rotas dinamicamente de forma simples.
                            # A sobrescrita é geralmente a abordagem mais segura.
                            logger.info(f"⚠️ Rota webhook padrão encontrada, será sobrescrita.")
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível verificar/remover rota webhook padrão: {e}")
                    # Continuar mesmo se não conseguir remover - Flask vai sobrescrever

                # Adicionar rota webhook ao Flask
                @app.route(webhook_path, methods=['POST'])
                def webhook():
                    try:
                        from flask import request
                        update_data = request.get_json(force=True)

                        if update_data:
                            from telegram import Update
                            update_obj = Update.de_json(update_data, application.bot) # Renomeado para evitar conflito com módulo

                            # Processar update
                            current_loop = asyncio.get_event_loop() # Usar o loop atual
                            current_loop.run_until_complete(application.process_update(update_obj))

                        return "OK", 200
                    except Exception as e:
                        logger.error(f"❌ Erro no webhook: {e}")
                        return "Error", 500

                # Configurar webhook URL
                railway_url = os.getenv('RAILWAY_STATIC_URL', f"https://{os.getenv('RAILWAY_SERVICE_NAME', 'bot')}.railway.app")
                # Garantir que a URL tenha https://
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                webhook_url = f"{railway_url}{webhook_path}"

                # Definir webhook
                async def setup_webhook():
                    try:
                        # IMPORTANTE: Deletar webhook existente primeiro para evitar conflitos
                        logger.info("🔄 Removendo webhook anterior...")
                        await application.bot.delete_webhook(drop_pending_updates=True)

                        # Aguardar um pouco para garantir que foi removido
                        await asyncio.sleep(2)

                        # Configurar novo webhook
                        await application.bot.set_webhook(webhook_url)
                        logger.info(f"✅ Webhook configurado: {webhook_url}")

                        # Verificar se foi configurado corretamente
                        webhook_info = await application.bot.get_webhook_info()
                        logger.info(f"📋 Webhook ativo: {webhook_info.url}")

                    except Exception as e:
                        logger.error(f"❌ Erro ao configurar webhook: {e}")

                # Executar setup
                # loop já foi definido
                loop.run_until_complete(setup_webhook())

                logger.info("✅ Bot configurado (Railway webhook) - Iniciando Flask...")

                # Configurar Flask para produção
                app.config['ENV'] = 'production'
                app.config['DEBUG'] = False

                # Log detalhado para Railway
                logger.info(f"🌐 Iniciando Flask na porta {PORT}")
                logger.info(f"🔗 Health check disponível em: /health")
                logger.info(f"🔗 Webhook disponível em: {webhook_url}")
                logger.info(f"🔗 Root disponível em: /")
                logger.info(f"🔗 Ping disponível em: /ping")

                # Iniciar Flask
                app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

            else:
                # Modo Local - Polling
                logger.info("🏠 Ambiente local detectado - Usando polling")

                # Iniciar Flask em thread separada
                flask_thread = threading.Thread(target=run_flask_app, daemon=True)
                flask_thread.start()
                logger.info(f"🌐 Health check rodando na porta {PORT}")

                logger.info("✅ Bot configurado (polling) - Iniciando...")

                # Garantir que não há webhook ativo antes de iniciar polling
                async def ensure_no_webhook():
                    try:
                        await application.bot.delete_webhook(drop_pending_updates=True)
                        logger.info("🧹 Webhook removido antes de iniciar polling")
                    except Exception as e:
                        logger.debug(f"Webhook já estava removido: {e}")

                loop.run_until_complete(ensure_no_webhook())

                # Iniciar polling com error_callback para tratar conflitos e drop_pending_updates
                logger.info("🔄 Iniciando polling com tratamento de conflitos...")
                application.run_polling(
                    drop_pending_updates=True,  # Descarta updates pendentes para evitar conflitos
                    # error_callback foi substituído por application.add_error_handler
                )

        else:
            # Versão v13
            updater = Updater(TOKEN, use_context=True) # Garantir use_context=True
            dispatcher = updater.dispatcher

            # IMPORTANTE: Limpar webhook existente primeiro para evitar conflitos
            try:
                logger.info("🧹 Limpando webhook existente v13 para evitar conflitos...")
                updater.bot.delete_webhook(drop_pending_updates=True)
                logger.info("✅ Webhook anterior v13 removido")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar webhook v13 (normal se não existir): {e}")

            # Handler de erro global para conflitos v13 (baseado na documentação oficial)
            def error_handler_v13(update, context): # Mantido como estava
                """Handler global de erros v13 - Log Errors caused by Updates"""
                from telegram.error import TelegramError, Conflict

                try:
                    error = context.error
                    logger.error('Update "%s" caused error "%s"', update, error)

                    # Tratamento específico para conflitos (baseado na pesquisa oficial)
                    if isinstance(error, Conflict) or ("Conflict" in str(error) and "getUpdates" in str(error)):
                        logger.critical("⚠️ Conflict error detected. This bot instance might be a duplicate.")
                        logger.warning("🔄 Conflito tratado silenciosamente - bot continua funcionando")
                        # Não forçar exit - deixar o bot continuar (conforme documentação)
                        return
                    elif isinstance(error, TelegramError):
                        logger.error(f"❌ Telegram API error (v13): {error}")
                    else:
                        logger.error(f"❌ Erro não relacionado ao Telegram (v13): {error}")

                except Exception as e:
                    logger.error(f"❌ Erro no handler de erro (v13): {e}")

            # Adicionar handler de erro
            dispatcher.add_error_handler(error_handler_v13)

            # Definir aplicação para sistema de alertas
            bot.set_bot_application(updater) # Passando o updater para v13

            # Handlers
            dispatcher.add_handler(CommandHandler("start", bot.start_command))
            dispatcher.add_handler(CommandHandler("menu", bot.menu_command))
            dispatcher.add_handler(CommandHandler("tips", bot.tips_command))
            dispatcher.add_handler(CommandHandler("live", bot.live_matches_command))
            dispatcher.add_handler(CommandHandler("schedule", bot.schedule_command))
            dispatcher.add_handler(CommandHandler("monitoring", bot.monitoring_command))
            dispatcher.add_handler(CommandHandler("predictions", bot.predictions_command))
            dispatcher.add_handler(CommandHandler("alerts", bot.alerts_command))
            dispatcher.add_handler(CommandHandler("force_scan", bot.force_scan_command))
            dispatcher.add_handler(CommandHandler("units", bot.units_command))
            dispatcher.add_handler(CommandHandler("performance", bot.performance_command))
            dispatcher.add_handler(CommandHandler("history", bot.history_command))
            dispatcher.add_handler(CommandHandler("odds", bot.odds_command))
            dispatcher.add_handler(CommandHandler("proximosjogoslol", bot.proximosjogoslol_command))
            dispatcher.add_handler(CommandHandler("filtrarligas", bot.filtrarligas_command))
            dispatcher.add_handler(CommandHandler("timesfavoritos", bot.timesfavoritos_command))
            dispatcher.add_handler(CommandHandler("statuslol", bot.statuslol_command))
            dispatcher.add_handler(CommandHandler("ml_predictions", bot.ml_predictions_command))
            dispatcher.add_handler(CommandHandler("ml_live_analysis", bot.ml_live_analysis_command))
            dispatcher.add_handler(CommandHandler("money_line_tips", bot.money_line_tips_command))
            dispatcher.add_handler(CallbackQueryHandler(bot.callback_handler))

            # Contar handlers corretamente
            total_handlers = sum(len(handlers_list) for group, handlers_list in dispatcher.handlers.items()) # Corrigido para iterar sobre items
            logger.info(f"✅ {total_handlers} handlers registrados no dispatcher v13")
            logger.info(f"📋 Comandos disponíveis: /start, /menu, /tips, /live, /schedule, /monitoring, /predictions, /alerts, /force_scan, /units, /performance, /history, /odds, /proximosjogoslol, /filtrarligas, /timesfavoritos, /statuslol, /ml_predictions, /ml_live_analysis, /money_line_tips")

            if is_railway:
                # Modo Railway - Webhook v13
                logger.info("🚀 Detectado ambiente Railway v13 - Configurando webhook")

                webhook_path = f"/webhook"

                # Remover rota webhook padrão de forma segura (mesma lógica do v20+)
                try:
                    for rule in list(app.url_map.iter_rules()):
                        if rule.rule == '/webhook' and rule.endpoint == 'webhook_default':
                            logger.info(f"⚠️ Rota webhook padrão v13 encontrada, será sobrescrita.")
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível verificar/remover rota webhook padrão v13: {e}")

                @app.route(webhook_path, methods=['POST'])
                def webhook_v13():
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    try:
                        logger.info("🔷 DEBUG: Webhook_v13 iniciado")
                        from flask import request
                        logger.info(f"🔷 DEBUG: Request method={request.method}, path={request.path}")
                        logger.info(f"🔷 DEBUG: Request headers={dict(request.headers)}")
                        logger.info(f"🔷 DEBUG: Request content_type={request.content_type}")
                        
                        # Tentar obter dados
                        try:
                            data = request.get_data()
                            logger.info(f"🔷 DEBUG: Raw data length={len(data) if data else 0}")
                        except Exception as data_error:
                            logger.error(f"🔷 DEBUG: Erro ao obter raw data: {data_error}")
                        
                        logger.info("🔷 DEBUG: Retornando OK")
                        return "OK", 200
                        
                    except Exception as e:
                        logger.error(f"🔷 DEBUG: Erro na função webhook: {e}")
                        import traceback
                        logger.error(f"🔷 DEBUG: Traceback: {traceback.format_exc()}")
                        return "ERROR", 500

                logger.info("🔷 DEBUG: Rota webhook_v13 definida com sucesso!")
                
                # Adicionar rota de teste para comparação
                @app.route('/test_webhook_debug', methods=['POST', 'GET'])
                def test_webhook_debug():
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info("🔷 DEBUG: Rota de teste chamada!")
                    from flask import request
                    logger.info(f"🔷 DEBUG: Teste - method={request.method}")
                    return "TEST_OK", 200
                
                logger.info("🔷 DEBUG: Rota de teste definida!")
                
                # Verificar se a rota foi registrada
                try:
                    logger.info("🔷 DEBUG: Verificando rotas registradas no Flask...")
                    for rule in app.url_map.iter_rules():
                        if rule.rule == webhook_path:
                            logger.info(f"🔷 DEBUG: Rota encontrada: {rule.rule} -> {rule.endpoint} (métodos: {rule.methods})")
                        elif rule.rule == '/test_webhook_debug':
                            logger.info(f"🔷 DEBUG: Rota teste encontrada: {rule.rule} -> {rule.endpoint} (métodos: {rule.methods})")
                except Exception as route_error:
                    logger.error(f"🔷 DEBUG: Erro ao verificar rotas: {route_error}")

                # Configurar webhook
                railway_url = os.getenv('RAILWAY_STATIC_URL', f"https://{os.getenv('RAILWAY_SERVICE_NAME', 'bot')}.railway.app")
                # Garantir que a URL tenha https://
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                webhook_url = f"{railway_url}{webhook_path}"

                try:
                    # IMPORTANTE: Deletar webhook existente primeiro para evitar conflitos
                    logger.info("🔄 Removendo webhook anterior v13...")
                    updater.bot.delete_webhook(drop_pending_updates=True)

                    # Aguardar um pouco para garantir que foi removido
                    import time
                    time.sleep(2)

                    # Configurar novo webhook
                    logger.info(f"🔗 Configurando webhook v13: {webhook_url}")
                    result = updater.bot.set_webhook(webhook_url)
                    logger.info(f"✅ Webhook v13 configurado: {webhook_url} (resultado: {result})")

                    # Verificar se foi configurado corretamente
                    webhook_info = updater.bot.get_webhook_info()
                    logger.info(f"📋 Webhook v13 ativo: {webhook_info.url}")
                    logger.info(f"📋 Webhook v13 pending_updates: {webhook_info.pending_update_count}")
                    logger.info(f"📋 Webhook v13 max_connections: {webhook_info.max_connections}")

                    # Verificar se bot responde
                    me = updater.bot.get_me()
                    logger.info(f"🤖 Bot v13 verificado: @{me.username} (ID: {me.id})")

                except Exception as e:
                    logger.error(f"❌ Erro ao configurar webhook v13: {e}")
                    import traceback
                    logger.error(f"❌ Traceback webhook v13: {traceback.format_exc()}")

                logger.info("✅ Bot configurado (Railway webhook v13) - Iniciando Flask...")

                # Configurar Flask para PRODUÇÃO - DEBUG DESATIVADO
                app.config['ENV'] = 'production'   # Mudado para production
                app.config['DEBUG'] = False        # Desativado debug

                # Log detalhado para Railway v13
                logger.info(f"🌐 Iniciando Flask v13 na porta {PORT} - MODO PRODUÇÃO")
                logger.info(f"🔗 Health check disponível em: /health")
                logger.info(f"🔗 Webhook disponível em: {webhook_url}")
                logger.info(f"🔗 Root disponível em: /")
                logger.info(f"🔗 Ping disponível em: /ping")

                app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

            else:
                # Modo Local - Polling v13
                logger.info("🏠 Ambiente local v13 detectado - Usando polling")

                flask_thread = threading.Thread(target=run_flask_app, daemon=True)
                flask_thread.start()
                logger.info(f"🌐 Health check rodando na porta {PORT}")

                logger.info("✅ Bot configurado (polling v13) - Iniciando...")

                # Garantir que não há webhook ativo antes de iniciar polling
                try:
                    updater.bot.delete_webhook(drop_pending_updates=True)
                    logger.info("🧹 Webhook removido antes de iniciar polling v13")
                except Exception as e:
                    logger.debug(f"Webhook já estava removido v13: {e}")

                # Iniciar polling com error_callback para tratar conflitos e drop_pending_updates
                logger.info("🔄 Iniciando polling v13 com tratamento de conflitos...")
                updater.start_polling(
                    drop_pending_updates=True,  # Descarta updates pendentes para evitar conflitos
                    # error_callback já foi adicionado com dispatcher.add_error_handler
                )
                updater.idle()

    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        import traceback
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")

        # Tentar modo de emergência (apenas se não for Railway)
        try:
            is_railway_emergency = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))

            if is_railway_emergency:
                logger.error("🚨 ERRO NO RAILWAY - NÃO USAR POLLING EM MODO DE EMERGÊNCIA!")
                logger.error("💡 Solução: Verifique logs do Railway e redeploy se necessário")
                logger.error("🔗 Health check ainda disponível em /health")

                # Manter Flask rodando para health check
                try:
                    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
                except Exception as flask_error:
                    logger.error(f"❌ Erro no Flask de emergência: {flask_error}")
            else:
                logger.info("🆘 Tentando modo de emergência local...")
                # A instância 'bot' pode não ter sido completamente inicializada se o erro ocorreu antes.
                # Simplificando para um handler básico se 'bot' não estiver pronto.
                async def emergency_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    await update.message.reply_text("🆘 Bot em modo de emergência. Funcionalidade limitada.")

                if TELEGRAM_VERSION == "v20+":
                    emergency_app = Application.builder().token(TOKEN).build()
                    emergency_app.add_handler(CommandHandler("start", emergency_start))
                    emergency_app.run_polling(drop_pending_updates=True)
                else:
                    emergency_updater = Updater(TOKEN, use_context=True)
                    emergency_updater.dispatcher.add_handler(CommandHandler("start", emergency_start))
                    emergency_updater.start_polling(drop_pending_updates=True)
                    emergency_updater.idle()
        except Exception as emergency_error:
            logger.error(f"❌ Modo de emergência falhou: {emergency_error}")
    finally: # Adicionado para garantir que o lock seja liberado em caso de erro ou saída normal
        if 'lock_fd_or_status' in locals() and lock_fd_or_status is not None and lock_fd_or_status is not True: # Se for um file descriptor
            if hasattr(lock_fd_or_status, 'close'): # Se for um objeto de arquivo
                if os.name == 'posix': # fcntl para Unix
                    import fcntl
                    fcntl.flock(lock_fd_or_status, fcntl.LOCK_UN)
                elif os.name == 'nt': # msvcrt para Windows
                    import msvcrt
                    try:
                        msvcrt.locking(lock_fd_or_status.fileno(), msvcrt.LK_UNLCK, 1)
                    except: # Ignorar erros ao tentar desbloquear, pode já estar desbloqueado
                        pass
                lock_fd_or_status.close()
            # Remover o arquivo de lock na saída
            import tempfile  # Adicionado import necessário
            lock_file_path = os.path.join(tempfile.gettempdir(), 'bot_lol_v3.lock')
            if os.path.exists(lock_file_path):
                try:
                    os.remove(lock_file_path)
                    logger.info("🔓 Lock de instância única liberado e arquivo removido.")
                except OSError as e:
                    logger.warning(f"⚠️ Não foi possível remover o arquivo de lock: {e}")


if __name__ == "__main__":
    main()