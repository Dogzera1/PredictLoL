# -*- coding: utf-8 -*-
"""
BotHandler - Sistema de manipulação de comandos Telegram
Integrado com bot_v13_railway.py
"""

import logging
import threading
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

class BotHandler:
    """Manipulador principal de comandos do bot"""

    def __init__(self):
        self.bot_application = None
        logger.info("🤖 BotHandler inicializado")

    def set_bot_application(self, application):
        """Define aplicação do bot"""
        self.bot_application = application

    def start_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /start"""
        try:
            welcome_message = """
🎮 **BOT LOL V3 - SISTEMA PROFISSIONAL DE TIPS**

🏆 **Sistema de Unidades Padrão Profissional**
💎 Baseado em grupos de apostas de elite
📊 Análise REAL das APIs da Riot Games
🤖 Machine Learning integrado

**Comandos Disponíveis:**
/menu - Menu principal interativo
/tips - Tips profissionais atuais
/live - Partidas ao vivo
/monitoring - Status do monitoramento
/units - Sistema de unidades

✨ **Novidades V3:**
• Sistema de cache inteligente
• Monitoramento automático 24/7
• Tips com critérios rigorosos (Conf ≥75%, EV ≥8%)
• Alertas automáticos para grupos

Digite /menu para começar! 🚀
            """
            
            keyboard = [
                [InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")],
                [InlineKeyboardButton("💎 Tips Ativos", callback_data="current_tips")],
                [InlineKeyboardButton("🔴 Partidas Ao Vivo", callback_data="live_matches")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                welcome_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando start: {e}")
            update.message.reply_text("❌ Erro interno. Tente novamente.")

    def menu_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /menu"""
        try:
            menu_text = """
🎮 **MENU PRINCIPAL - BOT LOL V3**

Escolha uma opção abaixo:
            """
            
            keyboard = [
                [InlineKeyboardButton("💎 Tips Profissionais", callback_data="tips_menu")],
                [InlineKeyboardButton("🔴 Partidas Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("📅 Agenda", callback_data="schedule_menu")],
                [InlineKeyboardButton("🔍 Monitoramento", callback_data="monitoring_menu")],
                [InlineKeyboardButton("📊 Predições", callback_data="predictions_menu")],
                [InlineKeyboardButton("🔔 Alertas", callback_data="alerts_menu")],
                [InlineKeyboardButton("💰 Sistema Unidades", callback_data="units_info")],
                [InlineKeyboardButton("📈 Performance", callback_data="performance_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                menu_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no menu: {e}")
            update.message.reply_text("❌ Erro ao carregar menu.")

    def tips_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /tips"""
        try:
            # Importar do arquivo principal
            from bot_v13_railway import match_monitor
            
            tips = match_monitor.found_tips[-5:] if match_monitor.found_tips else []
            
            if not tips:
                message = """
💎 **TIPS PROFISSIONAIS**

📭 Nenhum tip ativo no momento.

O sistema monitora automaticamente as partidas e gera tips apenas quando:
• Confiança ≥ 75%
• EV ≥ 8%
• Dados completos da partida

⏰ Próximo scan: 3 minutos
                """
            else:
                message = "💎 **TIPS PROFISSIONAIS ATIVOS**\n\n"
                for i, tip in enumerate(tips, 1):
                    message += f"**{i}. {tip['teams']}**\n"
                    message += f"🎯 Recomendação: {tip['recommended_team']}\n"
                    message += f"📊 Confiança: {tip['confidence_score']}%\n"
                    message += f"💰 EV: {tip['ev_percentage']:.1f}%\n"
                    message += f"💎 Unidades: {tip['units']}\n"
                    message += f"🏆 Liga: {tip['league']}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_tips")],
                [InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando tips: {e}")
            update.message.reply_text("❌ Erro ao buscar tips.")

    def live_matches_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /live"""
        try:
            def get_live_matches():
                try:
                    from bot_v13_railway import riot_client
                    import asyncio
                    return asyncio.run(riot_client.get_live_matches())
                except Exception as e:
                    logger.error(f"Erro ao buscar partidas: {e}")
                    return []
            
            matches = get_live_matches()
            
            if not matches:
                message = """
🔴 **PARTIDAS AO VIVO**

📭 Nenhuma partida ao vivo encontrada.

Possíveis motivos:
• Não há partidas oficiais no momento
• APIs temporariamente indisponíveis
• Região com poucas partidas ativas

⏰ Sistema verifica a cada 3 minutos
                """
            else:
                message = f"🔴 **PARTIDAS AO VIVO** ({len(matches)})\n\n"
                for i, match in enumerate(matches[:10], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team 1')
                        team2 = teams[1].get('name', 'Team 2')
                        league = match.get('league', 'Unknown')
                        game_time = match.get('game_time', 0)
                        
                        message += f"**{i}. {team1} vs {team2}**\n"
                        message += f"🏆 {league}\n"
                        message += f"⏱️ {game_time} min\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_live")],
                [InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando live: {e}")
            update.message.reply_text("❌ Erro ao buscar partidas ao vivo.")

    def schedule_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /schedule"""
        try:
            message = """
📅 **AGENDA DE PARTIDAS**

🔄 Carregando agenda...
Esta funcionalidade busca partidas agendadas para os próximos 7 dias.

⏳ Aguarde um momento...
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Carregar Agenda", callback_data="load_schedule")],
                [InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando schedule: {e}")
            update.message.reply_text("❌ Erro ao carregar agenda.")

    def monitoring_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /monitoring"""
        try:
            from bot_v13_railway import match_monitor
            
            status = match_monitor.get_monitoring_status()
            
            status_icon = "✅" if status['monitoring'] else "❌"
            thread_icon = "🟢" if status['thread_alive'] else "🔴"
            
            message = f"""
🔍 **STATUS DO MONITORAMENTO**

{status_icon} **Monitoramento:** {'Ativo' if status['monitoring'] else 'Inativo'}
{thread_icon} **Thread:** {'Rodando' if status['thread_alive'] else 'Parada'}
⏰ **Último Scan:** {status['last_scan']}
💎 **Tips Encontrados:** {status['tips_found']}
📊 **Partidas Processadas:** {status['matches_processed']}
🔄 **Intervalo:** {status['scan_interval']}
🤖 **Bot Conectado:** {'✅' if status['bot_connected'] else '❌'}

**Como Funciona:**
• Busca partidas a cada 3 minutos
• Analisa apenas jogos com dados completos
• Gera tips com critérios rigorosos
• Envia alertas automáticos
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Forçar Scan", callback_data="force_scan")],
                [InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando monitoring: {e}")
            update.message.reply_text("❌ Erro ao verificar monitoramento.")

    def force_scan_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /scan"""
        try:
            from bot_v13_railway import match_monitor
            
            update.message.reply_text("🔍 Iniciando scan manual...")
            
            def run_manual_scan():
                try:
                    asyncio.run(match_monitor._scan_live_matches_only())
                    
                    # Enviar resultado
                    tips_count = len(match_monitor.found_tips)
                    result_message = f"""
✅ **Scan Manual Completo**

💎 Tips ativos: {tips_count}
📊 Partidas processadas: {len(match_monitor.processed_matches)}
⏰ Concluído: {datetime.now().strftime('%H:%M:%S')}

Use /tips para ver os tips encontrados.
                    """
                    
                    if hasattr(update, 'message'):
                        update.message.reply_text(result_message, parse_mode='Markdown')
                        
                except Exception as e:
                    logger.error(f"Erro no scan manual: {e}")
                    if hasattr(update, 'message'):
                        update.message.reply_text(f"❌ Erro no scan: {str(e)[:100]}")
            
            # Executar em thread separada
            threading.Thread(target=run_manual_scan, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Erro no comando force_scan: {e}")
            update.message.reply_text("❌ Erro ao iniciar scan manual.")

    def callback_handler(self, update: Update, context: CallbackContext) -> None:
        """Manipulador de callbacks"""
        try:
            query = update.callback_query
            query.answer()
            
            data = query.data
            
            if data == "main_menu":
                self._handle_main_menu_callback(query)
            elif data == "current_tips" or data == "refresh_tips":
                self._handle_tips_callback(query)
            elif data == "live_matches" or data == "refresh_live":
                self._handle_live_matches_callback(query)
            elif data == "force_scan":
                self._handle_force_scan_callback(query)
            else:
                query.edit_message_text(
                    f"⚠️ Callback não implementado: {data}\n\nUse /menu para navegar.",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Erro no callback handler: {e}")

    def _handle_main_menu_callback(self, query):
        """Manipula callback do menu principal"""
        try:
            menu_text = """
🎮 **MENU PRINCIPAL - BOT LOL V3**

Escolha uma opção abaixo:
            """
            
            keyboard = [
                [InlineKeyboardButton("💎 Tips Profissionais", callback_data="tips_menu")],
                [InlineKeyboardButton("🔴 Partidas Ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton("📅 Agenda", callback_data="schedule_menu")],
                [InlineKeyboardButton("🔍 Monitoramento", callback_data="monitoring_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                menu_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no callback main_menu: {e}")

    def _handle_tips_callback(self, query) -> None:
        """Manipula callback de tips"""
        try:
            from bot_v13_railway import match_monitor
            
            tips = match_monitor.found_tips[-5:] if match_monitor.found_tips else []
            
            if not tips:
                message = """
💎 **TIPS PROFISSIONAIS**

📭 Nenhum tip ativo no momento.

O sistema monitora automaticamente e gera tips apenas quando:
• Confiança ≥ 75%
• EV ≥ 8%
• Dados completos da partida

⏰ Próximo scan: 3 minutos
                """
            else:
                message = "💎 **TIPS PROFISSIONAIS ATIVOS**\n\n"
                for i, tip in enumerate(tips, 1):
                    message += f"**{i}. {tip['teams']}**\n"
                    message += f"🎯 Recomendação: {tip['recommended_team']}\n"
                    message += f"📊 Confiança: {tip['confidence_score']}%\n"
                    message += f"💰 EV: {tip['ev_percentage']:.1f}%\n"
                    message += f"💎 Unidades: {tip['units']}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_tips")],
                [InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no callback tips: {e}")

    def _handle_live_matches_callback(self, query):
        """Manipula callback de partidas ao vivo"""
        try:
            def get_live_matches():
                try:
                    from bot_v13_railway import riot_client
                    import asyncio
                    return asyncio.run(riot_client.get_live_matches())
                except Exception as e:
                    logger.error(f"Erro ao buscar partidas: {e}")
                    return []
            
            matches = get_live_matches()
            
            if not matches:
                message = """
🔴 **PARTIDAS AO VIVO**

📭 Nenhuma partida ao vivo encontrada.

⏰ Sistema verifica a cada 3 minutos
                """
            else:
                message = f"🔴 **PARTIDAS AO VIVO** ({len(matches)})\n\n"
                for i, match in enumerate(matches[:8], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team 1')
                        team2 = teams[1].get('name', 'Team 2')
                        league = match.get('league', 'Unknown')
                        
                        message += f"**{i}. {team1} vs {team2}**\n"
                        message += f"🏆 {league}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_live")],
                [InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no callback live matches: {e}")

    def _handle_force_scan_callback(self, query):
        """Manipula callback de scan forçado"""
        try:
            query.edit_message_text("🔍 Iniciando scan manual...")
            
            def run_manual_scan():
                try:
                    from bot_v13_railway import match_monitor
                    asyncio.run(match_monitor._scan_live_matches_only())
                    
                    tips_count = len(match_monitor.found_tips)
                    result_message = f"""
✅ **Scan Manual Completo**

💎 Tips ativos: {tips_count}
📊 Partidas processadas: {len(match_monitor.processed_matches)}
⏰ Concluído: {datetime.now().strftime('%H:%M:%S')}

Use /tips para ver os tips encontrados.
                    """
                    
                    # Tentar editar a mensagem
                    keyboard = [[InlineKeyboardButton("📊 Menu Principal", callback_data="main_menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    query.edit_message_text(
                        result_message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    
                except Exception as e:
                    logger.error(f"Erro no scan manual: {e}")
                    query.edit_message_text(f"❌ Erro no scan: {str(e)[:100]}")
            
            # Executar em thread
            threading.Thread(target=run_manual_scan, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Erro no callback force_scan: {e}")

    # Comandos adicionais (stubs para compatibilidade)
    def predictions_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /predictions"""
        update.message.reply_text("📊 Funcionalidade em desenvolvimento...")

    def alerts_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /alerts"""
        update.message.reply_text("🔔 Funcionalidade em desenvolvimento...")

    def units_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /units"""
        message = """
💰 **SISTEMA DE UNIDADES PROFISSIONAL**

🎯 **Baseado em Grupos de Apostas Elite**

**Critérios para Tips:**
• Confiança mínima: 75%
• EV mínimo: 8%
• Dados completos da partida

**Cálculo de Unidades:**
• Tier 1 (LCK/LPL/LEC/LCS): Multiplicador 1.2x
• Tier 2 (Outras ligas): Multiplicador 1.0x
• EV alto (>15%): +1 unidade
• Confiança alta (>85%): +0.5 unidade

**Bankroll Padrão:** $1,000
        """
        update.message.reply_text(message, parse_mode='Markdown')

    def performance_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /performance"""
        update.message.reply_text("📈 Funcionalidade em desenvolvimento...")

    def history_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /history"""
        update.message.reply_text("📚 Funcionalidade em desenvolvimento...")

    def odds_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /odds"""
        update.message.reply_text("🎲 Funcionalidade em desenvolvimento...")

    def timesfavoritos_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /timesfavoritos"""
        update.message.reply_text("⭐ Funcionalidade em desenvolvimento...")

    def statuslol_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /statuslol"""
        try:
            from bot_v13_railway import match_monitor, riot_client
            
            message = f"""
🎮 **STATUS LOL BOT V3**

🔍 **Monitoramento:** {'✅ Ativo' if match_monitor.monitoring else '❌ Inativo'}
💎 **Tips Encontrados:** {len(match_monitor.found_tips)}
📊 **Partidas Processadas:** {len(match_monitor.processed_matches)}
⏰ **Último Scan:** {match_monitor.last_scan_time.strftime('%H:%M:%S') if match_monitor.last_scan_time else 'Nunca'}

🤖 **Sistema:** Operacional
📡 **APIs:** Riot Games + The Odds API
🔄 **Atualização:** A cada 3 minutos
            """
            
            update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erro no statuslol: {e}")
            update.message.reply_text("❌ Erro ao verificar status.") 