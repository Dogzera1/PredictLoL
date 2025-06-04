"""
Constantes globais do sistema Bot LoL V3 Ultra Avançado
"""

from __future__ import annotations

# Sistema de Unidades Profissionais
MIN_CONFIDENCE_FOR_TIP = 0.50
MIN_EV_FOR_TIP = 0.01
MIN_UNITS = 0.5
MAX_UNITS = 5.0

# Odds
MIN_ODDS = 1.50
MAX_ODDS = 8.00

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

# Chave de API da Riot para desenvolvimento/teste (atualizada)
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

# Status válidos para partidas ao vivo - EXPANDIDO
VALID_LIVE_STATUSES = {
    "inprogress",
    "live", 
    "ongoing",
    "in_progress",
    "started",
    "running",        # Adicionado para PandaScore
    "active",         # Status genérico
    "playing",        # Partida em andamento
    "draft",          # Fase de draft/pick & ban
    "loading",        # Carregando jogo
    "paused",         # Partida pausada (ainda válida)
    "ready",          # Pronta para iniciar
    "configured"      # Configurada e pronta
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

# Configurações do sistema de unidades - AJUSTADAS para desenvolvimento
UNITS_CONFIG = {
    "very_high_risk": {
        "min_confidence": 0.80,
        "min_ev": 0.10,
        "units": 5.0,
        "risk_level": "Risco Muito Alto"
    },
    "high_risk": {
        "min_confidence": 0.75,
        "min_ev": 0.08,
        "units": 4.0,
        "risk_level": "Risco Alto"
    },
    "high_risk_2": {
        "min_confidence": 0.70,
        "min_ev": 0.06,
        "units": 3.0,
        "risk_level": "Risco Alto"
    },
    "medium_high_risk": {
        "min_confidence": 0.65,
        "min_ev": 0.05,
        "units": 2.5,
        "risk_level": "Risco Médio-Alto"
    },
    "medium_risk": {
        "min_confidence": 0.60,
        "min_ev": 0.04,
        "units": 2.0,
        "risk_level": "Risco Médio"
    },
    "low_risk": {
        "min_confidence": 0.55,
        "min_ev": 0.03,
        "units": 1.0,
        "risk_level": "Risco Baixo"
    },
    "minimum": {
        "min_confidence": 0.50,
        "min_ev": 0.01,
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
    "bot_token": "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0",  # Token atual
    "parse_mode": "MarkdownV2",
    "disable_web_page_preview": True,
    "max_message_length": 4096,
    "rate_limit_per_user": 10,  # mensagens por hora por usuário
    "cache_duration_minutes": 5,
    "admin_user_ids": ["8012415611"]  # ID do admin como padrão
}

# Template melhorado para tips do Telegram - EXPERIÊNCIA PREMIUM
TIP_TEMPLATE = {
    "header": "🚀 **TIP PROFISSIONAL LoL** 🚀",
    "match_info": "🎮 **{team_a}** vs **{team_b}**\n🏆 **Liga:** {league} | 🗺️ **Mapa:** {map_number}\n⏰ **Tempo:** {game_time} | 🔴 **Status:** {match_status}",
    
    # Seção da tip principal
    "tip_main": "⚡ **APOSTAR EM:** {tip_on_team}\n💰 **Odds Atual:** {odds} | 📊 **Odds Mínima:** {min_odds}",
    
    # Explicação didática da tip
    "tip_explanation": "📝 **Por que apostar?**\n{explanation_text}",
    
    # Informações de gestão de risco
    "risk_management": "🎯 **Gestão de Risco:**\n{risk_emoji} **{units} unidades** ({risk_level})\n💡 **Valor da unidade:** R$ {unit_value}\n💸 **Apostar:** R$ {bet_amount}",
    
    # Análise técnica
    "technical_analysis": "📊 **Análise Técnica:**\n🎯 **Confiança:** {confidence_percentage}%\n📈 **Expected Value:** +{ev_percentage}%\n⭐ **Qualidade dos Dados:** {data_quality_score}%",
    
    # Situação atual da partida
    "game_situation": "🔥 **Situação Atual:**\n{game_situation_text}",
    
    # Próximos objetivos importantes
    "next_objectives": "⏳ **Próximos Objetivos:**\n{objectives_text}",
    
    # Timing da aposta
    "bet_timing": "⚠️ **Timing:**\n{timing_advice}",
    
    # Histórico dos times (se disponível)
    "teams_history": "📈 **Histórico Recente:**\n{history_text}",
    
    # Alertas importantes
    "alerts": "🚨 **Alertas:**\n{alerts_text}",
    
    # Rodapé
    "footer": "🤖 **Fonte:** {prediction_source} | ⏱️ **Gerado:** {generated_time}\n🔥 **Bot LoL V3 Ultra Avançado** | 📊 **Tip #{tip_id}**"
}

# Explicações didáticas para diferentes cenários
TIP_EXPLANATIONS = {
    "early_advantage": "O time {team} está com uma vantagem sólida no início da partida, controlando recursos importantes e demonstrando superioridade estratégica.",
    "momentum_shift": "Detectamos uma mudança de momentum favorável ao {team}, com conquistas recentes de objetivos cruciais que indicam domínio crescente.",
    "late_game_superior": "Em partidas longas, {team} tem composição e macro-jogo superiores, tornando-se favorito conforme o tempo passa.",
    "objective_control": "{team} está dominando objetivos estratégicos (Dragões, Baron), o que historicamente resulta em maior taxa de vitória.",
    "gold_lead_significant": "Vantagem de ouro de {gold_diff} está em nível crítico, onde estatisticamente {team} tem {win_rate}% de chance de vitória.",
    "team_comp_advantage": "A composição de {team} é superior na fase atual do jogo, com vantagem em teamfights e controle de mapa.",
    "default": "Baseado em análise de múltiplos fatores, {team} apresenta maior probabilidade de vitória neste momento da partida."
}

# Conselhos de timing para apostas
TIMING_ADVICE = {
    "immediate": "⚡ **Entre AGORA** - Situação ideal identificada",
    "wait_for_better_odds": "⏳ **Aguarde** - Odds podem melhorar nos próximos minutos",
    "last_chance": "🚨 **ÚLTIMA CHANCE** - Partida decidindo-se rapidamente",
    "stable_situation": "✅ **Situação estável** - Pode entrar com segurança",
    "risky_timing": "⚠️ **Timing arriscado** - Situação volátil, considere apostar menos"
}

# Alertas importantes para usuários
ALERT_MESSAGES = {
    "high_volatility": "🌪️ Partida muito volátil - Resultado pode mudar rapidamente",
    "comeback_possible": "🔄 Time perdedor ainda pode virar - Cuidado com reversões",
    "dominant_position": "👑 Posição dominante - Chance baixa de virada",
    "early_game": "🌅 Início de partida - Situação pode mudar drasticamente",
    "late_game_decide": "🌙 Partida decidindo - Próximo teamfight pode ser crucial",
    "baron_available": "🐲 Baron disponível - Próximos 5min são críticos",
    "elder_dragon_up": "🔥 Elder Dragon disponível - Pode decidir a partida",
    "inhibitor_down": "🏠 Inibidor destruído - Pressão significativa",
    "no_major_alerts": "✅ Situação controlada - Sem alertas especiais"
}

# Emojis para mapas
MAP_EMOJIS = {
    1: "🗺️ Mapa 1",
    2: "🗺️ Mapa 2", 
    3: "🗺️ Mapa 3",
    4: "🗺️ Mapa 4",
    5: "🗺️ Mapa 5",
    "unknown": "🗺️ Mapa ?"
}

# Status da partida em português
MATCH_STATUS_PT = {
    "live": "🔴 AO VIVO",
    "inprogress": "🔴 EM ANDAMENTO",
    "ongoing": "🔴 ACONTECENDO",
    "in_progress": "🔴 EM PROGRESSO",
    "started": "🔴 INICIADA",
    "draft": "📋 DRAFT",
    "lobby": "🏠 LOBBY",
    "unknown": "❓ DESCONHECIDO"
}

# Objetivos próximos baseados no tempo de jogo
NEXT_OBJECTIVES_BY_TIME = {
    "early": ["🐉 Primeiro Dragão (6min)", "🏰 Primeira Torre", "🦀 Caranguejo"],
    "mid": ["🐉 Alma do Dragão", "🐲 Baron Nashor (20min)", "🏰 Torres Externas"],
    "late": ["🔥 Elder Dragon", "🐲 Baron Buff", "🏠 Inibidores", "👑 Nexus"]
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

# Ligas suportadas para análise - EXPANDIDA PARA INCLUIR TODAS AS REGIONAIS
SUPPORTED_LEAGUES = {
    # Tier 1 - Principais ligas internacionais
    "LCS", "LEC", "LPL", "LCK", "CBLOL", "LLA", "WORLDS", "MSI",
    
    # Tier 2 - Ligas regionais importantes
    "LJL", "LCO", "VCS", "PCS", "TCL", "LCL",
    
    # Tier 3 - Ligas menores e qualificatórias  
    "LCKC", "LDL", "ERL", "ACADEMY", "PRIME",
    
    # Ligas regionais específicas - BRASIL
    "LRS", "Circuito Desafiante", "CBLOL Academy", "Liga Brasileira",
    
    # Ligas regionais específicas - EUROPA
    "LFL", "Prime League", "Superliga", "GLL", "LVP", "PG Nationals",
    "NLC", "Ultraliga", "TCL Academy", "LCL Academy",
    
    # EMEA Masters e variações - ADICIONADO EXPLICITAMENTE
    "EMEA Masters", "EM", "European Masters", "EU Masters", 
    "EMEA Championship", "European Championship", "EMEA",
    
    # Ligas regionais específicas - ÁSIA
    "LJL Academy", "LCO Academy", "VCS Academy", "PCS Academy",
    
    # Ligas regionais específicas - AMERICAS
    "LCS Academy", "LLA Academy", "Copa América",
    
    # Torneios e eventos especiais
    "Demacia Cup", "Rift Rivals", "All-Star", "Clash",
    "University Championship", "Student Championship",
    
    # Ligas semi-profissionais
    "Challengers", "Amateur", "Regional", "Open", "Qualifier",
    
    # Wildcards genéricos para capturar outras ligas
    "Academy", "Championship", "League", "Tournament", "Cup",
    "Series", "Circuit", "Challenge", "Masters", "Premier"
}

# Thresholds para sistema de predição - OTIMIZADOS para odds altas e valor
PREDICTION_THRESHOLDS = {
    "min_confidence": 0.45,          # Reduzido para permitir mais tips  
    "min_ev": 0.5,                   # EV mínimo para aceitar apostas
    "min_odds": 1.50,                # Odds mínima 1.5x conforme solicitado
    "max_odds": 8.00,                # Aumentado para incluir odds altas valiosas
    "min_game_time": 0,              # Permitir desde o draft/início
    "min_data_quality": 0.05,        # Aceitar dados básicos
    "cache_time_minutes": 10,        # Cache de predições
    "ml_confidence_threshold": 0.45,  # Threshold ML
    "hybrid_weight_ml": 0.6,         # Peso do ML no método híbrido
    "hybrid_weight_algo": 0.4,       # Peso dos algoritmos no híbrido
    # Configurações específicas para odds altas
    "high_odds_threshold": 4.0,      # Odds consideradas "altas"
    "high_odds_min_ev": 3.0,         # EV mínimo para odds altas (3%)
    "high_odds_confidence_penalty": 0.1  # Redução de confiança para odds altas
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

# Configurações de Qualidade de Dados
USE_ONLY_REAL_DATA = True  # Sistema trabalha apenas com dados reais, sem mocks/simulações
REQUIRE_LIVE_ODDS = True   # Exige odds reais para gerar tips
MIN_DATA_QUALITY_THRESHOLD = 0.8  # Qualidade mínima de dados para aceitar 
