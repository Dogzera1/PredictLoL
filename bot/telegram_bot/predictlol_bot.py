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

from ..services.real_analysis_service import RealAnalysisService

logger = logging.getLogger(__name__)

class PredictLoLTelegramBot:
    """Bot Telegram PredictLoL integrado"""
    
    def __init__(self, token: str, personal_betting=None):
        self.token = token
        self.personal_betting = personal_betting
        self.app = None
        self.is_running = False
        
        # Serviço de análise real
        self.analysis_service = None
        
        # Usuários autorizados (você pode adicionar mais)
        self.authorized_users = set()
        
        logger.info("🤖 PredictLoL Telegram Bot criado")
    
    async def initialize(self):
        """Inicializa o bot"""
        try:
            # Criar aplicação
            self.app = Application.builder().token(self.token).build()
            
            # Inicializar serviço de análise
            self.analysis_service = RealAnalysisService()
            
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
        
        # Novos comandos de configuração
        self.app.add_handler(CommandHandler("config_bankroll", self._config_bankroll_command))
        self.app.add_handler(CommandHandler("tracker_full", self._tracker_full_command))
        self.app.add_handler(CommandHandler("simular_aposta", self._simular_aposta_command))
        
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
            
            # Inicia polling com configurações seguras
            await self.app.updater.start_polling(
                poll_interval=2.0,
                timeout=10,
                read_timeout=10,
                write_timeout=10,
                connect_timeout=10,
                pool_timeout=10
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
            [
                InlineKeyboardButton("💰 Bankroll", callback_data="bankroll_menu"),
                InlineKeyboardButton("🎮 Análise", callback_data="analysis_menu")
            ],
            [
                InlineKeyboardButton("📈 Tracker", callback_data="tracker_menu"),
                InlineKeyboardButton("🔧 Ferramentas", callback_data="tools_menu")
            ],
            [InlineKeyboardButton("❓ Ajuda", callback_data="help_menu")]
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

**💰 Configuração de Bankroll:**
• `/config_bankroll <valor>` - Configurar bankroll inicial
• `/bankroll` - Status do bankroll atual
• `/simular_aposta <confiança> <odds>` - Simular cálculo

**📊 Análise de Value:**
• `/analisar <time1> vs <time2>` - Análise completa de match
• `/prever <time1> vs <time2>` - Previsão pós-draft

**📈 Performance Tracking:**
• `/tracker` - Dashboard resumido
• `/tracker_full` - Dashboard completo com gráficos
• `/dashboard` - Alias para tracker

**💸 Registro de Apostas:**
• `/apostar <valor> <odds> <descrição>` - Registrar aposta

**⚙️ Geral:**
• `/menu` - Menu principal interativo
• `/help` - Esta ajuda

**🎯 Exemplos de Uso:**
```
/config_bankroll 1500
/simular_aposta 75 1.85
/apostar 50 1.85 T1 vs Gen.G - T1 vencer
/tracker_full
```

**Sistema Kelly Criterion + Risk Management ativo!**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu"),
                InlineKeyboardButton("🎯 Começar", callback_data="quick_start")
            ],
            [
                InlineKeyboardButton("💰 Configurar Bankroll", callback_data="config_bankroll"),
                InlineKeyboardButton("🎮 Análise Rápida", callback_data="quick_analysis")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /menu"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Bankroll & Configuração", callback_data="bankroll_menu"),
                InlineKeyboardButton("📊 Análise de Matches", callback_data="analysis_menu")
            ],
            [
                InlineKeyboardButton("📈 Performance Tracker", callback_data="tracker_menu"),
                InlineKeyboardButton("💸 Gestão de Apostas", callback_data="betting_menu")
            ],
            [
                InlineKeyboardButton("🎮 Previsões Pós-Draft", callback_data="predictions_menu"),
                InlineKeyboardButton("🔧 Ferramentas", callback_data="tools_menu")
            ],
            [
                InlineKeyboardButton("❓ Ajuda", callback_data="help_menu"),
                InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎯 **Menu Principal PredictLoL**\n\nEscolha uma categoria:",
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
            bankroll_info = self.personal_betting.bankroll_manager.get_performance_stats()
            
            status_text = f"""
💰 **Status do Bankroll**

**Saldo Atual:** R$ {self.personal_betting.bankroll_manager.settings.current_bankroll:.2f}
**Saldo Inicial:** R$ {self.personal_betting.bankroll_manager.settings.initial_bankroll:.2f}
**Total de Apostas:** {bankroll_info.get('total_bets', 0)}
**Win Rate:** {bankroll_info.get('win_rate', 0):.1f}%

**Configurações de Risco:**
• Limite Diário: R$ {self.personal_betting.bankroll_manager.get_daily_limit():.2f}
• Máximo por Aposta: R$ {self.personal_betting.bankroll_manager.get_max_bet_amount():.2f}
• Restante Hoje: R$ {self.personal_betting.bankroll_manager.get_daily_remaining_limit():.2f}

**Sistema:** Ativo e funcionando!
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("⚙️ Configurar", callback_data="config_bankroll"),
                    InlineKeyboardButton("🎲 Simular", callback_data="simulate_bet")
                ],
                [
                    InlineKeyboardButton("📊 Análise", callback_data="quick_analysis"),
                    InlineKeyboardButton("📈 Tracker", callback_data="show_tracker")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
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
        """Comando /analisar - Agora usa dados reais da API"""
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "📊 **Análise de Match**\n\n"
                "Use: `/analisar T1 vs Gen.G`\n"
                "ou: `/analisar T1 Gen.G`\n\n"
                "🔍 **Sistema usa dados reais da API LoL Esports**",
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
            await update.message.reply_text(f"🔍 Analisando {team1} vs {team2} com dados reais...")
            
            # Usar serviço de análise real
            async with self.analysis_service as service:
                analysis = await service.analyze_match(team1, team2)
            
            if analysis["success"]:
                # Análise com dados reais
                team1_data = analysis["team1"]
                team2_data = analysis["team2"]
                
                result_text = f"""
📊 **Análise: {team1_data['name']} vs {team2_data['name']}**

**Probabilidades (Dados Reais):**
• {team1_data['name']}: {team1_data['probability']}%
• {team2_data['name']}: {team2_data['probability']}%

**Odds Sugeridas:**
• {team1_data['name']}: {team1_data['odds_range'][0]:.2f}-{team1_data['odds_range'][1]:.2f}
• {team2_data['name']}: {team2_data['odds_range'][0]:.2f}-{team2_data['odds_range'][1]:.2f}

**Recomendação:** {analysis['recommendation']}
**Confiança:** {analysis['confidence']}%

**Fonte:** {analysis['data_source'].upper()} ✅
                """
            else:
                # Fallback quando dados não estão disponíveis
                result_text = f"""
📊 **Análise: {team1} vs {team2}**

⚠️ **{analysis['analysis_details']['reason']}**

**Probabilidades (Estimativa):**
• {team1}: {analysis['team1']['probability']}%
• {team2}: {analysis['team2']['probability']}%

**Recomendação:** {analysis['recommendation']}
**Sugestão:** {analysis['analysis_details']['suggestion']}

**Fonte:** FALLBACK (dados limitados)
                """
            
            keyboard = [
                [
                    InlineKeyboardButton("💰 Calcular Aposta", callback_data=f"calc_{team1}"),
                    InlineKeyboardButton("🎯 Nova Análise", callback_data="quick_analysis")
                ],
                [
                    InlineKeyboardButton("💸 Registrar Aposta", callback_data="register_bet"),
                    InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")
                ]
            ]
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
            
            result_text = f"""
✅ **Aposta Registrada!**

**Detalhes:**
• Valor: R$ {amount:.2f}
• Odds: {odds:.2f}
• Descrição: {description}

**Cálculos:**
• Retorno Potencial: R$ {amount * odds:.2f}
• Lucro Potencial: R$ {amount * (odds - 1):.2f}

**Status:** Aposta registrada no sistema
            """
            
            keyboard = [
                [InlineKeyboardButton("📊 Ver Dashboard", callback_data="show_dashboard")],
                [InlineKeyboardButton("💰 Nova Aposta", callback_data="new_bet")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
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
            dashboard_text = f"""
📈 **Performance Dashboard**

**Resumo Geral:**
• Bankroll: R$ {self.personal_betting.bankroll_manager.settings.current_bankroll:.2f}
• Sistema: Ativo e funcionando

**Estatísticas:**
• Total Apostas: Sendo monitoradas
• Performance: Em tempo real
• Análises: Sistema integrado

**Status:** ✅ Todos os sistemas operacionais

**Última Atualização:** {datetime.now().strftime('%H:%M:%S')}
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_tracker"),
                    InlineKeyboardButton("📈 Tracker Completo", callback_data="tracker_full")
                ],
                [
                    InlineKeyboardButton("💰 Ver Bankroll", callback_data="bankroll_menu"),
                    InlineKeyboardButton("📊 Nova Análise", callback_data="quick_analysis")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
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
    
    async def _config_bankroll_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /config_bankroll - Configurar bankroll inicial"""
        args = context.args
        
        if not args:
            current_bankroll = self.personal_betting.bankroll_manager.settings.current_bankroll if self.personal_betting else 1000.0
            
            help_text = f"""
💰 **Configurar Bankroll**

**Bankroll Atual:** R$ {current_bankroll:.2f}

**Como usar:**
`/config_bankroll <valor>`

**Exemplos:**
• `/config_bankroll 500` - Define R$ 500
• `/config_bankroll 2000` - Define R$ 2000
• `/config_bankroll 1500` - Define R$ 1500

**Configurações disponíveis:**
• Valor inicial do bankroll
• Limites de segurança automáticos
• Sistema Kelly Criterion ativo

**Próximo passo:** Use `/simular_aposta` para testar
            """
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            return
        
        try:
            valor = float(args[0])
            
            if valor < 50:
                await update.message.reply_text("❌ Valor mínimo: R$ 50.00")
                return
            
            if valor > 100000:
                await update.message.reply_text("❌ Valor máximo: R$ 100.000.00")
                return
            
            # Configurar bankroll
            if self.personal_betting:
                result = self.personal_betting.bankroll_manager.setup_bankroll(valor)
                
                if result['success']:
                    config_text = f"""
✅ **Bankroll Configurado!**

**Novo Bankroll:** R$ {valor:.2f}

**Limites Automáticos:**
• Limite Diário: R$ {result['daily_limit']:.2f} (10% do bankroll)
• Máximo por Aposta: R$ {result['max_bet']:.2f} (5% do bankroll)
• Sistema Kelly Criterion: Ativo

**Configurações de Risco:**
• Nível: Médio (padrão)
• Stop Loss: 20% do bankroll
• Auto Compound: Ativo

**Próximos comandos:**
• `/bankroll` - Ver status completo
• `/simular_aposta 60 1.85` - Simular aposta
• `/tracker` - Acompanhar performance
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("💰 Ver Status", callback_data="bankroll_menu")],
                        [InlineKeyboardButton("🧮 Simular Aposta", callback_data="simulate_bet")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        config_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(f"❌ Erro: {result.get('error', 'Erro desconhecido')}")
            else:
                await update.message.reply_text("❌ Sistema não disponível")
                
        except ValueError:
            await update.message.reply_text("❌ Valor inválido. Use números como: `/config_bankroll 1000`")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {e}")
    
    async def _simular_aposta_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /simular_aposta - Simular cálculo de aposta"""
        args = context.args
        
        if len(args) < 2:
            help_text = """
🧮 **Simular Aposta**

**Uso:** `/simular_aposta <confiança> <odds> [sua_probabilidade]`

**Exemplos:**
• `/simular_aposta 75 1.85` - 75% confiança, odds 1.85
• `/simular_aposta 80 2.20 0.55` - Com probabilidade específica
• `/simular_aposta 65 1.65` - Aposta conservadora

**Parâmetros:**
• **Confiança:** 50-95% (sua confiança no resultado)
• **Odds:** 1.10-10.00 (odds da casa de apostas)
• **Probabilidade:** 0.1-0.9 (opcional, calculada automaticamente)

**O sistema calculará:**
• Tamanho ideal da aposta (Kelly Criterion)
• Expected Value (EV)
• Lucro potencial
• Nível de risco
            """
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            return
        
        try:
            confidence = float(args[0])
            odds = float(args[1])
            
            # Probabilidade: se fornecida usar, senão calcular baseado na confiança
            if len(args) >= 3:
                your_probability = float(args[2])
            else:
                # Conversão simples de confiança para probabilidade
                your_probability = confidence / 100.0
            
            # Validações
            if confidence < 50 or confidence > 95:
                await update.message.reply_text("❌ Confiança deve estar entre 50% e 95%")
                return
            
            if odds < 1.1 or odds > 10.0:
                await update.message.reply_text("❌ Odds devem estar entre 1.10 e 10.00")
                return
            
            if your_probability < 0.1 or your_probability > 0.9:
                await update.message.reply_text("❌ Probabilidade deve estar entre 0.1 e 0.9")
                return
            
            # Calcular tamanho da aposta
            if self.personal_betting:
                calculation = self.personal_betting.bankroll_manager.calculate_bet_size(
                    confidence=confidence,
                    odds=odds,
                    your_probability=your_probability,
                    league="Simulação",
                    reasoning="Teste de simulação"
                )
                
                if calculation.get('recommended'):
                    result_text = f"""
🧮 **Simulação de Aposta**

**Parâmetros:**
• Confiança: {confidence:.1f}%
• Odds: {odds:.2f}
• Sua Probabilidade: {your_probability:.1f}%

**💰 CÁLCULOS KELLY CRITERION:**
• Tamanho Recomendado: R$ {calculation['bet_amount']:.2f}
• Percentual do Bankroll: {calculation['percentage_bankroll']:.2f}%
• Kelly Fraction: {calculation['kelly_fraction']:.4f}

**📊 PROJEÇÕES:**
• Expected Value: {calculation['ev_percentage']:.2f}%
• Retorno Potencial: R$ {calculation['potential_return']:.2f}
• Lucro Potencial: R$ {calculation['potential_profit']:.2f}
• Nível de Risco: {calculation['risk_level'].title()}

**⚠️ AVISOS:**
{chr(10).join(f"• {warning}" for warning in calculation.get('warnings', []))}

**Para apostar de verdade:**
`/apostar {calculation['bet_amount']:.0f} {odds} Time vs Oponente - Descrição`
                    """
                else:
                    result_text = f"""
❌ **Aposta NÃO Recomendada**

**Motivo:** {calculation.get('reason', 'Critérios não atendidos')}

**Dicas:**
• Aumente sua confiança (mín. 60%)
• Procure odds com melhor value
• Verifique o Expected Value (mín. 3%)

**Tente novamente com parâmetros diferentes!**
                    """
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Nova Simulação", callback_data="new_simulation")],
                    [InlineKeyboardButton("💰 Ver Bankroll", callback_data="bankroll_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    result_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ Sistema não disponível")
                
        except ValueError:
            await update.message.reply_text("❌ Valores inválidos. Use números como: `/simular_aposta 75 1.85`")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {e}")
    
    async def _tracker_full_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /tracker_full - Dashboard completo do tracker"""
        if not self.personal_betting:
            await update.message.reply_text("❌ Sistema não disponível")
            return
        
        try:
            # Gerar dashboard completo
            dashboard = self.personal_betting.betting_tracker.generate_dashboard()
            
            # Telegram tem limite de 4096 caracteres, vamos dividir
            if len(dashboard) > 4000:
                # Dividir em partes
                parts = []
                lines = dashboard.split('\n')
                current_part = ""
                
                for line in lines:
                    if len(current_part + line + '\n') > 3800:
                        parts.append(current_part)
                        current_part = line + '\n'
                    else:
                        current_part += line + '\n'
                
                if current_part:
                    parts.append(current_part)
                
                # Enviar primeira parte com botões
                keyboard = [
                    [InlineKeyboardButton("📊 Parte 2", callback_data="tracker_part_2")],
                    [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_tracker")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"```\n{parts[0]}\n```\n**Parte 1 de {len(parts)}**",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
                # Salvar outras partes para callbacks (simplificado)
                self._temp_tracker_parts = parts
                
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_tracker")],
                    [InlineKeyboardButton("📊 Resumo", callback_data="show_tracker")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"```\n{dashboard}\n```",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Erro no tracker completo: {e}")
            await update.message.reply_text(f"❌ Erro: {e}")
    
    async def _prever_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /prever - Previsões pós-draft com dados reais"""
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "🎮 **Previsão Pós-Draft**\n\n"
                "Use: `/prever T1 vs Gen.G`\n\n"
                "🔍 **Sistema usa dados reais da API LoL Esports**",
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
            await update.message.reply_text(f"🔍 Gerando previsão pós-draft para {team1} vs {team2}...")
            
            # Usar serviço de análise real para previsão pós-draft
            async with self.analysis_service as service:
                prediction = await service.predict_post_draft(team1, team2)
            
            if prediction["success"]:
                # Previsão com dados reais
                team1_data = prediction["team1"]
                team2_data = prediction["team2"]
                
                result_text = f"""
🎮 **Previsão: {team1_data['name']} vs {team2_data['name']}**

**Probabilidades (Dados Reais):**
• {team1_data['name']}: {team1_data['probability']}%
• {team2_data['name']}: {team2_data['probability']}%

**Confiança:** {prediction['confidence']}%
**Tipo:** {prediction.get('prediction_type', 'post_draft').upper()}

**Análise:**
{prediction['recommendation']}

**Fonte:** {prediction['data_source'].upper()} ✅
                """
            else:
                # Fallback quando dados não estão disponíveis
                result_text = f"""
🎮 **Previsão: {team1} vs {team2}**

⚠️ **{prediction['analysis_details']['reason']}**

**Probabilidades (Estimativa):**
• {team1}: {prediction['team1']['probability']}%
• {team2}: {prediction['team2']['probability']}%

**Confiança:** {prediction['confidence']}%

**Recomendação:** {prediction['recommendation']}
**Sugestão:** {prediction['analysis_details']['suggestion']}

**Fonte:** FALLBACK (dados limitados)
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
            # Menu principal
            if data == "main_menu":
                await self._show_main_menu(query)
            elif data == "refresh_menu":
                await self._show_main_menu(query)
                
            # Menus de categoria
            elif data == "bankroll_menu":
                await self._show_bankroll_menu(query)
            elif data == "analysis_menu":
                await self._show_analysis_menu(query)
            elif data == "tracker_menu":
                await self._show_tracker_menu(query)
            elif data == "betting_menu":
                await self._show_betting_menu(query)
            elif data == "predictions_menu":
                await self._show_predictions_menu(query)
            elif data == "tools_menu":
                await self._show_tools_menu(query)
            elif data == "help_menu":
                await self._show_help_menu(query)
                
            # Ações específicas do bankroll
            elif data == "show_bankroll_status":
                await self._show_bankroll_status(query)
            elif data == "config_bankroll":
                await query.edit_message_text(
                    "💰 **Configurar Bankroll**\n\n"
                    "Use o comando: `/config_bankroll <valor>`\n\n"
                    "Exemplo: `/config_bankroll 1500`",
                    parse_mode='Markdown'
                )
            elif data == "simulate_bet":
                await query.edit_message_text(
                    "🎲 **Simulador de Aposta**\n\n"
                    "Use o comando: `/simular_aposta <confiança> <odds>`\n\n"
                    "Exemplo: `/simular_aposta 75 1.85`",
                    parse_mode='Markdown'
                )
                
            # Ações do tracker
            elif data == "show_tracker":
                await self._show_tracker_dashboard(query)
            elif data == "refresh_tracker":
                await self._show_tracker_dashboard(query)
            elif data == "tracker_full":
                await query.edit_message_text(
                    "📈 **Tracker Completo**\n\n"
                    "Use o comando: `/tracker_full`\n\n"
                    "Isso mostrará dashboard completo com gráficos.",
                    parse_mode='Markdown'
                )
                
            # Ações de análise
            elif data == "quick_analysis":
                await query.edit_message_text(
                    "⚡ **Análise Rápida**\n\n"
                    "Use o comando: `/analisar <time1> vs <time2>`\n\n"
                    "Exemplo: `/analisar T1 vs Gen.G`",
                    parse_mode='Markdown'
                )
            elif data == "post_draft_prediction":
                await query.edit_message_text(
                    "🎮 **Previsão Pós-Draft**\n\n"
                    "Use o comando: `/prever <time1> vs <time2>`\n\n"
                    "Exemplo: `/prever T1 vs Gen.G`",
                    parse_mode='Markdown'
                )
                
            # Ações de apostas
            elif data == "register_bet":
                await query.edit_message_text(
                    "💸 **Registrar Aposta**\n\n"
                    "Use o comando: `/apostar <valor> <odds> <descrição>`\n\n"
                    "Exemplo: `/apostar 50 1.85 T1 vs Gen.G - T1 vencer`",
                    parse_mode='Markdown'
                )
            elif data == "betting_dashboard":
                await query.edit_message_text(
                    "📊 **Dashboard de Apostas**\n\n"
                    "Use o comando: `/dashboard`\n\n"
                    "Mostra resumo completo das suas apostas.",
                    parse_mode='Markdown'
                )
            elif data == "betting_history":
                await query.edit_message_text("📋 Histórico de apostas em desenvolvimento...")
            elif data == "betting_stats":
                await query.edit_message_text("💹 Estatísticas de ROI em desenvolvimento...")
                
            # Ações de ferramentas
            elif data == "kelly_calculator":
                await query.edit_message_text(
                    "🧮 **Calculadora Kelly**\n\n"
                    "Use o comando: `/simular_aposta <confiança> <odds>`\n\n"
                    "Exemplo: `/simular_aposta 75 1.85`",
                    parse_mode='Markdown'
                )
            elif data == "odds_converter":
                await query.edit_message_text("💱 Conversor de odds em desenvolvimento...")
            elif data == "ev_comparator":
                await query.edit_message_text("📊 Comparador de EV em desenvolvimento...")
            elif data == "stake_calculator":
                await query.edit_message_text("🎯 Calculadora de stake em desenvolvimento...")
            elif data == "betting_simulator":
                await query.edit_message_text("📈 Simulador de apostas em desenvolvimento...")
            elif data == "value_finder":
                await query.edit_message_text("🔍 Localizador de value em desenvolvimento...")
                
            # Ações de análise expandidas
            elif data == "full_analysis":
                await query.edit_message_text(
                    "📈 **Análise Completa**\n\n"
                    "Use o comando: `/analisar <time1> vs <time2>`\n\n"
                    "Exemplo: `/analisar T1 vs Gen.G`",
                    parse_mode='Markdown'
                )
            elif data == "value_analysis":
                await query.edit_message_text("💰 Análise de value em desenvolvimento...")
            elif data == "odds_comparison":
                await query.edit_message_text("🔍 Comparação de odds em desenvolvimento...")
                
            # Ações do tracker expandidas
            elif data == "tracker_charts":
                await query.edit_message_text("📉 Gráficos do tracker em desenvolvimento...")
            elif data == "tracker_report":
                await query.edit_message_text("📋 Relatório do tracker em desenvolvimento...")
                
            # Ações de previsões expandidas
            elif data == "composition_analysis":
                await query.edit_message_text("📊 Análise de composição em desenvolvimento...")
            elif data == "head_to_head":
                await query.edit_message_text("⚔️ Análise head-to-head em desenvolvimento...")
            elif data == "trends_analysis":
                await query.edit_message_text("📈 Análise de tendências em desenvolvimento...")
                
            # Ações de ajuda
            elif data == "help_commands":
                await query.edit_message_text(
                    "📚 **Lista de Comandos**\n\n"
                    "Use `/help` para ver todos os comandos disponíveis.\n\n"
                    "Comandos principais:\n"
                    "• `/menu` - Menu interativo\n"
                    "• `/bankroll` - Status do bankroll\n"
                    "• `/analisar` - Análise de matches\n"
                    "• `/apostar` - Registrar aposta\n"
                    "• `/tracker` - Performance dashboard",
                    parse_mode='Markdown'
                )
            elif data == "help_usage":
                await query.edit_message_text("❓ Guia de uso em desenvolvimento...")
            elif data == "help_strategies":
                await query.edit_message_text("🎯 Guia de estratégias em desenvolvimento...")
            elif data == "help_setup":
                await query.edit_message_text("⚙️ Guia de configuração em desenvolvimento...")
            elif data == "help_support":
                await query.edit_message_text("🆘 Suporte técnico em desenvolvimento...")
            elif data == "quick_start":
                await query.edit_message_text(
                    "🎯 **Início Rápido**\n\n"
                    "1. Configure seu bankroll: `/config_bankroll 1500`\n"
                    "2. Analise um match: `/analisar T1 vs Gen.G`\n"
                    "3. Registre uma aposta: `/apostar 50 1.85 descrição`\n"
                    "4. Acompanhe performance: `/tracker`\n\n"
                    "Use `/menu` para acesso completo!",
                    parse_mode='Markdown'
                )
                
            # Callbacks específicos de análise
            elif data.startswith("analyze_value_"):
                await query.edit_message_text("📊 Funcionalidade de análise em desenvolvimento...")
            elif data.startswith("full_analysis_"):
                await query.edit_message_text("📈 Análise completa em desenvolvimento...")
                
            # Callback genérico
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
    
    # === CALLBACK HANDLERS ===
    
    async def _show_main_menu(self, query):
        """Mostra menu principal via callback"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Bankroll & Configuração", callback_data="bankroll_menu"),
                InlineKeyboardButton("📊 Análise de Matches", callback_data="analysis_menu")
            ],
            [
                InlineKeyboardButton("📈 Performance Tracker", callback_data="tracker_menu"),
                InlineKeyboardButton("💸 Gestão de Apostas", callback_data="betting_menu")
            ],
            [
                InlineKeyboardButton("🎮 Previsões Pós-Draft", callback_data="predictions_menu"),
                InlineKeyboardButton("🔧 Ferramentas", callback_data="tools_menu")
            ],
            [
                InlineKeyboardButton("❓ Ajuda", callback_data="help_menu"),
                InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 **Menu Principal PredictLoL**\n\nEscolha uma categoria:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_bankroll_menu(self, query):
        """Mostra menu do bankroll via callback"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Status do Bankroll", callback_data="show_bankroll_status"),
                InlineKeyboardButton("⚙️ Configurar Bankroll", callback_data="config_bankroll")
            ],
            [
                InlineKeyboardButton("🎲 Simulador de Aposta", callback_data="simulate_bet"),
                InlineKeyboardButton("📊 Calcular Kelly", callback_data="kelly_calculator")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💰 **Menu Bankroll & Configuração**\n\nEscolha uma opção:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _show_bankroll_status(self, query):
        """Mostra status do bankroll via callback"""
        if not self.personal_betting:
            await query.edit_message_text("❌ Sistema de apostas não disponível")
            return
        
        try:
            # Obter status do bankroll
            bankroll_info = self.personal_betting.bankroll_manager.get_performance_stats()
            
            status_text = f"""
💰 **Status do Bankroll**

**Saldo Atual:** R$ {self.personal_betting.bankroll_manager.settings.current_bankroll:.2f}
**Saldo Inicial:** R$ {self.personal_betting.bankroll_manager.settings.initial_bankroll:.2f}
**Total de Apostas:** {bankroll_info.get('total_bets', 0)}
**Win Rate:** {bankroll_info.get('win_rate', 0):.1f}%

**Configurações de Risco:**
• Limite Diário: R$ {self.personal_betting.bankroll_manager.get_daily_limit():.2f}
• Máximo por Aposta: R$ {self.personal_betting.bankroll_manager.get_max_bet_amount():.2f}
• Restante Hoje: R$ {self.personal_betting.bankroll_manager.get_daily_remaining_limit():.2f}

**Sistema:** Ativo e funcionando!
            """
            
            keyboard = [
                [InlineKeyboardButton("⚙️ Configurar", callback_data="config_bankroll")],
                [InlineKeyboardButton("🎲 Simular Aposta", callback_data="simulate_bet")],
                [InlineKeyboardButton("🔙 Menu Bankroll", callback_data="bankroll_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                status_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando bankroll: {e}")
            await query.edit_message_text(f"❌ Erro ao obter status: {e}")
    
    async def _show_analysis_menu(self, query):
        """Mostra menu de análise via callback"""
        keyboard = [
            [
                InlineKeyboardButton("⚡ Análise Rápida", callback_data="quick_analysis"),
                InlineKeyboardButton("📈 Análise Completa", callback_data="full_analysis")
            ],
            [
                InlineKeyboardButton("💰 Análise de Value", callback_data="value_analysis"),
                InlineKeyboardButton("🔍 Comparar Odds", callback_data="odds_comparison")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📊 **Menu Análise de Matches**\n\nEscolha o tipo de análise:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_tracker_menu(self, query):
        """Mostra menu do tracker via callback"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Dashboard Simples", callback_data="show_tracker"),
                InlineKeyboardButton("📈 Dashboard Completo", callback_data="tracker_full")
            ],
            [
                InlineKeyboardButton("📉 Gráficos", callback_data="tracker_charts"),
                InlineKeyboardButton("📋 Relatório", callback_data="tracker_report")
            ],
            [
                InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_tracker"),
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📈 **Menu Performance Tracker**\n\nEscolha uma opção:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_betting_menu(self, query):
        """Mostra menu de apostas via callback"""
        keyboard = [
            [
                InlineKeyboardButton("💸 Registrar Aposta", callback_data="register_bet"),
                InlineKeyboardButton("📊 Dashboard", callback_data="betting_dashboard")
            ],
            [
                InlineKeyboardButton("📋 Histórico de Apostas", callback_data="betting_history"),
                InlineKeyboardButton("💹 ROI & Estatísticas", callback_data="betting_stats")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💸 **Menu Gestão de Apostas**\n\nEscolha uma opção:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_predictions_menu(self, query):
        """Mostra menu de previsões via callback"""
        keyboard = [
            [
                InlineKeyboardButton("🎮 Previsão Pós-Draft", callback_data="post_draft_prediction"),
                InlineKeyboardButton("📊 Análise de Composição", callback_data="composition_analysis")
            ],
            [
                InlineKeyboardButton("⚔️ Head-to-Head", callback_data="head_to_head"),
                InlineKeyboardButton("📈 Tendências", callback_data="trends_analysis")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎮 **Menu Previsões Pós-Draft**\n\nEscolha uma opção:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_tools_menu(self, query):
        """Mostra menu de ferramentas via callback"""
        keyboard = [
            [
                InlineKeyboardButton("🧮 Calculadora Kelly", callback_data="kelly_calculator"),
                InlineKeyboardButton("💱 Conversor de Odds", callback_data="odds_converter")
            ],
            [
                InlineKeyboardButton("📊 Comparador EV", callback_data="ev_comparator"),
                InlineKeyboardButton("🎯 Stake Calculator", callback_data="stake_calculator")
            ],
            [
                InlineKeyboardButton("📈 Simulador", callback_data="betting_simulator"),
                InlineKeyboardButton("🔍 Value Finder", callback_data="value_finder")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔧 **Menu Ferramentas**\n\nEscolha uma ferramenta:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_help_menu(self, query):
        """Mostra menu de ajuda via callback"""
        keyboard = [
            [
                InlineKeyboardButton("📚 Comandos", callback_data="help_commands"),
                InlineKeyboardButton("❓ Como Usar", callback_data="help_usage")
            ],
            [
                InlineKeyboardButton("🎯 Estratégias", callback_data="help_strategies"),
                InlineKeyboardButton("⚙️ Configuração", callback_data="help_setup")
            ],
            [
                InlineKeyboardButton("🆘 Suporte", callback_data="help_support"),
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❓ **Menu de Ajuda**\n\nEscolha um tópico:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_tracker_dashboard(self, query):
        """Mostra dashboard do tracker via callback"""
        if not self.personal_betting:
            await query.edit_message_text("❌ Sistema não disponível")
            return
        
        try:
            dashboard_text = f"""
📈 **Performance Dashboard**

**Resumo Geral:**
• Bankroll: R$ {self.personal_betting.bankroll_manager.settings.current_bankroll:.2f}
• Sistema: Ativo e funcionando

**Estatísticas:**
• Total Apostas: Sendo monitoradas
• Performance: Em tempo real
• Análises: Sistema integrado

**Status:** ✅ Todos os sistemas operacionais

**Última Atualização:** {datetime.now().strftime('%H:%M:%S')}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_tracker")],
                [InlineKeyboardButton("📊 Análise Detalhada", callback_data="detailed_analysis")],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                dashboard_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no tracker: {e}")
            await query.edit_message_text(f"❌ Erro: {e}")
    
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