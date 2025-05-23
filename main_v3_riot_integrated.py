#!/usr/bin/env python3
"""
Bot LoL Predictor V3 - RIOT API INTEGRATED
Sistema completo integrado com API oficial da Riot Games
Dados reais de times, standings, partidas e rankings
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import threading
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports condicionais para modo teste
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
    TELEGRAM_AVAILABLE = True
    logger.info("✅ Telegram libraries carregadas")
except ImportError:
    # Modo teste - criar classes mock
    logger.warning("⚠️ Telegram libraries não encontradas - modo teste ativo")
    TELEGRAM_AVAILABLE = False
    
    class Update:
        pass
    
    class InlineKeyboardButton:
        def __init__(self, text, callback_data=None):
            self.text = text
            self.callback_data = callback_data
    
    class InlineKeyboardMarkup:
        def __init__(self, keyboard):
            self.keyboard = keyboard
    
    class MockBuilder:
        def token(self, token):
            return self
        
        def build(self):
            return MockApplication()
    
    class MockApplication:
        def __init__(self):
            self.builder = MockBuilder
            self.bot = None
        
        @staticmethod
        def builder():
            return MockBuilder()
        
        def add_handler(self, handler):
            pass  # Mock method
        
        async def initialize(self):
            pass  # Mock method
        
        async def start(self):
            pass  # Mock method
        
        async def stop(self):
            pass  # Mock method
    
    class Application:
        builder = MockApplication.builder
    
    class CommandHandler:
        def __init__(self, command, callback):
            pass
    
    class MessageHandler:
        def __init__(self, filters, callback):
            pass
    
    class CallbackQueryHandler:
        def __init__(self, callback):
            pass
    
    class filters:
        class TEXT:
            def __and__(self, other):
                return self
            def __invert__(self):
                return self
        
        class COMMAND:
            pass
        
        TEXT = TEXT()
        COMMAND = COMMAND()

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
    logger.info("✅ Flask carregado")
except ImportError:
    logger.warning("⚠️ Flask não encontrado - modo teste ativo")
    FLASK_AVAILABLE = False
    Flask = None

# Importar sistema Riot API
try:
    from riot_api_integration import riot_prediction_system
    logger.info("✅ Sistema Riot API carregado")
except ImportError:
    logger.error("❌ Sistema Riot API não encontrado")
    riot_prediction_system = None

print("🚀 BOT LOL PREDICTOR V3 - RIOT API INTEGRATED")

# Configuração
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    if os.environ.get("TELEGRAM_TOKEN") != "test-token-for-local-testing":
        print("⚠️ TELEGRAM_TOKEN não configurado - usando modo teste")


class TelegramBotV3:
    """Bot Telegram V3 com integração Riot API"""
    
    def __init__(self):
        self.app = Application.builder().token(TOKEN).build()
        self.riot_system = riot_prediction_system
        self.initialization_status = "pending"
        self.setup_handlers()
        
        # Inicializar Application de forma síncrona
        if TELEGRAM_AVAILABLE and TOKEN:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.app.initialize())
                    logger.info("✅ Application Telegram inicializada")
                except Exception as e:
                    logger.error(f"❌ Erro ao inicializar Application: {e}")
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"❌ Erro na inicialização do loop: {e}")
    
    async def initialize_riot_system(self):
        """Inicializa sistema Riot API em background"""
        if self.riot_system:
            try:
                logger.info("🔄 Inicializando sistema Riot API...")
                success = await self.riot_system.initialize()
                
                if success:
                    self.initialization_status = "success"
                    logger.info("✅ Sistema Riot API inicializado com sucesso")
                else:
                    self.initialization_status = "fallback"
                    logger.info("⚠️ Sistema em modo fallback")
                    
            except Exception as e:
                logger.error(f"❌ Erro na inicialização: {e}")
                self.initialization_status = "error"
        else:
            self.initialization_status = "not_available"
    
    def setup_handlers(self):
        """Configura todos os handlers V3"""
        
        if not TELEGRAM_AVAILABLE:
            logger.info("⚠️ Telegram não disponível - handlers desabilitados")
            return
        
        # Comandos principais V3
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("predict", self.predict_command))
        self.app.add_handler(CommandHandler("ranking", self.ranking_command))
        self.app.add_handler(CommandHandler("live", self.live_command))
        # self.app.add_handler(CommandHandler("teams", self.teams_command))  # TODO: Re-implement
        # self.app.add_handler(CommandHandler("schedule", self.schedule_command))  # TODO: Re-implement  
        # self.app.add_handler(CommandHandler("stats", self.stats_command))  # TODO: Re-implement
        # self.app.add_handler(CommandHandler("status", self.status_command))  # TODO: Re-implement
        # self.app.add_handler(CommandHandler("update", self.update_command))  # TODO: Re-implement
        
        # Handler para mensagens de texto
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message_handler))
        
        # Handler para inline keyboards
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context):
        """Comando /start com integração Riot API"""
        user = update.effective_user
        
        # Status do sistema
        if self.initialization_status == "success":
            api_status = "🌐 **API Riot Games:** Conectada"
            data_quality = "📊 **Dados:** Oficiais e atualizados"
        elif self.initialization_status == "fallback":
            api_status = "🆘 **API Riot Games:** Modo Fallback"
            data_quality = "📊 **Dados:** Simulados (confiáveis)"
        else:
            api_status = "⚠️ **API Riot Games:** Inicializando..."
            data_quality = "📊 **Dados:** Aguardando conexão"
        
        welcome_msg = f"""🎮 **BEM-VINDO AO LOL PREDICTOR V3!**

