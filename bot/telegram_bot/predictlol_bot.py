"""
PredictLoL Telegram Bot
Bot integrado com sistema de apostas pessoais e previsões pós-draft
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

logger = logging.getLogger(__name__)

class PredictLoLTelegramBot:
    """Bot Telegram PredictLoL integrado"""
    
    def __init__(self, token: str, personal_betting=None):
        self.token = token
        self.personal_betting = personal_betting
        self.app = None
        self.is_running = False
        
        # Usuários autorizados (você pode adicionar mais)
        self.authorized_users = set()
        
        logger.info("🤖 PredictLoL Telegram Bot criado")
    
    async def initialize(self):
        """Inicializa o bot"""
        try:
            # Criar aplicação
            self.app = Application.builder().token(self.token).build()
            
            # Registrar handlers
            await self._register_handlers()
            
            logger.info("✅ Bot Telegram inicializado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar bot: {e}")
            raise
    
    async def _register_handlers(self):
        """Registra todos os handlers do bot"""
        
        # Comandos principais
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("help", self._help_command))
        self.app.add_handler(CommandHandler("menu", self._menu_command))
        
        # Sistema de apostas pessoais
        self.app.add_handler(CommandHandler("bankroll", self._bankroll_command))
        self.app.add_handler(CommandHandler("analisar", self._analisar_command))
        self.app.add_handler(CommandHandler("apostar", self._apostar_command))
        self.app.add_handler(CommandHandler("tracker", self._tracker_command))
        self.app.add_handler(CommandHandler("dashboard", self._dashboard_command))
        
        # Previsões pós-draft
        self.app.add_handler(CommandHandler("prever", self._prever_command))
        
        # Callback queries (botões)
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Mensagens de texto
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
        
        logger.info("✅ Handlers registrados")
    
    async def start(self):
        """Inicia o bot"""
        if self.is_running:
            return
        
        try:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            self.is_running = True
            logger.info("🚀 Bot iniciado e fazendo polling")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar bot: {e}")
            raise
    
    async def stop(self):
        """Para o bot"""
        if not self.is_running:
            return
        
        try:
            if self.app and self.app.updater:
                await self.app.updater.stop()
            if self.app:
                await self.app.stop()
                await self.app.shutdown()
            
            self.is_running = False
            logger.info("🛑 Bot parado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar bot: {e}")
    
    # === COMANDOS PRINCIPAIS ===
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user = update.effective_user
        
        welcome_text = f"""
🎯 **PredictLoL - Sistema de Apostas Pessoais**

Olá {user.first_name}! 

Este bot te ajuda com:
• 💰 **Gestão de Bankroll** - Kelly Criterion + Risk Management
• 📊 **Análise de Value** - Comparação de odds + EV
• 📈 **Tracker de Apostas** - Performance tracking completo
• 🎮 **Previsões Pós-Draft** - Análise de composições

