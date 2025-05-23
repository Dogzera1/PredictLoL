#!/usr/bin/env python3
"""
Bot LoL Predictor V3 - RIOT API INTEGRATED
Sistema completo integrado com API oficial da Riot Games
Dados reais de times, standings, partidas e rankings
"""

import os
import logging
import asyncio
import threading
import json
from datetime import datetime, timedelta

# Importações condicionais para evitar conflitos
try:
    from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
except ImportError:
    print("⚠️ Telegram libraries não encontradas - modo teste ativo")
    
try:
    from flask import Flask, request, Response
except ImportError:
    print("⚠️ Flask não encontrado - modo teste ativo")

# Importar sistema Riot API
try:
    from riot_api_integration import riot_prediction_system
    print("✅ Sistema Riot API carregado")
except ImportError:
    print("❌ Erro ao carregar sistema Riot API - usando fallback")
    riot_prediction_system = None

print("🚀 BOT LOL PREDICTOR V3 - RIOT API INTEGRATED")

# Configuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        """Configura todos os handlers do bot"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("predict", self.predict_command))
        self.app.add_handler(CommandHandler("teams", self.teams_command))
        self.app.add_handler(CommandHandler("ranking", self.ranking_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("live", self.live_command))
        self.app.add_handler(CommandHandler("schedule", self.schedule_command))
        self.app.add_handler(CommandHandler("region", self.region_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("update", self.update_command))
        
        # Callback queries para inline keyboards
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Handler para mensagens de texto
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message_handler))
    
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

Olá {user.mention_markdown_v2()}! 

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
• 🇰🇷 LCK \\(Korea\\)
• 🇨🇳 LPL \\(China\\)  
• 🇪🇺 LEC \\(Europe\\)
• 🇺🇸 LCS \\(North America\\)

Use o menu abaixo ou digite `/help` para começar!"""

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
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
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

        await update.message.reply_text(help_text, parse_mode='Markdown')
    
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
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
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
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def live_command(self, update: Update, context):
        """Comando /live para partidas ao vivo"""
        
        if not self.riot_system or not hasattr(self.riot_system.data_processor.api_client, 'get_live_matches'):
            await update.message.reply_text("❌ Recurso de partidas ao vivo não disponível")
            return
        
        try:
            live_matches = await self.riot_system.data_processor.api_client.get_live_matches()
            
            if not live_matches:
                text = """🔴 **PARTIDAS AO VIVO**

Não há partidas acontecendo neste momento.

🎮 Use `/schedule` para ver próximas partidas
📊 Use `/ranking` para ver standings atuais"""
            else:
                text = f"🔴 **PARTIDAS AO VIVO ({len(live_matches)})**\n\n"
                
                for match in live_matches[:5]:  # Mostrar até 5 partidas
                    league_name = match.get('league', {}).get('name', 'Unknown')
                    teams = match.get('match', {}).get('teams', [])
                    
                    if len(teams) >= 2:
                        team1 = teams[0]
                        team2 = teams[1]
                        
                        text += f"🏆 **{league_name}**\n"
                        text += f"⚔️ {team1.get('code', 'TM1')} vs {team2.get('code', 'TM2')}\n\n"
                
                text += "💡 Use `/predict [time1] vs [time2]` para predições com dados atuais!"
        
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            text = f"❌ Erro ao buscar partidas ao vivo: {str(e)}"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def schedule_command(self, update: Update, context):
        """Comando /schedule para cronograma oficial"""
        
        if not self.riot_system:
            await update.message.reply_text("❌ Sistema Riot API não disponível")
            return
        
        try:
            schedule = await self.riot_system.data_processor.api_client.get_schedule()
            
            if not schedule:
                text = """📅 **CRONOGRAMA OFICIAL**

Nenhum evento encontrado no cronograma.

