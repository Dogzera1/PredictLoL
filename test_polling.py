"""
Script para testar o bot do Telegram em modo polling (sem webhook)
"""

import logging
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Handlers para comandos
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('✅ Bot ativo! Use /ajuda para ver os comandos disponíveis.')

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("""
📋 *Comandos disponíveis:*
/start - Iniciar o bot
/ajuda - Mostrar esta ajuda
/sobre - Informações sobre o bot

_Bot em modo de teste._
    """, parse_mode="Markdown")

def about_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("""
*LoL-GPT Betting Assistant* 🎮

Um bot para ajudar em apostas de League of Legends, usando modelos preditivos.
    """, parse_mode="Markdown")

def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"Você disse: {update.message.text}")

def main() -> None:
    # Tentar obter o token do config.py
    try:
        from config import BOT_TOKEN
        token = BOT_TOKEN
    except ImportError:
        token = None
    
    # Tentar obter o token da variável de ambiente
    env_token = os.environ.get("TELEGRAM_TOKEN")
    if env_token:
        token = env_token
    
    if not token or token == "SEU_TOKEN_AQUI":
        logger.error("Token do Telegram não definido!")
        return
    
    logger.info("Iniciando o bot em modo polling...")
    
    # Criar o updater e o dispatcher
    updater = Updater(token)
    dispatcher = updater.dispatcher
    
    # Registrar os handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("ajuda", help_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("sobre", about_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    
    # Iniciar o bot em modo polling
    updater.start_polling()
    logger.info("Bot iniciado. Pressione Ctrl+C para parar.")
    
    # Manter o bot rodando até que o usuário pressione Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main() 