Olá {user.first_name}! 

🚀 **NOVA VERSÃO COM RIOT API:**
{api_status}
{data_quality}

⚡ **RECURSOS V3:**
• Times e rankings oficiais
• Dados de partidas em tempo real
• Standings atualizados automaticamente
• Predições com base em performance real
• Cronograma de jogos oficial

🎯 **LIGAS SUPORTADAS:**
• 🇰🇷 LCK (Korea)
• 🇨🇳 LPL (China)  
• 🇪🇺 LEC (Europe)
• 🇺🇸 LCS (North America)

Use o menu abaixo ou digite /help para começar!"""

        # Inline keyboard com novas opções
        keyboard = [
            [
                InlineKeyboardButton("🔮 Predição Riot API", callback_data="riot_predict"),
                InlineKeyboardButton("📊 Rankings Oficiais", callback_data="riot_ranking")
            ],
            [
                InlineKeyboardButton("🔴 Partidas ao Vivo", callback_data="live_matches"),
                InlineKeyboardButton("📅 Cronograma", callback_data="schedule")
            ],
            [
                InlineKeyboardButton("🏆 Times por Liga", callback_data="teams_by_league"),
                InlineKeyboardButton("🌐 Status da API", callback_data="api_status")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_msg,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context):
        """Comando /help atualizado para V3"""
        help_text = """📚 **GUIA COMPLETO - LOL PREDICTOR V3**

🔮 **PREDIÇÕES (Com Riot API):**
• `/predict T1 vs G2` - Predição com dados oficiais
• `/predict T1 vs G2 bo5` - Com tipo de série
• `T1 vs G2` - Predição via texto simples

📊 **RANKINGS & TIMES (Dados Reais):**
• `/ranking` - Rankings oficiais globais
• `/ranking LCK` - Ranking por liga
• `/teams` - Lista times com dados oficiais
• `/teams LCK` - Times de uma liga específica

🔴 **PARTIDAS AO VIVO:**
• `/live` - Partidas acontecendo agora
• `/schedule` - Cronograma oficial

🌍 **REGIÕES & LIGAS:**
• `/region LCK` - Info da liga
• `/region LCK vs LPL` - Comparar ligas

⚡ **SISTEMA & API:**
• `/stats` - Estatísticas do sistema
• `/status` - Status da conexão Riot API
• `/update` - Forçar atualização dos dados

🎯 **EXEMPLOS COM DADOS REAIS:**
• `T1 vs JDG bo5` ➜ Com standings atuais
• `G2 vs FNC` ➜ Com records da temporada
• `Cloud9 vs Team Liquid` ➜ Performance real

💡 **NOVIDADES V3:**
• 🌐 Integração direta com Riot Games
• 📊 Dados oficiais de todas as partidas
• 🔄 Atualização automática de rankings
• 📈 Predições baseadas em performance real
• 🏆 Standings atualizados em tempo real

🚀 **POWERED BY RIOT GAMES API**"""

        await update.message.reply_text(help_text)
    
    async def predict_command(self, update: Update, context):
        """Comando /predict com Riot API"""
        if not context.args:
            await self.show_riot_prediction_menu(update)
            return
        
        # Parse dos argumentos
        args_text = " ".join(context.args)
        await self.handle_riot_prediction(update, args_text)
    
    async def show_riot_prediction_menu(self, update: Update):
        """Menu de predição com dados da Riot API"""
        
        api_status = "🌐 **PREDIÇÕES COM RIOT API**\n\n"
        
        if self.initialization_status == "success":
            api_status += "✅ Usando dados oficiais da Riot Games\n"
        elif self.initialization_status == "fallback":
            api_status += "⚠️ Usando dados de fallback (confiáveis)\n"
        else:
            api_status += "🔄 Inicializando conexão com Riot API...\n"
        
        text = api_status + """
**Formato:** `/predict TIME1 vs TIME2 [tipo]`
**Exemplo:** `/predict T1 vs G2 bo5`

