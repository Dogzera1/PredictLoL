"""
Configurações do Bot de Telegram para apostas em LoL

Este arquivo contém configurações e constantes utilizadas pelo bot.
"""

import os

# Token do bot do Telegram - USAR VARIÁVEL DE AMBIENTE EM PRODUÇÃO
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo")

# Configurações da API Riot
RIOT_API_KEY = os.environ.get("RIOT_API_KEY", "RGAPI-25f07e53-9e17-474b-a357-4e416d985311")
RIOT_API_BASE_URL = "https://esports-api.lolesports.com/persisted/gw"

# URLs para streams
TWITCH_URL = "https://www.twitch.tv/riotgames"
YOUTUBE_URL = "https://www.youtube.com/lolesports"

# Configurações do modelo de previsão
MODEL_CONFIDENCE_THRESHOLD = float(os.environ.get("MODEL_CONFIDENCE_THRESHOLD", "0.65"))

# Intervalos de atualização (em segundos)
UPDATE_INTERVAL = int(os.environ.get("UPDATE_INTERVAL", "60"))

# Mensagens padrão
MSG_NO_MATCHES = "📢 Não há partidas ao vivo no momento. Tente novamente mais tarde."
MSG_ERROR = "❌ Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde."
MSG_LOADING = "🔄 Carregando dados... Aguarde um momento." 