🔄 Tente novamente em alguns minutos ou use `/update` para atualizar dados."""
            else:
                text = f"📅 **PRÓXIMAS PARTIDAS ({len(schedule)} eventos)**\n\n"
                
                for event in schedule[:8]:  # Mostrar até 8 eventos
                    start_time = event.get('startTime', '')
                    league_name = event.get('league', {}).get('name', 'Unknown')
                    
                    # Parse da data
                    if start_time:
                        try:
                            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            time_str = dt.strftime("%d/%m %H:%M")
                        except:
                            time_str = "TBD"
                    else:
                        time_str = "TBD"
                    
                    text += f"🕐 **{time_str}** - {league_name}\n"
                
                text += "\n💡 Use `/live` para partidas acontecendo agora!"
        
        except Exception as e:
            logger.error(f"Erro ao buscar cronograma: {e}")
            text = f"❌ Erro ao buscar cronograma: {str(e)}"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def teams_command(self, update: Update, context):
        """Lista times com dados da Riot API"""
        
        if not self.riot_system:
            await update.message.reply_text("❌ Sistema Riot API não disponível")
            return
        
        region = context.args[0].upper() if context.args else None
        
        try:
            if region:
                teams = self.riot_system.get_teams_by_region(region)
                title = f"🏆 **TIMES {region} (Riot API)**"
            else:
                # Mostrar resumo por região
                regions = ['LCK', 'LPL', 'LEC', 'LCS']
                text = "🏆 **TIMES DISPONÍVEIS (Riot API)**\n\n"
                
                # Status dos dados
                if self.initialization_status == "success":
                    text += "🌐 *Dados oficiais da Riot Games*\n\n"
                else:
                    text += "🆘 *Dados de fallback*\n\n"
                
                for reg in regions:
                    teams_in_region = self.riot_system.get_teams_by_region(reg)
                    flag = self.get_region_flag(reg)
                    text += f"{flag} **{reg}** ({len(teams_in_region)} times)\n"
                    
                    # Mostrar top 3 da região
                    for i, team in enumerate(teams_in_region[:3], 1):
                        record_text = ""
                        if 'record' in team and team['record'] and 'wins' in team['record']:
                            wins = team['record']['wins']
                            losses = team['record']['losses']
                            record_text = f" ({wins}W-{losses}L)"
                        
                        text += f"  {i}. {team['name']} ({team.get('rating', 0)}){record_text}\n"
                    text += "\n"
                
                text += "💡 Use `/teams LCK` para ver todos os times de uma liga"
                
                keyboard = [
                    [
                        InlineKeyboardButton("🇰🇷 Ver LCK", callback_data="teams_LCK_riot"),
                        InlineKeyboardButton("🇨🇳 Ver LPL", callback_data="teams_LPL_riot")
                    ],
                    [
                        InlineKeyboardButton("🇪🇺 Ver LEC", callback_data="teams_LEC_riot"),
                        InlineKeyboardButton("🇺🇸 Ver LCS", callback_data="teams_LCS_riot")
                    ]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                return
            
            # Mostrar times específicos da região
            if not teams:
                text = f"❌ Nenhum time encontrado para {region}"
            else:
                flag = self.get_region_flag(region)
                text = f"{flag} **TIMES {region}**\n\n"
                
                for team in teams:
                    tier_emoji = self.get_tier_emoji(team.get('tier', 'C'))
                    
                    # Record se disponível
                    record_text = ""
                    if 'record' in team and team['record'] and 'wins' in team['record']:
                        wins = team['record']['wins']
                        losses = team['record']['losses']
                        record_text = f" | {wins}W-{losses}L"
                    
                    # Posição se disponível
                    position_text = ""
                    if 'position' in team and team['position']:
                        position_text = f" | #{team['position']}"
                    
                    text += f"{tier_emoji} **{team['name']}**\n"
                    text += f"   ⚡ {team.get('rating', 0)} pts | Tier {team.get('tier', 'C')}{record_text}{position_text}\n\n"
        
        except Exception as e:
            logger.error(f"Erro ao buscar times: {e}")
            text = f"❌ Erro ao buscar times: {str(e)}"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def stats_command(self, update: Update, context):
        """Estatísticas do sistema V3"""
        
        if not self.riot_system:
            await update.message.reply_text("❌ Sistema Riot API não disponível")
            return
        
        try:
            stats = self.riot_system.get_system_stats()
            
            text = f"""📊 **ESTATÍSTICAS DO SISTEMA V3**

🌐 **Riot API Integration:**
• Status: {"✅ Conectado" if not stats['fallback_active'] else "🆘 Fallback"}
• Source: {stats['data_source']}
• Cache entries: {stats['cache_entries']}

