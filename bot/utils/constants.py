"""
Constantes globais do sistema Bot LoL V3 Ultra Avançado
"""

from __future__ import annotations

# Sistema de Unidades Profissionais
MIN_CONFIDENCE_FOR_TIP = 0.70
MIN_EV_FOR_TIP = 0.05
MIN_UNITS = 0.5
MAX_UNITS = 5.0

# Odds
MIN_ODDS = 1.30
MAX_ODDS = 3.50

# Timing
SCAN_INTERVAL_MINUTES = 3
ODDS_CACHE_TIMEOUT_MINUTES = 5
MATCH_CACHE_TIMEOUT_MINUTES = 3
CLEANUP_INTERVAL_HOURS = 24  # Limpeza de dados a cada 24 horas

# API Timeouts
API_REQUEST_TIMEOUT_SECONDS = 5
TELEGRAM_REQUEST_TIMEOUT_SECONDS = 30

# Ligas e Tiers
LEAGUE_TIERS = {
    # Tier 1 - Principais ligas internacionais
    "LPL": 1,          # China
    "LCK": 1,          # Coreia do Sul
    "LEC": 1,          # Europa
    "LCS": 1,          # América do Norte
    "MSI": 1,          # Mid-Season Invitational
    "WORLDS": 1,       # World Championship
    
    # Tier 2 - Ligas regionais importantes
    "CBLOL": 2,        # Brasil
    "LLA": 2,          # América Latina
    "LJL": 2,          # Japão
    "LCO": 2,          # Oceania
    "VCS": 2,          # Vietnam
    "PCS": 2,          # Pacific Championship Series
    "TCL": 2,          # Turquia
    "LCL": 2,          # CIS
    
    # Tier 3 - Ligas menores e qualificatórias
    "LCKC": 3,         # LCK Challengers
    "LDL": 3,          # LPL Development League
    "ERL": 3,          # European Regional Leagues
    "ACADEMY": 3,      # LCS Academy
    "PRIME": 3,        # Prime League
}

# URLs base das APIs da Riot/Lolesports (baseado no openapi.yaml)
RIOT_API_ENDPOINTS = {
    "esports_api": "https://esports-api.lolesports.com/persisted/gw",
    "livestats_api": "https://feed.lolesports.com/livestats/v1", 
    "highlander_api": "https://api.lolesports.com/api/v1",
    "prod_relapi": "https://prod-relapi.ewp.gg/persisted/gw"
}

# Chave de API padrão da Lolesports (conforme documentação openapi.yaml)
RIOT_API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"

# PandaScore API
PANDASCORE_API_KEY = "90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ"
PANDASCORE_BASE_URL = "https://api.pandascore.co"

# Locales suportados (baseado no openapi.yaml)
SUPPORTED_LOCALES = [
    "en-US", "en-GB", "en-AU", "cs-CZ", "de-DE", "el-GR", "es-ES",
    "es-MX", "fr-FR", "hu-HU", "it-IT", "pl-PL", "pt-BR", "ro-RO", 
    "ru-RU", "tr-TR", "ja-JP", "ko-KR"
]

# Status válidos para partidas ao vivo
VALID_LIVE_STATUSES = {
    "inprogress",
    "live", 
    "ongoing",
    "in_progress",
    "started"
}

# Rate limits
RIOT_API_RATE_LIMITS = {
    "requests_per_second": 20,
    "requests_per_two_minutes": 100
}

PANDASCORE_RATE_LIMITS = {
    "requests_per_second": 10,
    "requests_per_hour": 1000
}

# Configurações do sistema de unidades
UNITS_CONFIG = {
    "very_high_risk": {
        "min_confidence": 0.90,
        "min_ev": 0.15,
        "units": 5.0,
        "risk_level": "Risco Muito Alto"
    },
    "high_risk": {
        "min_confidence": 0.85,
        "min_ev": 0.12,
        "units": 4.0,
        "risk_level": "Risco Alto"
    },
    "high_risk_2": {
        "min_confidence": 0.80,
        "min_ev": 0.10,
        "units": 3.0,
        "risk_level": "Risco Alto"
    },
    "medium_high_risk": {
        "min_confidence": 0.75,
        "min_ev": 0.08,
        "units": 2.5,
        "risk_level": "Risco Médio-Alto"
    },
    "medium_risk": {
        "min_confidence": 0.70,
        "min_ev": 0.06,
        "units": 2.0,
        "risk_level": "Risco Médio"
    },
    "low_risk": {
        "min_confidence": 0.65,
        "min_ev": 0.05,
        "units": 1.0,
        "risk_level": "Risco Baixo"
    },
    "minimum": {
        "min_confidence": 0.60,
        "min_ev": 0.03,
        "units": 0.5,
        "risk_level": "Risco Mínimo"
    }
}

