"""
Serviço para formatação de mensagens para o Telegram.

Funções para formatar dados de partidas, previsões e análises em mensagens
amigáveis para o usuário usando Markdown.
"""

import logging
import sys
import os
from datetime import datetime
from datetime import timedelta

# Adicionar diretório raiz ao path para importar outros módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import emoji

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def escape_markdown(text):
    """
    Escapa caracteres especiais para Markdown
    
    Args:
        text: Texto a ser escapado
        
    Returns:
        Texto com caracteres especiais escapados
    """
    if not text:
        return ""
        
    # Caracteres para escapar: _ * [ ] ( ) ~ ` > # + - = | { } . !
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
        
    return text

def format_match_message(match):
    """
    Formata uma mensagem básica para uma partida
    
    Args:
        match: Dados da partida
        
    Returns:
        Mensagem formatada em Markdown
    """
    # Header com informações básicas
    header = f"{emoji.TOURNAMENT} *{match.get('league', 'Torneio')}*\n\n"
    header += f"{emoji.MATCH} *{match.get('teamA', 'Time A')} vs {match.get('teamB', 'Time B')}*\n\n"
    
    # Status da partida
    status_line = f"{emoji.TIME} *Status:* {match.get('status', 'Ao vivo')}\n"
    
    # Placar da partida
    score_line = ""
    if all(k in match for k in ["team_a_result", "team_b_result"]):
        team_a_wins = match['team_a_result'].get('gameWins', 0)
        team_b_wins = match['team_b_result'].get('gameWins', 0)
        score_line = f"{emoji.TOURNAMENT} *Placar:* {team_a_wins} - {team_b_wins}\n\n"
    
    # Composições, se disponíveis
    compositions = ""
    if all(k in match for k in ["composition_a", "composition_b"]):
        if match["composition_a"] and match["composition_b"]:
            compositions = f"{emoji.BLUE_TEAM} *{match['teamA']}:* {', '.join(match['composition_a'])}\n"
            compositions += f"{emoji.RED_TEAM} *{match['teamB']}:* {', '.join(match['composition_b'])}\n\n"
    
    # Adicionar link para stream
    stream_link = f"{emoji.STREAM} [Assistir ao vivo]({match.get('stream_url', 'https://www.twitch.tv/riotgames')})"
    
    return f"{header}{status_line}{score_line}{compositions}{stream_link}"

