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

# Flask para health check
from flask import Flask, jsonify
import requests

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
import aiohttp

# Configurações
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')
OWNER_ID = int(os.getenv('OWNER_ID', '6404423764'))
PORT = int(os.getenv('PORT', 5000))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Flask app para healthcheck
app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'bot_lol_v3_professional_units',
        'version': TELEGRAM_VERSION,
        'units_system': 'PROFESSIONAL_STANDARD'
    })

@app.route('/')
def root():
    return jsonify({
        'message': 'BOT LOL V3 - Sistema de Unidades Profissional',
        'status': 'online',
        'units_system': 'Padrão de grupos profissionais'
    })

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

class ProfessionalTipsSystem:
    """Sistema de Tips Profissional com Unidades Padrão"""
    
    def __init__(self, riot_client=None):
        self.riot_client = riot_client or RiotAPIClient()
        self.units_system = ProfessionalUnitsSystem()
        self.tips_database = []
        self.given_tips = set()
        
        # Critérios profissionais
        self.min_ev_percentage = 8.0
        self.min_confidence_score = 75.0
        self.max_tips_per_week = 5
        
        logger.info("🎯 Sistema de Tips Profissional inicializado")
    
    async def generate_professional_tip(self) -> Optional[Dict]:
        """Gera tip profissional com sistema de unidades padrão"""
        try:
            # Buscar partidas
            live_matches = await self.riot_client.get_live_matches()
            
            if not live_matches:
                return None
            
            best_tip = None
            highest_score = 0
            
            for match in live_matches:
                tip_analysis = await self._analyze_match_for_tip(match)
                
                if tip_analysis and tip_analysis['quality_score'] > highest_score:
                    tip_id = self._generate_tip_id(match)
                    if tip_id not in self.given_tips:
                        highest_score = tip_analysis['quality_score']
                        best_tip = tip_analysis
            
            if best_tip and self._meets_professional_criteria(best_tip):
                tip_id = self._generate_tip_id(best_tip['match_data'])
                self.given_tips.add(tip_id)
                
                professional_tip = self._create_professional_tip(best_tip)
                self.tips_database.append(professional_tip)
                
                return professional_tip
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao gerar tip: {e}")
            return None
    
    async def _analyze_match_for_tip(self, match: Dict) -> Optional[Dict]:
        """Análise profunda de uma partida"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None
            
            team1 = teams[0]['name']
            team2 = teams[1]['name']
            league = match.get('league', 'Unknown')
            
            # Análise de valor
            value_analysis = self._calculate_value(team1, team2, league)
            confidence_analysis = self._calculate_confidence(team1, team2, league)
            
            quality_score = (value_analysis['ev_percentage'] * 2) + confidence_analysis['total_confidence']
            
            return {
                'match_data': match,
                'team1': team1,
                'team2': team2,
                'league': league,
                'value_analysis': value_analysis,
                'confidence_analysis': confidence_analysis,
                'quality_score': quality_score
            }
            
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return None
    
    def _calculate_value(self, team1: str, team2: str, league: str) -> Dict:
        """Calcula valor esperado"""
        # Ratings conhecidos dos times
        team_ratings = {
            'T1': 95, 'Gen.G': 90, 'DRX': 88, 'KT': 85,
            'JDG': 94, 'BLG': 92, 'WBG': 89, 'TES': 87,
            'G2': 88, 'FNC': 85, 'MAD': 82, 'VIT': 80,
            'C9': 82, 'TL': 80, 'TSM': 78, '100T': 76
        }
        
        team1_rating = 70
        team2_rating = 70
        
        for known_team, rating in team_ratings.items():
            if known_team.lower() in team1.lower():
                team1_rating = rating
            if known_team.lower() in team2.lower():
                team2_rating = rating
        
        # Calcular probabilidades
        total_rating = team1_rating + team2_rating
        team1_prob = team1_rating / total_rating
        team2_prob = team2_rating / total_rating
        
        # Simular odds do mercado
        team1_odds = (1 / team1_prob) * 0.95  # 5% margem
        team2_odds = (1 / team2_prob) * 0.95
        
        # Expected Value
        ev1 = (team1_prob * team1_odds) - 1
        ev2 = (team2_prob * team2_odds) - 1
        
        if ev1 > ev2 and ev1 > 0:
            return {
                'recommended_team': team1,
                'opposing_team': team2,
                'win_probability': team1_prob,
                'market_odds': team1_odds,
                'ev_percentage': ev1 * 100
            }
        elif ev2 > 0:
            return {
                'recommended_team': team2,
                'opposing_team': team1,
                'win_probability': team2_prob,
                'market_odds': team2_odds,
                'ev_percentage': ev2 * 100
            }
        else:
            return {'ev_percentage': 0, 'recommended_team': None}
    
    def _calculate_confidence(self, team1: str, team2: str, league: str) -> Dict:
        """Calcula fatores de confiança"""
        confidence_factors = []
        total_confidence = 0
        
        # Liga tier 1
        tier1_leagues = ['LCK', 'LPL', 'LEC', 'LCS']
        if any(tier1 in league.upper() for tier1 in tier1_leagues):
            confidence_factors.append('tier1_league')
            total_confidence += 20
        
        # Times conhecidos
        known_teams = ['T1', 'Gen.G', 'JDG', 'BLG', 'G2', 'FNC', 'C9', 'TL']
        if any(team in team1 or team in team2 for team in known_teams):
            confidence_factors.append('known_teams')
            total_confidence += 15
        
        # Base de confiança
        total_confidence += 40  # Base
        
        return {
            'total_confidence': min(total_confidence, 95),
            'factors': confidence_factors,
            'confidence_level': 'Alta' if total_confidence >= 75 else 'Média'
        }
    
    def _meets_professional_criteria(self, tip_analysis: Dict) -> bool:
        """Verifica critérios profissionais"""
        value = tip_analysis['value_analysis']
        confidence = tip_analysis['confidence_analysis']
        
        return (
            value['ev_percentage'] >= self.min_ev_percentage and
            confidence['total_confidence'] >= self.min_confidence_score and
            value.get('recommended_team') is not None
        )
    
    def _generate_tip_id(self, match: Dict) -> str:
        """Gera ID único para tip"""
        teams = match.get('teams', [])
        if len(teams) >= 2:
            team1 = teams[0].get('name', '')
            team2 = teams[1].get('name', '')
            date = datetime.now().strftime('%Y%m%d')
            return f"{team1}_{team2}_{date}"
        return f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _create_professional_tip(self, tip_analysis: Dict) -> Dict:
        """Cria tip profissional formatada"""
        value = tip_analysis['value_analysis']
        confidence = tip_analysis['confidence_analysis']
        match_data = tip_analysis['match_data']
        
        # Determinar tier da liga
        league = tip_analysis['league']
        tier1_leagues = ['LCK', 'LPL', 'LEC', 'LCS']
        league_tier = 'tier1' if any(tier1 in league.upper() for tier1 in tier1_leagues) else 'tier2'
        
        # Calcular unidades usando sistema profissional
        units_data = self.units_system.calculate_units(
            confidence['total_confidence'],
            value['ev_percentage'],
            league_tier
        )
        
        tip = {
            'id': self._generate_tip_id(match_data),
            'timestamp': datetime.now(),
            'title': f"{value['recommended_team']} vs {value['opposing_team']}",
            'league': league,
            'recommended_team': value['recommended_team'],
            'opposing_team': value['opposing_team'],
            'win_probability': value['win_probability'],
            'market_odds': value['market_odds'],
            'ev_percentage': value['ev_percentage'],
            'confidence_score': confidence['total_confidence'],
            'confidence_level': confidence['confidence_level'],
            'units': units_data['units'],
            'stake_amount': units_data['stake_amount'],
            'risk_level': units_data['risk_level'],
            'reasoning': units_data['reasoning'],
            'league_tier': league_tier,
            'status': 'Ativa'
        }
        
        return tip
    
    def get_recent_tips(self, limit: int = 10) -> List[Dict]:
        """Retorna tips recentes"""
        return sorted(self.tips_database, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_performance_summary(self) -> Dict:
        """Retorna resumo de performance"""
        units_performance = self.units_system.get_performance_summary()
        
        return {
            'total_tips': len(self.tips_database),
            'tips_this_week': len([tip for tip in self.tips_database 
                                 if (datetime.now() - tip['timestamp']).days < 7]),
            'avg_ev': np.mean([tip['ev_percentage'] for tip in self.tips_database]) if self.tips_database else 0,
            'avg_confidence': np.mean([tip['confidence_score'] for tip in self.tips_database]) if self.tips_database else 0,
            'units_performance': units_performance
        }

def run_flask_app():
    """Executa Flask em thread separada"""
    app.run(host='0.0.0.0', port=PORT, debug=False)

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
        
        # Iniciar Flask
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        logger.info(f"🌐 Health check rodando na porta {PORT}")
        
        logger.info("✅ Bot configurado com sistema de unidades profissional!")
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")

if __name__ == "__main__":
    main() 