**Vantagens V3:**
• Dados oficiais de standings
• Records reais da temporada
• Performance baseada em partidas oficiais
• Ratings calculados com base real"""

        keyboard = [
            [
                InlineKeyboardButton("🇰🇷 LCK Match", callback_data="predict_lck_riot"),
                InlineKeyboardButton("🇨🇳 LPL Match", callback_data="predict_lpl_riot")
            ],
            [
                InlineKeyboardButton("🇪🇺 LEC Match", callback_data="predict_lec_riot"),
                InlineKeyboardButton("🇺🇸 LCS Match", callback_data="predict_lcs_riot")
            ],
            [
                InlineKeyboardButton("🌍 Inter-Regional", callback_data="predict_inter_riot"),
                InlineKeyboardButton("🔄 Atualizar Dados", callback_data="update_riot_data")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def ranking_command(self, update: Update, context):
        """Comando /ranking com dados da Riot API"""
        
        if not self.riot_system:
            await update.message.reply_text("❌ Sistema Riot API não disponível")
            return
        
        region = context.args[0].upper() if context.args else None
        
        try:
            if region:
                teams = self.riot_system.get_teams_by_region(region)
                title = f"🏆 **RANKING {region} (Riot API)**"
            else:
                teams = self.riot_system.get_global_rankings(15)
                title = "🏆 **RANKING GLOBAL (Riot API)**"
            
            text = f"{title}\n\n"
            
            # Status dos dados
            if self.initialization_status == "success":
                text += "🌐 *Dados oficiais da Riot Games*\n\n"
            else:
                text += "🆘 *Dados de fallback*\n\n"
            
            for i, team in enumerate(teams[:15], 1):
                tier_emoji = self.get_tier_emoji(team.get('tier', 'C'))
                region_flag = self.get_region_flag(team.get('region', ''))
                
                # Mostrar record se disponível
                record_text = ""
                if 'record' in team and team['record'] and 'wins' in team['record']:
                    wins = team['record']['wins']
                    losses = team['record']['losses']
                    record_text = f" ({wins}W-{losses}L)"
                
                text += f"{i}. {tier_emoji} **{team['name']}** {region_flag}\n"
                text += f"   ⚡ {team.get('rating', 0)} pts | Tier {team.get('tier', 'C')}{record_text}\n\n"
            
            # Timestamp da última atualização
            if self.riot_system.last_update:
                last_update = self.riot_system.last_update.strftime("%H:%M")
                text += f"🕐 *Última atualização: {last_update}*"
        
        except Exception as e:
            logger.error(f"Erro no ranking: {e}")
            text = f"❌ Erro ao buscar ranking: {str(e)}"
        
        # Botões de navegação
        keyboard = [
            [
                InlineKeyboardButton("🇰🇷 LCK", callback_data="ranking_LCK_riot"),
                InlineKeyboardButton("🇨🇳 LPL", callback_data="ranking_LPL_riot")
            ],
            [
                InlineKeyboardButton("🇪🇺 LEC", callback_data="ranking_LEC_riot"),
                InlineKeyboardButton("🇺🇸 LCS", callback_data="ranking_LCS_riot")
            ],
            [
                InlineKeyboardButton("🌍 Global", callback_data="ranking_GLOBAL_riot"),
                InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_rankings")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def live_command(self, update: Update, context):
        """Comando /live para partidas ao vivo com interface interativa"""
        
        if not self.riot_system:
            await update.message.reply_text("❌ Sistema Riot API não disponível")
            return
        
        try:
            # Buscar partidas ao vivo formatadas para interface
            interactive_matches = await self.riot_system.get_live_matches_interactive()
            
            if not interactive_matches:
                text = """🔴 **PARTIDAS AO VIVO**

Não há partidas acontecendo neste momento.

