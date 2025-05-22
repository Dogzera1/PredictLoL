"""
Manipuladores de comandos para o bot do Telegram.

Define handlers para comandos como /start, /ao_vivo, etc.
"""

import logging
import sys
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

# Adicionar diretório raiz ao path para importar outros módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import riot_api, predictor
from services import formatter
from utils import emoji
from config import MSG_LOADING, MSG_NO_MATCHES, MSG_ERROR

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Instanciar serviços
predictor_service = predictor.PredictorService()

def error_handler(update: Update, context: CallbackContext):
    """Handler de erro global"""
    logger.error(f"Erro durante processamento: {context.error}")
    
    if update and update.effective_message:
        update.effective_message.reply_text(
            f"{emoji.ERROR} Ocorreu um erro durante o processamento do seu comando. "
            "Por favor, tente novamente mais tarde."
        )

def start_handler(update: Update, context: CallbackContext):
    """Handler para o comando /start"""
    user = update.effective_user
    
    # Mensagem de boas-vindas
    welcome_message = (
        f"{emoji.INFO} Olá, {user.first_name}! Bem-vindo ao LoL-GPT Betting Assistant!\n\n"
        f"Este bot utiliza Machine Learning para analisar partidas de League of Legends "
        f"e fornecer previsões para apostas.\n\n"
        f"Selecione uma opção:"
    )
    
    # Botões para navegação inicial
    keyboard = [
        [InlineKeyboardButton(f"{emoji.LIVE} Partidas Ao Vivo", callback_data="live_matches")],
        [InlineKeyboardButton(f"{emoji.SCHEDULED} Próximas Partidas", callback_data="upcoming_matches")],
        [InlineKeyboardButton(f"{emoji.INFO} Sobre o Bot", callback_data="about")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Enviar mensagem com botões
    update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def help_handler(update: Update, context: CallbackContext):
    """Handler para o comando /ajuda"""
    help_message = (
        f"{emoji.INFO} *Comandos do LoL-GPT Betting Assistant*\n\n"
        f"{emoji.LIVE} */ao_vivo* - Ver partidas que estão acontecendo agora e suas previsões\n"
        f"{emoji.SCHEDULED} */proximas* - Ver próximas partidas agendadas\n"
        f"{emoji.MATCH} */partida [id]* - Ver detalhes de uma partida específica\n"
        f"{emoji.INFO} */sobre* - Informações sobre o bot\n"
        f"{emoji.HOME} */ajuda* - Mostrar esta mensagem\n\n"
        f"Para mais detalhes, use o comando específico seguido de 'ajuda'.\n"
        f"Exemplo: */ao_vivo ajuda*"
    )
    
    update.message.reply_text(help_message, parse_mode="Markdown")

def about_handler(update: Update, context: CallbackContext):
    """Handler para o comando /sobre"""
    about_message = (
        f"{emoji.INFO} *Sobre o LoL-GPT Betting Assistant*\n\n"
        f"Este bot utiliza modelos de Machine Learning para analisar partidas de League of Legends "
        f"e fornecer previsões para apostas.\n\n"
        f"Versão: *1.0.0*\n"
        f"Dados: API Lolesports\n"
        f"Modelo: Algoritmo preditivo baseado em estatísticas e histórico\n\n"
        f"O bot foi desenvolvido para fins educacionais e para auxiliar apostadores "
        f"com análises objetivas e baseadas em dados."
    )
    
    # Botões para navegação
    keyboard = [
        [InlineKeyboardButton(f"{emoji.LIVE} Partidas Ao Vivo", callback_data="live_matches")],
        [InlineKeyboardButton(f"{emoji.HOME} Menu Principal", callback_data="start")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(about_message, reply_markup=reply_markup, parse_mode="Markdown")

def live_matches_handler(update: Update, context: CallbackContext):
    """Handler para o comando /ao_vivo"""
    # Verificar se é ajuda para comando
    if len(context.args) > 0 and context.args[0].lower() == "ajuda":
        help_text = (
            f"{emoji.LIVE} *Comando /ao_vivo*\n\n"
            f"Este comando mostra as partidas de LoL que estão acontecendo neste momento.\n\n"
            f"Para cada partida, você poderá ver:\n"
            f"• Nome dos times\n"
            f"• Competição/torneio\n"
            f"• Placar atual\n\n"
            f"Você pode selecionar uma partida para ver mais detalhes e previsões."
        )
        update.message.reply_text(help_text, parse_mode="Markdown")
        return
    
    # Enviar mensagem de espera
    loading_message = update.message.reply_text(
        MSG_LOADING,
        parse_mode="Markdown"
    )
    
    try:
        # Buscar partidas ao vivo
        matches = riot_api.get_live_matches()
        
        # Se não há partidas, mostrar mensagem e sugerir ver próximas
        if not matches:
            # Tentar dados mockados para debug se necessário
            if context.args and context.args[0] == "debug":
                matches = riot_api.get_mock_live_matches()
            # Se ainda não há partidas, mostrar mensagem
            if not matches:
                # Criar botões para outras opções
                keyboard = [
                    [InlineKeyboardButton(f"{emoji.SCHEDULED} Ver Próximas Partidas", callback_data="upcoming_matches")],
                    [InlineKeyboardButton(f"{emoji.HOME} Menu Principal", callback_data="start")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Deletar mensagem de carregamento
                try:
                    context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=loading_message.message_id
                    )
                except:
                    pass
                
                update.message.reply_text(
                    MSG_NO_MATCHES,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return
        
        # Formatar lista de partidas
        formatted_list = formatter.format_match_list(matches)
        
        # Criar botões para cada partida
        keyboard = []
        for i, match in enumerate(matches):
            match_id = match.get('match_id', f"match_{i}")
            team_a = match.get('teamA', 'Time A')
            team_b = match.get('teamB', 'Time B')
            
            # Texto do botão
            button_text = f"{emoji.DETAILS} Ver detalhes"
            
            # Callback data
            callback_data = f"match_{match_id}"
            
            # Adicionar botão para a partida
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Adicionar botões de navegação
        keyboard.append([
            InlineKeyboardButton(f"{emoji.REFRESH} Atualizar", callback_data="refresh_live_matches"),
            InlineKeyboardButton(f"{emoji.SCHEDULED} Próximas", callback_data="upcoming_matches")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Deletar mensagem de carregamento
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
        
        # Enviar lista de partidas
        message = update.message.reply_text(
            formatted_list,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Armazenar partidas no contexto para uso futuro
        if not context.user_data:
            context.user_data = {}
        
        context.user_data['live_matches'] = matches
        
    except Exception as e:
        logger.error(f"Erro ao buscar partidas ao vivo: {str(e)}")
        
        # Tentar deletar mensagem de carregamento
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
            
        update.message.reply_text(MSG_ERROR, parse_mode="Markdown")

def upcoming_matches_handler(update: Update, context: CallbackContext):
    """Handler para o comando /proximas"""
    # Verificar se é ajuda para comando
    if len(context.args) > 0 and context.args[0].lower() == "ajuda":
        help_text = (
            f"{emoji.SCHEDULED} *Comando /proximas*\n\n"
            f"Este comando mostra as próximas partidas de LoL agendadas.\n\n"
            f"Para cada partida, você poderá ver:\n"
            f"• Nome dos times\n"
            f"• Competição/torneio\n"
            f"• Data e horário de início\n\n"
        )
        update.message.reply_text(help_text, parse_mode="Markdown")
        return
    
    # Enviar mensagem de espera
    loading_message = update.message.reply_text(
        MSG_LOADING,
        parse_mode="Markdown"
    )
    
    try:
        # Buscar próximas partidas (até 8)
        matches = riot_api.get_upcoming_matches(count=8)
        
        # Se não há partidas, mostrar mensagem
        if not matches:
            # Criar botões para outras opções
            keyboard = [
                [InlineKeyboardButton(f"{emoji.LIVE} Ver Partidas ao Vivo", callback_data="live_matches")],
                [InlineKeyboardButton(f"{emoji.HOME} Menu Principal", callback_data="start")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Deletar mensagem de carregamento
            try:
                context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=loading_message.message_id
                )
            except:
                pass
            
            update.message.reply_text(
                f"{emoji.WARNING} Não há próximas partidas agendadas disponíveis.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        # Formatar lista de próximas partidas
        formatted_list = formatter.format_upcoming_matches(matches)
        
        # Criar botões de navegação
        keyboard = [
            [InlineKeyboardButton(f"{emoji.LIVE} Ver Partidas ao Vivo", callback_data="live_matches")],
            [InlineKeyboardButton(f"{emoji.REFRESH} Atualizar", callback_data="refresh_upcoming")],
            [InlineKeyboardButton(f"{emoji.HOME} Menu Principal", callback_data="start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Deletar mensagem de carregamento
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
        
        # Enviar lista de próximas partidas
        update.message.reply_text(
            formatted_list,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Armazenar partidas no contexto para uso futuro
        if not context.user_data:
            context.user_data = {}
        
        context.user_data['upcoming_matches'] = matches
        
    except Exception as e:
        logger.error(f"Erro ao buscar próximas partidas: {str(e)}")
        
        # Tentar deletar mensagem de carregamento
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
            
        update.message.reply_text(MSG_ERROR, parse_mode="Markdown")

def match_handler(update: Update, context: CallbackContext):
    """Handler para o comando /partida"""
    # Verificar se é ajuda para comando
    if len(context.args) > 0 and context.args[0].lower() == "ajuda":
        help_text = (
            f"{emoji.MATCH} *Comando /partida*\n\n"
            f"Este comando mostra detalhes de uma partida específica.\n\n"
            f"Uso: */partida [ID da partida]*\n\n"
            f"O ID da partida pode ser encontrado ao usar o comando /ao_vivo "
            f"e selecionar uma partida."
        )
        update.message.reply_text(help_text, parse_mode="Markdown")
        return
    
    # Verificar se ID da partida foi fornecido
    if not context.args:
        update.message.reply_text(
            f"{emoji.WARNING} Por favor, especifique o ID da partida.\n"
            f"Exemplo: /partida 12345",
            parse_mode="Markdown"
        )
        return
    
    match_id = context.args[0]
    
    # Enviar mensagem de espera
    loading_message = update.message.reply_text(
        MSG_LOADING,
        parse_mode="Markdown"
    )
    
    try:
        # Buscar detalhes da partida
        match_details = riot_api.get_match_details(match_id)
        
        if not match_details:
            # Tentar deletar mensagem de carregamento
            try:
                context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=loading_message.message_id
                )
            except:
                pass
                
            update.message.reply_text(
                f"{emoji.WARNING} Partida não encontrada ou não está mais disponível.",
                parse_mode="Markdown"
            )
            return
        
        # Buscar a partida completa para ter todos os dados
        matches = riot_api.get_live_matches()
        match = None
        
        for m in matches:
            if m.get('match_id') == match_id:
                match = m
                match.update(match_details)  # Atualizar com os detalhes adicionais
                break
        
        if not match:
            # Se não encontrou a partida, criar objeto básico
            match = {
                'match_id': match_id,
                'teamA': 'Time A',
                'teamB': 'Time B',
                'league': 'League of Legends',
                'stream_url': 'https://www.twitch.tv/riotgames'
            }
            match.update(match_details)
        
        # Obter previsão para a partida
        prediction = None
        compositions = None
        
        if "composition_a" in match and "composition_b" in match:
            compositions = {
                "composition_a": match["composition_a"],
                "composition_b": match["composition_b"]
            }
            
        prediction = predictor_service.get_prediction(
            match['teamA'], 
            match['teamB'],
            compositions,
            match
        )
        
        # Formatar mensagem com os detalhes e previsão
        formatted_message = formatter.format_match_with_stats(match, prediction)
        
        # Criar botões para mais opções
        keyboard = [
            [
                InlineKeyboardButton(f"{emoji.PREDICTION} Análise Detalhada", callback_data=f"analyze_{match_id}"),
                InlineKeyboardButton(f"{emoji.REFRESH} Atualizar", callback_data=f"refresh_match_{match_id}")
            ],
            [
                InlineKeyboardButton(f"{emoji.BACK} Ver Todas Partidas", callback_data="live_matches"),
                InlineKeyboardButton(f"{emoji.HOME} Menu Principal", callback_data="start")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Deletar mensagem de carregamento
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
            
        # Enviar mensagem formatada
        update.message.reply_text(
            formatted_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Armazenar a partida no contexto para uso futuro
        if not context.user_data:
            context.user_data = {}
            
        context.user_data['current_match'] = match
        context.user_data['current_prediction'] = prediction
        
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes da partida: {str(e)}")
        
        # Tentar deletar mensagem de carregamento
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
            
        update.message.reply_text(MSG_ERROR, parse_mode="Markdown") 