Use /menu para ver todas as opções ou /help para ajuda detalhada.
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")],
            [InlineKeyboardButton("💰 Bankroll", callback_data="bankroll_menu")],
            [InlineKeyboardButton("🎮 Análise", callback_data="analysis_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_text = """
🔧 **Comandos Disponíveis:**

**💰 Gestão de Bankroll:**
• `/bankroll` - Status do bankroll atual
• `/apostar <valor> <odds> <descrição>` - Registrar aposta

**📊 Análise de Value:**
• `/analisar <time1> vs <time2>` - Análise completa de match
• `/prever <time1> vs <time2>` - Previsão pós-draft

**📈 Performance:**
• `/tracker` - Dashboard de performance
• `/dashboard` - Estatísticas detalhadas

**🎮 Previsões:**
• `/prever <match>` - Análise de composição pós-draft

**⚙️ Geral:**
• `/menu` - Menu principal
• `/help` - Esta ajuda

**Exemplo de uso:**
`/apostar 50 1.85 T1 vs Gen.G - T1 vencer`
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def _menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /menu"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Bankroll", callback_data="bankroll_menu"),
                InlineKeyboardButton("📊 Análise", callback_data="analysis_menu")
            ],
            [
                InlineKeyboardButton("📈 Tracker", callback_data="tracker_menu"),
                InlineKeyboardButton("🎮 Previsões", callback_data="predictions_menu")
            ],
            [
                InlineKeyboardButton("⚙️ Configurações", callback_data="settings_menu"),
                InlineKeyboardButton("❓ Ajuda", callback_data="help_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎯 **Menu Principal PredictLoL**\n\nEscolha uma opção:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # === SISTEMA DE APOSTAS ===
    
    async def _bankroll_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /bankroll"""
        if not self.personal_betting:
            await update.message.reply_text("❌ Sistema de apostas não disponível")
            return
        
        try:
            # Obter status do bankroll
            bankroll_status = self.personal_betting.bankroll_manager.get_bankroll_status()
            
            status_text = f"""
💰 **Status do Bankroll**

**Saldo Atual:** R$ {bankroll_status['current_balance']:.2f}
**Saldo Inicial:** R$ {bankroll_status['initial_balance']:.2f}
**Lucro/Prejuízo:** R$ {bankroll_status['profit_loss']:.2f}
**ROI:** {bankroll_status['roi']:.2f}%

**Configurações de Risco:**
• Nível: {bankroll_status['risk_level']}
• Limite Diário: R$ {bankroll_status['daily_limit']:.2f}
• Apostado Hoje: R$ {bankroll_status['daily_bet']:.2f}

**Estatísticas:**
• Total de Apostas: {bankroll_status['total_bets']}
• Apostas Ganhas: {bankroll_status['won_bets']}
• Win Rate: {bankroll_status['win_rate']:.1f}%
            """
            
            keyboard = [
                [InlineKeyboardButton("📊 Fazer Análise", callback_data="start_analysis")],
                [InlineKeyboardButton("📈 Ver Tracker", callback_data="show_tracker")],
                [InlineKeyboardButton("⚙️ Configurar", callback_data="bankroll_settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                status_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando bankroll: {e}")
            await update.message.reply_text(f"❌ Erro ao obter status: {e}")
    
    async def _analisar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /analisar"""
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "📊 **Análise de Match**\n\n"
                "Use: `/analisar T1 vs Gen.G`\n"
                "ou: `/analisar T1 Gen.G`",
                parse_mode='Markdown'
            )
            return
        
        # Processar argumentos
        match_text = " ".join(args)
        teams = self._extract_teams(match_text)
        
        if len(teams) < 2:
            await update.message.reply_text(
                "❌ Formato inválido. Use: `/analisar Time1 vs Time2`",
                parse_mode='Markdown'
            )
            return
        
        team1, team2 = teams[0], teams[1]
        
        try:
            await update.message.reply_text(f"🔍 Analisando {team1} vs {team2}...")
            
            # Análise com value analyzer
            analysis = self.personal_betting.value_analyzer.analyze_match(
                team1=team1,
                team2=team2,
                bookmaker_odds={
                    'bet365': {'team1': 1.80, 'team2': 2.00},
                    'betfair': {'team1': 1.85, 'team2': 1.95}
                }
            )
            
            result_text = f"""
📊 **Análise: {team1} vs {team2}**

**Avaliação dos Times:**
• {team1}: {analysis['team1_rating']:.1f}/10
• {team2}: {analysis['team2_rating']:.1f}/10

**Probabilidades:**
• {team1}: {analysis['team1_probability']:.1f}%
• {team2}: {analysis['team2_probability']:.1f}%

**Melhores Odds:**
• {team1}: {analysis['best_odds_team1']:.2f}
• {team2}: {analysis['best_odds_team2']:.2f}

**Expected Value:**
• {team1}: {analysis['ev_team1']:.2f}%
• {team2}: {analysis['ev_team2']:.2f}%

**Recomendação:** {analysis['recommendation']}
            """
            
            keyboard = []
            if analysis['has_value']:
                keyboard.append([
                    InlineKeyboardButton(
                        f"💰 Apostar em {analysis['best_bet']}", 
                        callback_data=f"bet_{analysis['best_bet']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🎯 Nova Análise", callback_data="new_analysis")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                result_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            await update.message.reply_text(f"❌ Erro na análise: {e}")
    
    async def _apostar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /apostar"""
        args = context.args
        
        if len(args) < 3:
            await update.message.reply_text(
                "💰 **Registrar Aposta**\n\n"
                "Use: `/apostar <valor> <odds> <descrição>`\n\n"
                "Exemplo: `/apostar 50 1.85 T1 vs Gen.G - T1 vencer`",
                parse_mode='Markdown'
            )
            return
        
        try:
            amount = float(args[0])
            odds = float(args[1])
            description = " ".join(args[2:])
            
            # Registrar aposta
            bet_result = self.personal_betting.bankroll_manager.place_bet(
                amount=amount,
                odds=odds,
                description=description
            )
            
            if bet_result['success']:
                result_text = f"""
✅ **Aposta Registrada!**

**Detalhes:**
• Valor: R$ {amount:.2f}
• Odds: {odds:.2f}
• Descrição: {description}

**Kelly Fraction:** {bet_result['kelly_fraction']:.3f}
**Tamanho Sugerido:** R$ {bet_result['suggested_amount']:.2f}
**Retorno Potencial:** R$ {bet_result['potential_return']:.2f}

**Novo Saldo:** R$ {bet_result['new_balance']:.2f}
                """
                
                keyboard = [
                    [InlineKeyboardButton("📊 Ver Dashboard", callback_data="show_dashboard")],
                    [InlineKeyboardButton("💰 Nova Aposta", callback_data="new_bet")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
            else:
                result_text = f"❌ **Erro:** {bet_result['error']}"
                reply_markup = None
            
            await update.message.reply_text(
                result_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except ValueError:
            await update.message.reply_text("❌ Valores inválidos. Use números para valor e odds.")
        except Exception as e:
            logger.error(f"Erro ao registrar aposta: {e}")
            await update.message.reply_text(f"❌ Erro: {e}")
    
    async def _tracker_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /tracker"""
        if not self.personal_betting:
            await update.message.reply_text("❌ Sistema não disponível")
            return
        
        try:
            # Gerar dashboard
            dashboard = self.personal_betting.betting_tracker.generate_dashboard()
            
            # Converter para texto do Telegram
            dashboard_text = f"""
📈 **Performance Dashboard**

**Resumo Geral:**
• Bankroll: R$ {dashboard['current_balance']:.2f}
• Lucro: R$ {dashboard['total_profit']:.2f}
• ROI: {dashboard['roi']:.1f}%
• Win Rate: {dashboard['win_rate']:.1f}%

**Estatísticas:**
• Total Apostas: {dashboard['total_bets']}
• Apostas Ganhas: {dashboard['won_bets']}
• Sequência Atual: {dashboard['current_streak']}
• Melhor Sequência: {dashboard['best_streak']}

**Gráfico de Evolução:**
```
{dashboard['ascii_chart']}
```

**Última Atualização:** {datetime.now().strftime('%H:%M:%S')}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_tracker")],
                [InlineKeyboardButton("📊 Análise Detalhada", callback_data="detailed_analysis")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                dashboard_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no tracker: {e}")
            await update.message.reply_text(f"❌ Erro: {e}")
    
    async def _dashboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /dashboard"""
        await self._tracker_command(update, context)
    
    async def _prever_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /prever - Previsões pós-draft"""
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "🎮 **Previsão Pós-Draft**\n\n"
                "Use: `/prever T1 vs Gen.G`",
                parse_mode='Markdown'
            )
            return
        
        match_text = " ".join(args)
        teams = self._extract_teams(match_text)
        
        if len(teams) < 2:
            await update.message.reply_text("❌ Formato inválido. Use: `/prever Time1 vs Time2`")
            return
        
        team1, team2 = teams[0], teams[1]
        
        try:
            await update.message.reply_text(f"🔍 Gerando previsão para {team1} vs {team2}...")
            
            # Usar pre-game analyzer
            prediction = self.personal_betting.pre_game_analyzer.analyze_match(
                team1=team1,
                team2=team2
            )
            
            result_text = f"""
🎮 **Previsão: {team1} vs {team2}**

**Probabilidades:**
• {team1}: {prediction['team1_probability']:.1f}%
• {team2}: {prediction['team2_probability']:.1f}%

**Confiança:** {prediction['confidence']:.1f}%
**Qualidade:** {prediction['quality']}/10

**Análise:**
{prediction['analysis_summary']}

**Recomendação:** {prediction['recommendation']}
            """
            
            keyboard = [
                [InlineKeyboardButton("📊 Análise Completa", callback_data=f"full_analysis_{team1}_{team2}")],
                [InlineKeyboardButton("💰 Analisar Value", callback_data=f"analyze_value_{team1}_{team2}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                result_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro na previsão: {e}")
            await update.message.reply_text(f"❌ Erro: {e}")
    
    # === HANDLERS DE CALLBACK ===
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries (botões)"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data == "main_menu":
                await self._menu_command(update, context)
            elif data == "bankroll_menu":
                await self._bankroll_command(update, context)
            elif data == "show_tracker":
                await self._tracker_command(update, context)
            elif data == "refresh_tracker":
                await self._tracker_command(update, context)
            elif data.startswith("analyze_value_"):
                teams = data.replace("analyze_value_", "").split("_")
                if len(teams) >= 2:
                    # Simular análise de value
                    context.args = [teams[0], "vs", teams[1]]
                    await self._analisar_command(update, context)
            else:
                await query.edit_message_text("🔧 Funcionalidade em desenvolvimento...")
                
        except Exception as e:
            logger.error(f"Erro no callback: {e}")
            await query.edit_message_text(f"❌ Erro: {e}")
    
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle mensagens de texto"""
        text = update.message.text.lower()
        
        if "vs" in text or "x" in text:
            # Detectar análise de match
            await update.message.reply_text(
                f"🔍 Detectei um match! Use `/analisar {update.message.text}` para análise completa."
            )
        else:
            await update.message.reply_text(
                "👋 Olá! Use /menu para ver as opções ou /help para ajuda."
            )
    
    # === UTILS ===
    
    def _extract_teams(self, text: str) -> List[str]:
        """Extrai nomes dos times do texto"""
        text = text.lower()
        
        # Separadores possíveis
        separators = [' vs ', ' x ', ' vs. ', ' versus ']
        
        for sep in separators:
            if sep in text:
                teams = text.split(sep)
                return [team.strip().title() for team in teams[:2]]
        
        # Fallback: separar por espaços
        words = text.split()
        if len(words) >= 2:
            return [words[0].title(), words[-1].title()]
        
        return [] 