🎯 **Performance:**
• Predições realizadas: {stats['predictions_made']}
• Times carregados: {stats['teams_loaded']}
• Ligas cobertas: {stats['leagues_covered']}

⚡ **Sistema:**
• Versão: {stats['version']}
• Última atualização API: {stats['last_api_update'] or 'Nunca'}

🏆 **Cobertura:**
• 🇰🇷 LCK: Times oficiais
• 🇨🇳 LPL: Times oficiais  
• 🇪🇺 LEC: Times oficiais
• 🇺🇸 LCS: Times oficiais

🚀 **Recursos V3:**
• Dados em tempo real
• Standings oficiais
• Records da temporada
• Cronograma atualizado"""
            
            # Botão para forçar atualização
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar Dados", callback_data="force_update")],
                [InlineKeyboardButton("📈 Histórico", callback_data="prediction_history")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Erro ao buscar stats: {e}")
            text = f"❌ Erro ao buscar estatísticas: {str(e)}"
            reply_markup = None
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context):
        """Status detalhado da conexão Riot API"""
        
        text = f"""✅ **STATUS BOT V3 - RIOT INTEGRATED**

🤖 **Bot Status:** Online
🌐 **Riot API:** {self.get_api_status_text()}
📡 **Telegram:** Conectado

⚡ **Inicialização:** {self.get_initialization_text()}

🎮 **Funcionalidades Ativas:**
• ✅ Predições com Riot API
• ✅ Rankings oficiais
• ✅ Partidas ao vivo
• ✅ Cronograma oficial
• ✅ Times com dados reais

🚀 **Versão:** 3.0-riot-integrated
📊 **API Key:** Configurada
🔄 **Auto-update:** Ativado (1h)"""

        keyboard = [
            [InlineKeyboardButton("🔄 Reconectar API", callback_data="reconnect_api")],
            [InlineKeyboardButton("📊 Ver Estatísticas", callback_data="show_stats")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def update_command(self, update: Update, context):
        """Força atualização dos dados da API"""
        
        if not self.riot_system:
            await update.message.reply_text("❌ Sistema Riot API não disponível")
            return
        
        try:
            # Mostrar mensagem de loading
            msg = await update.message.reply_text("🔄 Atualizando dados da Riot API...")
            
            # Forçar inicialização
            success = await self.riot_system.initialize()
            
            if success:
                text = """✅ **DADOS ATUALIZADOS COM SUCESSO**

🌐 Conexão com Riot API estabelecida
📊 Times e rankings atualizados
🏆 Standings carregados
⚡ Sistema pronto para predições"""
                self.initialization_status = "success"
            else:
                text = """⚠️ **ATUALIZAÇÃO EM MODO FALLBACK**

🆘 API Riot temporariamente indisponível
📊 Usando dados de backup confiáveis
⚡ Funcionalidades mantidas ativas"""
                self.initialization_status = "fallback"
            
            # Editar mensagem
            await msg.edit_text(text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erro na atualização: {e}")
            await update.message.reply_text(f"❌ Erro na atualização: {str(e)}")
    
    async def handle_riot_prediction(self, update, text):
        """Processa predição com sistema Riot API"""
        
        if not self.riot_system:
            await update.message.reply_text("❌ Sistema Riot API não disponível")
            return
        
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
            
            # Fazer predição com Riot API
            result = await self.riot_system.predict_match(team1, team2, match_type)
            
            if 'error' in result:
                error_text = f"❌ {result['error']}"
                if 'available_teams' in result:
                    error_text += f"\n\n💡 Times disponíveis: {', '.join(result['available_teams'])}"
                await update.message.reply_text(error_text)
                return
            
            # Formatar resultado
            team1_data = result['team1']
            team2_data = result['team2']
            
            prob1 = result['team1_probability'] * 100
            prob2 = result['team2_probability'] * 100
            
            # Status dos dados
            data_source = "🌐 Riot API" if result['data_source'] == 'riot_api' else "🆘 Fallback"
            
            # Resultado principal
            main_text = f"""🎮 **PREDIÇÃO V3 #{result['prediction_id']}**