def format_match_with_stats(match, prediction=None):
    """
    Formata mensagem completa de partida incluindo estatísticas e previsão
    
    Args:
        match: Dados da partida
        prediction: Previsão da partida (opcional)
        
    Returns:
        Mensagem formatada em Markdown
    """
    try:
        # Obter informações básicas
        team_a = match.get('teamA', 'Time A')
        team_b = match.get('teamB', 'Time B')
        league = match.get('league', 'Torneio')
        tournament = match.get('tournament', 'Competição')
        
        # Header com informações básicas
        header = f"{emoji.TOURNAMENT} *{league}* - {tournament}\n\n"
        header += f"{emoji.MATCH} *{team_a} vs {team_b}*\n\n"
        
        # Status da partida e placar
        status = match.get('status', 'Ao vivo')
        status_line = f"{emoji.LIVE} *Status:* {status}\n"
        
        # Placar da partida
        score_line = ""
        if all(k in match for k in ["team_a_result", "team_b_result"]):
            team_a_wins = match['team_a_result'].get('gameWins', 0)
            team_b_wins = match['team_b_result'].get('gameWins', 0)
            score_line = f"{emoji.MATCH} *Placar:* {team_a_wins} - {team_b_wins}\n\n"
        
        # Estatísticas do jogo atual, se disponíveis
        game_stats = ""
        if "current_game_stats" in match and match["current_game_stats"]:
            stats = match["current_game_stats"]
            game_time = stats.get("game_time", "00:00")
            
            # Cabeçalho de estatísticas
            game_stats = f"{emoji.TIME} *Tempo de jogo:* {game_time}\n\n"
            
            # Obter estatísticas de cada time
            team_a_stats = stats.get("team_a", {})
            team_b_stats = stats.get("team_b", {})
            
            # Informações do time A
            gold_a = team_a_stats.get("gold", 0)
            kills_a = team_a_stats.get("kills", 0)
            dragons_a = len(team_a_stats.get("dragons", []))
            
            # Informações do time B
            gold_b = team_b_stats.get("gold", 0)
            kills_b = team_b_stats.get("kills", 0)
            dragons_b = len(team_b_stats.get("dragons", []))
            
            # Calcular diferença para mostrar tendência
            gold_diff = gold_a - gold_b
            gold_trend = emoji.trend_emoji(gold_diff / max(1000, (gold_a + gold_b) / 20))
            
            # Formatação das estatísticas
            game_stats += f"{emoji.BLUE_TEAM} *{team_a}:*\n"
            game_stats += f"  {emoji.GOLD} Ouro: {gold_a:,} {gold_trend}\n"
            game_stats += f"  {emoji.KILL} Kills: {kills_a}\n"
            game_stats += f"  {emoji.DRAGON} Dragões: {dragons_a}\n\n"
            
            game_stats += f"{emoji.RED_TEAM} *{team_b}:*\n"
            game_stats += f"  {emoji.GOLD} Ouro: {gold_b:,}\n"
            game_stats += f"  {emoji.KILL} Kills: {kills_b}\n"
            game_stats += f"  {emoji.DRAGON} Dragões: {dragons_b}\n\n"
        
        # Composições
        compositions = ""
        if all(k in match for k in ["composition_a", "composition_b"]):
            if match["composition_a"] and match["composition_b"]:
                compositions = f"{emoji.BLUE_TEAM} *Campeões {team_a}:* {', '.join(match['composition_a'])}\n"
                compositions += f"{emoji.RED_TEAM} *Campeões {team_b}:* {', '.join(match['composition_b'])}\n\n"
        
        # Previsão, se disponível
        prediction_section = ""
        if prediction:
            favorite_team = prediction.get('favorite_team', 'Time A')
            win_prob_a = prediction.get('probaA', 0.5) * 100
            win_prob_b = prediction.get('probaB', 0.5) * 100
            odds_a = prediction.get('oddsA', 2.0)
            odds_b = prediction.get('oddsB', 2.0)
            confidence = prediction.get('confidence', 'média')
            bet_tip = prediction.get('bet_tip', 'Sem palpite disponível.')
            
            prediction_section = (
                f"{emoji.PREDICTION} *Previsão:*\n"
                f"• Chances de vitória:\n"
                f"  {team_a}: {win_prob_a:.1f}%\n"
                f"  {team_b}: {win_prob_b:.1f}%\n\n"
                f"{emoji.ODDS} *Odd justa:*\n"
                f"  {team_a}: {odds_a}\n"
                f"  {team_b}: {odds_b}\n\n"
                f"{emoji.BOT_PICK} *Palpite:* _{bet_tip}_\n\n"
            )
        
        # Adicionar link para stream
        stream_link = f"{emoji.STREAM} [Assistir ao vivo]({match.get('stream_url', 'https://www.twitch.tv/riotgames')})"
        
        # Combinar todas as seções
        message = f"{header}{status_line}{score_line}{game_stats}{compositions}{prediction_section}{stream_link}"
        
        return message
    except Exception as e:
        logger.error(f"Erro ao formatar mensagem de partida: {str(e)}")
        return "❌ Erro ao formatar mensagem da partida."

def format_match_list(matches, title="Partidas ao Vivo"):
    """
    Formata uma lista de partidas em andamento
    
    Args:
        matches: Lista de partidas
        title: Título da lista
        
    Returns:
        Mensagem formatada em Markdown
    """
    if not matches:
        return f"{emoji.WARNING} Não há partidas disponíveis no momento."
    
    # Cabeçalho
    header = f"{emoji.LIVE} *{title.upper()}*\n\n"
    
    # Listar cada partida
    match_list = ""
    for i, match in enumerate(matches):
        team_a = match.get('teamA', 'Time A')
        team_b = match.get('teamB', 'Time B')
        league = match.get('league', 'Torneio')
        
        # Status/placar, se disponível
        status = ""
        if all(k in match for k in ["team_a_result", "team_b_result"]):
            team_a_wins = match['team_a_result'].get('gameWins', 0)
            team_b_wins = match['team_b_result'].get('gameWins', 0)
            status = f" [{team_a_wins} - {team_b_wins}]"
        
        match_list += f"{i+1}. *{team_a} vs {team_b}*{status}\n"
        match_list += f"   {emoji.TOURNAMENT} {league}\n\n"
    
    return header + match_list