# Eventos cruciais do LoL
CRUCIAL_EVENTS = {
    "dragon_soul": "DRAGON_SOUL",
    "elder_dragon": "ELDER_DRAGON",
    "baron": "BARON_NASHOR",
    "ace": "ACE",
    "inhibitor": "INHIBITOR_DESTROYED",
    "nexus_tower": "NEXUS_TURRET_DESTROYED",
    "teamfight": "TEAMFIGHT_WIN",
    "gold_lead": "GOLD_LEAD_SIGNIFICANT"
}

# Timing scores para análise
TIMING_SCORES = {
    "early_game": {"min": 0, "max": 15, "weight": 0.7},      # 0-15 min
    "mid_game": {"min": 15, "max": 30, "weight": 1.0},      # 15-30 min
    "late_game": {"min": 30, "max": 60, "weight": 0.8}      # 30+ min
}

# Headers para requisições HTTP
HTTP_HEADERS = {
    "User-Agent": "LoLBotV3/3.0.0 (Professional Esports Bot)",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Headers específicos da Riot API (baseado no openapi.yaml)
RIOT_HEADERS = {
    **HTTP_HEADERS,
    "x-api-key": RIOT_API_KEY
}

# Configurações do Telegram
TELEGRAM_CONFIG = {
    "bot_token": "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg",  # Token real como padrão
    "parse_mode": "MarkdownV2",
    "disable_web_page_preview": True,
    "max_message_length": 4096,
    "rate_limit_per_user": 10,  # mensagens por hora por usuário
    "cache_duration_minutes": 5,
    "admin_user_ids": ["8012415611"]  # ID do admin como padrão
}

# Template para tips do Telegram
TIP_TEMPLATE = {
    "header": "🚀 **TIP PROFISSIONAL LoL** 🚀",
    "match_format": "🎮 **{team_a} vs {team_b}**",
    "league_format": "🏆 **Liga:** {league}",
    "tip_format": "⚡ **Tip:** {tip_on_team}",
    "odds_format": "💰 **Odds:** {odds}",
    "units_format": "{risk_emoji} **Unidades:** {units} ({risk_level})",
    "time_format": "⏰ **Tempo:** {game_time}",
    "analysis_header": "📊 **Análise:**",
    "ev_format": "{ev_icon} **EV:** +{ev_percentage:.1f}%",
    "confidence_format": "🎯 **Confiança:** {confidence_percentage:.0f}%",
    "source_format": "🤖 **Fonte:** {prediction_source}",
    "quality_format": "⭐ **Qualidade:** {data_quality_score:.0%}",
    "footer": "🔥 **Bot LoL V3 Ultra Avançado**"
}

# Emojis para níveis de risco
RISK_EMOJIS = {
    "Risco Muito Alto": "🔥🔥🔥",
    "Risco Alto": "🔥🔥", 
    "Risco Médio-Alto": "🔥",
    "Risco Médio": "📊",
    "Risco Baixo": "🎯",
    "Risco Mínimo": "💡"
}

# Emojis para Expected Value
EV_EMOJIS = {
    "high": "📈",    # EV > 15%
    "medium": "📊",  # 5% < EV <= 15%
    "low": "📉"      # EV <= 5%
}

# Ligas suportadas para análise
SUPPORTED_LEAGUES = {
    "LCS", "LEC", "LPL", "LCK", "CBLOL", "LLA", "WORLDS", "MSI"
}

# Thresholds para sistema de predição
PREDICTION_THRESHOLDS = {
    "min_confidence": 0.65,          # Confiança mínima para tip
    "min_ev": 3.0,                   # EV mínimo em %
    "min_odds": 1.30,                # Odds mínima
    "max_odds": 3.50,                # Odds máxima
    "min_game_time": 300,            # Tempo mínimo de jogo (5min)
    "min_data_quality": 0.60,        # Qualidade mínima dos dados
    "cache_time_minutes": 10,        # Cache de predições
    "ml_confidence_threshold": 0.70,  # Threshold para ML
    "hybrid_weight_ml": 0.6,         # Peso do ML no método híbrido
    "hybrid_weight_algo": 0.4        # Peso dos algoritmos no híbrido
}

# Pesos para modelo ML simulado
ML_FEATURE_WEIGHTS = {
    "gold_advantage": 0.25,
    "tower_advantage": 0.20,
    "dragon_advantage": 0.15,
    "baron_advantage": 0.15,
    "kill_advantage": 0.10,
    "overall_advantage": 0.30,
    "game_phase": 0.05,
    "crucial_events": 0.10,
    "has_momentum": 0.08
} 