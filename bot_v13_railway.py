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

class LoLBotV3UltraAdvanced:
    """Bot LoL V3 Ultra Avançado com Sistema de Unidades Profissional"""
    
    def __init__(self):
        self.riot_client = RiotAPIClient()
        self.tips_system = ProfessionalTipsSystem(self.riot_client)
        self.live_matches_cache = {}
        self.cache_timestamp = None
        
        logger.info("🤖 Bot LoL V3 Ultra Avançado inicializado")
    
    async def start_command(self, update: Update, context) -> None:
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
• 🎯 Tips profissionais seletivos
• 📊 Sistema de unidades padrão
• 🎮 Partidas ao vivo selecionáveis
• 📈 Value betting avançado
• 📋 Estatísticas detalhadas

Use /menu para ver todas as opções!
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 Tips Profissionais", callback_data="tips")],
            [InlineKeyboardButton("🎮 Partidas Ao Vivo", callback_data="live_matches")],
            [InlineKeyboardButton("📊 Sistema de Unidades", callback_data="units_info")],
            [InlineKeyboardButton("📈 Value Betting", callback_data="value_betting")],
            [InlineKeyboardButton("📋 Menu Completo", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if TELEGRAM_VERSION == "v20+":
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def menu_command(self, update: Update, context) -> None:
        """Comando /menu"""
        menu_message = """
🎮 **MENU PRINCIPAL - BOT LOL V3** 🎮

🎯 **TIPS & ANÁLISES:**
• /tips - Tips profissionais
• /live - Partidas ao vivo
• /value - Value betting
• /stats - Estatísticas

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
            [InlineKeyboardButton("🎯 Tips", callback_data="tips"), 
             InlineKeyboardButton("🎮 Ao Vivo", callback_data="live_matches")],
            [InlineKeyboardButton("📈 Value Bets", callback_data="value_betting"), 
             InlineKeyboardButton("📊 Unidades", callback_data="units_info")],
            [InlineKeyboardButton("📋 Stats", callback_data="stats"), 
             InlineKeyboardButton("❓ Ajuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if TELEGRAM_VERSION == "v20+":
            await update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
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
        """Handler para callbacks dos botões"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data == "tips":
                await self._handle_tips_callback(query)
            elif data == "live_matches":
                await self._handle_live_matches_callback(query)
            elif data == "units_info":
                await self._handle_units_info_callback(query)
            elif data == "value_betting":
                await self._handle_value_betting_callback(query)
            elif data == "main_menu":
                await self._handle_main_menu_callback(query)
            elif data.startswith("match_"):
                match_index = int(data.split("_")[1])
                await self._handle_match_details_callback(query, match_index)
            else:
                await query.edit_message_text("❌ Opção não reconhecida.")
                
        except Exception as e:
            logger.error(f"Erro no callback handler: {e}")
            await query.edit_message_text("❌ Erro interno. Tente novamente.")
    
    async def _handle_units_info_callback(self, query) -> None:
        """Mostra informações do sistema de unidades"""
        units_info = self.tips_system.units_system.get_units_explanation()
        
        keyboard = [
            [InlineKeyboardButton("🎯 Gerar Tip", callback_data="tips")],
            [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(units_info, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

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
        
        # Inicializar bot
        bot = LoLBotV3UltraAdvanced()
        
        if TELEGRAM_VERSION == "v20+":
            # Versão v20+
            application = Application.builder().token(TOKEN).build()
            
            # Handlers
            application.add_handler(CommandHandler("start", bot.start_command))
            application.add_handler(CommandHandler("menu", bot.menu_command))
            application.add_handler(CommandHandler("tips", bot.tips_command))
            application.add_handler(CommandHandler("live", bot.live_matches_command))
            application.add_handler(CallbackQueryHandler(bot.callback_handler))
            
            logger.info("✅ Bot configurado (v20+) - Iniciando polling...")
            application.run_polling()
            
        else:
            # Versão v13
            updater = Updater(TOKEN)
            dispatcher = updater.dispatcher
            
            # Handlers
            dispatcher.add_handler(CommandHandler("start", bot.start_command))
            dispatcher.add_handler(CommandHandler("menu", bot.menu_command))
            dispatcher.add_handler(CommandHandler("tips", bot.tips_command))
            dispatcher.add_handler(CommandHandler("live", bot.live_matches_command))
            dispatcher.add_handler(CallbackQueryHandler(bot.callback_handler))
            
            logger.info("✅ Bot configurado (v13) - Iniciando polling...")
            updater.start_polling()
            updater.idle()
                
    except Exception as e:
        logger.error(f"❌ Erro: {e}")

if __name__ == "__main__":
    main() 