def format_upcoming_matches(matches):
    """
    Formata uma lista de próximas partidas agendadas
    
    Args:
        matches: Lista de partidas
        
    Returns:
        Mensagem formatada em Markdown
    """
    if not matches:
        return f"{emoji.WARNING} Não há próximas partidas agendadas."
    
    # Cabeçalho
    header = f"{emoji.SCHEDULED} *PRÓXIMAS PARTIDAS*\n\n"
    
    # Listar cada partida
    match_list = ""
    for i, match in enumerate(matches):
        team_a = match.get('teamA', 'Time A')
        team_b = match.get('teamB', 'Time B')
        league = match.get('league', 'Torneio')
        
        # Converter timestamp para data/hora legível
        start_time = match.get('start_time', '')
        try:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            # Converter para horário de Brasília (UTC-3)
            dt_brasilia = dt - timedelta(hours=3)
            formatted_time = dt_brasilia.strftime("%d/%m/%Y %H:%M") + " (Brasília)"
        except:
            formatted_time = start_time
            
        match_list += f"{i+1}. *{team_a} vs {team_b}*\n"
        match_list += f"   {emoji.TOURNAMENT} {league}\n"
        match_list += f"   {emoji.TIME} {formatted_time}\n\n"
    
    return header + match_list

def format_team_history(team_name, history):
    """
    Formata o histórico de um time
    
    Args:
        team_name: Nome do time
        history: Lista de partidas recentes
        
    Returns:
        Mensagem formatada em Markdown
    """
    if not history:
        return f"{emoji.WARNING} Não há histórico disponível para {team_name}."
    
    # Cabeçalho
    header = f"{emoji.INFO} *HISTÓRICO DE {team_name.upper()}*\n\n"
    
    # Informações de performance
    wins = sum(1 for match in history if match.get('result') == 'win')
    losses = sum(1 for match in history if match.get('result') == 'loss')
    
    performance = (
        f"• Últimas {len(history)} partidas: {wins}W - {losses}L\n"
        f"• Taxa de vitória: {(wins/max(1, len(history)))*100:.1f}%\n\n"
    )
    
    # Listar partidas recentes
    matches_list = "*Partidas Recentes:*\n"
    for i, match in enumerate(history[:5]):  # Mostrar apenas as 5 mais recentes
        opponent = match.get('opponent', 'Desconhecido')
        result = 'Vitória' if match.get('result') == 'win' else 'Derrota'
        score = match.get('score', 'N/A')
        date = match.get('date', 'Data desconhecida')
        
        result_emoji = emoji.UP_TREND if match.get('result') == 'win' else emoji.DOWN_TREND
        
        matches_list += f"{i+1}. {result_emoji} {result} vs {opponent} ({score}) - {date}\n"
    
    return f"{header}{performance}{matches_list}"

def format_match_analysis(analysis, match_data):
    """
    Formata uma análise detalhada da partida
    
    Args:
        analysis: Análise da partida
        match_data: Dados da partida
        
    Returns:
        Mensagem formatada em Markdown
    """
    if not analysis:
        return f"{emoji.WARNING} Análise não disponível."
    
    team_a = match_data.get('teamA', 'Time A')
    team_b = match_data.get('teamB', 'Time B')
    
    # Cabeçalho
    header = f"{emoji.PREDICTION} *ANÁLISE DETALHADA*\n"
    header += f"*{team_a} vs {team_b}*\n\n"
    
    # Previsão de probabilidades e odds
    probabilities = (
        f"*Probabilidades:*\n"
        f"• {team_a}: {analysis['win_probability']['team_a']*100:.1f}%\n"
        f"• {team_b}: {analysis['win_probability']['team_b']*100:.1f}%\n\n"
        
        f"*Odds justas:*\n"
        f"• {team_a}: {analysis['current_odds']['team_a']}\n"
        f"• {team_b}: {analysis['current_odds']['team_b']}\n\n"
    )
    
    # Análise textual
    text_analysis = f"*Análise:* {analysis.get('analysis', 'Não disponível.')}\n\n"
    
    # Fatores-chave, se disponíveis
    key_factors = ""
    if "key_factors" in analysis and analysis["key_factors"]:
        key_factors = "*Fatores-chave:*\n"
        for factor in analysis["key_factors"]:
            key_factors += f"• {factor}\n"
        key_factors += "\n"
    
    # Palpite para apostas
    bet_tip = f"*Recomendação:* _{analysis.get('bet_tip', 'Sem recomendação disponível.')}_"
    
    return f"{header}{probabilities}{text_analysis}{key_factors}{bet_tip}" 