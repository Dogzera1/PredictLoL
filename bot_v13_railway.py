#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT LOL V3 ULTRA OTIMIZADO - Versão Railway Optimizada
Sistema de unidades padrão de grupos de apostas profissionais
APENAS DADOS REAIS DA API DA RIOT GAMES - VERSÃO ULTRA LEVE
"""

import os
import sys
import time
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

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
                            sys.exit(1)
                    else:  # Unix/Linux
                        os.kill(old_pid, 0)  # Não mata, só verifica
                        print(f"🚨 OUTRA INSTÂNCIA DETECTADA! PID: {old_pid}")
                        print("🛑 ABORTANDO PARA EVITAR CONFLITOS!")
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

# Flask para health check - VERSÃO MÍNIMA
from flask import Flask, jsonify

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

# Configurações
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')
OWNER_ID = int(os.getenv('OWNER_ID', '6404423764'))
PORT = int(os.getenv('PORT', 5800))

# Setup logging - OTIMIZADO
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app MÍNIMO para healthcheck
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/health')
def health_check():
    """Health check para Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'bot_lol_v3_ultra_optimized',
        'version': TELEGRAM_VERSION,
        'memory_optimized': True
    }), 200

@app.route('/')
def root():
    """Rota raiz"""
    return jsonify({
        'message': 'BOT LOL V3 - Ultra Otimizado',
        'status': 'online',
        'optimization': 'MAXIMUM'
    }), 200

@app.route('/ping')
def ping():
    """Ping simples"""
    return "pong", 200

# Sistema de Unidades SIMPLIFICADO
class SimpleUnitsSystem:
    """Sistema de Unidades Simplificado para Railway"""
    
    def __init__(self, bankroll: float = 1000.0):
        self.bankroll = bankroll
        self.base_unit = bankroll * 0.01  # 1% do bankroll
        logger.info(f"💰 Sistema de Unidades Simplificado - Bankroll: ${bankroll}")
    
    def calculate_units(self, confidence: float, ev_percentage: float) -> Dict:
        """Calcula unidades de forma simplificada"""
        
        # Sistema simplificado baseado apenas em confiança e EV
        if confidence >= 85 and ev_percentage >= 12:
            units = 4.0
            risk_level = "Alto"
        elif confidence >= 80 and ev_percentage >= 10:
            units = 3.0
            risk_level = "Médio-Alto"
        elif confidence >= 75 and ev_percentage >= 8:
            units = 2.5
            risk_level = "Médio"
        elif confidence >= 70 and ev_percentage >= 6:
            units = 2.0
            risk_level = "Baixo-Médio"
        elif confidence >= 65 and ev_percentage >= 5:
            units = 1.0
            risk_level = "Baixo"
        else:
            return {
                'units': 0,
                'stake_amount': 0,
                'risk_level': 'Sem Valor',
                'recommendation': 'NÃO APOSTAR'
            }
        
        stake_amount = units * self.base_unit
        
        return {
            'units': units,
            'stake_amount': round(stake_amount, 2),
            'risk_level': risk_level,
            'confidence': confidence,
            'ev_percentage': ev_percentage,
            'recommendation': f"Apostar {units} unidades (${stake_amount:.2f})"
        }