🎮 Use `/schedule` para ver próximas partidas
📊 Use `/ranking` para ver standings atuais
💡 Use `/predict` para simular predições"""
                
                keyboard = [
                    [InlineKeyboardButton("📅 Ver Cronograma", callback_data="show_schedule")],
                    [InlineKeyboardButton("📊 Ver Rankings", callback_data="riot_ranking")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup)
                return
            
            # Mostrar partidas ao vivo com botões interativos
            text = f"🔴 **PARTIDAS AO VIVO ({len(interactive_matches)})**\n\n"
            text += "👆 **Clique em uma partida para ver:**\n"
            text += "• 🔮 Predição detalhada\n"
            text += "• ⏰ Melhor momento para apostar\n"
            text += "• 📊 Percentuais em tempo real\n"
            text += "• 💰 Análise de odds e value bets\n\n"
            
            # Adicionar info básica das partidas
            for i, match in enumerate(interactive_matches[:5], 1):  # Mostrar até 5 partidas
                state_emoji = {
                    'unstarted': '⏳',
                    'inprogress': '🔴',
                    'completed': '✅'
                }.get(match['state'], '❓')
                
                text += f"{state_emoji} **{match['league']}**\n"
                text += f"⚔️ {match['team1']['code']} vs {match['team2']['code']}\n"
                text += f"📊 Rating: {match['team1']['rating']} vs {match['team2']['rating']}\n\n"
            
            # Criar botões para cada partida
            keyboard = []
            for match in interactive_matches[:6]:  # Máximo 6 partidas
                button_text = f"📊 {match['team1']['code']} vs {match['team2']['code']}"
                callback_data = f"live_analyze_{match['id']}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Botões adicionais
            keyboard.append([
                InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_live"),
                InlineKeyboardButton("📅 Cronograma", callback_data="show_schedule")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup)
        
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            text = f"❌ Erro ao buscar partidas ao vivo: {str(e)}"
            await update.message.reply_text(text)
    
    async def analyze_live_match_callback(self, query, match_id: str):
        """Callback para análise detalhada de partida ao vivo"""
        
        try:
            # Mostrar loading
            await query.edit_message_text("🔄 Analisando partida ao vivo...")
            
            # Fazer análise completa
            analysis = await self.riot_system.analyze_live_match_detailed(match_id)
            
            if 'error' in analysis:
                await query.edit_message_text(f"❌ {analysis['error']}")
                return
            
            # Formatar resultado
            text = self._format_live_analysis(analysis)
            
            # Botões de ação
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Atualizar Análise", callback_data=f"live_analyze_{match_id}"),
                    InlineKeyboardButton("📊 Ver Odds", callback_data=f"live_odds_{match_id}")
                ],
                [
                    InlineKeyboardButton("⏰ Timing Detalhes", callback_data=f"live_timing_{match_id}"),
                    InlineKeyboardButton("📈 Momentum", callback_data=f"live_momentum_{match_id}")
                ],
                [
                    InlineKeyboardButton("🔙 Voltar às Partidas", callback_data="refresh_live"),
                    InlineKeyboardButton("🔮 Nova Predição", callback_data="riot_predict")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro na análise de partida: {e}")
            await query.edit_message_text(f"❌ Erro na análise: {str(e)}")
    
    def _format_live_analysis(self, analysis: Dict) -> str:
        """Formata análise completa de partida ao vivo"""
        
        team1 = analysis['teams']['team1']
        team2 = analysis['teams']['team2']
        prediction = analysis['prediction']
        timing = analysis['timing_analysis']
        momentum = analysis['momentum']
        odds = analysis['live_odds']
        
        # Header
        text = f"🔴 **ANÁLISE AO VIVO - {analysis['league']}**\n\n"
        
        # Teams e predição
        text += f"⚔️ **{team1['name']}** vs **{team2['name']}**\n\n"
        
        # Probabilidades principais
        prob1 = odds['team1']['probability']
        prob2 = odds['team2']['probability']
        text += f"📊 **PROBABILIDADES EM TEMPO REAL:**\n"
        text += f"• {team1['name']}: **{prob1:.1f}%**\n"
        text += f"• {team2['name']}: **{prob2:.1f}%**\n\n"
        
        # Vencedor previsto
        winner = prediction['predicted_winner']
        confidence = prediction['confidence_level']
        text += f"🏆 **VENCEDOR PREVISTO:** {winner}\n"
        text += f"🔥 **CONFIANÇA:** {confidence} ({prediction['confidence']:.1%})\n\n"
        
        # Timing de apostas
        text += f"⏰ **TIMING DE APOSTAS:**\n"
        text += f"• **Status:** {timing['recommendation']}\n"
        text += f"• **Razão:** {timing['reasoning']}\n"
        text += f"• **Risco:** {timing['risk_level']}\n\n"
        
        # Momentum
        text += f"📈 **MOMENTUM ATUAL:**\n"
        text += f"• **Direção:** {momentum['direction']}\n"
        text += f"• **Intensidade:** {momentum['strength']}\n\n"
        
        # Odds e value
        text += f"💰 **ODDS E VALUE BETS:**\n"
        text += f"• {team1['name']}: {odds['team1']['decimal_odds']} | {odds['team1']['value_rating']}\n"
        text += f"• {team2['name']}: {odds['team2']['decimal_odds']} | {odds['team2']['value_rating']}\n\n"
        
        # Recomendação final
        if timing['game_phase'] == 'pre_game':
            text += f"💡 **RECOMENDAÇÃO:** Momento ideal para apostar!\n"
        elif timing['game_phase'] == 'early_game':
            text += f"💡 **RECOMENDAÇÃO:** Ainda é bom momento para apostar.\n"
        elif timing['game_phase'] == 'mid_game':
            text += f"⚠️ **RECOMENDAÇÃO:** Aposte com cautela, jogo pode virar.\n"
        else:
            text += f"❌ **RECOMENDAÇÃO:** Evite apostar neste momento.\n"
        
        text += f"\n🕐 *Atualizado: {datetime.now().strftime('%H:%M:%S')}*"
        
        return text
    
    async def show_live_odds_callback(self, query, match_id: str):
        """Callback para mostrar odds detalhadas"""
        
        try:
            await query.edit_message_text("🔄 Calculando odds...")
            
            analysis = await self.riot_system.analyze_live_match_detailed(match_id)
            
            if 'error' in analysis:
                await query.edit_message_text(f"❌ {analysis['error']}")
                return
            
            odds = analysis['live_odds']
            team1 = analysis['teams']['team1']
            team2 = analysis['teams']['team2']
            timing = analysis['timing_analysis']
            
            text = f"💰 **ODDS EM TEMPO REAL**\n\n"
            
            text += f"🎯 **{team1['name']}**\n"
            text += f"• Probabilidade: **{odds['team1']['probability']:.1f}%**\n"
            text += f"• Odds: **{odds['team1']['decimal_odds']}**\n"
            text += f"• Value: {odds['team1']['value_rating']}\n\n"
            
            text += f"🎯 **{team2['name']}**\n"
            text += f"• Probabilidade: **{odds['team2']['probability']:.1f}%**\n"
            text += f"• Odds: **{odds['team2']['decimal_odds']}**\n"
            text += f"• Value: {odds['team2']['value_rating']}\n\n"
            
            text += f"📊 **ANÁLISE DE MERCADO:**\n"
            text += f"• Volatilidade: {odds['volatility']:.1%}\n"
            text += f"• Confiança: {odds['market_confidence']:.1%}\n"
            text += f"• Fase: {timing['game_phase'].replace('_', ' ').title()}\n\n"
            
            text += f"💡 **COMO INTERPRETAR:**\n"
            text += f"🟢 ALTA VALUE = Aposta com muito valor\n"
            text += f"🟡 BOA VALUE = Aposta favorável\n"
            text += f"⚪ NEUTRA = Odds equilibradas\n"
            text += f"🔴 SEM VALUE = Evitar aposta\n"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Voltar à Análise", callback_data=f"live_analyze_{match_id}")],
                [InlineKeyboardButton("⏰ Ver Timing", callback_data=f"live_timing_{match_id}")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar odds: {e}")
            await query.edit_message_text(f"❌ Erro: {str(e)}")
    
    async def show_live_timing_callback(self, query, match_id: str):
        """Callback para mostrar análise de timing detalhada"""
        
        try:
            await query.edit_message_text("🔄 Analisando timing...")
            
            analysis = await self.riot_system.analyze_live_match_detailed(match_id)
            
            if 'error' in analysis:
                await query.edit_message_text(f"❌ {analysis['error']}")
                return
            
            timing = analysis['timing_analysis']
            
            text = f"⏰ **ANÁLISE DE TIMING PARA APOSTAS**\n\n"
            
            text += f"🎮 **FASE ATUAL:** {timing['game_phase'].replace('_', ' ').title()}\n\n"
            
            text += f"📋 **RECOMENDAÇÃO:**\n"
            text += f"{timing['recommendation']}\n\n"
            
            text += f"💭 **JUSTIFICATIVA:**\n"
            text += f"{timing['reasoning']}\n\n"
            
            text += f"⚖️ **ANÁLISE DE RISCO:**\n"
            text += f"• Nível: {timing['risk_level']}\n"
            text += f"• Confiança ajustada: {timing['adjusted_confidence']:.1%}\n"
            text += f"• Multiplicador: {timing['multiplier']:.2f}x\n\n"
            
            text += f"📚 **EXPLICAÇÃO DAS FASES:**\n\n"
            text += f"⭐ **PRÉ-JOGO:** Melhor momento, odds estáveis\n"
            text += f"✅ **EARLY GAME:** Ainda confiável, predições válidas\n"
            text += f"⚠️ **MID GAME:** Cautela, mudanças táticas\n"
            text += f"❌ **LATE GAME:** Arriscado, alta volatilidade\n"
            text += f"🚫 **PÓS-JOGO:** Partida encerrada\n\n"
            
            # Dica baseada na fase atual
            if timing['game_phase'] == 'pre_game':
                text += f"💡 **DICA:** Este é o momento perfeito para apostar! As predições são mais confiáveis antes do jogo começar."
            elif timing['game_phase'] == 'early_game':
                text += f"💡 **DICA:** Ainda é um bom momento. O jogo está no início e as predições ainda são válidas."
            elif timing['game_phase'] == 'mid_game':
                text += f"💡 **DICA:** Cuidado! O mid game pode ter viradas inesperadas. Aposte apenas se tiver muita confiança."
            else:
                text += f"💡 **DICA:** Evite apostar agora. O late game é muito imprevisível no LoL."
            
            keyboard = [
                [InlineKeyboardButton("🔙 Voltar à Análise", callback_data=f"live_analyze_{match_id}")],
                [InlineKeyboardButton("📈 Ver Momentum", callback_data=f"live_momentum_{match_id}")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar timing: {e}")
            await query.edit_message_text(f"❌ Erro: {str(e)}")
    
    async def show_live_momentum_callback(self, query, match_id: str):
        """Callback para mostrar análise de momentum"""
        
        try:
            await query.edit_message_text("🔄 Analisando momentum...")
            
            analysis = await self.riot_system.analyze_live_match_detailed(match_id)
            
            if 'error' in analysis:
                await query.edit_message_text(f"❌ {analysis['error']}")
                return
            
            momentum = analysis['momentum']
            team1 = analysis['teams']['team1']
            team2 = analysis['teams']['team2']
            
            text = f"📈 **ANÁLISE DE MOMENTUM**\n\n"
            
            text += f"🎯 **MOMENTUM ATUAL:**\n"
            text += f"{momentum['direction']}\n"
            text += f"Intensidade: **{momentum['strength']}**\n\n"
            
            text += f"📊 **DISTRIBUIÇÃO:**\n"
            team1_momentum = momentum['team1_momentum'] * 100
            team2_momentum = momentum['team2_momentum'] * 100
            text += f"• {team1['name']}: {team1_momentum:.1f}%\n"
            text += f"• {team2['name']}: {team2_momentum:.1f}%\n\n"
            
            # Barra visual de momentum
            text += f"📈 **MOMENTUM VISUAL:**\n"
            total_bars = 10
            team1_bars = int(momentum['team1_momentum'] * total_bars)
            team2_bars = total_bars - team1_bars
            
            momentum_bar = "🟢" * team1_bars + "🔴" * team2_bars
            text += f"{momentum_bar}\n"
            text += f"🟢 {team1['name']} | 🔴 {team2['name']}\n\n"
            
            text += f"⚡ **IMPACTO NA CONFIANÇA:**\n"
            confidence_impact = momentum['confidence_impact']
            if confidence_impact > 0.05:
                text += f"Alto (+{confidence_impact:.1%}) - Momentum claro\n"
            elif confidence_impact > 0.02:
                text += f"Moderado (+{confidence_impact:.1%}) - Ligeira vantagem\n"
            else:
                text += f"Baixo (+{confidence_impact:.1%}) - Jogo equilibrado\n"
            
            text += f"\n💡 **O QUE É MOMENTUM:**\n"
            text += f"Momentum representa a tendência atual da partida baseada em:\n"
            text += f"• Performance recente dos times\n"
            text += f"• Situação atual do jogo\n"
            text += f"• Fatores psicológicos\n"
            text += f"• Controle de objetivos\n\n"
            
            text += f"🔄 *Momentum atualiza em tempo real durante a partida*"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Voltar à Análise", callback_data=f"live_analyze_{match_id}")],
                [InlineKeyboardButton("💰 Ver Odds", callback_data=f"live_odds_{match_id}")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar momentum: {e}")
            await query.edit_message_text(f"❌ Erro: {str(e)}")
    
    async def text_message_handler(self, update: Update, context):
        """Handler para mensagens de texto (predições com Riot API)"""
        text = update.message.text.strip()
        
        # Verificar se é formato de predição
        if " vs " in text.lower():
            await self.handle_riot_prediction(update, text)
        else:
            # Mensagem genérica
            await update.message.reply_text(
                "💡 **Para fazer uma predição V3:**\n"
                "`TIME1 vs TIME2` ou `/predict TIME1 vs TIME2`\n\n"
                "**Exemplos com dados Riot API:**\n"
                "• `T1 vs G2 bo3` - Com dados oficiais\n"
                "• `JDG vs TES` - Standings atuais LPL\n"
                "• `Cloud9 vs Team Liquid` - Records reais\n\n"
                "Digite `/help` para ver todos os comandos V3!")
    
    async def handle_riot_prediction(self, update, text):
        """Processa predição com dados da Riot API"""
        try:
            # Parse do texto
            lower_text = text.lower()
            
            if " vs " not in lower_text:
                await update.message.reply_text("❌ Formato inválido! Use: `TIME1 vs TIME2`")
                return
            
            # Extrair times e tipo de série
            parts = lower_text.split()
            vs_index = parts.index("vs")
            
            team1 = " ".join(parts[:vs_index])
            remaining = parts[vs_index + 1:]
            
            # Verificar se tem tipo de série no final
            match_types = ["bo1", "bo3", "bo5"]
            match_type = "bo1"
            
            if remaining and remaining[-1] in match_types:
                match_type = remaining[-1]
                team2 = " ".join(remaining[:-1])
            else:
                team2 = " ".join(remaining)
            
            # Fazer predição com sistema Riot API
            if not self.riot_system:
                await update.message.reply_text("❌ Sistema Riot API não disponível")
                return
            
            await update.message.reply_text("🔮 Analisando com dados da Riot API...")
            
            result = await self.riot_system.predict_match(team1, team2, match_type)
            
            if 'error' in result:
                await update.message.reply_text(f"❌ {result['error']}")
                return
            
            # Formatear resultado V3
            team1_data = result['team1']
            team2_data = result['team2']
            
            prob1 = result['team1_probability'] * 100
            prob2 = result['team2_probability'] * 100
            
            # Emojis baseados na probabilidade
            if prob1 > prob2:
                winner_emoji = "🏆"
                loser_emoji = "🥈"
            else:
                winner_emoji = "🥈"
                loser_emoji = "🏆"
            
            confidence_emoji = {
                "Muito Alta": "🔥",
                "Alta": "✅", 
                "Média": "⚠️",
                "Baixa": "❓",
                "Muito Baixa": "⚡"
            }.get(result['confidence_level'], "🎯")
            
            # Status dos dados
            data_source = "🌐 **Dados Riot API**" if result.get('data_source') == 'riot_api' else "🆘 **Modo Fallback**"
            
            # Resultado principal V3
            main_text = f"""🎮 **PREDIÇÃO V3 #{result['prediction_id']}**

