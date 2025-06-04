"""
Configuração do sistema de logging
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import colorlog


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configura o sistema de logging do bot
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho do arquivo de log (opcional)
        max_file_size: Tamanho máximo do arquivo de log em bytes
        backup_count: Número de backups de arquivo de log
        
    Returns:
        Logger configurado
    """
    # Converte string do nível para constante do logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Cria logger principal
    logger = logging.getLogger("bot_lol_v3")
    logger.setLevel(numeric_level)
    
    # Remove handlers existentes para evitar duplicação
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formato das mensagens
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Handler para console com cores
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    # Formato colorido para console
    color_format = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    color_formatter = colorlog.ColoredFormatter(
        color_format,
        datefmt=date_format,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if log_file:
        # Cria diretório se não existir
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handler com rotação de arquivos
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        # Formato simples para arquivo
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtém logger com nome específico
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(f"bot_lol_v3.{name}")


def setup_component_loggers() -> None:
    """
    Configura loggers específicos para componentes do sistema
    """
    # Logger para API clients
    api_logger = get_logger("api_clients")
    api_logger.setLevel(logging.INFO)
    
    # Logger para sistema de predição
    prediction_logger = get_logger("prediction")
    prediction_logger.setLevel(logging.INFO)
    
    # Logger para sistema de tips
    tips_logger = get_logger("tips")
    tips_logger.setLevel(logging.INFO)
    
    # Logger para bot do Telegram
    telegram_logger = get_logger("telegram")
    telegram_logger.setLevel(logging.INFO)
    
    # Logger para sistema de alertas
    alerts_logger = get_logger("alerts")
    alerts_logger.setLevel(logging.INFO)
    
    # Logger para web app
    web_logger = get_logger("web")
    web_logger.setLevel(logging.INFO)


def log_system_info() -> None:
    """
    Registra informações do sistema no log
    """
    logger = get_logger("system")
    
    logger.info("🚀 Bot LoL V3 Ultra Avançado - Iniciando sistema")
    logger.info(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🖥️ Sistema Operacional: {os.name}")
    logger.info(f"📁 Diretório de trabalho: {os.getcwd()}")
    
    # Verifica variáveis de ambiente importantes
    env_vars = [
        "RIOT_API_KEY",
        "THE_ODDS_API_KEY", 
        "TELEGRAM_BOT_TOKEN",
        "ADMIN_TELEGRAM_USER_ID"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mostra apenas primeiros e últimos caracteres para segurança
            masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            logger.info(f"🔑 {var}: {masked_value}")
        else:
            logger.warning(f"⚠️ {var}: NÃO CONFIGURADA")


def log_performance_metrics(
    operation: str,
    duration: float,
    success: bool = True,
    details: Optional[str] = None
) -> None:
    """
    Registra métricas de performance
    
    Args:
        operation: Nome da operação
        duration: Duração em segundos
        success: Se a operação foi bem-sucedida
        details: Detalhes adicionais
    """
    logger = get_logger("performance")
    
    status = "✅ SUCESSO" if success else "❌ FALHA"
    duration_ms = duration * 1000
    
    message = f"📊 {operation} - {status} - {duration_ms:.2f}ms"
    if details:
        message += f" - {details}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message)


def log_api_request(
    api_name: str,
    endpoint: str,
    method: str = "GET",
    status_code: Optional[int] = None,
    duration: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """
    Registra requisições de API
    
    Args:
        api_name: Nome da API (ex: "Riot API", "The Odds API")
        endpoint: Endpoint da requisição
        method: Método HTTP
        status_code: Código de status da resposta
        duration: Duração da requisição em segundos
        error: Mensagem de erro (se houver)
    """
    logger = get_logger("api")
    
    duration_text = f" - {duration*1000:.2f}ms" if duration else ""
    status_text = f" - {status_code}" if status_code else ""
    
    if error:
        logger.error(f"🌐 {api_name} {method} {endpoint}{status_text}{duration_text} - ❌ {error}")
    else:
        logger.info(f"🌐 {api_name} {method} {endpoint}{status_text}{duration_text} - ✅")


def log_tip_generated(
    team1: str,
    team2: str,
    league: str,
    confidence: float,
    ev: float,
    units: float
) -> None:
    """
    Registra geração de tip profissional
    
    Args:
        team1: Primeiro time
        team2: Segundo time
        league: Liga
        confidence: Confiança
        ev: Expected Value
        units: Unidades
    """
    logger = get_logger("tips")
    
    logger.info(
        f"🔥 TIP GERADA: {team1} vs {team2} ({league}) - "
        f"Confiança: {confidence:.1%} - EV: {ev:.1%} - Unidades: {units}"
    )


def log_error_with_context(
    logger_name: str,
    error: Exception,
    context: Optional[str] = None,
    **kwargs
) -> None:
    """
    Registra erro com contexto adicional
    
    Args:
        logger_name: Nome do logger
        error: Exceção capturada
        context: Contexto adicional
        **kwargs: Dados adicionais para contexto
    """
    logger = get_logger(logger_name)
    
    error_msg = f"❌ ERRO: {type(error).__name__}: {str(error)}"
    
    if context:
        error_msg += f" - Contexto: {context}"
    
    if kwargs:
        context_data = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        error_msg += f" - Dados: {context_data}"
    
    logger.error(error_msg, exc_info=True)


# Configuração padrão ao importar o módulo
def configure_default_logging() -> None:
    """
    Configura logging padrão se ainda não foi configurado
    """
    root_logger = logging.getLogger("bot_lol_v3")
    
    # Se não há handlers, configura logging básico
    if not root_logger.handlers:
        log_file = os.getenv("LOG_FILE_PATH", "logs/bot.log")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        
        setup_logging(log_level=log_level, log_file=log_file)
        setup_component_loggers()


# Configura logging automaticamente na importação
configure_default_logging() 
