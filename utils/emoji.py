"""
Utilitário de emojis para padronização de indicadores visuais no bot.

Define emojis para diferentes status, eventos e elementos do jogo.
"""

# Emojis de elementos de jogo
GOLD = "💰"
KILL = "☠️"
DEATH = "💀"
DRAGON = "🐉"
BARON = "🦄"
TOWER = "🏯"
HERALD = "👁️"
INHIBITOR = "🏛️"
TIME = "⏱️"

# Emojis de status
LIVE = "🔴"
SCHEDULED = "⏳"
COMPLETED = "✅"
ERROR = "❌"
WARNING = "⚠️"
INFO = "ℹ️"
LOADING = "🔄"

# Emojis de times/lanes
BLUE_TEAM = "🟦"
RED_TEAM = "🟥"
TOP = "⬆️"
JUNGLE = "🌳"
MID = "↔️"
ADC = "🏹"
SUPPORT = "🛡️"

# Emojis de previsão
PREDICTION = "🔮"
ODDS = "📊"
BOT_PICK = "🤖"
UP_TREND = "📈"
DOWN_TREND = "📉"
NEUTRAL_TREND = "➖"

# Emojis de navegação
BACK = "◀️"
REFRESH = "🔄"
DETAILS = "📋"
HOME = "🏠"
SETTINGS = "⚙️"

# Emojis de torneios/partidas
MATCH = "⚔️"
TOURNAMENT = "🏆"
LEAGUE = "🌐"
STREAM = "📺"

# Funções úteis
def trend_emoji(value):
    """Retorna emoji de tendência baseado no valor (+, -, neutro)"""
    if value > 0.15:
        return UP_TREND
    elif value < -0.15:
        return DOWN_TREND
    else:
        return NEUTRAL_TREND 