{data_source}

{winner_emoji if prob1 > prob2 else loser_emoji} **{team1_data['name']}** vs **{team2_data['name']}** {loser_emoji if prob1 > prob2 else winner_emoji}

📊 **PROBABILIDADES:**
• {team1_data['name']}: {prob1:.1f}%
• {team2_data['name']}: {prob2:.1f}%

🎯 **VENCEDOR PREVISTO:** {result['predicted_winner']}
{confidence_emoji} **CONFIANÇA:** {result['confidence_level']} ({result['confidence']:.1%})

📈 **DETALHES V3:**
• Tipo: {match_type.upper()}
• Tier: {team1_data.get('tier', 'N/A')} vs {team2_data.get('tier', 'N/A')}
• Região: {team1_data.get('region', 'N/A')} vs {team2_data.get('region', 'N/A')}"""

            # Adicionar análise
            if 'analysis' in result:
                analysis_text = f"\n\n{result['analysis']}"
                full_text = main_text + analysis_text
            else:
                full_text = main_text
            
            # Botões para ações adicionais V3
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Nova Predição", callback_data="riot_predict"),
                    InlineKeyboardButton("📊 Rankings V3", callback_data="riot_ranking")
                ],
                [
                    InlineKeyboardButton("🔴 Partidas ao Vivo", callback_data="live_matches"),
                    InlineKeyboardButton("🌐 Status API", callback_data="api_status")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                full_text,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro na predição V3: {e}")
            await update.message.reply_text(f"❌ Erro ao processar predição V3: {str(e)}")
    
    async def button_callback(self, update: Update, context):
        """Handler para inline keyboard callbacks V3"""
        query = update.callback_query
        
        data = query.data
        
        # Callbacks de análise ao vivo
        if data.startswith("live_analyze_"):
            match_id = data.replace("live_analyze_", "")
            await self.analyze_live_match_callback(query, match_id)
        elif data.startswith("live_odds_"):
            match_id = data.replace("live_odds_", "")
            await self.show_live_odds_callback(query, match_id)
        elif data.startswith("live_timing_"):
            match_id = data.replace("live_timing_", "")
            await self.show_live_timing_callback(query, match_id)
        elif data.startswith("live_momentum_"):
            match_id = data.replace("live_momentum_", "")
            await self.show_live_momentum_callback(query, match_id)
        elif data == "refresh_live":
            await self.refresh_live_matches_callback(query)
        
        # Callbacks existentes
        elif data == "riot_predict":
            await self.show_riot_prediction_menu(query)
        elif data == "riot_ranking":
            await self.show_riot_ranking_callback(query)
        elif data == "live_matches":
            await self.show_live_matches_callback(query)
        elif data == "api_status":
            await self.show_api_status_callback(query)
        elif data == "force_update":
            await self.force_update_callback(query)
        elif data.startswith("ranking_") and data.endswith("_riot"):
            region = data.split("_")[1]
            await self.show_ranking_by_region_riot(query, region)
        elif data.startswith("teams_") and data.endswith("_riot"):
            region = data.split("_")[1]
            await self.show_teams_by_region_riot(query, region)
    
    async def refresh_live_matches_callback(self, query):
        """Callback para atualizar lista de partidas ao vivo"""
        
        try:
            await query.edit_message_text("🔄 Atualizando partidas ao vivo...")
            
            # Buscar partidas atualizadas
            interactive_matches = await self.riot_system.get_live_matches_interactive()
            
            if not interactive_matches:
                text = """🔴 **PARTIDAS AO VIVO**

