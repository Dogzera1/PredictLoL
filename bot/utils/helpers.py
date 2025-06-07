"""
Funções auxiliares e utilitários gerais
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
try:
    from fuzzywuzzy import fuzz
except ImportError:  # Fallback simples caso fuzzywuzzy não esteja instalado
    from difflib import SequenceMatcher

    class _FuzzWrapper:
        @staticmethod
        def ratio(a: str, b: str) -> float:
            """Calcula similaridade aproximada usando difflib."""
            return SequenceMatcher(None, a, b).ratio() * 100

    fuzz = _FuzzWrapper()


def normalize_team_name(team_name: str) -> str:
    """
    Normaliza nome de time para comparação
    
    Args:
        team_name: Nome do time original
        
    Returns:
        Nome normalizado
    """
    if not team_name:
        return ""
    
    # Remove espaços, converte para minúsculo
    normalized = team_name.strip().lower()
    
    # Remove caracteres especiais comuns
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Remove espaços extras
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def teams_similarity(team1: str, team2: str, threshold: float = 0.8) -> bool:
    """
    Verifica similaridade entre nomes de times
    
    Args:
        team1: Primeiro time
        team2: Segundo time
        threshold: Limite de similaridade (0-1)
        
    Returns:
        True se times são similares
    """
    if not team1 or not team2:
        return False
    
    # Normaliza nomes
    norm1 = normalize_team_name(team1)
    norm2 = normalize_team_name(team2)
    
    # Verifica igualdade exata
    if norm1 == norm2:
        return True
    
    # Verifica similaridade usando fuzzywuzzy
    similarity = fuzz.ratio(norm1, norm2) / 100.0
    
    return similarity >= threshold


def format_timedelta(seconds: int) -> str:
    """
    Formata tempo em segundos para string legível
    
    Args:
        seconds: Tempo em segundos
        
    Returns:
        String formatada (ex: "25min", "1h 30min")
    """
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes}min {remaining_seconds}s"
        return f"{minutes}min"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}min"
    return f"{hours}h"


def format_game_time(game_time_seconds: Optional[int]) -> str:
    """
    Formata tempo de jogo para exibição
    
    Args:
        game_time_seconds: Tempo de jogo em segundos
        
    Returns:
        String formatada para exibição
    """
    if not game_time_seconds:
        return "N/A"
    
    minutes = game_time_seconds // 60
    seconds = game_time_seconds % 60
    
    return f"{minutes:02d}:{seconds:02d}"


def escape_markdown_v2(text: str) -> str:
    """
    Escapa caracteres especiais para Markdown V2 do Telegram
    
    Args:
        text: Texto original
        
    Returns:
        Texto escapado
    """
    if not text:
        return ""
    
    # Caracteres que precisam ser escapados no MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    
    return escaped_text


def format_telegram_message_markdown_v2(text: str) -> str:
    """
    Formata mensagem para Telegram com MarkdownV2
    
    Args:
        text: Texto da mensagem
        
    Returns:
        Texto formatado e escapado
    """
    # Primeiro escapa caracteres especiais
    escaped = escape_markdown_v2(text)
    
    # Aplica formatação específica (revertendo escape onde necessário)
    # Bold
    escaped = re.sub(r'\\\*\\\*(.*?)\\\*\\\*', r'**\1**', escaped)
    
    # Italic  
    escaped = re.sub(r'\\_(.*?)\\_', r'_\1_', escaped)
    
    # Code
    escaped = re.sub(r'\\`(.*?)\\`', r'`\1`', escaped)
    
    return escaped


def calculate_percentage(value: float, decimal_places: int = 1) -> str:
    """
    Calcula e formata porcentagem
    
    Args:
        value: Valor decimal (ex: 0.75 para 75%)
        decimal_places: Casas decimais
        
    Returns:
        String formatada (ex: "75.0%")
    """
    percentage = value * 100
    return f"{percentage:.{decimal_places}f}%"


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """
    Divisão segura que evita divisão por zero
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor padrão se denominador for zero
        
    Returns:
        Resultado da divisão ou valor padrão
    """
    if denominator == 0:
        return default
    return numerator / denominator


def timestamp_to_datetime(timestamp: Union[int, float, str]) -> Optional[datetime]:
    """
    Converte timestamp para datetime
    
    Args:
        timestamp: Timestamp em segundos ou milissegundos
        
    Returns:
        Objeto datetime ou None se inválido
    """
    try:
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        
        # Se timestamp está em milissegundos, converte para segundos
        if timestamp > 1e10:
            timestamp = timestamp / 1000
        
        return datetime.fromtimestamp(timestamp)
    except (ValueError, OSError):
        return None


def get_time_ago(timestamp: Union[int, float, str]) -> str:
    """
    Calcula tempo passado desde timestamp
    
    Args:
        timestamp: Timestamp
        
    Returns:
        String descritiva (ex: "há 5 minutos")
    """
    dt = timestamp_to_datetime(timestamp)
    if not dt:
        return "tempo desconhecido"
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"há {diff.days} dia{'s' if diff.days > 1 else ''}"
    
    hours = diff.seconds // 3600
    if hours > 0:
        return f"há {hours} hora{'s' if hours > 1 else ''}"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"há {minutes} minuto{'s' if minutes > 1 else ''}"
    
    return "há poucos segundos"


def clean_dict(data: Dict) -> Dict:
    """
    Remove chaves com valores None ou vazios de um dicionário
    
    Args:
        data: Dicionário original
        
    Returns:
        Dicionário limpo
    """
    return {k: v for k, v in data.items() if v is not None and v != ""}


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto se exceder tamanho máximo
    
    Args:
        text: Texto original
        max_length: Tamanho máximo
        suffix: Sufixo para texto truncado
        
    Returns:
        Texto truncado se necessário
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def validate_odds(odds: Union[str, float]) -> Optional[float]:
    """
    Valida e converte odds para float
    
    Args:
        odds: Odds como string ou float
        
    Returns:
        Odds válida como float ou None
    """
    try:
        odds_float = float(odds)
        if odds_float > 0:
            return odds_float
    except (ValueError, TypeError):
        pass
    
    return None


def format_odds(odds: float, decimal_places: int = 2) -> str:
    """
    Formata odds para exibição
    
    Args:
        odds: Valor das odds
        decimal_places: Casas decimais
        
    Returns:
        String formatada
    """
    return f"{odds:.{decimal_places}f}"


def get_current_timestamp() -> int:
    """
    Obtém timestamp atual em segundos
    
    Returns:
        Timestamp atual
    """
    return int(time.time())


def is_valid_email(email: str) -> bool:
    """
    Valida formato de email básico
    
    Args:
        email: Email para validar
        
    Returns:
        True se email é válido
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_match_id(team1: str, team2: str, timestamp: Optional[int] = None) -> str:
    """
    Gera ID único para uma partida
    
    Args:
        team1: Nome do primeiro time
        team2: Nome do segundo time
        timestamp: Timestamp opcional
        
    Returns:
        ID único da partida
    """
    if not timestamp:
        timestamp = get_current_timestamp()
    
    # Normaliza nomes dos times
    norm_team1 = normalize_team_name(team1)
    norm_team2 = normalize_team_name(team2)
    
    # Ordena times para consistência
    teams = sorted([norm_team1, norm_team2])
    
    return f"{teams[0]}_vs_{teams[1]}_{timestamp}"


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Divide lista em chunks menores
    
    Args:
        lst: Lista original
        chunk_size: Tamanho de cada chunk
        
    Returns:
        Lista de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Decorator para retry com backoff exponencial
    
    Args:
        max_retries: Número máximo de tentativas
        backoff_factor: Fator de multiplicação do delay
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = backoff_factor ** attempt
                        time.sleep(delay)
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator 