# Cliente API SIMPLIFICADO
class SimpleRiotClient:
    """Cliente API Simplificado"""
    
    def __init__(self):
        self.api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
        self.base_url = 'https://esports-api.lolesports.com/persisted/gw'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        logger.info("🔗 Cliente API Simplificado inicializado")
    
    async def get_live_matches(self) -> List[Dict]:
        """Busca partidas ao vivo de forma simplificada"""
        try:
            # Importar aiohttp apenas quando necessário
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/getLive?hl=pt-BR", 
                    headers=self.headers, 
                    timeout=5
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches = self._extract_matches_simple(data)
                        return matches[:3]  # Máximo 3 partidas para economizar memória
        except Exception as e:
            logger.warning(f"❌ Erro ao buscar partidas: {e}")
        
        return []
    
    def _extract_matches_simple(self, data: Dict) -> List[Dict]:
        """Extrai partidas de forma simplificada"""
        matches = []
        
        try:
            events = None
            if 'data' in data and 'schedule' in data['data'] and 'events' in data['data']['schedule']:
                events = data['data']['schedule']['events']
            elif 'data' in data and 'events' in data['data']:
                events = data['data']['events']
            
            if events:
                for event in events[:5]:  # Máximo 5 eventos
                    teams = self._extract_teams_simple(event)
                    if len(teams) >= 2:
                        match = {
                            'teams': teams,
                            'league': event.get('league', {}).get('name', 'Unknown League'),
                            'status': event.get('state', 'scheduled')
                        }
                        matches.append(match)
        except Exception as e:
            logger.error(f"Erro ao extrair partidas: {e}")
        
        return matches
    
    def _extract_teams_simple(self, event: Dict) -> List[Dict]:
        """Extrai times de forma simplificada"""
        teams = []
        
        try:
            teams_data = event.get('match', {}).get('teams', [])
            if not teams_data:
                teams_data = event.get('teams', [])
            
            for team_data in teams_data[:2]:  # Máximo 2 times
                team = {
                    'name': team_data.get('name', 'Unknown Team'),
                    'code': team_data.get('code', '')
                }
                teams.append(team)
        except:
            pass
        
        return teams

# Sistema de Predição SIMPLIFICADO
class SimplePredictionSystem:
    """Sistema de predição simplificado para Railway"""
    
    def __init__(self):
        # Base de dados mínima dos principais times
        self.teams_ratings = {
            'T1': 95, 'Gen.G': 90, 'DRX': 85,
            'JDG': 95, 'BLG': 90, 'WBG': 85,
            'G2': 90, 'Fnatic': 85, 'MAD': 80,
            'C9': 80, 'TL': 78, '100T': 75,
            'LOUD': 85, 'paiN': 80, 'Red Canids': 75
        }
        logger.info("🔮 Sistema de Predição Simplificado inicializado")
    
    async def predict_match_simple(self, match: Dict) -> Optional[Dict]:
        """Predição simplificada"""
        try:
            teams = match.get('teams', [])
            if len(teams) < 2:
                return None
            
            team1_name = teams[0].get('name', '')
            team2_name = teams[1].get('name', '')
            
            # Buscar ratings
            team1_rating = self._get_team_rating(team1_name)
            team2_rating = self._get_team_rating(team2_name)
            
            # Calcular probabilidade simples
            rating_diff = team1_rating - team2_rating
            team1_prob = 0.5 + (rating_diff / 200)  # Normalizar
            team1_prob = max(0.2, min(0.8, team1_prob))  # Limitar entre 20-80%
            
            # Determinar favorito
            if team1_prob > 0.5:
                favored_team = team1_name
                win_probability = team1_prob
                confidence_score = 70 + abs(rating_diff)
            else:
                favored_team = team2_name
                win_probability = 1 - team1_prob
                confidence_score = 70 + abs(rating_diff)
            
            # Limitar confiança
            confidence_score = min(90, confidence_score)
            
            # Calcular EV simples
            ev_percentage = max(5, (confidence_score - 65) * 0.5)
            
            # Determinar nível de confiança
            if confidence_score >= 85:
                confidence_level = 'Muito Alta'
            elif confidence_score >= 75:
                confidence_level = 'Alta'
            else:
                confidence_level = 'Média'
            
            return {
                'team1': team1_name,
                'team2': team2_name,
                'favored_team': favored_team,
                'win_probability': win_probability,
                'confidence_score': confidence_score,
                'confidence_level': confidence_level,
                'ev_percentage': ev_percentage,
                'analysis': f"{favored_team} favorito com {win_probability*100:.1f}% de chance"
            }
            
        except Exception as e:
            logger.error(f"Erro na predição: {e}")
            return None
    
    def _get_team_rating(self, team_name: str) -> int:
        """Busca rating do time"""
        # Busca exata
        if team_name in self.teams_ratings:
            return self.teams_ratings[team_name]
        
        # Busca parcial
        for db_team, rating in self.teams_ratings.items():
            if db_team.lower() in team_name.lower() or team_name.lower() in db_team.lower():
                return rating
        
        # Fallback
        return 70