Não há partidas acontecendo neste momento.

🎮 Use `/schedule` para ver próximas partidas
📊 Use `/ranking` para ver standings atuais"""
                
                keyboard = [
                    [InlineKeyboardButton("📅 Ver Cronograma", callback_data="show_schedule")],
                    [InlineKeyboardButton("📊 Ver Rankings", callback_data="riot_ranking")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup)
                return
            
            # Mesmo formato do comando /live
            text = f"🔴 **PARTIDAS AO VIVO ({len(interactive_matches)})**\n\n"
            text += "👆 **Clique em uma partida para ver:**\n"
            text += "• 🔮 Predição detalhada\n"
            text += "• ⏰ Melhor momento para apostar\n"
            text += "• 📊 Percentuais em tempo real\n"
            text += "• 💰 Análise de odds e value bets\n\n"
            
            for i, match in enumerate(interactive_matches[:5], 1):
                state_emoji = {
                    'unstarted': '⏳',
                    'inprogress': '🔴',
                    'completed': '✅'
                }.get(match['state'], '❓')
                
                text += f"{state_emoji} **{match['league']}**\n"
                text += f"⚔️ {match['team1']['code']} vs {match['team2']['code']}\n"
                text += f"📊 Rating: {match['team1']['rating']} vs {match['team2']['rating']}\n\n"
            
            keyboard = []
            for match in interactive_matches[:6]:
                button_text = f"📊 {match['team1']['code']} vs {match['team2']['code']}"
                callback_data = f"live_analyze_{match['id']}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            keyboard.append([
                InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_live"),
                InlineKeyboardButton("📅 Cronograma", callback_data="show_schedule")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar partidas: {e}")
            await query.edit_message_text(f"❌ Erro ao atualizar: {str(e)}")
    
    # Métodos auxiliares
    def get_tier_emoji(self, tier: str) -> str:
        """Retorna emoji baseado no tier"""
        emojis = {
            'S+': '🌟', 'S': '🏆', 'S-': '⭐',
            'A+': '🥇', 'A': '🥈', 'A-': '🥉',
            'B+': '🎖️', 'B': '🏅', 'B-': '🎗️',
            'C+': '🎯', 'C': '🎮'
        }
        return emojis.get(tier, '🎮')
    
    def get_region_flag(self, region: str) -> str:
        """Retorna flag baseada na região"""
        flags = {
            'LCK': '🇰🇷', 'LPL': '🇨🇳', 
            'LEC': '🇪🇺', 'LCS': '🇺🇸'
        }
        return flags.get(region, '🌍')
    
    def get_api_status_text(self) -> str:
        """Retorna texto do status da API"""
        if self.initialization_status == "success":
            return "✅ Conectada"
        elif self.initialization_status == "fallback":
            return "⚠️ Modo Fallback"
        elif self.initialization_status == "error":
            return "❌ Erro de Conexão"
        else:
            return "🔄 Inicializando..."
    
    def get_initialization_text(self) -> str:
        """Retorna texto do status de inicialização"""
        if self.initialization_status == "success":
            return "✅ Completa com Riot API"
        elif self.initialization_status == "fallback":
            return "⚠️ Modo seguro ativo"
        elif self.initialization_status == "error":
            return "❌ Falha na conexão"
        else:
            return "🔄 Em andamento..."
    
    # Callback methods específicos para V3
    async def show_riot_ranking_callback(self, query):
        """Callback para mostrar ranking Riot"""
        # Implementar ranking callback
        pass
    
    async def show_live_matches_callback(self, query):
        """Callback para mostrar partidas ao vivo"""
        # Implementar live matches callback
        pass
    
    async def show_api_status_callback(self, query):
        """Callback para mostrar status da API"""
        # Implementar API status callback
        pass
    
    async def force_update_callback(self, query):
        """Callback para forçar atualização"""
        # Implementar force update callback
        pass


# Flask App para webhook
if FLASK_AVAILABLE:
    app = Flask(__name__)
else:
    app = None

# Instância do bot V3 - DEVE VIR ANTES da criação do Flask app
telegram_bot_v3 = TelegramBotV3()

def create_flask_app():
    """Cria app Flask se disponível"""
    if not FLASK_AVAILABLE:
        logger.warning("⚠️ Flask não disponível - webhook desabilitado")
        return None
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return jsonify({
            "status": "online",
            "version": "3.0-riot-integrated",
            "features": {
                "riot_api": riot_prediction_system is not None,
                "live_betting": True,
                "timing_analysis": True,
                "value_betting": True,
                "momentum_tracking": True
            },
            "telegram_available": TELEGRAM_AVAILABLE,
            "api_status": "connected" if riot_prediction_system else "unavailable"
        })
    
    @app.route('/health')
    def health():
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "telegram": TELEGRAM_AVAILABLE,
                "riot_api": riot_prediction_system is not None,
                "flask": True
            }
        }
        
        if riot_prediction_system:
            stats = riot_prediction_system.get_system_stats()
            health_status["riot_stats"] = stats
        
        return jsonify(health_status)
    
    if TELEGRAM_AVAILABLE:
        @app.route('/webhook', methods=['POST'])
        def webhook():
            try:
                # Verificar se temos dados
                json_data = request.get_json()
                if not json_data:
                    logger.error("❌ Webhook: Dados JSON vazios")
                    return "NO DATA", 400
                
                # Verificar se o bot está disponível
                if not telegram_bot_v3 or not telegram_bot_v3.app or not telegram_bot_v3.app.bot:
                    logger.error("❌ Webhook: Bot não disponível")
                    return "BOT NOT AVAILABLE", 500
                
                # Processar update
                logger.info(f"📨 Webhook: Processando update {json_data.get('update_id', 'unknown')}")
                
                update = Update.de_json(json_data, telegram_bot_v3.app.bot)
                
                # Processamento simplificado sem threading
                try:
                    # Usar asyncio.run que cria e gerencia o loop automaticamente
                    asyncio.run(telegram_bot_v3.app.process_update(update))
                    logger.info("✅ Webhook: Update processado com sucesso")
                    return "OK"
                except Exception as e:
                    logger.error(f"❌ Webhook: Erro no processamento: {e}")
                    return f"ERROR: {str(e)}", 500
                
            except Exception as e:
                logger.error(f"Erro no webhook: {e}")
                return "ERROR", 500
    
    return app

# Instanciar app
if FLASK_AVAILABLE:
    app = create_flask_app()

if __name__ == "__main__":
    print("🚀 Iniciando LOL Predictor V3 - Riot API Integration...")
    
    # Inicializar sistema Riot em background
    async def init_riot_system():
        await telegram_bot_v3.initialize_riot_system()
    
    # Executar inicialização em thread separada
    def run_init():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(init_riot_system())
        loop.close()
    
    init_thread = threading.Thread(target=run_init)
    init_thread.start()
    
    print("🌐 Sistema Riot API inicializando em background...")
    print("🎮 Interface Telegram com dados reais ativa")
    print("⚡ Bot V3 pronto para uso!")
    
    # Iniciar Flask
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port) 