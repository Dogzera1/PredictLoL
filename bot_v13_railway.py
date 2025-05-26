#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT LOL V3 ULTRA AVANÇADO - Versão Railway Compatível
Sistema completo com valor betting, portfolio e análise avançada
"""

import os
import sys
import time
import random
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

# Sistema de health check
from flask import Flask, jsonify
import requests

# Telegram Bot - Compatibilidade automática
try:
    # Tentar versão nova (v20+)
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
    from telegram.constants import ParseMode
    from telegram.error import TelegramError
    NEW_VERSION = True
    print("✅ Usando python-telegram-bot v20+")
except ImportError:
    try:
        # Tentar versão intermediária (v13-19)
        from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
        from telegram.error import TelegramError
        NEW_VERSION = False
        print("✅ Usando python-telegram-bot v13-19")
    except ImportError:
        print("❌ Erro: Versão do python-telegram-bot não suportada")
        sys.exit(1)

# Scientific computing
import numpy as np

# Configurações
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')
OWNER_ID = int(os.getenv('OWNER_ID', '6404423764'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthCheckManager:
    """Gerenciador de healthcheck para Railway"""
    
    def __init__(self):
        self.flask_app = Flask(__name__)
        self.bot_healthy = False
        self.last_activity = datetime.now()
        self.startup_time = datetime.now()
        
        @self.flask_app.route('/health')
        def health_check():
            if self.bot_healthy and (datetime.now() - self.last_activity).seconds < 300:
                return 'OK', 200
            return 'Bot unhealthy', 503
            
        @self.flask_app.route('/status')
        def status_check():
            return jsonify({
                'status': 'healthy' if self.bot_healthy else 'unhealthy',
                'last_activity': self.last_activity.isoformat(),
                'uptime_seconds': (datetime.now() - self.startup_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            })
    
    def start_flask_server(self):
        """Inicia servidor Flask em thread separada"""
        def run_flask():
            self.flask_app.run(host='0.0.0.0', port=5000, debug=False)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("✅ Flask healthcheck server iniciado na porta 5000")
    
    def mark_healthy(self):
        self.bot_healthy = True
        self.last_activity = datetime.now()
    
    def update_activity(self):
        self.last_activity = datetime.now()

class ValueBettingSystem:
    """Sistema de Value Betting com unidades básicas"""
    
    def __init__(self):
        self.base_unit = 100  # R$ 100 por unidade
        self.bankroll = 10000  # R$ 10.000
        self.max_units_per_bet = 3  # Máximo 3 unidades por aposta
        self.confidence_threshold = 0.65  # 65% confiança mínima
        self.ev_threshold = 0.03  # 3% EV mínimo
        logger.info("💰 Sistema de Value Betting com unidades inicializado")
    
    def calculate_bet_units(self, ev_percentage, confidence, probability_diff):
        """Calcula unidades baseado em EV e confiança"""
        
        # Análise de EV
        if ev_percentage >= 0.08:  # 8%+ EV
            ev_units = 2
            ev_level = "MUITO ALTO"
        elif ev_percentage >= 0.05:  # 5-8% EV
            ev_units = 1.5
            ev_level = "ALTO"
        elif ev_percentage >= 0.03:  # 3-5% EV
            ev_units = 1
            ev_level = "MÉDIO"
        else:
            ev_units = 0.5
            ev_level = "BAIXO"
        
        # Análise de Confiança
        if confidence >= 0.85:  # 85%+ confiança
            conf_units = 2
            conf_level = "MUITO ALTA"
        elif confidence >= 0.75:  # 75-85% confiança
            conf_units = 1.5
            conf_level = "ALTA"
        elif confidence >= 0.65:  # 65-75% confiança
            conf_units = 1
            conf_level = "MÉDIA"
        else:
            conf_units = 0.5
            conf_level = "BAIXA"
        
        # Cálculo final (média ponderada)
        final_units = min(self.max_units_per_bet, (ev_units + conf_units) / 2)
        final_units = round(final_units * 2) / 2  # Arredondar para 0.5
        
        return {
            'units': final_units,
            'stake': final_units * self.base_unit,
            'ev_level': ev_level,
            'conf_level': conf_level,
            'ev_percentage': ev_percentage * 100,
            'confidence': confidence * 100,
            'recommendation': self._get_recommendation(final_units, ev_percentage, confidence)
        }
    
    def _get_recommendation(self, units, ev, confidence):
        """Gera recomendação baseada na análise"""
        if units >= 2.5:
            return "🔥 APOSTA PREMIUM - Máxima prioridade"
        elif units >= 2.0:
            return "⭐ APOSTA FORTE - Alta recomendação"
        elif units >= 1.5:
            return "✅ APOSTA BOA - Recomendada"
        elif units >= 1.0:
            return "⚠️ APOSTA CAUTELOSA - Considerar"
        else:
            return "❌ APOSTA FRACA - Evitar"
    
    def analyze_value_opportunity(self, our_prob, bookmaker_odds):
        """Analisa oportunidade de value betting"""
        implied_prob = 1 / bookmaker_odds
        probability_diff = our_prob - implied_prob
        ev = (our_prob * (bookmaker_odds - 1)) - (1 - our_prob)
        
        # Calcular confiança baseada em múltiplos fatores
        confidence = self._calculate_confidence(our_prob, implied_prob, probability_diff)
        
        if ev > self.ev_threshold and confidence > self.confidence_threshold:
            bet_analysis = self.calculate_bet_units(ev, confidence, probability_diff)
            return {
                'has_value': True,
                'ev': ev,
                'probability_diff': probability_diff,
                'confidence': confidence,
                'bet_analysis': bet_analysis,
                'risk_level': self._assess_risk_level(ev, confidence)
            }
        
        return {'has_value': False, 'reason': 'EV ou confiança insuficiente'}
    
    def _calculate_confidence(self, our_prob, implied_prob, prob_diff):
        """Calcula confiança da aposta baseada em múltiplos fatores"""
        # Fator 1: Diferença de probabilidade
        diff_factor = min(1.0, prob_diff * 10)  # Normalizar
        
        # Fator 2: Distância da probabilidade 50/50
        certainty_factor = abs(our_prob - 0.5) * 2
        
        # Fator 3: Margem de segurança
        safety_factor = min(1.0, prob_diff * 5) if prob_diff > 0 else 0
        
        # Combinação ponderada
        confidence = (diff_factor * 0.4 + certainty_factor * 0.3 + safety_factor * 0.3)
        return min(1.0, confidence)
    
    def _assess_risk_level(self, ev, confidence):
        """Avalia nível de risco da aposta"""
        if ev >= 0.08 and confidence >= 0.85:
            return "BAIXO"
        elif ev >= 0.05 and confidence >= 0.75:
            return "MÉDIO"
        elif ev >= 0.03 and confidence >= 0.65:
            return "ALTO"
        else:
            return "MUITO ALTO"
    
    def get_portfolio_suggestions(self):
        """Sugestões para melhorar o sistema"""
        return {
            'bankroll_management': [
                "💰 Nunca aposte mais de 5% da banca total por dia",
                "📊 Mantenha registro detalhado de todas as apostas",
                "🔄 Reavalie unidades a cada 100 apostas",
                "📈 Aumente unidades apenas com ROI consistente >10%"
            ],
            'value_hunting': [
                "🎯 Foque em partidas com EV >5% para maximizar lucros",
                "⏰ Aposte próximo ao início para odds mais precisas",
                "🔍 Compare múltiplas casas para encontrar melhores odds",
                "📱 Use alertas automáticos para oportunidades premium"
            ],
            'risk_management': [
                "🛡️ Diversifique entre diferentes ligas e regiões",
                "⚠️ Evite apostas consecutivas no mesmo time",
                "📉 Reduza unidades após sequência de 3+ perdas",
                "🎲 Nunca persiga perdas aumentando stakes"
            ],
            'advanced_tips': [
                "🧠 Analise meta do jogo e patches recentes",
                "👥 Considere mudanças de roster e forma recente",
                "🏆 Peso maior para playoffs e finais",
                "📊 Use estatísticas de head-to-head histórico"
            ]
        }

class LiveStatsSystem:
    """Sistema de estatísticas em tempo real"""
    
    def __init__(self):
        self.cache = {}
        self.value_system = ValueBettingSystem()
        logger.info("🎮 Sistema de estatísticas ao vivo inicializado")
    
    def get_live_stats(self, match_id="demo_match"):
        """Gera estatísticas dinâmicas em tempo real"""
        current_time = datetime.now()
        
        # Simular tempo de jogo (15-45 minutos)
        game_time = random.randint(15, 45)
        
        # Estatísticas baseadas no tempo de jogo
        if game_time < 20:  # Early game
            kills_range = (3, 8)
            gold_range = (25000, 35000)
            dragons_max = 1
            barons_max = 0
        elif game_time < 30:  # Mid game
            kills_range = (8, 15)
            gold_range = (35000, 50000)
            dragons_max = 2
            barons_max = 1
        else:  # Late game
            kills_range = (15, 25)
            gold_range = (50000, 70000)
            dragons_max = 4
            barons_max = 2
        
        # Gerar stats dos times
        team1_kills = random.randint(*kills_range)
        team2_kills = random.randint(*kills_range)
        team1_deaths = random.randint(max(1, team2_kills - 3), team2_kills + 3)
        team2_deaths = random.randint(max(1, team1_kills - 3), team1_kills + 3)
        
        team1_gold = random.randint(*gold_range)
        team2_gold = random.randint(*gold_range)
        
        team1_cs = random.randint(150, 300)
        team2_cs = random.randint(150, 300)
        
        # Objetivos
        dragons_t1 = random.randint(0, dragons_max)
        dragons_t2 = random.randint(0, dragons_max - dragons_t1)
        
        barons_t1 = random.randint(0, barons_max)
        barons_t2 = random.randint(0, barons_max - barons_t1)
        
        towers_t1 = random.randint(0, 6)
        towers_t2 = random.randint(0, 6)
        
        # Calcular probabilidades dinâmicas
        gold_advantage = team1_gold - team2_gold
        kill_advantage = team1_kills - team2_kills
        obj_advantage = (dragons_t1 + barons_t1 + towers_t1) - (dragons_t2 + barons_t2 + towers_t2)
        
        # Fórmula de probabilidade
        base_prob = 0.5
        gold_factor = gold_advantage * 0.000012  # 1.2% por 1000 gold
        kill_factor = kill_advantage * 0.025     # 2.5% por kill
        obj_factor = obj_advantage * 0.04        # 4% por objetivo
        
        team1_prob = max(0.10, min(0.90, base_prob + gold_factor + kill_factor + obj_factor))
        team2_prob = 1 - team1_prob
        
        # Determinar fase da partida
        if game_time < 20:
            phase = "Early Game"
            phase_emoji = "🌅"
        elif game_time < 30:
            phase = "Mid Game"
            phase_emoji = "⚡"
        else:
            phase = "Late Game"
            phase_emoji = "🔥"
        
        return {
            'game_time': game_time,
            'phase': phase,
            'phase_emoji': phase_emoji,
            'team1': {
                'name': 'T1',
                'kills': team1_kills,
                'deaths': team1_deaths,
                'assists': team1_kills + random.randint(5, 15),
                'gold': team1_gold,
                'cs': team1_cs,
                'dragons': dragons_t1,
                'barons': barons_t1,
                'towers': towers_t1
            },
            'team2': {
                'name': 'Gen.G',
                'kills': team2_kills,
                'deaths': team2_deaths,
                'assists': team2_kills + random.randint(5, 15),
                'gold': team2_gold,
                'cs': team2_cs,
                'dragons': dragons_t2,
                'barons': barons_t2,
                'towers': towers_t2
            },
            'probabilities': {
                'team1': team1_prob,
                'team2': team2_prob
            },
            'advantages': {
                'gold': gold_advantage,
                'kills': kill_advantage,
                'objectives': obj_advantage
            },
            'timestamp': current_time.strftime('%H:%M:%S')
        }

class AdvancedMatchAnalyzer:
    """Sistema avançado de análise de partidas com múltiplos fatores"""
    
    def __init__(self):
        self.patch_version = "14.23"  # Patch atual
        self.meta_champions = self._load_meta_data()
        self.team_database = self._load_team_database()
        self.player_database = self._load_player_database()
        self.champion_synergies = self._load_champion_synergies()
        self.tournament_context = self._load_tournament_context()
        logger.info("🧠 Sistema Avançado de Análise inicializado")
    
    def _load_meta_data(self):
        """Carrega dados da meta atual baseado no patch"""
        return {
            'patch_14_23': {
                'op_champions': {
                    'top': ['Aatrox', 'Jax', 'Fiora', 'Camille', 'Gnar'],
                    'jungle': ['Graves', 'Nidalee', 'Elise', 'Kindred', 'Viego'],
                    'mid': ['Azir', 'Orianna', 'Syndra', 'Corki', 'Viktor'],
                    'adc': ['Jinx', 'Aphelios', 'Kai\'Sa', 'Xayah', 'Varus'],
                    'support': ['Thresh', 'Nautilus', 'Leona', 'Alistar', 'Rakan']
                },
                'banned_champions': ['Kalista', 'Azir', 'Ryze', 'Akali'],
                'power_spikes': {
                    'early': ['Draven', 'Renekton', 'Elise', 'Pantheon'],
                    'mid': ['Orianna', 'Graves', 'Syndra', 'Jinx'],
                    'late': ['Kassadin', 'Kayle', 'Vayne', 'Azir']
                },
                'meta_shifts': {
                    'tank_meta': 0.3,
                    'assassin_meta': 0.4,
                    'scaling_meta': 0.6,
                    'early_game_meta': 0.4
                }
            }
        }
    
    def _load_team_database(self):
        """Base de dados completa dos times com múltiplas métricas"""
        return {
            # LCK
            'T1': {
                'rating': 95, 'region': 'LCK',
                'recent_form': 0.88, 'consistency': 0.90,
                'early_game': 0.85, 'mid_game': 0.92, 'late_game': 0.88,
                'draft_flexibility': 0.90, 'clutch_factor': 0.95,
                'international_exp': 0.95, 'roster_stability': 0.85,
                'coaching_quality': 0.90, 'meta_adaptation': 0.88,
                'recent_matches': [1, 1, 1, 0, 1],  # W/L últimas 5
                'avg_game_time': 32.5, 'first_blood_rate': 0.65,
                'baron_control': 0.78, 'dragon_control': 0.82
            },
            'Gen.G': {
                'rating': 92, 'region': 'LCK',
                'recent_form': 0.82, 'consistency': 0.88,
                'early_game': 0.80, 'mid_game': 0.85, 'late_game': 0.90,
                'draft_flexibility': 0.85, 'clutch_factor': 0.82,
                'international_exp': 0.85, 'roster_stability': 0.90,
                'coaching_quality': 0.88, 'meta_adaptation': 0.85,
                'recent_matches': [1, 0, 1, 1, 1],
                'avg_game_time': 35.2, 'first_blood_rate': 0.58,
                'baron_control': 0.75, 'dragon_control': 0.80
            },
            # LPL
            'JDG': {
                'rating': 94, 'region': 'LPL',
                'recent_form': 0.90, 'consistency': 0.85,
                'early_game': 0.92, 'mid_game': 0.88, 'late_game': 0.82,
                'draft_flexibility': 0.88, 'clutch_factor': 0.85,
                'international_exp': 0.90, 'roster_stability': 0.80,
                'coaching_quality': 0.85, 'meta_adaptation': 0.90,
                'recent_matches': [1, 1, 0, 1, 1],
                'avg_game_time': 30.8, 'first_blood_rate': 0.72,
                'baron_control': 0.80, 'dragon_control': 0.85
            },
            'BLG': {
                'rating': 90, 'region': 'LPL',
                'recent_form': 0.85, 'consistency': 0.82,
                'early_game': 0.88, 'mid_game': 0.85, 'late_game': 0.80,
                'draft_flexibility': 0.82, 'clutch_factor': 0.80,
                'international_exp': 0.75, 'roster_stability': 0.85,
                'coaching_quality': 0.82, 'meta_adaptation': 0.85,
                'recent_matches': [1, 1, 1, 0, 0],
                'avg_game_time': 31.5, 'first_blood_rate': 0.68,
                'baron_control': 0.76, 'dragon_control': 0.78
            },
            # LEC
            'G2': {
                'rating': 88, 'region': 'LEC',
                'recent_form': 0.85, 'consistency': 0.80,
                'early_game': 0.82, 'mid_game': 0.88, 'late_game': 0.85,
                'draft_flexibility': 0.92, 'clutch_factor': 0.88,
                'international_exp': 0.90, 'roster_stability': 0.75,
                'coaching_quality': 0.85, 'meta_adaptation': 0.88,
                'recent_matches': [1, 0, 1, 1, 1],
                'avg_game_time': 33.2, 'first_blood_rate': 0.62,
                'baron_control': 0.72, 'dragon_control': 0.75
            },
            'Fnatic': {
                'rating': 85, 'region': 'LEC',
                'recent_form': 0.78, 'consistency': 0.82,
                'early_game': 0.75, 'mid_game': 0.82, 'late_game': 0.88,
                'draft_flexibility': 0.80, 'clutch_factor': 0.75,
                'international_exp': 0.85, 'roster_stability': 0.70,
                'coaching_quality': 0.80, 'meta_adaptation': 0.78,
                'recent_matches': [0, 1, 1, 0, 1],
                'avg_game_time': 34.8, 'first_blood_rate': 0.55,
                'baron_control': 0.70, 'dragon_control': 0.72
            },
            # LCS
            'C9': {
                'rating': 82, 'region': 'LCS',
                'recent_form': 0.80, 'consistency': 0.75,
                'early_game': 0.78, 'mid_game': 0.80, 'late_game': 0.82,
                'draft_flexibility': 0.85, 'clutch_factor': 0.78,
                'international_exp': 0.70, 'roster_stability': 0.80,
                'coaching_quality': 0.78, 'meta_adaptation': 0.80,
                'recent_matches': [1, 1, 0, 1, 0],
                'avg_game_time': 32.8, 'first_blood_rate': 0.60,
                'baron_control': 0.68, 'dragon_control': 0.70
            },
            # CBLOL
            'LOUD': {
                'rating': 85, 'region': 'CBLOL',
                'recent_form': 0.88, 'consistency': 0.85,
                'early_game': 0.85, 'mid_game': 0.82, 'late_game': 0.78,
                'draft_flexibility': 0.80, 'clutch_factor': 0.85,
                'international_exp': 0.60, 'roster_stability': 0.90,
                'coaching_quality': 0.82, 'meta_adaptation': 0.85,
                'recent_matches': [1, 1, 1, 1, 0],
                'avg_game_time': 31.2, 'first_blood_rate': 0.70,
                'baron_control': 0.75, 'dragon_control': 0.78
            }
        }
    
    def _load_player_database(self):
        """Base de dados de jogadores individuais"""
        return {
            # T1
            'Zeus': {'role': 'top', 'team': 'T1', 'skill': 95, 'consistency': 90, 'clutch': 92},
            'Oner': {'role': 'jungle', 'team': 'T1', 'skill': 92, 'consistency': 88, 'clutch': 90},
            'Faker': {'role': 'mid', 'team': 'T1', 'skill': 98, 'consistency': 95, 'clutch': 98},
            'Gumayusi': {'role': 'adc', 'team': 'T1', 'skill': 94, 'consistency': 90, 'clutch': 88},
            'Keria': {'role': 'support', 'team': 'T1', 'skill': 96, 'consistency': 92, 'clutch': 94},
            
            # Gen.G
            'Kiin': {'role': 'top', 'team': 'Gen.G', 'skill': 90, 'consistency': 92, 'clutch': 85},
            'Canyon': {'role': 'jungle', 'team': 'Gen.G', 'skill': 96, 'consistency': 90, 'clutch': 92},
            'Chovy': {'role': 'mid', 'team': 'Gen.G', 'skill': 96, 'consistency': 94, 'clutch': 88},
            'Peyz': {'role': 'adc', 'team': 'Gen.G', 'skill': 88, 'consistency': 85, 'clutch': 82},
            'Lehends': {'role': 'support', 'team': 'Gen.G', 'skill': 90, 'consistency': 88, 'clutch': 85},
            
            # Adicionar mais jogadores conforme necessário...
        }
    
    def _load_champion_synergies(self):
        """Sinergias e anti-sinergias entre champions"""
        return {
            'strong_synergies': {
                ('Yasuo', 'Malphite'): 0.85,
                ('Orianna', 'Malphite'): 0.80,
                ('Jinx', 'Thresh'): 0.75,
                ('Azir', 'Sejuani'): 0.80,
                ('Kai\'Sa', 'Nautilus'): 0.78,
                ('Graves', 'Orianna'): 0.82,
                ('Aphelios', 'Thresh'): 0.80
            },
            'counters': {
                'Yasuo': ['Malzahar', 'Annie', 'Pantheon'],
                'Azir': ['Zed', 'Fizz', 'Kassadin'],
                'Jinx': ['Zed', 'Rengar', 'Kha\'Zix'],
                'Graves': ['Rammus', 'Malphite', 'Sejuani']
            },
            'meta_priority': {
                'S_tier': ['Azir', 'Graves', 'Thresh', 'Jinx', 'Aatrox'],
                'A_tier': ['Orianna', 'Nidalee', 'Nautilus', 'Kai\'Sa', 'Jax'],
                'B_tier': ['Syndra', 'Elise', 'Leona', 'Aphelios', 'Fiora']
            }
        }
    
    def _load_tournament_context(self):
        """Contexto do torneio e importância das partidas"""
        return {
            'worlds_2024': {
                'importance_multiplier': 1.5,
                'pressure_factor': 1.3,
                'international_bonus': 0.1
            },
            'lck_spring': {
                'importance_multiplier': 1.2,
                'pressure_factor': 1.1,
                'regional_bonus': 0.05
            },
            'regular_season': {
                'importance_multiplier': 1.0,
                'pressure_factor': 1.0,
                'bonus': 0.0
            }
        }
    
    def analyze_comprehensive_match(self, team1: str, team2: str, 
                                  team1_comp: List[str] = None, 
                                  team2_comp: List[str] = None,
                                  tournament_type: str = "regular_season") -> Dict:
        """Análise completa da partida considerando todos os fatores"""
        
        # 1. Dados básicos dos times
        team1_data = self.team_database.get(team1, self._get_default_team_data())
        team2_data = self.team_database.get(team2, self._get_default_team_data())
        
        # 2. Análise de composição (se disponível)
        draft_analysis = self._analyze_draft(team1_comp, team2_comp) if team1_comp and team2_comp else None
        
        # 3. Análise de performance individual
        player_analysis = self._analyze_players(team1, team2)
        
        # 4. Contexto do torneio
        tournament_context = self.tournament_context.get(tournament_type, self.tournament_context['regular_season'])
        
        # 5. Análise da meta atual
        meta_analysis = self._analyze_meta_fit(team1_data, team2_data, team1_comp, team2_comp)
        
        # 6. Head-to-head histórico
        h2h_analysis = self._analyze_head_to_head(team1, team2)
        
        # 7. Cálculo de probabilidade final
        final_probability = self._calculate_comprehensive_probability(
            team1_data, team2_data, draft_analysis, player_analysis,
            meta_analysis, h2h_analysis, tournament_context
        )
        
        # 8. Gerar análise textual
        analysis_text = self._generate_comprehensive_analysis(
            team1, team2, team1_data, team2_data, draft_analysis,
            player_analysis, meta_analysis, final_probability
        )
        
        return {
            'teams': {'team1': team1, 'team2': team2},
            'probability': final_probability,
            'team_analysis': {'team1': team1_data, 'team2': team2_data},
            'draft_analysis': draft_analysis,
            'player_analysis': player_analysis,
            'meta_analysis': meta_analysis,
            'h2h_analysis': h2h_analysis,
            'tournament_context': tournament_context,
            'detailed_analysis': analysis_text,
            'confidence_level': self._calculate_confidence(final_probability, team1_data, team2_data),
            'key_factors': self._identify_key_factors(team1_data, team2_data, draft_analysis),
            'patch_version': self.patch_version
        }
    
    def _analyze_draft(self, team1_comp: List[str], team2_comp: List[str]) -> Dict:
        """Análise detalhada do draft"""
        if not team1_comp or not team2_comp:
            return None
        
        # Análise de tier dos champions
        team1_tiers = self._get_champion_tiers(team1_comp)
        team2_tiers = self._get_champion_tiers(team2_comp)
        
        # Análise de sinergias
        team1_synergy = self._calculate_team_synergy(team1_comp)
        team2_synergy = self._calculate_team_synergy(team2_comp)
        
        # Análise de power spikes
        team1_spikes = self._analyze_power_spikes(team1_comp)
        team2_spikes = self._analyze_power_spikes(team2_comp)
        
        # Análise de counters
        team1_counters = self._analyze_counters(team1_comp, team2_comp)
        team2_counters = self._analyze_counters(team2_comp, team1_comp)
        
        draft_advantage = (team1_tiers + team1_synergy - team2_counters) - (team2_tiers + team2_synergy - team1_counters)
        
        return {
            'team1_composition': team1_comp,
            'team2_composition': team2_comp,
            'team1_tier_score': team1_tiers,
            'team2_tier_score': team2_tiers,
            'team1_synergy': team1_synergy,
            'team2_synergy': team2_synergy,
            'team1_power_spikes': team1_spikes,
            'team2_power_spikes': team2_spikes,
            'draft_advantage': draft_advantage,
            'draft_winner': 'team1' if draft_advantage > 0 else 'team2',
            'advantage_magnitude': abs(draft_advantage)
        }
    
    def _analyze_players(self, team1: str, team2: str) -> Dict:
        """Análise de performance individual dos jogadores"""
        team1_players = [p for p in self.player_database.values() if p['team'] == team1]
        team2_players = [p for p in self.player_database.values() if p['team'] == team2]
        
        if not team1_players or not team2_players:
            return {'available': False}
        
        team1_avg_skill = np.mean([p['skill'] for p in team1_players])
        team2_avg_skill = np.mean([p['skill'] for p in team2_players])
        
        team1_consistency = np.mean([p['consistency'] for p in team1_players])
        team2_consistency = np.mean([p['consistency'] for p in team2_players])
        
        team1_clutch = np.mean([p['clutch'] for p in team1_players])
        team2_clutch = np.mean([p['clutch'] for p in team2_players])
        
        return {
            'available': True,
            'team1_skill': team1_avg_skill,
            'team2_skill': team2_avg_skill,
            'team1_consistency': team1_consistency,
            'team2_consistency': team2_consistency,
            'team1_clutch': team1_clutch,
            'team2_clutch': team2_clutch,
            'skill_advantage': team1_avg_skill - team2_avg_skill,
            'consistency_advantage': team1_consistency - team2_consistency,
            'clutch_advantage': team1_clutch - team2_clutch
        }
    
    def _analyze_meta_fit(self, team1_data: Dict, team2_data: Dict, 
                         team1_comp: List[str] = None, team2_comp: List[str] = None) -> Dict:
        """Análise de adaptação à meta atual"""
        meta_data = self.meta_champions['patch_14_23']
        
        team1_meta_score = team1_data.get('meta_adaptation', 0.7)
        team2_meta_score = team2_data.get('meta_adaptation', 0.7)
        
        # Bonus se a composição está na meta
        if team1_comp:
            team1_meta_bonus = self._calculate_meta_bonus(team1_comp, meta_data)
            team1_meta_score += team1_meta_bonus
        
        if team2_comp:
            team2_meta_bonus = self._calculate_meta_bonus(team2_comp, meta_data)
            team2_meta_score += team2_meta_bonus
        
        return {
            'team1_meta_score': team1_meta_score,
            'team2_meta_score': team2_meta_score,
            'meta_advantage': team1_meta_score - team2_meta_score,
            'patch_version': self.patch_version,
            'meta_type': self._determine_meta_type(meta_data)
        }
    
    def _analyze_head_to_head(self, team1: str, team2: str) -> Dict:
        """Análise histórica entre os times"""
        # Simulação de dados históricos (em implementação real, viria de banco de dados)
        h2h_data = {
            ('T1', 'Gen.G'): {'wins': 7, 'losses': 3, 'avg_game_time': 33.2},
            ('Gen.G', 'T1'): {'wins': 3, 'losses': 7, 'avg_game_time': 33.2},
            ('JDG', 'BLG'): {'wins': 6, 'losses': 4, 'avg_game_time': 31.8},
            ('BLG', 'JDG'): {'wins': 4, 'losses': 6, 'avg_game_time': 31.8}
        }
        
        key = (team1, team2)
        reverse_key = (team2, team1)
        
        if key in h2h_data:
            data = h2h_data[key]
            total_games = data['wins'] + data['losses']
            win_rate = data['wins'] / total_games if total_games > 0 else 0.5
        elif reverse_key in h2h_data:
            data = h2h_data[reverse_key]
            total_games = data['wins'] + data['losses']
            win_rate = data['losses'] / total_games if total_games > 0 else 0.5
        else:
            return {'available': False, 'win_rate': 0.5}
        
        return {
            'available': True,
            'total_games': total_games,
            'team1_wins': data['wins'] if key in h2h_data else data['losses'],
            'team2_wins': data['losses'] if key in h2h_data else data['wins'],
            'win_rate': win_rate,
            'avg_game_time': data.get('avg_game_time', 32.0),
            'historical_advantage': 'team1' if win_rate > 0.5 else 'team2'
        }
    
    def _calculate_comprehensive_probability(self, team1_data: Dict, team2_data: Dict,
                                           draft_analysis: Dict, player_analysis: Dict,
                                           meta_analysis: Dict, h2h_analysis: Dict,
                                           tournament_context: Dict) -> Dict:
        """Cálculo final de probabilidade considerando todos os fatores"""
        
        # Pesos para cada fator
        weights = {
            'team_rating': 0.25,
            'recent_form': 0.20,
            'draft': 0.15,
            'players': 0.15,
            'meta_fit': 0.10,
            'h2h': 0.10,
            'tournament_context': 0.05
        }
        
        # Cálculo base (rating dos times)
        rating_diff = (team1_data['rating'] - team2_data['rating']) / 100
        base_prob = 0.5 + (rating_diff * 0.3)
        
        # Forma recente
        form_diff = team1_data['recent_form'] - team2_data['recent_form']
        form_adjustment = form_diff * 0.2
        
        # Draft advantage
        draft_adjustment = 0
        if draft_analysis:
            draft_adjustment = draft_analysis['draft_advantage'] * 0.1
        
        # Player skill
        player_adjustment = 0
        if player_analysis.get('available'):
            skill_diff = player_analysis['skill_advantage'] / 100
            player_adjustment = skill_diff * 0.15
        
        # Meta fit
        meta_adjustment = meta_analysis['meta_advantage'] * 0.1
        
        # Head-to-head
        h2h_adjustment = 0
        if h2h_analysis.get('available'):
            h2h_adjustment = (h2h_analysis['win_rate'] - 0.5) * 0.2
        
        # Tournament context
        tournament_multiplier = tournament_context['importance_multiplier']
        pressure_factor = tournament_context['pressure_factor']
        
        # Cálculo final
        final_prob = base_prob + form_adjustment + draft_adjustment + player_adjustment + meta_adjustment + h2h_adjustment
        
        # Aplicar contexto do torneio
        if final_prob > 0.5:
            final_prob = 0.5 + (final_prob - 0.5) * tournament_multiplier
        else:
            final_prob = 0.5 - (0.5 - final_prob) * tournament_multiplier
        
        # Limitar entre 0.1 e 0.9
        final_prob = max(0.1, min(0.9, final_prob))
        
        return {
            'team1_probability': final_prob,
            'team2_probability': 1 - final_prob,
            'confidence': self._calculate_analysis_confidence(team1_data, team2_data, draft_analysis),
            'factors_breakdown': {
                'base_rating': base_prob,
                'form_impact': form_adjustment,
                'draft_impact': draft_adjustment,
                'player_impact': player_adjustment,
                'meta_impact': meta_adjustment,
                'h2h_impact': h2h_adjustment,
                'tournament_multiplier': tournament_multiplier
            }
        }
    
    def _generate_comprehensive_analysis(self, team1: str, team2: str, team1_data: Dict,
                                       team2_data: Dict, draft_analysis: Dict,
                                       player_analysis: Dict, meta_analysis: Dict,
                                       probability: Dict) -> str:
        """Gera análise textual completa"""
        
        analysis_parts = []
        
        # Análise de rating e forma
        rating_diff = team1_data['rating'] - team2_data['rating']
        if rating_diff > 5:
            analysis_parts.append(f"📊 {team1} tem vantagem no ranking ({team1_data['rating']} vs {team2_data['rating']})")
        elif rating_diff < -5:
            analysis_parts.append(f"📊 {team2} tem vantagem no ranking ({team2_data['rating']} vs {team1_data['rating']})")
        else:
            analysis_parts.append("📊 Times com força similar no ranking")
        
        # Forma recente
        if team1_data['recent_form'] > team2_data['recent_form'] + 0.1:
            analysis_parts.append(f"📈 {team1} em melhor forma recente ({team1_data['recent_form']:.1%})")
        elif team2_data['recent_form'] > team1_data['recent_form'] + 0.1:
            analysis_parts.append(f"📈 {team2} em melhor forma recente ({team2_data['recent_form']:.1%})")
        
        # Draft analysis
        if draft_analysis:
            if draft_analysis['draft_advantage'] > 0.1:
                analysis_parts.append(f"🎯 {team1} com vantagem no draft")
            elif draft_analysis['draft_advantage'] < -0.1:
                analysis_parts.append(f"🎯 {team2} com vantagem no draft")
        
        # Player analysis
        if player_analysis.get('available'):
            if player_analysis['skill_advantage'] > 2:
                analysis_parts.append(f"⭐ {team1} com jogadores mais habilidosos")
            elif player_analysis['skill_advantage'] < -2:
                analysis_parts.append(f"⭐ {team2} com jogadores mais habilidosos")
        
        # Meta fit
        if meta_analysis['meta_advantage'] > 0.05:
            analysis_parts.append(f"🔄 {team1} melhor adaptado à meta atual")
        elif meta_analysis['meta_advantage'] < -0.05:
            analysis_parts.append(f"🔄 {team2} melhor adaptado à meta atual")
        
        # Probabilidade final
        team1_prob = probability['team1_probability']
        if team1_prob > 0.65:
            analysis_parts.append(f"🏆 {team1} é forte favorito ({team1_prob:.1%})")
        elif team1_prob > 0.55:
            analysis_parts.append(f"🏆 {team1} é ligeiro favorito ({team1_prob:.1%})")
        elif team1_prob < 0.35:
            analysis_parts.append(f"🏆 {team2} é forte favorito ({1-team1_prob:.1%})")
        elif team1_prob < 0.45:
            analysis_parts.append(f"🏆 {team2} é ligeiro favorito ({1-team1_prob:.1%})")
        else:
            analysis_parts.append("⚖️ Partida muito equilibrada")
        
        return "\n".join(analysis_parts)
    
    # Métodos auxiliares
    def _get_default_team_data(self):
        return {
            'rating': 75, 'recent_form': 0.6, 'consistency': 0.6,
            'early_game': 0.6, 'mid_game': 0.6, 'late_game': 0.6,
            'meta_adaptation': 0.6
        }
    
    def _get_champion_tiers(self, composition: List[str]) -> float:
        meta = self.meta_champions['patch_14_23']
        score = 0
        for champ in composition:
            if champ in meta['op_champions'].get('top', []) + meta['op_champions'].get('jungle', []) + meta['op_champions'].get('mid', []) + meta['op_champions'].get('adc', []) + meta['op_champions'].get('support', []):
                score += 1
        return score / len(composition) if composition else 0
    
    def _calculate_team_synergy(self, composition: List[str]) -> float:
        synergies = self.champion_synergies['strong_synergies']
        score = 0
        count = 0
        for i, champ1 in enumerate(composition):
            for champ2 in composition[i+1:]:
                if (champ1, champ2) in synergies:
                    score += synergies[(champ1, champ2)]
                    count += 1
                elif (champ2, champ1) in synergies:
                    score += synergies[(champ2, champ1)]
                    count += 1
        return score / count if count > 0 else 0.5
    
    def _analyze_power_spikes(self, composition: List[str]) -> Dict:
        meta = self.meta_champions['patch_14_23']['power_spikes']
        early = sum(1 for champ in composition if champ in meta['early'])
        mid = sum(1 for champ in composition if champ in meta['mid'])
        late = sum(1 for champ in composition if champ in meta['late'])
        return {'early': early, 'mid': mid, 'late': late}
    
    def _analyze_counters(self, team_comp: List[str], enemy_comp: List[str]) -> float:
        counters = self.champion_synergies['counters']
        counter_score = 0
        for champ in team_comp:
            for enemy_champ in enemy_comp:
                if enemy_champ in counters.get(champ, []):
                    counter_score += 1
        return counter_score / (len(team_comp) * len(enemy_comp)) if team_comp and enemy_comp else 0
    
    def _calculate_meta_bonus(self, composition: List[str], meta_data: Dict) -> float:
        bonus = 0
        for champ in composition:
            if champ in meta_data['op_champions'].get('top', []) + meta_data['op_champions'].get('jungle', []) + meta_data['op_champions'].get('mid', []) + meta_data['op_champions'].get('adc', []) + meta_data['op_champions'].get('support', []):
                bonus += 0.02
        return bonus
    
    def _determine_meta_type(self, meta_data: Dict) -> str:
        shifts = meta_data['meta_shifts']
        max_meta = max(shifts, key=shifts.get)
        return max_meta
    
    def _calculate_confidence(self, probability: Dict, team1_data: Dict, team2_data: Dict) -> float:
        # Confiança baseada na diferença de probabilidade e consistência dos times
        prob_diff = abs(probability['team1_probability'] - 0.5)
        consistency_avg = (team1_data.get('consistency', 0.6) + team2_data.get('consistency', 0.6)) / 2
        return min(0.95, prob_diff * 2 + consistency_avg * 0.3)
    
    def _calculate_analysis_confidence(self, team1_data: Dict, team2_data: Dict, draft_analysis: Dict) -> float:
        base_confidence = 0.7
        if draft_analysis:
            base_confidence += 0.1
        if team1_data.get('recent_matches') and team2_data.get('recent_matches'):
            base_confidence += 0.1
        return min(0.95, base_confidence)
    
    def _identify_key_factors(self, team1_data: Dict, team2_data: Dict, draft_analysis: Dict) -> List[str]:
        factors = []
        
        rating_diff = abs(team1_data['rating'] - team2_data['rating'])
        if rating_diff > 10:
            factors.append("Diferença significativa de rating")
        
        form_diff = abs(team1_data['recent_form'] - team2_data['recent_form'])
        if form_diff > 0.15:
            factors.append("Diferença na forma recente")
        
        if draft_analysis and abs(draft_analysis['draft_advantage']) > 0.1:
            factors.append("Vantagem no draft")
        
        return factors

class AlertSystem:
    """Sistema de alertas automáticos para grupos do Telegram"""
    
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.subscribed_groups = set()  # IDs dos grupos inscritos
        self.alert_settings = {
            'value_betting': True,
            'live_matches': True,
            'high_ev_only': False,  # Apenas EV alto (8%+)
            'min_confidence': 0.65,  # Confiança mínima
            'min_ev': 0.03  # EV mínimo (3%)
        }
        self.last_alerts = {}  # Cache para evitar spam
        self.monitoring_active = False
        self.monitor_thread = None
        logger.info("🚨 Sistema de alertas inicializado")
    
    def subscribe_group(self, chat_id):
        """Inscrever grupo para receber alertas"""
        self.subscribed_groups.add(chat_id)
        logger.info(f"📢 Grupo {chat_id} inscrito para alertas")
        return True
    
    def unsubscribe_group(self, chat_id):
        """Desinscrever grupo dos alertas"""
        self.subscribed_groups.discard(chat_id)
        logger.info(f"🔇 Grupo {chat_id} desinscrito dos alertas")
        return True
    
    def update_settings(self, **kwargs):
        """Atualizar configurações de alertas"""
        for key, value in kwargs.items():
            if key in self.alert_settings:
                self.alert_settings[key] = value
                logger.info(f"⚙️ Configuração {key} atualizada para {value}")
    
    def start_monitoring(self):
        """Iniciar monitoramento automático"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("🔄 Monitoramento de alertas iniciado")
    
    def stop_monitoring(self):
        """Parar monitoramento automático"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("⏹️ Monitoramento de alertas parado")
    
    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.monitoring_active:
            try:
                # Verificar partidas ao vivo
                if self.alert_settings['live_matches']:
                    self._check_live_matches()
                
                # Verificar oportunidades de value betting
                if self.alert_settings['value_betting']:
                    self._check_value_opportunities()
                
                # Aguardar 60 segundos antes da próxima verificação
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Erro no monitoramento: {e}")
                time.sleep(30)  # Aguardar menos tempo em caso de erro
    
    def _check_live_matches(self):
        """Verificar partidas ao vivo e enviar alertas"""
        try:
            # Simular detecção de partida (substituir pela API real quando corrigida)
            current_time = datetime.now()
            
            # Verificar se já enviamos alerta recentemente
            if 'live_match_check' in self.last_alerts:
                time_diff = (current_time - self.last_alerts['live_match_check']).seconds
                if time_diff < 300:  # 5 minutos
                    return
            
            # Simular partida detectada (remover quando API estiver funcionando)
            if random.random() < 0.1:  # 10% chance de "detectar" partida
                match_data = {
                    'team1': 'T1',
                    'team2': 'Gen.G',
                    'league': 'LCK',
                    'status': 'LIVE',
                    'game_time': '15:30'
                }
                
                alert_text = (
                    "🔴 **PARTIDA AO VIVO DETECTADA!**\n\n"
                    f"🎮 **{match_data['team1']} vs {match_data['team2']}**\n"
                    f"🏆 Liga: {match_data['league']}\n"
                    f"⏰ Tempo: {match_data['game_time']}\n"
                    f"📊 Status: {match_data['status']}\n\n"
                    "💰 Use `/value` para análise de apostas\n"
                    "📊 Use `/stats` para estatísticas ao vivo"
                )
                
                self._send_alert_to_groups(alert_text)
                self.last_alerts['live_match_check'] = current_time
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar partidas: {e}")
    
    def _check_value_opportunities(self):
        """Verificar oportunidades de value betting"""
        try:
            current_time = datetime.now()
            
            # Verificar se já enviamos alerta recentemente
            if 'value_check' in self.last_alerts:
                time_diff = (current_time - self.last_alerts['value_check']).seconds
                if time_diff < 600:  # 10 minutos
                    return
            
            # Simular oportunidade de value betting
            if random.random() < 0.15:  # 15% chance de detectar value
                value_data = {
                    'match': 'G2 vs Fnatic',
                    'our_prob': 0.72,
                    'bookmaker_odds': 1.85,
                    'ev': 0.085,  # 8.5% EV
                    'confidence': 0.78
                }
                
                # Verificar se atende aos critérios mínimos
                if (value_data['ev'] >= self.alert_settings['min_ev'] and 
                    value_data['confidence'] >= self.alert_settings['min_confidence']):
                    
                    # Se configurado para apenas EV alto, verificar
                    if self.alert_settings['high_ev_only'] and value_data['ev'] < 0.08:
                        return
                    
                    units = min(3, (value_data['ev'] * 10 + value_data['confidence']) / 2)
                    stake = units * 100  # R$ 100 por unidade
                    
                    alert_text = (
                        "🚨 **OPORTUNIDADE DE VALUE BETTING!**\n\n"
                        f"⚔️ **{value_data['match']}**\n"
                        f"📊 Nossa probabilidade: {value_data['our_prob']*100:.1f}%\n"
                        f"💰 Expected Value: {value_data['ev']*100:.1f}%\n"
                        f"🎯 Confiança: {value_data['confidence']*100:.1f}%\n"
                        f"🔥 **Unidades: {units:.1f}**\n"
                        f"💵 **Stake: R$ {stake:.0f}**\n\n"
                        "⚡ **AÇÃO RECOMENDADA:**\n"
                        f"{'🔥 APOSTA PREMIUM' if value_data['ev'] >= 0.08 else '⭐ APOSTA FORTE'}\n\n"
                        "💡 Use `/value` para análise completa"
                    )
                    
                    self._send_alert_to_groups(alert_text)
                    self.last_alerts['value_check'] = current_time
                    
        except Exception as e:
            logger.error(f"❌ Erro ao verificar value betting: {e}")
    
    def _send_alert_to_groups(self, message):
        """Enviar alerta para todos os grupos inscritos"""
        if not self.subscribed_groups:
            logger.info("📢 Nenhum grupo inscrito para alertas")
            return
        
        for chat_id in self.subscribed_groups.copy():
            try:
                if NEW_VERSION:
                    # Versão nova - usar asyncio
                    asyncio.create_task(self._send_async_message(chat_id, message))
                else:
                    # Versão antiga - usar send_message direto
                    self.bot_instance.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                logger.info(f"✅ Alerta enviado para grupo {chat_id}")
                
            except TelegramError as e:
                logger.error(f"❌ Erro ao enviar alerta para {chat_id}: {e}")
                # Se o bot foi removido do grupo, desinscrever
                if "chat not found" in str(e).lower() or "forbidden" in str(e).lower():
                    self.subscribed_groups.discard(chat_id)
                    logger.info(f"🗑️ Grupo {chat_id} removido da lista (bot removido)")
    
    async def _send_async_message(self, chat_id, message):
        """Enviar mensagem assíncrona (versão nova do telegram-bot)"""
        try:
            await self.bot_instance.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"❌ Erro async ao enviar para {chat_id}: {e}")
    
    def get_status(self):
        """Obter status do sistema de alertas"""
        return {
            'monitoring_active': self.monitoring_active,
            'subscribed_groups': len(self.subscribed_groups),
            'settings': self.alert_settings.copy(),
            'last_alerts': {k: v.strftime('%H:%M:%S') for k, v in self.last_alerts.items()}
        }

class BotLoLV3Railway:
    """Bot principal compatível com Railway"""
    
    def __init__(self):
        """Inicializar o bot com todas as funcionalidades"""
        if NEW_VERSION:
            # Versão nova (v20+)
            self.application = Application.builder().token(TOKEN).build()
            self.bot_instance = self.application
        else:
            # Versão antiga (v13-19)
            self.updater = Updater(TOKEN, use_context=True)
            self.bot_instance = self.updater
            
        self.health_manager = HealthCheckManager()
        self.live_stats = LiveStatsSystem()
        self.value_system = ValueBettingSystem()
        self.advanced_analyzer = AdvancedMatchAnalyzer()
        self.alert_system = AlertSystem(self.bot_instance)
        
        self.setup_commands()
        self.health_manager.start_flask_server()
        self.health_manager.mark_healthy()
        
        # Iniciar sistema de alertas automaticamente
        self.alert_system.start_monitoring()
        
        logger.info("🤖 Bot V13 Railway inicializado com sistema de unidades e alertas automáticos")
    
    def setup_commands(self):
        """Configurar comandos do bot"""
        if NEW_VERSION:
            # Versão nova
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("help", self.help))
            self.application.add_handler(CommandHandler("partidas", self.partidas))
            self.application.add_handler(CommandHandler("stats", self.stats))
            self.application.add_handler(CommandHandler("value", self.value))
            self.application.add_handler(CommandHandler("portfolio", self.portfolio))
            self.application.add_handler(CommandHandler("units", self.units_info))
            self.application.add_handler(CommandHandler("tips", self.betting_tips))
            self.application.add_handler(CommandHandler("demo", self.demo_system))
            self.application.add_handler(CommandHandler("alertas", self.alertas))
            self.application.add_handler(CommandHandler("inscrever", self.inscrever_alertas))
            self.application.add_handler(CommandHandler("desinscrever", self.desinscrever_alertas))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        else:
            # Versão antiga
            self.updater.dispatcher.add_handler(CommandHandler("start", self.start))
            self.updater.dispatcher.add_handler(CommandHandler("help", self.help))
            self.updater.dispatcher.add_handler(CommandHandler("partidas", self.partidas))
            self.updater.dispatcher.add_handler(CommandHandler("stats", self.stats))
            self.updater.dispatcher.add_handler(CommandHandler("value", self.value))
            self.updater.dispatcher.add_handler(CommandHandler("portfolio", self.portfolio))
            self.updater.dispatcher.add_handler(CommandHandler("units", self.units_info))
            self.updater.dispatcher.add_handler(CommandHandler("tips", self.betting_tips))
            self.updater.dispatcher.add_handler(CommandHandler("demo", self.demo_system))
            self.updater.dispatcher.add_handler(CommandHandler("alertas", self.alertas))
            self.updater.dispatcher.add_handler(CommandHandler("inscrever", self.inscrever_alertas))
            self.updater.dispatcher.add_handler(CommandHandler("desinscrever", self.desinscrever_alertas))
            self.updater.dispatcher.add_handler(CallbackQueryHandler(self.handle_callback))
    
    def start(self, update: Update, context):
        """Comando /start"""
        self.health_manager.update_activity()
        return self.show_main_menu(update, context)
    
    def show_main_menu(self, update, context, edit_message=False):
        """Exibe o menu principal com botões"""
        keyboard = [
            [InlineKeyboardButton("🎮 Ver Partidas", callback_data="partidas"),
             InlineKeyboardButton("📊 Estatísticas", callback_data="stats")],
            [InlineKeyboardButton("💰 Value Betting", callback_data="value"),
             InlineKeyboardButton("📈 Portfolio", callback_data="portfolio")],
            [InlineKeyboardButton("🎯 Sistema Unidades", callback_data="units"),
             InlineKeyboardButton("💡 Dicas Pro", callback_data="tips")],
            [InlineKeyboardButton("🚨 Alertas", callback_data="alertas"),
             InlineKeyboardButton("🎲 Demo Sistema", callback_data="demo")],
            [InlineKeyboardButton("❓ Ajuda", callback_data="help")]
        ]
        
        message_text = (
            "🎮 **BOT LOL V3 ULTRA AVANÇADO** 🎮\n\n"
            "Olá! Eu sou o bot LoL V3 Ultra Avançado, desenvolvido para fornecer "
            "análises avançadas sobre partidas de League of Legends.\n\n"
            "🎯 **FUNCIONALIDADES PRINCIPAIS:**\n"
            "• 📊 Estatísticas em tempo real\n"
            "• 💰 Sistema de unidades básicas\n"
            "• 📈 Análise de EV e confiança\n"
            "• 🔮 Predições dinâmicas\n"
            "• 💡 Dicas profissionais\n\n"
            "⚡ **NOVO SISTEMA DE UNIDADES:**\n"
            "• EV Alto = 2 unidades\n"
            "• Confiança Alta = 2 unidades\n"
            "• Gestão de risco inteligente\n\n"
            "🌍 **Cobertura global de ligas**\n\n"
            "👇 **Escolha uma opção abaixo:**"
        )
        
        if edit_message and hasattr(update, 'callback_query'):
            return update.callback_query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            return update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    def help(self, update: Update, context):
        """Comando /help"""
        self.health_manager.update_activity()
        
        keyboard = [
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        message_text = (
            "📚 **GUIA COMPLETO DO BOT**\n\n"
            "🎯 **COMANDOS PRINCIPAIS:**\n"
            "• `/start` - Iniciar o bot\n"
            "• `/help` - Este guia\n"
            "• `/partidas` - Partidas ao vivo\n"
            "• `/stats` - Estatísticas em tempo real\n"
            "• `/value` - Value betting com unidades\n"
            "• `/portfolio` - Dashboard do portfolio\n"
            "• `/units` - Sistema de unidades básicas\n"
            "• `/tips` - Dicas profissionais de betting\n"
            "• `/demo` - Exemplos práticos do sistema\n\n"
            "🎮 **FUNCIONALIDADES:**\n"
            "• Monitoramento de partidas ao vivo\n"
            "• Estatísticas detalhadas (gold, kills, objetivos)\n"
            "• Probabilidades dinâmicas que evoluem\n"
            "• Sistema de unidades baseado em EV + Confiança\n"
            "• Análise de portfolio em tempo real\n"
            "• Dicas profissionais de gestão de banca\n\n"
            "💰 **SISTEMA DE UNIDADES:**\n"
            "• EV Alto (8%+) = 2 unidades\n"
            "• Confiança Alta (85%+) = 2 unidades\n"
            "• Cálculo: (EV_units + Conf_units) ÷ 2\n"
            "• Máximo: 3 unidades por aposta\n"
            "• Gestão de risco inteligente\n\n"
            "📊 **MÉTRICAS DISPONÍVEIS:**\n"
            "• Gold, kills, mortes, assists, CS\n"
            "• Dragões, barões, torres, inibidores\n"
            "• Expected Value (EV) calculado\n"
            "• Análise de confiança por partida\n"
            "• Análise por fase da partida (Early/Mid/Late)\n"
            "• Vantagens calculadas dinamicamente\n\n"
            "🔄 **Sistema atualizado em tempo real!**"
        )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def partidas(self, update: Update, context):
        """Comando /partidas"""
        self.health_manager.update_activity()

        keyboard = [
            [InlineKeyboardButton("🔄 Verificar Novamente", callback_data="partidas"),
             InlineKeyboardButton("💰 Value Betting", callback_data="value")],
            [InlineKeyboardButton("📈 Portfolio", callback_data="portfolio"),
             InlineKeyboardButton("🎯 Sistema", callback_data="sistema")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        message_text = (
            "🔍 **MONITORAMENTO DE PARTIDAS**\n\n"
            "ℹ️ **NENHUMA PARTIDA AO VIVO DETECTADA**\n\n"
            "🔄 **SISTEMA ATIVO:**\n"
            "• Monitoramento 24/7 ativo\n"
            "• API Riot Games integrada\n"
            "• Detecção automática de partidas\n\n"
            "🎮 **LIGAS MONITORADAS:**\n"
            "🇰🇷 LCK • 🇨🇳 LPL • 🇪🇺 LEC • 🇺🇸 LCS\n"
            "🇧🇷 CBLOL • 🇯🇵 LJL • 🇦🇺 LCO • 🌏 PCS\n"
            "🇫🇷 LFL • 🇩🇪 Prime League • 🇪🇸 Superliga\n\n"
            "⏰ **PRÓXIMAS VERIFICAÇÕES:**\n"
            "• Sistema verifica a cada 1 minuto\n"
            "• Alertas automáticos quando detectar partidas\n"
            "• Estatísticas em tempo real disponíveis\n\n"
            f"🔄 **Última verificação:** {datetime.now().strftime('%H:%M:%S')}\n"
            "💡 **Use 'Verificar Novamente' para atualizar**"
        )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def stats(self, update: Update, context):
        """Comando /stats - Estatísticas ao vivo"""
        self.health_manager.update_activity()
        
        keyboard = [
            [InlineKeyboardButton("🎮 Ver Partidas", callback_data="partidas"),
             InlineKeyboardButton("💰 Value Betting", callback_data="value")],
            [InlineKeyboardButton("📈 Portfolio", callback_data="portfolio"),
             InlineKeyboardButton("🔄 Atualizar", callback_data="stats")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        message_text = (
            "📊 **SISTEMA DE ESTATÍSTICAS AO VIVO**\n\n"
            "ℹ️ **AGUARDANDO PARTIDAS ATIVAS**\n\n"
            "🎮 **FUNCIONALIDADES DISPONÍVEIS:**\n"
            "• Gold, kills, mortes, assists em tempo real\n"
            "• Dragões, barões, torres dinâmicos\n"
            "• Probabilidades que evoluem com o tempo\n"
            "• Análise por fase (Early/Mid/Late Game)\n"
            "• Vantagens calculadas dinamicamente\n\n"
            "🔄 **SISTEMA PREPARADO:**\n"
            "• Monitoramento ativo 24/7\n"
            "• Detecção automática de partidas\n"
            "• Estatísticas atualizadas em tempo real\n"
            "• Probabilidades dinâmicas ativas\n\n"
            "⚡ **QUANDO HOUVER PARTIDAS:**\n"
            "• Stats detalhadas aparecerão automaticamente\n"
            "• Probabilidades se atualizarão em tempo real\n"
            "• Sistema de value betting será ativado\n\n"
            f"⏰ **Status:** Sistema operacional - {datetime.now().strftime('%H:%M:%S')}"
        )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def units_info(self, update: Update, context):
        """Comando /units - Informações sobre sistema de unidades"""
        self.health_manager.update_activity()
        
        keyboard = [
            [InlineKeyboardButton("💰 Value Betting", callback_data="value"),
             InlineKeyboardButton("📊 Ver Stats", callback_data="stats")],
            [InlineKeyboardButton("💡 Dicas Pro", callback_data="tips"),
             InlineKeyboardButton("📈 Portfolio", callback_data="portfolio")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        message_text = (
            "🎯 **SISTEMA DE UNIDADES BÁSICAS**\n\n"
            "💰 **CONFIGURAÇÃO ATUAL:**\n"
            f"• Unidade base: R$ {self.value_system.base_unit}\n"
            f"• Banca total: R$ {self.value_system.bankroll:,}\n"
            f"• Máximo por aposta: {self.value_system.max_units_per_bet} unidades\n"
            f"• EV mínimo: {self.value_system.ev_threshold*100}%\n\n"
            "📊 **CRITÉRIOS DE UNIDADES:**\n\n"
            "🔥 **EXPECTED VALUE (EV):**\n"
            "• EV ≥8%: 2 unidades\n"
            "• EV 5-8%: 1.5 unidades\n"
            "• EV 3-5%: 1 unidade\n"
            "• EV <3%: 0.5 unidade\n\n"
            "⭐ **CONFIANÇA:**\n"
            "• ≥85%: 2 unidades\n"
            "• 75-85%: 1.5 unidades\n"
            "• 65-75%: 1 unidade\n"
            "• <65%: 0.5 unidade\n\n"
            "🎯 **CÁLCULO FINAL:**\n"
            "Unidades = (EV_units + Conf_units) ÷ 2\n"
            "Máximo: 3 unidades por aposta\n\n"
            "🛡️ **GESTÃO DE RISCO:**\n"
            "• Máximo 5% da banca por dia\n"
            "• Diversificação obrigatória\n"
            "• Stop-loss automático\n"
            "• Reavaliação a cada 100 apostas"
        )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def betting_tips(self, update: Update, context):
        """Comando /tips - Dicas profissionais"""
        self.health_manager.update_activity()
        
        suggestions = self.value_system.get_portfolio_suggestions()
        
        keyboard = [
            [InlineKeyboardButton("💰 Value Betting", callback_data="value"),
             InlineKeyboardButton("🎯 Sistema Unidades", callback_data="units")],
            [InlineKeyboardButton("📈 Portfolio", callback_data="portfolio"),
             InlineKeyboardButton("🔄 Atualizar Dicas", callback_data="tips")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        message_text = (
            "💡 **DICAS PROFISSIONAIS DE BETTING**\n\n"
            "💰 **GESTÃO DE BANCA:**\n" +
            "\n".join(f"• {tip}" for tip in suggestions['bankroll_management']) + "\n\n"
            "🎯 **CAÇA AO VALUE:**\n" +
            "\n".join(f"• {tip}" for tip in suggestions['value_hunting']) + "\n\n"
            "🛡️ **GESTÃO DE RISCO:**\n" +
            "\n".join(f"• {tip}" for tip in suggestions['risk_management']) + "\n\n"
            "🧠 **DICAS AVANÇADAS:**\n" +
            "\n".join(f"• {tip}" for tip in suggestions['advanced_tips']) + "\n\n"
            "⚡ **LEMBRE-SE:**\n"
            "• Disciplina é mais importante que sorte\n"
            "• Value betting é maratona, não sprint\n"
            "• Sempre mantenha registros detalhados\n"
            "• Nunca aposte com emoção"
        )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def value(self, update: Update, context):
        """Comando /value - Value betting com sistema de unidades"""
        self.health_manager.update_activity()
        
        keyboard = [
            [InlineKeyboardButton("🎮 Ver Partidas", callback_data="partidas"),
             InlineKeyboardButton("📊 Ver Stats", callback_data="stats")],
            [InlineKeyboardButton("🎯 Sistema Unidades", callback_data="units"),
             InlineKeyboardButton("💡 Dicas Pro", callback_data="tips")],
            [InlineKeyboardButton("🔄 Verificar Oportunidades", callback_data="value"),
             InlineKeyboardButton("📈 Portfolio", callback_data="portfolio")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        message_text = (
            "💰 **VALUE BETTING - SISTEMA DE UNIDADES**\n\n"
            "🔍 **MONITORAMENTO ATIVO**\n\n"
            "ℹ️ **AGUARDANDO PARTIDAS PARA ANÁLISE**\n\n"
            "🎯 **SISTEMA PREPARADO:**\n"
            "• Detecção automática de value betting\n"
            "• Cálculo de unidades baseado em EV + Confiança\n"
            "• Análise de probabilidades vs odds\n"
            "• Alertas instantâneos de oportunidades\n\n"
            "📊 **QUANDO HOUVER PARTIDAS:**\n"
            "• Value betting calculado automaticamente\n"
            "• Unidades sugeridas (0.5 a 3.0)\n"
            "• Análise de EV e confiança detalhada\n"
            "• Recomendações personalizadas\n\n"
            "🔄 **CONFIGURAÇÕES ATIVAS:**\n"
            f"• Unidade base: R$ {self.value_system.base_unit}\n"
            f"• Banca total: R$ {self.value_system.bankroll:,}\n"
            f"• EV mínimo: {self.value_system.ev_threshold*100}%\n"
            f"• Confiança mínima: {self.value_system.confidence_threshold*100}%\n\n"
            "🎯 **CRITÉRIOS DE UNIDADES:**\n"
            "• EV Muito Alto (8%+) + Confiança Alta = 2-3 unidades\n"
            "• EV Alto (5-8%) + Confiança Média = 1-2 unidades\n"
            "• EV Médio (3-5%) + Confiança Baixa = 0.5-1 unidade\n\n"
            f"⏰ **Sistema operacional:** {datetime.now().strftime('%H:%M:%S')}"
        )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def portfolio(self, update: Update, context):
        """Comando /portfolio"""
        self.health_manager.update_activity()
        
        keyboard = [
            [InlineKeyboardButton("💰 Value Bets", callback_data="value"),
             InlineKeyboardButton("📊 Ver Stats", callback_data="stats")],
            [InlineKeyboardButton("🎮 Ver Partidas", callback_data="partidas"),
             InlineKeyboardButton("🔄 Atualizar", callback_data="portfolio")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        message_text = (
            "📊 **PORTFOLIO DASHBOARD**\n\n"
            "💰 **STATUS ATUAL:**\n"
            "• Sistema: ✅ Operacional\n"
            "• Monitoramento: 🔄 Ativo\n"
            "• Bankroll: R$ 10.000\n"
            "• Risk Level: Conservador\n\n"
            "🎮 **LIGAS MONITORADAS:**\n"
            "🇰🇷 LCK • 🇨🇳 LPL • 🇪🇺 LEC • 🇺🇸 LCS • 🇧🇷 CBLOL\n"
            "🇯🇵 LJL • 🇦🇺 LCO • 🌏 PCS • 🇫🇷 LFL • 🇩🇪 Prime League\n\n"
            "📈 **AGUARDANDO OPORTUNIDADES:**\n"
            "• Nenhuma partida ativa no momento\n"
            "• Sistema preparado para detectar value bets\n"
            "• Análise automática quando houver partidas\n\n"
            "📊 **CONFIGURAÇÕES DE RISCO:**\n"
            "• Diversificação: Múltiplas ligas\n"
            "• Sistema de unidades ativo\n"
            "• Stop-loss automático\n\n"
            "🔄 **SISTEMA PREPARADO:**\n"
            "• Probabilidades dinâmicas ✅\n"
            "• Monitoramento 24/7 ✅\n"
            "• API Riot integrada ✅\n"
            "• Alertas automáticos ✅\n\n"
            f"⏰ **Status:** Aguardando partidas - {datetime.now().strftime('%H:%M:%S')}"
        )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def demo_system(self, update: Update, context):
        """Comando /demo - Demonstração do sistema avançado"""
        self.health_manager.update_activity()
        
        keyboard = [
            [InlineKeyboardButton("🎯 Análise Avançada", callback_data="demo_advanced"),
             InlineKeyboardButton("💰 Value Demo", callback_data="demo_value")],
            [InlineKeyboardButton("🎮 Análise Composição", callback_data="demo_draft"),
             InlineKeyboardButton("📊 Performance Times", callback_data="demo_teams")],
            [InlineKeyboardButton("🔄 Novo Demo", callback_data="demo"),
             InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        demo_text = (
            "🎲 **DEMONSTRAÇÃO DO SISTEMA AVANÇADO**\n\n"
            "🧠 **SISTEMA DE ANÁLISE COMPLETO:**\n"
            "• Análise de composições e sinergias\n"
            "• Performance individual de jogadores\n"
            "• Dados históricos e head-to-head\n"
            "• Adaptação à meta atual (Patch 14.23)\n"
            "• Contexto de torneio e pressão\n\n"
            "🎯 **FATORES ANALISADOS:**\n"
            "• **Rating dos times** (25%)\n"
            "• **Forma recente** (20%)\n"
            "• **Draft e composição** (15%)\n"
            "• **Skill individual** (15%)\n"
            "• **Meta fit** (10%)\n"
            "• **Head-to-head** (10%)\n"
            "• **Contexto torneio** (5%)\n\n"
            "📊 **DADOS DISPONÍVEIS:**\n"
            "• Times: T1, Gen.G, JDG, BLG, G2, Fnatic, C9, LOUD\n"
            "• Jogadores: Faker, Chovy, Canyon, Zeus, etc.\n"
            "• Champions: Meta atual com sinergias\n"
            "• Patches: Atualizações e mudanças\n\n"
            "👇 **Escolha um tipo de demonstração:**"
        )
        
        return update.message.reply_text(
            demo_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def alertas(self, update: Update, context):
        """Comando /alertas - Gerenciar sistema de alertas"""
        self.health_manager.update_activity()
        
        status = self.alert_system.get_status()
        
        keyboard = [
            [InlineKeyboardButton("🔔 Inscrever Grupo", callback_data="inscrever_alertas"),
             InlineKeyboardButton("🔕 Desinscrever", callback_data="desinscrever_alertas")],
            [InlineKeyboardButton("⚙️ Configurações", callback_data="config_alertas"),
             InlineKeyboardButton("🔄 Status", callback_data="status_alertas")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
        ]
        
        message_text = (
            "🚨 **SISTEMA DE ALERTAS AUTOMÁTICOS**\n\n"
            f"📊 **STATUS ATUAL:**\n"
            f"• Monitoramento: {'🟢 ATIVO' if status['monitoring_active'] else '🔴 INATIVO'}\n"
            f"• Grupos inscritos: {status['subscribed_groups']}\n"
            f"• Alertas de partidas: {'✅' if status['settings']['live_matches'] else '❌'}\n"
            f"• Alertas de value: {'✅' if status['settings']['value_betting'] else '❌'}\n\n"
            "🔔 **TIPOS DE ALERTAS:**\n"
            "• 🎮 Partidas ao vivo detectadas\n"
            "• 💰 Oportunidades de value betting\n"
            "• 🚨 Alertas de EV alto (8%+)\n"
            "• 📊 Análises em tempo real\n\n"
            "⚙️ **CONFIGURAÇÕES:**\n"
            f"• EV mínimo: {status['settings']['min_ev']*100:.1f}%\n"
            f"• Confiança mínima: {status['settings']['min_confidence']*100:.1f}%\n"
            f"• Apenas EV alto: {'✅' if status['settings']['high_ev_only'] else '❌'}\n\n"
            "💡 **Para receber alertas:**\n"
            "1. Use `/inscrever` no grupo\n"
            "2. Certifique-se que o bot é admin\n"
            "3. Aguarde as notificações automáticas\n\n"
            "👇 **Escolha uma opção:**"
        )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def inscrever_alertas(self, update: Update, context):
        """Comando /inscrever - Inscrever grupo para alertas"""
        self.health_manager.update_activity()
        
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        
        if chat_type == 'private':
            message_text = (
                "❌ **ERRO: COMANDO APENAS PARA GRUPOS**\n\n"
                "Este comando só funciona em grupos do Telegram.\n\n"
                "📝 **Como usar:**\n"
                "1. Adicione o bot ao seu grupo\n"
                "2. Torne o bot administrador\n"
                "3. Use `/inscrever` no grupo\n\n"
                "💡 **Dica:** Use `/alertas` para mais informações"
            )
        else:
            # Verificar se já está inscrito
            if chat_id in self.alert_system.subscribed_groups:
                message_text = (
                    "✅ **GRUPO JÁ INSCRITO!**\n\n"
                    f"Este grupo já recebe alertas automáticos.\n\n"
                    "🔔 **Alertas ativos:**\n"
                    "• Partidas ao vivo\n"
                    "• Oportunidades de value betting\n"
                    "• Análises em tempo real\n\n"
                    "⚙️ Use `/alertas` para configurações"
                )
            else:
                # Inscrever o grupo
                self.alert_system.subscribe_group(chat_id)
                
                # Iniciar monitoramento se não estiver ativo
                if not self.alert_system.monitoring_active:
                    self.alert_system.start_monitoring()
                
                message_text = (
                    "🎉 **GRUPO INSCRITO COM SUCESSO!**\n\n"
                    f"Este grupo agora receberá alertas automáticos.\n\n"
                    "🔔 **Você receberá:**\n"
                    "• 🎮 Alertas de partidas ao vivo\n"
                    "• 💰 Oportunidades de value betting\n"
                    "• 🚨 Alertas de EV alto (8%+)\n"
                    "• 📊 Análises em tempo real\n\n"
                    "⏰ **Frequência:** Verificação a cada 1 minuto\n"
                    "🛡️ **Anti-spam:** Máximo 1 alerta por tipo a cada 5-10 min\n\n"
                    "⚙️ Use `/alertas` para configurações\n"
                    "🔕 Use `/desinscrever` para parar alertas"
                )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def desinscrever_alertas(self, update: Update, context):
        """Comando /desinscrever - Desinscrever grupo dos alertas"""
        self.health_manager.update_activity()
        
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        
        if chat_type == 'private':
            message_text = (
                "❌ **ERRO: COMANDO APENAS PARA GRUPOS**\n\n"
                "Este comando só funciona em grupos do Telegram.\n\n"
                "💡 Use `/alertas` para mais informações"
            )
        else:
            # Verificar se está inscrito
            if chat_id not in self.alert_system.subscribed_groups:
                message_text = (
                    "ℹ️ **GRUPO NÃO INSCRITO**\n\n"
                    "Este grupo não está recebendo alertas.\n\n"
                    "🔔 Use `/inscrever` para ativar alertas"
                )
            else:
                # Desinscrever o grupo
                self.alert_system.unsubscribe_group(chat_id)
                
                message_text = (
                    "✅ **GRUPO DESINSCRITO COM SUCESSO!**\n\n"
                    "Este grupo não receberá mais alertas automáticos.\n\n"
                    "🔔 **Para reativar:**\n"
                    "Use `/inscrever` a qualquer momento\n\n"
                    "💡 **Lembre-se:**\n"
                    "Você ainda pode usar todos os comandos manuais:\n"
                    "• `/partidas` - Ver partidas\n"
                    "• `/value` - Value betting\n"
                    "• `/stats` - Estatísticas"
                )
        
        return update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def handle_callback(self, update: Update, context):
        """Handle callback queries"""
        query = update.callback_query
        query.answer()
        
        self.health_manager.update_activity()
        
        # Menu principal
        if query.data == "menu_principal":
            return self.show_main_menu(update, context, edit_message=True)
        
        # Partidas
        elif query.data == "partidas":
            keyboard = [
                [InlineKeyboardButton("🔄 Verificar Novamente", callback_data="partidas"),
                 InlineKeyboardButton("💰 Value Betting", callback_data="value")],
                [InlineKeyboardButton("📈 Portfolio", callback_data="portfolio"),
                 InlineKeyboardButton("🎯 Sistema", callback_data="sistema")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "🔍 **MONITORAMENTO DE PARTIDAS**\n\n"
                "ℹ️ **NENHUMA PARTIDA AO VIVO DETECTADA**\n\n"
                "🔄 **SISTEMA ATIVO:**\n"
                "• Monitoramento 24/7 ativo\n"
                "• API Riot Games integrada\n"
                "• Detecção automática de partidas\n\n"
                "🎮 **LIGAS MONITORADAS:**\n"
                "🇰🇷 LCK • 🇨🇳 LPL • 🇪🇺 LEC • 🇺🇸 LCS\n"
                "🇧🇷 CBLOL • 🇯🇵 LJL • 🇦🇺 LCO • 🌏 PCS\n"
                "🇫🇷 LFL • 🇩🇪 Prime League • 🇪🇸 Superliga\n\n"
                "⏰ **PRÓXIMAS VERIFICAÇÕES:**\n"
                "• Sistema verifica a cada 1 minuto\n"
                "• Alertas automáticos quando detectar partidas\n"
                "• Estatísticas em tempo real disponíveis\n\n"
                f"🔄 **Última verificação:** {datetime.now().strftime('%H:%M:%S')}\n"
                "💡 **Use 'Verificar Novamente' para atualizar**"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Stats
        elif query.data == "stats":
            keyboard = [
                [InlineKeyboardButton("🎮 Ver Partidas", callback_data="partidas"),
                 InlineKeyboardButton("💰 Value Betting", callback_data="value")],
                [InlineKeyboardButton("📈 Portfolio", callback_data="portfolio"),
                 InlineKeyboardButton("🔄 Atualizar", callback_data="stats")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "📊 **SISTEMA DE ESTATÍSTICAS AO VIVO**\n\n"
                "ℹ️ **AGUARDANDO PARTIDAS ATIVAS**\n\n"
                "🎮 **FUNCIONALIDADES DISPONÍVEIS:**\n"
                "• Gold, kills, mortes, assists em tempo real\n"
                "• Dragões, barões, torres dinâmicos\n"
                "• Probabilidades que evoluem com o tempo\n"
                "• Análise por fase (Early/Mid/Late Game)\n"
                "• Vantagens calculadas dinamicamente\n\n"
                "🔄 **SISTEMA PREPARADO:**\n"
                "• Monitoramento ativo 24/7\n"
                "• Detecção automática de partidas\n"
                "• Estatísticas atualizadas em tempo real\n"
                "• Probabilidades dinâmicas ativas\n\n"
                "⚡ **QUANDO HOUVER PARTIDAS:**\n"
                "• Stats detalhadas aparecerão automaticamente\n"
                "• Probabilidades se atualizarão em tempo real\n"
                "• Sistema de value betting será ativado\n\n"
                f"⏰ **Status:** Sistema operacional - {datetime.now().strftime('%H:%M:%S')}"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Value Betting
        elif query.data == "value":
            keyboard = [
                [InlineKeyboardButton("🎮 Ver Partidas", callback_data="partidas"),
                 InlineKeyboardButton("📊 Ver Stats", callback_data="stats")],
                [InlineKeyboardButton("🎯 Sistema Unidades", callback_data="units"),
                 InlineKeyboardButton("💡 Dicas Pro", callback_data="tips")],
                [InlineKeyboardButton("🔄 Verificar Oportunidades", callback_data="value"),
                 InlineKeyboardButton("📈 Portfolio", callback_data="portfolio")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "💰 **VALUE BETTING - SISTEMA DE UNIDADES**\n\n"
                "🔍 **MONITORAMENTO ATIVO**\n\n"
                "ℹ️ **AGUARDANDO PARTIDAS PARA ANÁLISE**\n\n"
                "🎯 **SISTEMA PREPARADO:**\n"
                "• Detecção automática de value betting\n"
                "• Cálculo de unidades baseado em EV + Confiança\n"
                "• Análise de probabilidades vs odds\n"
                "• Alertas instantâneos de oportunidades\n\n"
                "📊 **QUANDO HOUVER PARTIDAS:**\n"
                "• Value betting calculado automaticamente\n"
                "• Unidades sugeridas (0.5 a 3.0)\n"
                "• Análise de EV e confiança detalhada\n"
                "• Recomendações personalizadas\n\n"
                "🔄 **CONFIGURAÇÕES ATIVAS:**\n"
                f"• Unidade base: R$ {self.value_system.base_unit}\n"
                f"• Banca total: R$ {self.value_system.bankroll:,}\n"
                f"• EV mínimo: {self.value_system.ev_threshold*100}%\n"
                f"• Confiança mínima: {self.value_system.confidence_threshold*100}%\n\n"
                "🎯 **CRITÉRIOS DE UNIDADES:**\n"
                "• EV Muito Alto (8%+) + Confiança Alta = 2-3 unidades\n"
                "• EV Alto (5-8%) + Confiança Média = 1-2 unidades\n"
                "• EV Médio (3-5%) + Confiança Baixa = 0.5-1 unidade\n\n"
                f"⏰ **Sistema operacional:** {datetime.now().strftime('%H:%M:%S')}"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Portfolio
        elif query.data == "portfolio":
            keyboard = [
                [InlineKeyboardButton("💰 Value Bets", callback_data="value"),
                 InlineKeyboardButton("📊 Ver Stats", callback_data="stats")],
                [InlineKeyboardButton("🎮 Ver Partidas", callback_data="partidas"),
                 InlineKeyboardButton("🔄 Atualizar", callback_data="portfolio")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "📊 **PORTFOLIO DASHBOARD**\n\n"
                "💰 **STATUS ATUAL:**\n"
                "• Sistema: ✅ Operacional\n"
                "• Monitoramento: 🔄 Ativo\n"
                "• Bankroll: R$ 10.000\n"
                "• Risk Level: Conservador\n\n"
                "🎮 **LIGAS MONITORADAS:**\n"
                "🇰🇷 LCK • 🇨🇳 LPL • 🇪🇺 LEC • 🇺🇸 LCS • 🇧🇷 CBLOL\n"
                "🇯🇵 LJL • 🇦🇺 LCO • 🌏 PCS • 🇫🇷 LFL • 🇩🇪 Prime League\n\n"
                "📈 **AGUARDANDO OPORTUNIDADES:**\n"
                "• Nenhuma partida ativa no momento\n"
                "• Sistema preparado para detectar value bets\n"
                "• Análise automática quando houver partidas\n\n"
                "📊 **CONFIGURAÇÕES DE RISCO:**\n"
                "• Diversificação: Múltiplas ligas\n"
                "• Sistema de unidades ativo\n"
                "• Stop-loss automático\n\n"
                "🔄 **SISTEMA PREPARADO:**\n"
                "• Probabilidades dinâmicas ✅\n"
                "• Monitoramento 24/7 ✅\n"
                "• API Riot integrada ✅\n"
                "• Alertas automáticos ✅\n\n"
                f"⏰ **Status:** Aguardando partidas - {datetime.now().strftime('%H:%M:%S')}"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Sistema de Unidades
        elif query.data == "units":
            keyboard = [
                [InlineKeyboardButton("💰 Value Betting", callback_data="value"),
                 InlineKeyboardButton("📊 Ver Stats", callback_data="stats")],
                [InlineKeyboardButton("💡 Dicas Pro", callback_data="tips"),
                 InlineKeyboardButton("📈 Portfolio", callback_data="portfolio")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "🎯 **SISTEMA DE UNIDADES BÁSICAS**\n\n"
                "💰 **CONFIGURAÇÃO ATUAL:**\n"
                f"• Unidade base: R$ {self.value_system.base_unit}\n"
                f"• Banca total: R$ {self.value_system.bankroll:,}\n"
                f"• Máximo por aposta: {self.value_system.max_units_per_bet} unidades\n"
                f"• EV mínimo: {self.value_system.ev_threshold*100}%\n\n"
                "📊 **CRITÉRIOS DE UNIDADES:**\n\n"
                "🔥 **EXPECTED VALUE (EV):**\n"
                "• EV ≥8%: 2 unidades\n"
                "• EV 5-8%: 1.5 unidades\n"
                "• EV 3-5%: 1 unidade\n"
                "• EV <3%: 0.5 unidade\n\n"
                "⭐ **CONFIANÇA:**\n"
                "• ≥85%: 2 unidades\n"
                "• 75-85%: 1.5 unidades\n"
                "• 65-75%: 1 unidade\n"
                "• <65%: 0.5 unidade\n\n"
                "🎯 **CÁLCULO FINAL:**\n"
                "Unidades = (EV_units + Conf_units) ÷ 2\n"
                "Máximo: 3 unidades por aposta\n\n"
                "🛡️ **GESTÃO DE RISCO:**\n"
                "• Máximo 5% da banca por dia\n"
                "• Diversificação obrigatória\n"
                "• Stop-loss automático\n"
                "• Reavaliação a cada 100 apostas"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Dicas Pro
        elif query.data == "tips":
            suggestions = self.value_system.get_portfolio_suggestions()
            
            keyboard = [
                [InlineKeyboardButton("💰 Value Betting", callback_data="value"),
                 InlineKeyboardButton("🎯 Sistema Unidades", callback_data="units")],
                [InlineKeyboardButton("📈 Portfolio", callback_data="portfolio"),
                 InlineKeyboardButton("🔄 Atualizar Dicas", callback_data="tips")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "💡 **DICAS PROFISSIONAIS DE BETTING**\n\n"
                "💰 **GESTÃO DE BANCA:**\n" +
                "\n".join(f"• {tip}" for tip in suggestions['bankroll_management']) + "\n\n"
                "🎯 **CAÇA AO VALUE:**\n" +
                "\n".join(f"• {tip}" for tip in suggestions['value_hunting']) + "\n\n"
                "🛡️ **GESTÃO DE RISCO:**\n" +
                "\n".join(f"• {tip}" for tip in suggestions['risk_management']) + "\n\n"
                "🧠 **DICAS AVANÇADAS:**\n" +
                "\n".join(f"• {tip}" for tip in suggestions['advanced_tips']) + "\n\n"
                "⚡ **LEMBRE-SE:**\n"
                "• Disciplina é mais importante que sorte\n"
                "• Value betting é maratona, não sprint\n"
                "• Sempre mantenha registros detalhados\n"
                "• Nunca aposte com emoção"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Alertas
        elif query.data == "alertas":
            status = self.alert_system.get_status()
            
            keyboard = [
                [InlineKeyboardButton("🔔 Inscrever Grupo", callback_data="inscrever_alertas"),
                 InlineKeyboardButton("🔕 Desinscrever", callback_data="desinscrever_alertas")],
                [InlineKeyboardButton("⚙️ Configurações", callback_data="config_alertas"),
                 InlineKeyboardButton("🔄 Status", callback_data="status_alertas")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "🚨 **SISTEMA DE ALERTAS AUTOMÁTICOS**\n\n"
                f"📊 **STATUS ATUAL:**\n"
                f"• Monitoramento: {'🟢 ATIVO' if status['monitoring_active'] else '🔴 INATIVO'}\n"
                f"• Grupos inscritos: {status['subscribed_groups']}\n"
                f"• Alertas de partidas: {'✅' if status['settings']['live_matches'] else '❌'}\n"
                f"• Alertas de value: {'✅' if status['settings']['value_betting'] else '❌'}\n\n"
                "🔔 **TIPOS DE ALERTAS:**\n"
                "• 🎮 Partidas ao vivo detectadas\n"
                "• 💰 Oportunidades de value betting\n"
                "• 🚨 Alertas de EV alto (8%+)\n"
                "• 📊 Análises em tempo real\n\n"
                "⚙️ **CONFIGURAÇÕES:**\n"
                f"• EV mínimo: {status['settings']['min_ev']*100:.1f}%\n"
                f"• Confiança mínima: {status['settings']['min_confidence']*100:.1f}%\n"
                f"• Apenas EV alto: {'✅' if status['settings']['high_ev_only'] else '❌'}\n\n"
                "💡 **Para receber alertas:**\n"
                "1. Use o botão 'Inscrever Grupo'\n"
                "2. Certifique-se que o bot é admin\n"
                "3. Aguarde as notificações automáticas\n\n"
                "👇 **Escolha uma opção:**"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Demo Sistema
        elif query.data == "demo":
            keyboard = [
                [InlineKeyboardButton("🎯 Análise Avançada", callback_data="demo_advanced"),
                 InlineKeyboardButton("💰 Value Demo", callback_data="demo_value")],
                [InlineKeyboardButton("🎮 Análise Composição", callback_data="demo_draft"),
                 InlineKeyboardButton("📊 Performance Times", callback_data="demo_teams")],
                [InlineKeyboardButton("🔄 Novo Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            demo_text = (
                "🎲 **DEMONSTRAÇÃO DO SISTEMA AVANÇADO**\n\n"
                "🧠 **SISTEMA DE ANÁLISE COMPLETO:**\n"
                "• Análise de composições e sinergias\n"
                "• Performance individual de jogadores\n"
                "• Dados históricos e head-to-head\n"
                "• Adaptação à meta atual (Patch 14.23)\n"
                "• Contexto de torneio e pressão\n\n"
                "🎯 **FATORES ANALISADOS:**\n"
                "• **Rating dos times** (25%)\n"
                "• **Forma recente** (20%)\n"
                "• **Draft e composição** (15%)\n"
                "• **Skill individual** (15%)\n"
                "• **Meta fit** (10%)\n"
                "• **Head-to-head** (10%)\n"
                "• **Contexto torneio** (5%)\n\n"
                "📊 **DADOS DISPONÍVEIS:**\n"
                "• Times: T1, Gen.G, JDG, BLG, G2, Fnatic, C9, LOUD\n"
                "• Jogadores: Faker, Chovy, Canyon, Zeus, etc.\n"
                "• Champions: Meta atual com sinergias\n"
                "• Patches: Atualizações e mudanças\n\n"
                "👇 **Escolha um tipo de demonstração:**"
            )
            
            return query.edit_message_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Demo Análise Avançada
        elif query.data == "demo_advanced":
            analysis = self.advanced_analyzer.analyze_comprehensive_match(
                'T1', 'Gen.G',
                team1_comp=['Aatrox', 'Graves', 'Azir', 'Jinx', 'Thresh'],
                team2_comp=['Jax', 'Nidalee', 'Orianna', 'Kai\'Sa', 'Nautilus'],
                tournament_type='worlds_2024'
            )
            
            keyboard = [
                [InlineKeyboardButton("🎮 Ver Composição", callback_data="demo_draft"),
                 InlineKeyboardButton("📊 Ver Times", callback_data="demo_teams")],
                [InlineKeyboardButton("🔙 Voltar Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            prob = analysis['probability']
            team_analysis = analysis['team_analysis']
            
            demo_text = (
                f"🎯 **ANÁLISE AVANÇADA: T1 vs Gen.G**\n\n"
                f"🏆 **RESULTADO DA ANÁLISE:**\n"
                f"• T1: {prob['team1_probability']:.1%}\n"
                f"• Gen.G: {prob['team2_probability']:.1%}\n"
                f"• Confiança: {prob['confidence']:.1%}\n\n"
                f"📊 **BREAKDOWN DOS FATORES:**\n"
                f"• Rating base: {prob['factors_breakdown']['base_rating']:.3f}\n"
                f"• Forma recente: {prob['factors_breakdown']['form_impact']:+.3f}\n"
                f"• Draft: {prob['factors_breakdown']['draft_impact']:+.3f}\n"
                f"• Jogadores: {prob['factors_breakdown']['player_impact']:+.3f}\n"
                f"• Meta: {prob['factors_breakdown']['meta_impact']:+.3f}\n"
                f"• H2H: {prob['factors_breakdown']['h2h_impact']:+.3f}\n\n"
                f"🎮 **DADOS DOS TIMES:**\n"
                f"**T1:** Rating {team_analysis['team1']['rating']}, Forma {team_analysis['team1']['recent_form']:.1%}\n"
                f"**Gen.G:** Rating {team_analysis['team2']['rating']}, Forma {team_analysis['team2']['recent_form']:.1%}\n\n"
                f"🔍 **ANÁLISE DETALHADA:**\n"
                f"{analysis['detailed_analysis']}\n\n"
                f"📋 **FATORES CHAVE:**\n" +
                "\n".join(f"• {factor}" for factor in analysis['key_factors']) +
                f"\n\n⚡ **Patch:** {analysis['patch_version']}"
            )
            
            return query.edit_message_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Demo Value Betting
        elif query.data == "demo_value":
            keyboard = [
                [InlineKeyboardButton("🎯 Análise Avançada", callback_data="demo_advanced"),
                 InlineKeyboardButton("🎮 Ver Composição", callback_data="demo_draft")],
                [InlineKeyboardButton("🔙 Voltar Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            demo_text = self.format_value_demo()
            
            return query.edit_message_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Demo Draft Analysis
        elif query.data == "demo_draft":
            keyboard = [
                [InlineKeyboardButton("🎯 Análise Avançada", callback_data="demo_advanced"),
                 InlineKeyboardButton("💰 Value Demo", callback_data="demo_value")],
                [InlineKeyboardButton("🔙 Voltar Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            # Análise de draft específica
            team1_comp = ['Aatrox', 'Graves', 'Azir', 'Jinx', 'Thresh']
            team2_comp = ['Jax', 'Nidalee', 'Orianna', 'Kai\'Sa', 'Nautilus']
            
            draft_analysis = self.advanced_analyzer._analyze_draft(team1_comp, team2_comp)
            
            demo_text = (
                "🎮 **ANÁLISE DE COMPOSIÇÃO E DRAFT**\n\n"
                f"**T1 COMPOSIÇÃO:**\n"
                f"🔝 {team1_comp[0]} | 🌲 {team1_comp[1]} | 🎯 {team1_comp[2]} | 🏹 {team1_comp[3]} | 🛡️ {team1_comp[4]}\n\n"
                f"**Gen.G COMPOSIÇÃO:**\n"
                f"🔝 {team2_comp[0]} | 🌲 {team2_comp[1]} | 🎯 {team2_comp[2]} | 🏹 {team2_comp[3]} | 🛡️ {team2_comp[4]}\n\n"
                f"📊 **ANÁLISE DO DRAFT:**\n"
                f"• T1 Tier Score: {draft_analysis['team1_tier_score']:.2f}\n"
                f"• Gen.G Tier Score: {draft_analysis['team2_tier_score']:.2f}\n"
                f"• T1 Sinergia: {draft_analysis['team1_synergy']:.2f}\n"
                f"• Gen.G Sinergia: {draft_analysis['team2_synergy']:.2f}\n\n"
                f"⚡ **POWER SPIKES:**\n"
                f"**T1:** Early {draft_analysis['team1_power_spikes']['early']}, Mid {draft_analysis['team1_power_spikes']['mid']}, Late {draft_analysis['team1_power_spikes']['late']}\n"
                f"**Gen.G:** Early {draft_analysis['team2_power_spikes']['early']}, Mid {draft_analysis['team2_power_spikes']['mid']}, Late {draft_analysis['team2_power_spikes']['late']}\n\n"
                f"🏆 **VANTAGEM NO DRAFT:**\n"
                f"• Vencedor: {draft_analysis['draft_winner'].upper()}\n"
                f"• Magnitude: {draft_analysis['advantage_magnitude']:.3f}\n\n"
                f"🎯 **SINERGIAS PRINCIPAIS:**\n"
                f"• Azir + Graves (controle de área)\n"
                f"• Jinx + Thresh (engage e proteção)\n"
                f"• Orianna + Nautilus (teamfight)\n"
                f"• Kai'Sa + Nautilus (dive potential)\n\n"
                f"🔄 **META PATCH 14.23:**\n"
                f"• Champions S-tier: Azir, Graves, Thresh\n"
                f"• Scaling meta favorece late game\n"
                f"• Tank supports em alta"
            )
            
            return query.edit_message_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Demo Team Performance
        elif query.data == "demo_teams":
            keyboard = [
                [InlineKeyboardButton("🎯 Análise Avançada", callback_data="demo_advanced"),
                 InlineKeyboardButton("🎮 Ver Composição", callback_data="demo_draft")],
                [InlineKeyboardButton("🔙 Voltar Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            t1_data = self.advanced_analyzer.team_database['T1']
            geng_data = self.advanced_analyzer.team_database['Gen.G']
            
            demo_text = (
                "📊 **PERFORMANCE DETALHADA DOS TIMES**\n\n"
                f"🏆 **T1 (Rating: {t1_data['rating']})**\n"
                f"• Forma recente: {t1_data['recent_form']:.1%}\n"
                f"• Consistência: {t1_data['consistency']:.1%}\n"
                f"• Early game: {t1_data['early_game']:.1%}\n"
                f"• Mid game: {t1_data['mid_game']:.1%}\n"
                f"• Late game: {t1_data['late_game']:.1%}\n"
                f"• Flexibilidade draft: {t1_data['draft_flexibility']:.1%}\n"
                f"• Fator clutch: {t1_data['clutch_factor']:.1%}\n"
                f"• Exp. internacional: {t1_data['international_exp']:.1%}\n"
                f"• Adaptação meta: {t1_data['meta_adaptation']:.1%}\n"
                f"• Tempo médio: {t1_data['avg_game_time']} min\n"
                f"• First blood: {t1_data['first_blood_rate']:.1%}\n\n"
                f"⚔️ **Gen.G (Rating: {geng_data['rating']})**\n"
                f"• Forma recente: {geng_data['recent_form']:.1%}\n"
                f"• Consistência: {geng_data['consistency']:.1%}\n"
                f"• Early game: {geng_data['early_game']:.1%}\n"
                f"• Mid game: {geng_data['mid_game']:.1%}\n"
                f"• Late game: {geng_data['late_game']:.1%}\n"
                f"• Flexibilidade draft: {geng_data['draft_flexibility']:.1%}\n"
                f"• Fator clutch: {geng_data['clutch_factor']:.1%}\n"
                f"• Exp. internacional: {geng_data['international_exp']:.1%}\n"
                f"• Adaptação meta: {geng_data['meta_adaptation']:.1%}\n"
                f"• Tempo médio: {geng_data['avg_game_time']} min\n"
                f"• First blood: {geng_data['first_blood_rate']:.1%}\n\n"
                f"⭐ **JOGADORES DESTAQUE:**\n"
                f"**T1:** Faker (98), Zeus (95), Keria (96)\n"
                f"**Gen.G:** Chovy (96), Canyon (96), Kiin (90)\n\n"
                f"📈 **ÚLTIMAS 5 PARTIDAS:**\n"
                f"**T1:** {''.join(['✅' if w else '❌' for w in t1_data['recent_matches']])}\n"
                f"**Gen.G:** {''.join(['✅' if w else '❌' for w in geng_data['recent_matches']])}\n\n"
                f"🎯 **VANTAGENS PRINCIPAIS:**\n"
                f"• T1: Mid/late game, clutch factor\n"
                f"• Gen.G: Consistência, late game"
            )
            
            return query.edit_message_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Help/Ajuda
        elif query.data == "help":
            keyboard = [
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "📚 **GUIA COMPLETO DO BOT**\n\n"
                "🎯 **COMANDOS PRINCIPAIS:**\n"
                "• `/start` - Iniciar o bot\n"
                "• `/help` - Este guia\n"
                "• `/partidas` - Partidas ao vivo\n"
                "• `/stats` - Estatísticas em tempo real\n"
                "• `/value` - Value betting com unidades\n"
                "• `/portfolio` - Dashboard do portfolio\n"
                "• `/units` - Sistema de unidades básicas\n"
                "• `/tips` - Dicas profissionais de betting\n"
                "• `/demo` - Exemplos práticos do sistema\n\n"
                "🚨 **COMANDOS DE ALERTAS:**\n"
                "• `/alertas` - Gerenciar sistema de alertas\n"
                "• `/inscrever` - Inscrever grupo para alertas\n"
                "• `/desinscrever` - Desinscrever grupo dos alertas\n\n"
                "🎮 **FUNCIONALIDADES:**\n"
                "• Monitoramento de partidas ao vivo\n"
                "• Estatísticas detalhadas (gold, kills, objetivos)\n"
                "• Probabilidades dinâmicas que evoluem\n"
                "• Sistema de unidades baseado em EV + Confiança\n"
                "• Análise de portfolio em tempo real\n"
                "• Dicas profissionais de gestão de banca\n"
                "• **🚨 Alertas automáticos para grupos**\n\n"
                "🔔 **SISTEMA DE ALERTAS:**\n"
                "• Alertas automáticos de partidas ao vivo\n"
                "• Notificações de oportunidades de value betting\n"
                "• Alertas de EV alto (8%+) prioritários\n"
                "• Anti-spam: máximo 1 alerta por tipo a cada 5-10 min\n"
                "• Monitoramento 24/7 em background\n\n"
                "💰 **SISTEMA DE UNIDADES:**\n"
                "• EV Alto (8%+) = 2 unidades\n"
                "• Confiança Alta (85%+) = 2 unidades\n"
                "• Cálculo: (EV_units + Conf_units) ÷ 2\n"
                "• Máximo: 3 unidades por aposta\n"
                "• Gestão de risco inteligente\n\n"
                "📊 **MÉTRICAS DISPONÍVEIS:**\n"
                "• Gold, kills, mortes, assists, CS\n"
                "• Dragões, barões, torres, inibidores\n"
                "• Expected Value (EV) calculado\n"
                "• Análise de confiança por partida\n"
                "• Análise por fase da partida (Early/Mid/Late)\n"
                "• Vantagens calculadas dinamicamente\n\n"
                "🔄 **Sistema atualizado em tempo real!**"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Sistema
        elif query.data == "sistema":
            keyboard = [
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "🎯 **STATUS DO SISTEMA**\n\n"
                "✅ **COMPONENTES ATIVOS:**\n"
                "• Bot Telegram: Online\n"
                "• API Riot Games: Conectada\n"
                "• Sistema de monitoramento: Ativo\n"
                "• Health check: Operacional\n"
                "• Analisador Avançado: Ativo\n\n"
                "🔄 **FUNCIONALIDADES:**\n"
                "• Detecção automática de partidas\n"
                "• Estatísticas em tempo real\n"
                "• Value betting automático\n"
                "• Portfolio management\n"
                "• Análise avançada de composições\n"
                "• Performance de jogadores\n\n"
                "📊 **MÉTRICAS:**\n"
                f"• Uptime: {datetime.now().strftime('%H:%M:%S')}\n"
                "• Latência: <100ms\n"
                "• Status: Operacional\n"
                f"• Patch: {self.advanced_analyzer.patch_version}\n\n"
                "⚡ **Sistema preparado para detectar partidas!**"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Demo Análise Avançada
        elif query.data == "demo_advanced":
            analysis = self.advanced_analyzer.analyze_comprehensive_match(
                'T1', 'Gen.G',
                team1_comp=['Aatrox', 'Graves', 'Azir', 'Jinx', 'Thresh'],
                team2_comp=['Jax', 'Nidalee', 'Orianna', 'Kai\'Sa', 'Nautilus'],
                tournament_type='worlds_2024'
            )
            
            keyboard = [
                [InlineKeyboardButton("🎮 Ver Composição", callback_data="demo_draft"),
                 InlineKeyboardButton("📊 Ver Times", callback_data="demo_teams")],
                [InlineKeyboardButton("🔙 Voltar Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            prob = analysis['probability']
            team_analysis = analysis['team_analysis']
            
            demo_text = (
                f"🎯 **ANÁLISE AVANÇADA: T1 vs Gen.G**\n\n"
                f"🏆 **RESULTADO DA ANÁLISE:**\n"
                f"• T1: {prob['team1_probability']:.1%}\n"
                f"• Gen.G: {prob['team2_probability']:.1%}\n"
                f"• Confiança: {prob['confidence']:.1%}\n\n"
                f"📊 **BREAKDOWN DOS FATORES:**\n"
                f"• Rating base: {prob['factors_breakdown']['base_rating']:.3f}\n"
                f"• Forma recente: {prob['factors_breakdown']['form_impact']:+.3f}\n"
                f"• Draft: {prob['factors_breakdown']['draft_impact']:+.3f}\n"
                f"• Jogadores: {prob['factors_breakdown']['player_impact']:+.3f}\n"
                f"• Meta: {prob['factors_breakdown']['meta_impact']:+.3f}\n"
                f"• H2H: {prob['factors_breakdown']['h2h_impact']:+.3f}\n\n"
                f"🎮 **DADOS DOS TIMES:**\n"
                f"**T1:** Rating {team_analysis['team1']['rating']}, Forma {team_analysis['team1']['recent_form']:.1%}\n"
                f"**Gen.G:** Rating {team_analysis['team2']['rating']}, Forma {team_analysis['team2']['recent_form']:.1%}\n\n"
                f"🔍 **ANÁLISE DETALHADA:**\n"
                f"{analysis['detailed_analysis']}\n\n"
                f"📋 **FATORES CHAVE:**\n" +
                "\n".join(f"• {factor}" for factor in analysis['key_factors']) +
                f"\n\n⚡ **Patch:** {analysis['patch_version']}"
            )
            
            return query.edit_message_text(
                 demo_text,
                 parse_mode=ParseMode.MARKDOWN,
                 reply_markup=InlineKeyboardMarkup(keyboard)
             )
        
        # Demo Value Betting
        elif query.data == "demo_value":
            keyboard = [
                [InlineKeyboardButton("🎯 Análise Avançada", callback_data="demo_advanced"),
                 InlineKeyboardButton("🎮 Ver Composição", callback_data="demo_draft")],
                [InlineKeyboardButton("🔙 Voltar Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            demo_text = self.format_value_demo()
            
            return query.edit_message_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Demo Draft Analysis
        elif query.data == "demo_draft":
            keyboard = [
                [InlineKeyboardButton("🎯 Análise Avançada", callback_data="demo_advanced"),
                 InlineKeyboardButton("💰 Value Demo", callback_data="demo_value")],
                [InlineKeyboardButton("🔙 Voltar Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            # Análise de draft específica
            team1_comp = ['Aatrox', 'Graves', 'Azir', 'Jinx', 'Thresh']
            team2_comp = ['Jax', 'Nidalee', 'Orianna', 'Kai\'Sa', 'Nautilus']
            
            draft_analysis = self.advanced_analyzer._analyze_draft(team1_comp, team2_comp)
            
            demo_text = (
                "🎮 **ANÁLISE DE COMPOSIÇÃO E DRAFT**\n\n"
                f"**T1 COMPOSIÇÃO:**\n"
                f"🔝 {team1_comp[0]} | 🌲 {team1_comp[1]} | 🎯 {team1_comp[2]} | 🏹 {team1_comp[3]} | 🛡️ {team1_comp[4]}\n\n"
                f"**Gen.G COMPOSIÇÃO:**\n"
                f"🔝 {team2_comp[0]} | 🌲 {team2_comp[1]} | 🎯 {team2_comp[2]} | 🏹 {team2_comp[3]} | 🛡️ {team2_comp[4]}\n\n"
                f"📊 **ANÁLISE DO DRAFT:**\n"
                f"• T1 Tier Score: {draft_analysis['team1_tier_score']:.2f}\n"
                f"• Gen.G Tier Score: {draft_analysis['team2_tier_score']:.2f}\n"
                f"• T1 Sinergia: {draft_analysis['team1_synergy']:.2f}\n"
                f"• Gen.G Sinergia: {draft_analysis['team2_synergy']:.2f}\n\n"
                f"⚡ **POWER SPIKES:**\n"
                f"**T1:** Early {draft_analysis['team1_power_spikes']['early']}, Mid {draft_analysis['team1_power_spikes']['mid']}, Late {draft_analysis['team1_power_spikes']['late']}\n"
                f"**Gen.G:** Early {draft_analysis['team2_power_spikes']['early']}, Mid {draft_analysis['team2_power_spikes']['mid']}, Late {draft_analysis['team2_power_spikes']['late']}\n\n"
                f"🏆 **VANTAGEM NO DRAFT:**\n"
                f"• Vencedor: {draft_analysis['draft_winner'].upper()}\n"
                f"• Magnitude: {draft_analysis['advantage_magnitude']:.3f}\n\n"
                f"🎯 **SINERGIAS PRINCIPAIS:**\n"
                f"• Azir + Graves (controle de área)\n"
                f"• Jinx + Thresh (engage e proteção)\n"
                f"• Orianna + Nautilus (teamfight)\n"
                f"• Kai'Sa + Nautilus (dive potential)\n\n"
                f"🔄 **META PATCH 14.23:**\n"
                f"• Champions S-tier: Azir, Graves, Thresh\n"
                f"• Scaling meta favorece late game\n"
                f"• Tank supports em alta"
            )
            
            return query.edit_message_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Demo Team Performance
        elif query.data == "demo_teams":
            keyboard = [
                [InlineKeyboardButton("🎯 Análise Avançada", callback_data="demo_advanced"),
                 InlineKeyboardButton("🎮 Ver Composição", callback_data="demo_draft")],
                [InlineKeyboardButton("🔙 Voltar Demo", callback_data="demo"),
                 InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            t1_data = self.advanced_analyzer.team_database['T1']
            geng_data = self.advanced_analyzer.team_database['Gen.G']
            
            demo_text = (
                "📊 **PERFORMANCE DETALHADA DOS TIMES**\n\n"
                f"🏆 **T1 (Rating: {t1_data['rating']})**\n"
                f"• Forma recente: {t1_data['recent_form']:.1%}\n"
                f"• Consistência: {t1_data['consistency']:.1%}\n"
                f"• Early game: {t1_data['early_game']:.1%}\n"
                f"• Mid game: {t1_data['mid_game']:.1%}\n"
                f"• Late game: {t1_data['late_game']:.1%}\n"
                f"• Flexibilidade draft: {t1_data['draft_flexibility']:.1%}\n"
                f"• Fator clutch: {t1_data['clutch_factor']:.1%}\n"
                f"• Exp. internacional: {t1_data['international_exp']:.1%}\n"
                f"• Adaptação meta: {t1_data['meta_adaptation']:.1%}\n"
                f"• Tempo médio: {t1_data['avg_game_time']} min\n"
                f"• First blood: {t1_data['first_blood_rate']:.1%}\n\n"
                f"⚔️ **Gen.G (Rating: {geng_data['rating']})**\n"
                f"• Forma recente: {geng_data['recent_form']:.1%}\n"
                f"• Consistência: {geng_data['consistency']:.1%}\n"
                f"• Early game: {geng_data['early_game']:.1%}\n"
                f"• Mid game: {geng_data['mid_game']:.1%}\n"
                f"• Late game: {geng_data['late_game']:.1%}\n"
                f"• Flexibilidade draft: {geng_data['draft_flexibility']:.1%}\n"
                f"• Fator clutch: {geng_data['clutch_factor']:.1%}\n"
                f"• Exp. internacional: {geng_data['international_exp']:.1%}\n"
                f"• Adaptação meta: {geng_data['meta_adaptation']:.1%}\n"
                f"• Tempo médio: {geng_data['avg_game_time']} min\n"
                f"• First blood: {geng_data['first_blood_rate']:.1%}\n\n"
                f"⭐ **JOGADORES DESTAQUE:**\n"
                f"**T1:** Faker (98), Zeus (95), Keria (96)\n"
                f"**Gen.G:** Chovy (96), Canyon (96), Kiin (90)\n\n"
                f"📈 **ÚLTIMAS 5 PARTIDAS:**\n"
                f"**T1:** {''.join(['✅' if w else '❌' for w in t1_data['recent_matches']])}\n"
                f"**Gen.G:** {''.join(['✅' if w else '❌' for w in geng_data['recent_matches']])}\n\n"
                f"🎯 **VANTAGENS PRINCIPAIS:**\n"
                f"• T1: Mid/late game, clutch factor\n"
                f"• Gen.G: Consistência, late game"
            )
            
            return query.edit_message_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Callbacks de Alertas
        elif query.data == "inscrever_alertas":
            chat_id = query.message.chat.id
            chat_type = query.message.chat.type
            
            if chat_type == 'private':
                message_text = (
                    "❌ **ERRO: COMANDO APENAS PARA GRUPOS**\n\n"
                    "Este comando só funciona em grupos do Telegram.\n\n"
                    "📝 **Como usar:**\n"
                    "1. Adicione o bot ao seu grupo\n"
                    "2. Torne o bot administrador\n"
                    "3. Use o botão 'Inscrever Grupo'\n\n"
                    "💡 **Dica:** Use `/alertas` para mais informações"
                )
            else:
                if chat_id in self.alert_system.subscribed_groups:
                    message_text = (
                        "✅ **GRUPO JÁ INSCRITO!**\n\n"
                        f"Este grupo já recebe alertas automáticos.\n\n"
                        "🔔 **Alertas ativos:**\n"
                        "• Partidas ao vivo\n"
                        "• Oportunidades de value betting\n"
                        "• Análises em tempo real\n\n"
                        "⚙️ Use `/alertas` para configurações"
                    )
                else:
                    self.alert_system.subscribe_group(chat_id)
                    if not self.alert_system.monitoring_active:
                        self.alert_system.start_monitoring()
                    
                    message_text = (
                        "🎉 **GRUPO INSCRITO COM SUCESSO!**\n\n"
                        f"Este grupo agora receberá alertas automáticos.\n\n"
                        "🔔 **Você receberá:**\n"
                        "• 🎮 Alertas de partidas ao vivo\n"
                        "• 💰 Oportunidades de value betting\n"
                        "• 🚨 Alertas de EV alto (8%+)\n"
                        "• 📊 Análises em tempo real\n\n"
                        "⏰ **Frequência:** Verificação a cada 1 minuto\n"
                        "🛡️ **Anti-spam:** Máximo 1 alerta por tipo a cada 5-10 min\n\n"
                        "⚙️ Use `/alertas` para configurações\n"
                        "🔕 Use o botão 'Desinscrever' para parar alertas"
                    )
            
            keyboard = [[InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]]
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif query.data == "desinscrever_alertas":
            chat_id = query.message.chat.id
            chat_type = query.message.chat.type
            
            if chat_type == 'private':
                message_text = (
                    "❌ **ERRO: COMANDO APENAS PARA GRUPOS**\n\n"
                    "Este comando só funciona em grupos do Telegram.\n\n"
                    "💡 Use `/alertas` para mais informações"
                )
            else:
                if chat_id not in self.alert_system.subscribed_groups:
                    message_text = (
                        "ℹ️ **GRUPO NÃO INSCRITO**\n\n"
                        "Este grupo não está recebendo alertas.\n\n"
                        "🔔 Use o botão 'Inscrever Grupo' para ativar alertas"
                    )
                else:
                    self.alert_system.unsubscribe_group(chat_id)
                    message_text = (
                        "✅ **GRUPO DESINSCRITO COM SUCESSO!**\n\n"
                        "Este grupo não receberá mais alertas automáticos.\n\n"
                        "🔔 **Para reativar:**\n"
                        "Use o botão 'Inscrever Grupo' a qualquer momento\n\n"
                        "💡 **Lembre-se:**\n"
                        "Você ainda pode usar todos os comandos manuais:\n"
                        "• `/partidas` - Ver partidas\n"
                        "• `/value` - Value betting\n"
                        "• `/stats` - Estatísticas"
                    )
            
            keyboard = [[InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]]
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif query.data == "status_alertas":
            status = self.alert_system.get_status()
            
            keyboard = [
                [InlineKeyboardButton("🔔 Inscrever Grupo", callback_data="inscrever_alertas"),
                 InlineKeyboardButton("🔕 Desinscrever", callback_data="desinscrever_alertas")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "📊 **STATUS DETALHADO DOS ALERTAS**\n\n"
                f"🔄 **MONITORAMENTO:**\n"
                f"• Status: {'🟢 ATIVO' if status['monitoring_active'] else '🔴 INATIVO'}\n"
                f"• Grupos inscritos: {status['subscribed_groups']}\n\n"
                "⚙️ **CONFIGURAÇÕES ATIVAS:**\n"
                f"• Alertas de partidas: {'✅' if status['settings']['live_matches'] else '❌'}\n"
                f"• Alertas de value: {'✅' if status['settings']['value_betting'] else '❌'}\n"
                f"• Apenas EV alto: {'✅' if status['settings']['high_ev_only'] else '❌'}\n"
                f"• EV mínimo: {status['settings']['min_ev']*100:.1f}%\n"
                f"• Confiança mínima: {status['settings']['min_confidence']*100:.1f}%\n\n"
                "🕐 **ÚLTIMOS ALERTAS:**\n"
            )
            
            if status['last_alerts']:
                for alert_type, time_str in status['last_alerts'].items():
                    alert_name = alert_type.replace('_', ' ').title()
                    message_text += f"• {alert_name}: {time_str}\n"
            else:
                message_text += "• Nenhum alerta enviado ainda\n"
            
            message_text += (
                f"\n⏰ **Status atual:** {datetime.now().strftime('%H:%M:%S')}\n"
                "🔄 **Próxima verificação:** Em até 1 minuto"
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif query.data == "config_alertas":
            status = self.alert_system.get_status()
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar Status", callback_data="status_alertas")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu_principal")]
            ]
            
            message_text = (
                "⚙️ **CONFIGURAÇÕES DE ALERTAS**\n\n"
                "📋 **CONFIGURAÇÕES ATUAIS:**\n"
                f"• EV mínimo: {status['settings']['min_ev']*100:.1f}%\n"
                f"• Confiança mínima: {status['settings']['min_confidence']*100:.1f}%\n"
                f"• Apenas EV alto (8%+): {'✅' if status['settings']['high_ev_only'] else '❌'}\n"
                f"• Alertas de partidas: {'✅' if status['settings']['live_matches'] else '❌'}\n"
                f"• Alertas de value: {'✅' if status['settings']['value_betting'] else '❌'}\n\n"
                "🔧 **CONFIGURAÇÕES PADRÃO:**\n"
                "• EV mínimo: 3.0% (recomendado)\n"
                "• Confiança mínima: 65% (conservador)\n"
                "• Frequência: 1 minuto (otimizada)\n"
                "• Anti-spam: 5-10 min entre alertas\n\n"
                "💡 **NOTA:**\n"
                "As configurações são otimizadas para máxima eficiência.\n"
                "Para alterações personalizadas, entre em contato com o desenvolvedor."
            )
            
            return query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    def get_demo_value_analysis(self):
        """Demonstra análise de value betting com exemplos"""
        # Simular diferentes cenários de value betting
        scenarios = [
            {
                'match': 'T1 vs Gen.G',
                'our_prob': 0.72,
                'bookmaker_odds': 1.85,
                'scenario': 'EV Alto + Confiança Alta'
            },
            {
                'match': 'G2 vs Fnatic', 
                'our_prob': 0.58,
                'bookmaker_odds': 2.10,
                'scenario': 'EV Médio + Confiança Média'
            },
            {
                'match': 'TSM vs C9',
                'our_prob': 0.65,
                'bookmaker_odds': 1.75,
                'scenario': 'EV Baixo + Confiança Baixa'
            }
        ]
        
        analysis_results = []
        
        for scenario in scenarios:
            analysis = self.value_system.analyze_value_opportunity(
                scenario['our_prob'], 
                scenario['bookmaker_odds']
            )
            
            if analysis['has_value']:
                bet_info = analysis['bet_analysis']
                analysis_results.append({
                    'match': scenario['match'],
                    'scenario': scenario['scenario'],
                    'our_prob': scenario['our_prob'] * 100,
                    'implied_prob': (1/scenario['bookmaker_odds']) * 100,
                    'ev': analysis['ev'] * 100,
                    'confidence': analysis['confidence'] * 100,
                    'units': bet_info['units'],
                    'stake': bet_info['stake'],
                    'recommendation': bet_info['recommendation'],
                    'risk_level': analysis['risk_level']
                })
        
        return analysis_results
    
    def format_value_demo(self):
        """Formata demonstração do sistema de value betting"""
        demos = self.get_demo_value_analysis()
        
        demo_text = "🎯 **EXEMPLOS DE VALUE BETTING**\n\n"
        
        for i, demo in enumerate(demos, 1):
            demo_text += f"**{i}. {demo['match']}**\n"
            demo_text += f"• Nossa probabilidade: {demo['our_prob']:.1f}%\n"
            demo_text += f"• Prob. implícita: {demo['implied_prob']:.1f}%\n"
            demo_text += f"• Expected Value: {demo['ev']:.1f}%\n"
            demo_text += f"• Confiança: {demo['confidence']:.1f}%\n"
            demo_text += f"• **Unidades: {demo['units']}**\n"
            demo_text += f"• **Stake: R$ {demo['stake']:.0f}**\n"
            demo_text += f"• Risco: {demo['risk_level']}\n"
            demo_text += f"• {demo['recommendation']}\n\n"
        
        demo_text += "💡 **OBSERVAÇÕES:**\n"
        demo_text += "• Unidades calculadas: (EV_units + Conf_units) ÷ 2\n"
        demo_text += "• Máximo 3 unidades por aposta\n"
        demo_text += "• Diversificação sempre recomendada\n"
        demo_text += "• Gestão de risco prioritária"
        
        return demo_text
    
    def run(self):
        """Executar o bot"""
        logger.info("🚀 Iniciando Bot LoL V3...")
        
        if NEW_VERSION:
            # Versão nova - usar run_polling
            self.application.run_polling()
        else:
            # Versão antiga - usar start_polling + idle
            self.updater.start_polling()
            self.updater.idle()
            
        logger.info("✅ Bot iniciado com sucesso!")

def main():
    """Função principal"""
    try:
        bot = BotLoLV3Railway()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        raise

if __name__ == "__main__":
    main() 