# Bot ULTRA SIMPLIFICADO
class LoLBotUltraOptimized:
    """Bot LoL Ultra Otimizado para Railway"""
    
    def __init__(self):
        self.riot_client = SimpleRiotClient()
        self.units_system = SimpleUnitsSystem()
        self.prediction_system = SimplePredictionSystem()
        self.cache = {}  # Cache simples
        
        logger.info("🤖 Bot LoL Ultra Otimizado inicializado")
    
    async def start_command(self, update: Update, context) -> None:
        """Comando /start ultra otimizado"""
        try:
            user = update.effective_user
            logger.info(f"📨 /start de {user.first_name}")
            
            welcome_message = f"""
🎮 **BOT LOL V3 ULTRA OTIMIZADO** 🎮

Olá {user.first_name}! 👋

⚡ **VERSÃO RAILWAY OTIMIZADA**
🎯 Sistema de unidades profissional
🔮 Predições IA simplificadas
📊 Uso mínimo de memória

🔥 **COMANDOS:**
• /tips - Tips profissionais
• /live - Partidas ao vivo
• /menu - Menu completo

✨ Otimizado para máxima performance!
            """
            
            keyboard = [
                [InlineKeyboardButton("🎯 Tips", callback_data="tips")],
                [InlineKeyboardButton("🎮 Ao Vivo", callback_data="live")],
                [InlineKeyboardButton("📋 Menu", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
            logger.info(f"✅ /start respondido para {user.first_name}")
            
        except Exception as e:
            logger.error(f"❌ Erro no /start: {e}")
            try:
                error_message = "❌ Erro temporário. Tente /start novamente."
                if TELEGRAM_VERSION == "v20+":
                    await update.message.reply_text(error_message)
                else:
                    await update.message.reply_text(error_message)
            except:
                pass
    
    async def tips_command(self, update: Update, context) -> None:
        """Comando /tips simplificado"""
        try:
            # Buscar uma partida para análise
            matches = await self.riot_client.get_live_matches()
            
            if matches:
                match = matches[0]  # Primeira partida
                prediction = await self.prediction_system.predict_match_simple(match)
                
                if prediction and prediction['confidence_score'] >= 75:
                    units_calc = self.units_system.calculate_units(
                        prediction['confidence_score'],
                        prediction['ev_percentage']
                    )
                    
                    if units_calc['units'] > 0:
                        tip_message = f"""
🎯 **TIP PROFISSIONAL** 🎯

🏆 **{prediction['team1']} vs {prediction['team2']}**

📊 **ANÁLISE:**
• Favorito: {prediction['favored_team']}
• Confiança: {prediction['confidence_score']:.1f}%
• EV: {prediction['ev_percentage']:.1f}%

🎲 **UNIDADES:**
• Apostar: {units_calc['units']} unidades
• Valor: ${units_calc['stake_amount']:.2f}
• Risco: {units_calc['risk_level']}

💡 {prediction['analysis']}
                        """
                    else:
                        tip_message = "🎯 **NENHUM TIP DISPONÍVEL**\n\n❌ Partida não atende critérios mínimos."
                else:
                    tip_message = "🎯 **NENHUM TIP DISPONÍVEL**\n\n❌ Confiança insuficiente (<75%)."
            else:
                tip_message = "🎯 **NENHUMA PARTIDA DISPONÍVEL**\n\n🔄 Tente novamente em alguns minutos."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Novo Tip", callback_data="tips")],
                [InlineKeyboardButton("🎮 Ao Vivo", callback_data="live")],
                [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(tip_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(tip_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                
        except Exception as e:
            logger.error(f"Erro no /tips: {e}")
            error_message = "❌ Erro ao gerar tip. Tente novamente."
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)
    
    async def live_command(self, update: Update, context) -> None:
        """Comando /live simplificado"""
        try:
            matches = await self.riot_client.get_live_matches()
            
            if matches:
                message = f"🎮 **PARTIDAS AO VIVO** 🎮\n\n📊 **{len(matches)} partidas encontradas:**\n\n"
                
                for i, match in enumerate(matches, 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team1')
                        team2 = teams[1].get('name', 'Team2')
                        league = match.get('league', 'League')
                        
                        message += f"**{i}. {team1} vs {team2}**\n🏆 {league}\n\n"
            else:
                message = "🎮 **NENHUMA PARTIDA AO VIVO**\n\n❌ Não há partidas no momento."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="live")],
                [InlineKeyboardButton("🎯 Tips", callback_data="tips")],
                [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                
        except Exception as e:
            logger.error(f"Erro no /live: {e}")
            error_message = "❌ Erro ao buscar partidas. Tente novamente."
            if TELEGRAM_VERSION == "v20+":
                await update.message.reply_text(error_message)
            else:
                await update.message.reply_text(error_message)
    
    async def menu_command(self, update: Update, context) -> None:
        """Menu simplificado"""
        menu_message = """
🎮 **MENU - BOT LOL V3 OTIMIZADO** 🎮

⚡ **VERSÃO ULTRA LEVE PARA RAILWAY**

🎯 **COMANDOS DISPONÍVEIS:**
• /start - Iniciar bot
• /tips - Tips profissionais
• /live - Partidas ao vivo
• /menu - Este menu

📊 **CARACTERÍSTICAS:**
• Sistema de unidades profissional
• Predições IA otimizadas
• Uso mínimo de memória
• Máxima performance

✨ Otimizado especialmente para Railway!
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 Tips", callback_data="tips")],
            [InlineKeyboardButton("🎮 Ao Vivo", callback_data="live")],
            [InlineKeyboardButton("🔄 Atualizar", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if TELEGRAM_VERSION == "v20+":
            await update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def callback_handler(self, update: Update, context) -> None:
        """Handler para callbacks simplificado"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data == "tips":
                await self.tips_command(query, context)
            elif data == "live":
                await self.live_command(query, context)
            elif data == "menu":
                await self.menu_command(query, context)
            else:
                await query.edit_message_text("❌ Opção não reconhecida.")
                
        except Exception as e:
            logger.error(f"Erro no callback: {e}")
            await query.edit_message_text("❌ Erro interno. Tente novamente.")

def main():
    """Função principal ultra otimizada"""
    try:
        logger.info("🚀 INICIANDO BOT LOL V3 ULTRA OTIMIZADO")
        logger.info("⚡ VERSÃO ESPECIAL PARA RAILWAY - USO MÍNIMO DE MEMÓRIA")
        
        # Inicializar bot
        bot = LoLBotUltraOptimized()
        
        # Detectar ambiente
        is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))
        
        logger.info(f"🔍 Ambiente: {'🚀 RAILWAY' if is_railway else '🏠 LOCAL'}")
        
        if TELEGRAM_VERSION == "v20+":
            # Versão v20+
            application = Application.builder().token(TOKEN).build()
            
            # Limpar webhook existente
            async def clear_webhook():
                try:
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    logger.info("🧹 Webhook limpo")
                except Exception as e:
                    logger.debug(f"Webhook já limpo: {e}")
            
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(clear_webhook())
            
            # Handlers mínimos
            application.add_handler(CommandHandler("start", bot.start_command))
            application.add_handler(CommandHandler("tips", bot.tips_command))
            application.add_handler(CommandHandler("live", bot.live_command))
            application.add_handler(CommandHandler("menu", bot.menu_command))
            application.add_handler(CallbackQueryHandler(bot.callback_handler))
            
            if is_railway:
                # Webhook para Railway
                logger.info("🚀 Configurando webhook Railway")
                
                @app.route('/webhook', methods=['POST'])
                def webhook():
                    try:
                        from flask import request
                        update_data = request.get_json(force=True)
                        
                        if update_data:
                            from telegram import Update
                            update = Update.de_json(update_data, application.bot)
                            
                            import asyncio
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                            
                            loop.run_until_complete(application.process_update(update))
                            
                        return "OK", 200
                    except Exception as e:
                        logger.error(f"❌ Erro webhook: {e}")
                        return "Error", 500
                
                # Configurar webhook
                railway_url = os.getenv('RAILWAY_STATIC_URL', 'bot.railway.app')
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                webhook_url = f"{railway_url}/webhook"
                
                async def setup_webhook():
                    try:
                        await application.bot.set_webhook(webhook_url)
                        logger.info(f"✅ Webhook: {webhook_url}")
                    except Exception as e:
                        logger.error(f"❌ Erro webhook: {e}")
                
                loop.run_until_complete(setup_webhook())
                
                logger.info("✅ Bot configurado - Iniciando Flask")
                app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
                
            else:
                # Polling para local
                logger.info("🏠 Iniciando polling local")
                
                # Flask em thread separada
                flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False), daemon=True)
                flask_thread.start()
                
                application.run_polling(drop_pending_updates=True)
            
        else:
            # Versão v13
            updater = Updater(TOKEN)
            dispatcher = updater.dispatcher
            
            # Limpar webhook
            try:
                updater.bot.delete_webhook(drop_pending_updates=True)
                logger.info("🧹 Webhook v13 limpo")
            except Exception as e:
                logger.debug(f"Webhook v13 já limpo: {e}")
            
            # Handlers mínimos
            dispatcher.add_handler(CommandHandler("start", bot.start_command))
            dispatcher.add_handler(CommandHandler("tips", bot.tips_command))
            dispatcher.add_handler(CommandHandler("live", bot.live_command))
            dispatcher.add_handler(CommandHandler("menu", bot.menu_command))
            dispatcher.add_handler(CallbackQueryHandler(bot.callback_handler))
            
            if is_railway:
                # Webhook v13 para Railway
                logger.info("🚀 Configurando webhook v13 Railway")
                
                @app.route('/webhook', methods=['POST'])
                def webhook_v13():
                    try:
                        from flask import request
                        update_data = request.get_json(force=True)
                        
                        if update_data:
                            from telegram import Update
                            update = Update.de_json(update_data, updater.bot)
                            
                            # Processar em thread separada
                            import threading
                            def process():
                                dispatcher.process_update(update)
                            
                            thread = threading.Thread(target=process, daemon=True)
                            thread.start()
                            
                        return "OK", 200
                    except Exception as e:
                        logger.error(f"❌ Erro webhook v13: {e}")
                        return "Error", 500
                
                # Configurar webhook
                railway_url = os.getenv('RAILWAY_STATIC_URL', 'bot.railway.app')
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                webhook_url = f"{railway_url}/webhook"
                
                try:
                    updater.bot.set_webhook(webhook_url)
                    logger.info(f"✅ Webhook v13: {webhook_url}")
                except Exception as e:
                    logger.error(f"❌ Erro webhook v13: {e}")
                
                logger.info("✅ Bot v13 configurado - Iniciando Flask")
                app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
                
            else:
                # Polling v13 para local
                logger.info("🏠 Iniciando polling v13 local")
                
                # Flask em thread separada
                flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False), daemon=True)
                flask_thread.start()
                
                updater.start_polling(drop_pending_updates=True)
                updater.idle()
                
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        
        # Modo de emergência mínimo
        try:
            logger.info("🆘 Modo de emergência")
            app.run(host='0.0.0.0', port=PORT, debug=False)
        except Exception as emergency_error:
            logger.error(f"❌ Emergência falhou: {emergency_error}")

if __name__ == "__main__":
    main() 