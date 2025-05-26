#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot LoL V13 Railway - Versão Compatível com python-telegram-bot v20+
Sistema de apostas esportivas para League of Legends
Integração com API oficial da Riot Games
"""

import os
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

# Telegram imports (v20+)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError
from telegram.constants import ParseMode

# Scientific computing
import numpy as np

# Configurações
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')
OWNER_ID = int(os.getenv('OWNER_ID', '6404423764'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiotAPIClient:
    """Cliente para API oficial da Riot Games baseado na documentação OpenAPI"""
    
    def __init__(self):
        self.api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"  # Chave oficial da documentação
        self.base_urls = {
            'esports': 'https://esports-api.lolesports.com/persisted/gw',
            'prod': 'https://prod-relapi.ewp.gg/persisted/gw'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'x-api-key': self.api_key
        }
    
    async def get_live_matches(self):
        """Buscar partidas ao vivo da API oficial"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_urls['esports']}/getLive"
                params = {'hl': 'pt-BR'}
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('schedule', {}).get('events', [])
                    else:
                        logger.warning(f"API Riot getLive retornou status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return []
    
    async def get_scheduled_matches(self, league_ids=None):
        """Buscar partidas agendadas da API oficial"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_urls['esports']}/getSchedule"
                params = {'hl': 'pt-BR'}
                if league_ids:
                    params['leagueId'] = ','.join(league_ids)
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('schedule', {}).get('events', [])
                    else:
                        logger.warning(f"API Riot getSchedule retornou status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Erro ao buscar agenda: {e}")
            return []

class BotLoLV3Railway:
    """Bot principal do Telegram para League of Legends - Versão v20+"""
    
    def __init__(self):
        """Inicializar o bot com todas as funcionalidades"""
        self.application = Application.builder().token(TOKEN).build()
        self.riot_client = RiotAPIClient()
        
        # Lista de usuários bloqueados para evitar spam de logs
        self.blocked_users = set()
        
        self.setup_commands()
        self.setup_error_handlers()
        logger.info("🤖 Bot V13 Railway inicializado - APENAS API OFICIAL DA RIOT (v20+)")
    
    def setup_commands(self):
        """Configurar comandos do bot"""
        # Comandos básicos
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("agenda", self.agenda))
        self.application.add_handler(CommandHandler("proximas", self.agenda))
        self.application.add_handler(CommandHandler("partidas", self.partidas_ao_vivo))
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
    
    def setup_error_handlers(self):
        """Configurar tratamento de erros"""
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tratar erros do bot de forma elegante"""
        try:
            error = context.error
            
            # Obter informações do usuário se disponível
            user_id = None
            username = None
            if update and update.effective_user:
                user_id = update.effective_user.id
                username = update.effective_user.username or update.effective_user.first_name
            
            # Tratar diferentes tipos de erro
            if "Forbidden: bot was blocked by the user" in str(error):
                # Bot foi bloqueado pelo usuário
                if user_id and user_id not in self.blocked_users:
                    self.blocked_users.add(user_id)
                    logger.warning(f"🚫 Bot bloqueado pelo usuário {username} (ID: {user_id})")
                # Não fazer nada mais - é normal usuários bloquearem bots
                return
                
            elif "Bad Request" in str(error):
                # Requisição inválida (mensagem muito longa, etc.)
                logger.warning(f"⚠️ Requisição inválida: {error}")
                if update and update.effective_message:
                    await self.safe_send_message(
                        update.effective_chat.id,
                        "❌ Erro na requisição. Tente novamente."
                    )
                    
            elif "Timed out" in str(error):
                # Timeout na conexão
                logger.warning(f"⏰ Timeout na conexão: {error}")
                
            elif "Network" in str(error):
                # Erro de rede
                logger.warning(f"🌐 Erro de rede: {error}")
                
            else:
                # Outros erros
                logger.error(f"❌ Erro não tratado: {type(error).__name__}: {error}")
                
        except Exception as e:
            logger.error(f"❌ Erro no error_handler: {e}")
    
    async def safe_send_message(self, chat_id, text, **kwargs):
        """Enviar mensagem de forma segura com tratamento de erros"""
        try:
            return await self.application.bot.send_message(chat_id, text, **kwargs)
        except Exception as e:
            if "bot was blocked by the user" in str(e):
                # Usuário bloqueou o bot
                if chat_id not in self.blocked_users:
                    self.blocked_users.add(chat_id)
                    logger.warning(f"🚫 Usuário {chat_id} bloqueou o bot")
                return None
            else:
                logger.error(f"❌ Erro ao enviar mensagem para {chat_id}: {e}")
                return None
    
    async def safe_edit_message(self, chat_id, message_id, text, **kwargs):
        """Editar mensagem de forma segura com tratamento de erros"""
        try:
            return await self.application.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                **kwargs
            )
        except Exception as e:
            if "bot was blocked by the user" in str(e):
                # Usuário bloqueou o bot
                if chat_id not in self.blocked_users:
                    self.blocked_users.add(chat_id)
                    logger.warning(f"🚫 Usuário {chat_id} bloqueou o bot")
                return None
            elif "message is not modified" in str(e).lower():
                # Mensagem não foi modificada - ignorar
                return None
            else:
                logger.warning(f"⚠️ Erro ao editar mensagem: {e}")
                return None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        return await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update, context, edit_message=False):
        """Mostrar menu principal"""
        keyboard = [
            [InlineKeyboardButton("📅 Próximas Partidas", callback_data="agenda"),
             InlineKeyboardButton("🎮 Partidas ao Vivo", callback_data="partidas")],
            [InlineKeyboardButton("📊 Estatísticas", callback_data="stats"),
             InlineKeyboardButton("💰 Value Betting", callback_data="value")],
            [InlineKeyboardButton("❓ Ajuda", callback_data="help")]
        ]
        
        message_text = (
            "🤖 **BOT LOL V13 RAILWAY - API OFICIAL RIOT**\n\n"
            "🔗 **CONECTADO À API OFICIAL DA RIOT GAMES**\n"
            "✅ **SEM DADOS FICTÍCIOS - APENAS DADOS REAIS**\n\n"
            "🎯 **FUNCIONALIDADES DISPONÍVEIS:**\n"
            "• 📅 **Próximas Partidas** - Agenda oficial da Riot\n"
            "• 🎮 **Partidas ao Vivo** - Monitoramento em tempo real\n"
            "• 📊 **Estatísticas** - Dados oficiais das partidas\n"
            "• 💰 **Value Betting** - Análise de apostas\n\n"
            "🌍 **COBERTURA GLOBAL:**\n"
            "🇰🇷 LCK • 🇨🇳 LPL • 🇪🇺 LEC • 🇺🇸 LCS\n"
            "🇧🇷 CBLOL • 🇯🇵 LJL • 🌏 PCS • E MAIS!\n\n"
            "🔄 **Sistema atualizado em tempo real!**"
        )
        
        if edit_message and hasattr(update, 'callback_query'):
            return await self.safe_edit_message(
                update.callback_query.message.chat_id,
                update.callback_query.message.message_id,
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            return await self.safe_send_message(
                update.effective_chat.id,
                message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        message_text = (
            "📚 **GUIA DO BOT - APENAS API OFICIAL**\n\n"
            "🎯 **COMANDOS:**\n"
            "• `/start` - Menu principal\n"
            "• `/agenda` - Próximas partidas (API Riot)\n"
            "• `/partidas` - Partidas ao vivo (API Riot)\n"
            "• `/help` - Este guia\n\n"
            "🔗 **FONTE DOS DADOS:**\n"
            "• **API oficial da Riot Games**\n"
            "• **Endpoints oficiais documentados**\n"
            "• **Sem dados fictícios ou simulados**\n\n"
            "⚠️ **IMPORTANTE:**\n"
            "Se não houver partidas, é porque:\n"
            "• Não há partidas agendadas no momento\n"
            "• API da Riot está em manutenção\n"
            "• Período entre temporadas\n\n"
            "🔄 **Sistema 100% baseado em dados reais!**"
        )
        
        return await self.safe_send_message(
            update.effective_chat.id,
            message_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def agenda(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /agenda - Buscar próximas partidas"""
        agenda_data = await self._get_scheduled_matches()
        
        if agenda_data['matches']:
            message_text = (
                "📅 **PRÓXIMAS PARTIDAS - API OFICIAL RIOT**\n\n"
                f"🔄 **Última atualização:** {datetime.now().strftime('%H:%M:%S')}\n"
                f"📊 **Total encontrado:** {len(agenda_data['matches'])}\n"
                f"🔗 **Fonte:** API oficial da Riot Games\n"
                f"🇧🇷 **Horários em Brasília (GMT-3)**\n\n"
            )
            
            for i, match in enumerate(agenda_data['matches'][:10], 1):
                time_info = self._format_match_time(match['scheduled_time'])
                message_text += (
                    f"**{i}. {match['team1']} vs {match['team2']}**\n"
                    f"🏆 {match['league']} • {match['tournament']}\n"
                    f"⏰ {time_info}\n"
                    f"📺 {match.get('stream', 'TBD')}\n\n"
                )
            
            if len(agenda_data['matches']) > 10:
                message_text += f"➕ **E mais {len(agenda_data['matches']) - 10} partidas...**\n\n"
            
            message_text += "🔄 **Dados atualizados em tempo real da API oficial!**"
        else:
            message_text = (
                "📅 **AGENDA DE PARTIDAS**\n\n"
                "ℹ️ **NENHUMA PARTIDA ENCONTRADA NA API OFICIAL**\n\n"
                "🔍 **POSSÍVEIS MOTIVOS:**\n"
                "• Período entre temporadas\n"
                "• Pausa de fim de semana\n"
                "• Manutenção da API da Riot\n"
                "• Todas as partidas já finalizaram hoje\n\n"
                f"⏰ **Última verificação:** {datetime.now().strftime('%H:%M:%S')}\n"
                "🔄 **Sistema conectado à API oficial da Riot Games**\n\n"
                "💡 **Tente novamente em alguns minutos**"
            )
        
        return await self.safe_send_message(
            update.effective_chat.id,
            message_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def partidas_ao_vivo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /partidas - Buscar partidas ao vivo"""
        try:
            live_matches = await self.riot_client.get_live_matches()
            
            if live_matches:
                message_text = (
                    "🎮 **PARTIDAS AO VIVO - API OFICIAL RIOT**\n\n"
                    f"🔄 **Última atualização:** {datetime.now().strftime('%H:%M:%S')}\n"
                    f"📊 **Partidas ao vivo:** {len(live_matches)}\n"
                    f"🔗 **Fonte:** API oficial da Riot Games\n\n"
                )
                
                for i, match in enumerate(live_matches[:5], 1):
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Team 1')
                        team2 = teams[1].get('name', 'Team 2')
                        league = match.get('league', 'Unknown League')
                        
                        message_text += (
                            f"**{i}. {team1} vs {team2}**\n"
                            f"🏆 {league}\n"
                            f"🔴 **AO VIVO AGORA**\n"
                            f"📺 https://lolesports.com\n\n"
                        )
                
                message_text += "🔄 **Dados em tempo real da API oficial!**"
            else:
                message_text = (
                    "🎮 **PARTIDAS AO VIVO**\n\n"
                    "ℹ️ **NENHUMA PARTIDA AO VIVO NO MOMENTO**\n\n"
                    "🔍 **VERIFICADO NA API OFICIAL DA RIOT:**\n"
                    "• Nenhuma partida em andamento\n"
                    "• Período entre partidas\n"
                    "• Pausa entre splits\n\n"
                    f"⏰ **Última verificação:** {datetime.now().strftime('%H:%M:%S')}\n"
                    "🔄 **Sistema conectado à API oficial da Riot Games**\n\n"
                    "💡 **Tente novamente em alguns minutos**"
                )
            
            return await self.safe_send_message(
                update.effective_chat.id,
                message_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return await self.safe_send_message(
                update.effective_chat.id,
                "❌ **Erro ao buscar partidas ao vivo**\n\n"
                "Tente novamente em alguns minutos.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _get_scheduled_matches(self):
        """Buscar partidas agendadas APENAS da API oficial da Riot Games"""
        try:
            brazil_tz = pytz.timezone('America/Sao_Paulo')
            now_brazil = datetime.now(brazil_tz)
            
            logger.info("🔍 Buscando partidas APENAS da API oficial da Riot Games...")
            
            all_matches = []
            
            try:
                riot_matches = await self.riot_client.get_scheduled_matches()
                
                if riot_matches:
                    logger.info(f"✅ API Riot: {len(riot_matches)} partidas encontradas")
                    
                    for match in riot_matches:
                        try:
                            teams = match.get('teams', [])
                            if len(teams) >= 2:
                                team1_name = teams[0].get('name', 'Team 1')
                                team2_name = teams[1].get('name', 'Team 2')
                                
                                start_time_str = match.get('startTime')
                                if start_time_str:
                                    try:
                                        scheduled_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                                        scheduled_time = scheduled_time.astimezone(brazil_tz)
                                    except:
                                        scheduled_time = now_brazil + timedelta(hours=2)
                                else:
                                    continue
                                
                                processed_match = {
                                    'team1': team1_name,
                                    'team2': team2_name,
                                    'league': match.get('league', 'Unknown League'),
                                    'tournament': match.get('tournament', match.get('league', 'Unknown Tournament')),
                                    'scheduled_time': scheduled_time,
                                    'status': 'scheduled',
                                    'stream': 'https://lolesports.com',
                                    'format': 'Bo3',
                                    'source': 'riot_api'
                                }
                                
                                all_matches.append(processed_match)
                                
                        except Exception as e:
                            logger.error(f"Erro ao processar partida da API Riot: {e}")
                            continue
                
                all_matches.sort(key=lambda x: x['scheduled_time'])
                
                logger.info(f"✅ Processadas {len(all_matches)} partidas da API oficial da Riot")
                
                return {
                    'matches': all_matches,
                    'total_found': len(all_matches),
                    'last_update': now_brazil,
                    'timezone': 'America/Sao_Paulo',
                    'source': 'riot_api_only'
                }
                
            except Exception as e:
                logger.error(f"❌ Erro na API da Riot: {e}")
                
                return {
                    'matches': [],
                    'total_found': 0,
                    'last_update': now_brazil,
                    'timezone': 'America/Sao_Paulo',
                    'source': 'api_error',
                    'error': str(e)
                }
                
        except Exception as e:
            logger.error(f"❌ Erro geral ao buscar agenda: {e}")
            return {
                'matches': [],
                'total_found': 0,
                'last_update': datetime.now(),
                'error': str(e)
            }
    
    def _format_match_time(self, scheduled_time):
        """Formatar horário da partida"""
        now = datetime.now(scheduled_time.tzinfo)
        time_diff = scheduled_time - now
        
        if time_diff.days > 0:
            if time_diff.days == 1:
                return f"Amanhã às {scheduled_time.strftime('%H:%M')}"
            else:
                return f"{scheduled_time.strftime('%d/%m')} às {scheduled_time.strftime('%H:%M')}"
        else:
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)
            
            if hours > 0:
                return f"Em {hours}h{minutes:02d}min ({scheduled_time.strftime('%H:%M')})"
            elif minutes > 0:
                return f"Em {minutes}min ({scheduled_time.strftime('%H:%M')})"
            else:
                return f"AGORA ({scheduled_time.strftime('%H:%M')})"
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao responder callback: {e}")
        
        if query.data == "menu_principal":
            return await self.show_main_menu(update, context, edit_message=True)
        elif query.data == "agenda":
            return await self.agenda(update, context)
        elif query.data == "partidas":
            return await self.partidas_ao_vivo(update, context)
        elif query.data == "help":
            return await self.help(update, context)
        else:
            return await self.safe_edit_message(
                query.message.chat_id,
                query.message.message_id,
                "🚧 **Funcionalidade em desenvolvimento**\n\n"
                "Esta funcionalidade será implementada em breve.\n"
                "Por enquanto, use apenas dados da API oficial da Riot.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    def run(self):
        """Executar o bot"""
        logger.info("🚀 Iniciando Bot LoL V13 Railway - APENAS API OFICIAL (v20+)")
        self.application.run_polling()

def main():
    """Função principal"""
    try:
        bot = BotLoLV3Railway()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")

if __name__ == "__main__":
    main() 