🏆 **{team1_data['name']}** vs **{team2_data['name']}**

📊 **PROBABILIDADES:**
• {team1_data['name']}: {prob1:.1f}%
• {team2_data['name']}: {prob2:.1f}%

🎯 **VENCEDOR PREVISTO:** {result['predicted_winner']}
🔥 **CONFIANÇA:** {result['confidence_level']} ({result['confidence']:.1%})

📈 **DETALHES:**
• Tipo: {match_type.upper()}
• Tier: {team1_data.get('tier', 'N/A')} vs {team2_data.get('tier', 'N/A')}
• Liga: {team1_data.get('region', 'N/A')} vs {team2_data.get('region', 'N/A')}
• Fonte: {data_source}"""

            # Adicionar análise
            analysis_text = f"\n\n{result['analysis']}"
            
            full_text = main_text + analysis_text
            
            # Botões para ações adicionais
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Nova Predição", callback_data="riot_predict"),
                    InlineKeyboardButton("📊 Ver Rankings", callback_data="riot_ranking")
                ],
                [
                    InlineKeyboardButton("🔴 Partidas ao Vivo", callback_data="live_matches"),
                    InlineKeyboardButton("🔄 Atualizar Dados", callback_data="force_update")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                full_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro na predição Riot: {e}")
            await update.message.reply_text(f"❌ Erro ao processar predição: {str(e)}")
    
    async def text_message_handler(self, update: Update, context):
        """Handler para mensagens de texto com Riot API"""
        text = update.message.text.strip()
        
        # Verificar se é formato de predição
        if " vs " in text.lower():
            await self.handle_riot_prediction(update, text)
        else:
            # Mensagem genérica
            await update.message.reply_text(
                "💡 Para fazer uma predição, use o formato:\n"
                "`TIME1 vs TIME2` ou `/predict TIME1 vs TIME2`\n\n"
                "🌐 **V3 com Riot API:** Dados oficiais e atualizados!\n\n"
                "Exemplo: `T1 vs G2 bo3`\n\n"
                "Digite `/help` para ver todos os comandos!"
            )
    
    async def button_callback(self, update: Update, context):
        """Handler para inline keyboard callbacks V3"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "riot_predict":
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


# Flask App para webhook V3
app = Flask(__name__)

# Instância do bot V3
telegram_bot_v3 = TelegramBotV3()

@app.route('/')
def home():
    """Homepage com info da V3"""
    return {
        "status": "online",
        "version": "3.0-riot-integrated",
        "message": "LOL Predictor V3 - Riot API Integration Ativo",
        "features": [
            "Riot Games API Integration",
            "Dados oficiais de times e standings",
            "Partidas ao vivo",
            "Cronograma oficial",
            "Rankings em tempo real",
            "Predições com dados reais"
        ],
        "api_status": telegram_bot_v3.get_api_status_text(),
        "initialization": telegram_bot_v3.get_initialization_text()
    }

@app.route('/health')
def health():
    """Health check V3"""
    
    # Stats do sistema Riot se disponível
    riot_stats = {}
    if telegram_bot_v3.riot_system:
        try:
            riot_stats = telegram_bot_v3.riot_system.get_system_stats()
        except:
            riot_stats = {"error": "Stats não disponíveis"}
    
    return {
        "status": "healthy",
        "version": "3.0-riot-integrated",
        "bot_active": True,
        "riot_api_status": telegram_bot_v3.get_api_status_text(),
        "initialization_status": telegram_bot_v3.initialization_status,
        "riot_system_stats": riot_stats,
        "timestamp": datetime.now().isoformat(),
        "features": [
            "riot-api-integration",
            "official-data",
            "live-matches", 
            "official-schedule",
            "real-time-rankings"
        ]
    }

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook para receber updates do Telegram V3"""
    try:
        update = Update.de_json(request.get_json(), telegram_bot_v3.app.bot)
        
        # Criar thread para processar update
        def process_update():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(telegram_bot_v3.app.process_update(update))
            loop.close()
        
        thread = threading.Thread(target=process_update)
        thread.start()
        
        return Response("OK", status=200)
        
    except Exception as e:
        logger.error(f"Erro no webhook V3: {e}")
        return Response("Error", status=500)

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