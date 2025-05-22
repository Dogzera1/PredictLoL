"""
Manipuladores de callbacks para botões inline.

Define handlers para responder a interações do usuário com botões.
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
from handlers.main import start_handler, live_matches_handler, upcoming_matches_handler

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Instanciar serviços
predictor_service = predictor.PredictorService()

def callback_handler(update: Update, context: CallbackContext):
    """
    Handler geral para todos os callbacks de botões inline
    
    Args:
        update: Update do Telegram
        context: Contexto da conversa
    """
    query = update.callback_query
    data = query.data
    
    try:
        # Responder ao callback para remover o "loading" do botão
        query.answer()
        
        # Rotear para o handler específico com base no callback data
        if data == "start":
            handle_start_callback(update, context)
        
        elif data == "about":
            handle_about_callback(update, context)
        
        elif data == "live_matches" or data == "refresh_live_matches":
            handle_live_matches_callback(update, context)
        
        elif data == "upcoming_matches" or data == "refresh_upcoming":
            handle_upcoming_matches_callback(update, context)
        
        elif data.startswith("match_"):
            match_id = data[6:]  # Remover prefixo "match_"
            handle_match_details_callback(update, context, match_id)
        
        elif data.startswith("analyze_"):
            match_id = data[8:]  # Remover prefixo "analyze_"
            handle_match_analysis_callback(update, context, match_id)
        
        elif data.startswith("refresh_match_"):
            match_id = data[14:]  # Remover prefixo "refresh_match_"
            handle_match_refresh_callback(update, context, match_id)
        
        else:
            query.edit_message_text(f"{emoji.WARNING} Opção não reconhecida.")
    
    except Exception as e:
        logger.error(f"Erro ao processar callback: {str(e)}")
        try:
            query.edit_message_text(
                f"{emoji.ERROR} Ocorreu um erro ao processar sua solicitação.\n\nDetalhes: {str(e)}",
                parse_mode="Markdown"
            )
        except:
            pass

def handle_start_callback(update: Update, context: CallbackContext):
    """
    Handler para o callback 'start'
    
    Args:
        update: Update do Telegram
        context: Contexto da conversa
    """
    query = update.callback_query
    
    # Mensagem de boas-vindas
    welcome_message = (
        f"{emoji.INFO} Bem-vindo ao LoL-GPT Betting Assistant!\n\n"
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
    
    # Editar mensagem atual com o menu inicial
    query.edit_message_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def handle_about_callback(update: Update, context: CallbackContext):
    """
    Handler para o callback 'about'
    
    Args:
        update: Update do Telegram
        context: Contexto da conversa
    """
    query = update.callback_query
    
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
    
    query.edit_message_text(
        about_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def handle_live_matches_callback(update: Update, context: CallbackContext):
    """
    Handler para os callbacks 'live_matches' e 'refresh_live_matches'
    
    Args:
        update: Update do Telegram
        context: Contexto da conversa
    """
    query = update.callback_query
    
    # Mostrar mensagem de carregamento
    query.edit_message_text(
        MSG_LOADING,
        parse_mode="Markdown"
    )
    
    try:
        # Buscar partidas ao vivo
        matches = riot_api.get_live_matches()
        
        # Se não há partidas, mostrar mensagem e sugerir ver próximas
        if not matches:
            # Criar botões para outras opções
            keyboard = [
                [InlineKeyboardButton(f"{emoji.SCHEDULED} Ver Próximas Partidas", callback_data="upcoming_matches")],
                [InlineKeyboardButton(f"{emoji.HOME} Menu Principal", callback_data="start")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
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
        
        # Enviar lista de partidas
        query.edit_message_text(
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
        query.edit_message_text(MSG_ERROR, parse_mode="Markdown")

def handle_upcoming_matches_callback(update: Update, context: CallbackContext):
    """
    Handler para os callbacks 'upcoming_matches' e 'refresh_upcoming'
    
    Args:
        update: Update do Telegram
        context: Contexto da conversa
    """
    query = update.callback_query
    
    # Mostrar mensagem de carregamento
    query.edit_message_text(
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
            
            query.edit_message_text(
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
        
        # Enviar lista de próximas partidas
        query.edit_message_text(
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
        query.edit_message_text(MSG_ERROR, parse_mode="Markdown")

def handle_match_details_callback(update: Update, context: CallbackContext, match_id: str):
    """
    Handler para o callback 'match_[id]'
    
    Args:
        update: Update do Telegram
        context: Contexto da conversa
        match_id: ID da partida
    """
    query = update.callback_query
    
    # Mostrar mensagem de carregamento
    query.edit_message_text(
        f"{emoji.LOADING} Carregando detalhes da partida...",
        parse_mode="Markdown"
    )
    
    try:
        # Buscar detalhes da partida
        match_details = riot_api.get_match_details(match_id)
        
        if not match_details:
            query.edit_message_text(
                f"{emoji.WARNING} Partida não encontrada ou não está mais disponível.",
                parse_mode="Markdown"
            )
            return
        
        # Verificar se temos a partida armazenada no contexto
        match = None
        if 'live_matches' in context.user_data:
            for m in context.user_data['live_matches']:
                if m.get('match_id') == match_id:
                    match = m
                    match.update(match_details)  # Atualizar com os detalhes adicionais
                    break
        
        if not match:
            # Se não encontrou a partida no contexto, buscar novamente
            matches = riot_api.get_live_matches()
            for m in matches:
                if m.get('match_id') == match_id:
                    match = m
                    match.update(match_details)  # Atualizar com os detalhes adicionais
                    break
        
        if not match:
            # Se ainda não encontrou, criar objeto básico
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
        
        # Enviar mensagem formatada
        query.edit_message_text(
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
        query.edit_message_text(MSG_ERROR, parse_mode="Markdown")

def handle_match_analysis_callback(update: Update, context: CallbackContext, match_id: str):
    """
    Handler para o callback 'analyze_[id]'
    
    Args:
        update: Update do Telegram
        context: Contexto da conversa
        match_id: ID da partida
    """
    query = update.callback_query
    
    # Mostrar mensagem de carregamento
    query.edit_message_text(
        f"{emoji.LOADING} Carregando análise detalhada...",
        parse_mode="Markdown"
    )
    
    try:
        # Verificar se temos a partida armazenada no contexto
        match = None
        if 'current_match' in context.user_data:
            match = context.user_data['current_match']
            if match.get('match_id') != match_id:
                match = None
        
        if not match and 'live_matches' in context.user_data:
            for m in context.user_data['live_matches']:
                if m.get('match_id') == match_id:
                    match = m
                    break
        
        if not match:
            # Se não encontrou a partida no contexto, buscar novamente
            match_details = riot_api.get_match_details(match_id)
            matches = riot_api.get_live_matches()
            
            for m in matches:
                if m.get('match_id') == match_id:
                    match = m
                    if match_details:
                        match.update(match_details)
                    break
        
        if not match:
            query.edit_message_text(
                f"{emoji.WARNING} Partida não encontrada ou não está mais disponível.",
                parse_mode="Markdown"
            )
            return
        
        # Obter análise da partida
        analysis = predictor_service.get_match_analysis(match)
        
        # Formatar análise
        formatted_analysis = formatter.format_match_analysis(analysis, match)
        
        # Criar botões para voltar à partida
        keyboard = [
            [
                InlineKeyboardButton(f"{emoji.BACK} Voltar à partida", callback_data=f"match_{match_id}"),
                InlineKeyboardButton(f"{emoji.REFRESH} Atualizar", callback_data=f"analyze_{match_id}")
            ],
            [
                InlineKeyboardButton(f"{emoji.LIVE} Ver Todas Partidas", callback_data="live_matches"),
                InlineKeyboardButton(f"{emoji.HOME} Menu Principal", callback_data="start")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enviar análise formatada
        query.edit_message_text(
            formatted_analysis,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar análise da partida: {str(e)}")
        query.edit_message_text(MSG_ERROR, parse_mode="Markdown")

def handle_match_refresh_callback(update: Update, context: CallbackContext, match_id: str):
    """
    Handler para o callback 'refresh_match_[id]'
    
    Args:
        update: Update do Telegram
        context: Contexto da conversa
        match_id: ID da partida
    """
    # Simplesmente redirecionar para o handler de detalhes da partida para atualizar
    handle_match_details_callback(update, context, match_id) 