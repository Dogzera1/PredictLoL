"""
Bot principal do LoL-GPT Betting Assistant.

Configura e inicia o bot do Telegram.
"""

import logging
import os
import argparse
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# Importar configurações
from config import BOT_TOKEN

# Importar handlers
from handlers.main import (
    start_handler, 
    help_handler, 
    about_handler, 
    live_matches_handler, 
    upcoming_matches_handler, 
    match_handler,
    error_handler
)
from handlers.callbacks import callback_handler

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def train_model():
    """Função para treinar o modelo do zero com dados históricos"""
    try:
        from services.model_trainer import ModelTrainer
        
        logger.info("Iniciando treinamento do modelo com dados históricos...")
        trainer = ModelTrainer()
        
        # Coletar dados históricos
        logger.info("Coletando dados históricos...")
        success = trainer.collect_historical_data()
        
        if not success:
            logger.error("Falha ao coletar dados históricos. Verifique a chave da API e conexão.")
            return False
        
        # Treinar modelo
        logger.info("Treinando modelo...")
        success = trainer.train_model()
        
        if success:
            logger.info("Modelo treinado com sucesso!")
            return True
        else:
            logger.error("Falha ao treinar modelo.")
            return False
    except Exception as e:
        logger.error(f"Erro durante treinamento do modelo: {str(e)}")
        return False

def main():
    """Função principal para iniciar o bot"""
    # Verificar se o token está definido
    if not BOT_TOKEN or BOT_TOKEN == "SEU_TOKEN_AQUI":
        logger.error("Token do Telegram não definido. Por favor, atualize o arquivo config.py.")
        return
    
    # Criar o updater e dispatcher
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    # Registrar handlers para comandos
    dp.add_handler(CommandHandler("start", start_handler))
    dp.add_handler(CommandHandler("ajuda", help_handler))
    dp.add_handler(CommandHandler("help", help_handler))
    dp.add_handler(CommandHandler("sobre", about_handler))
    dp.add_handler(CommandHandler("ao_vivo", live_matches_handler))
    dp.add_handler(CommandHandler("proximas", upcoming_matches_handler))
    dp.add_handler(CommandHandler("partida", match_handler))
    
    # Registrar handler para callbacks de botões
    dp.add_handler(CallbackQueryHandler(callback_handler))
    
    # Handler para comandos desconhecidos
    dp.add_handler(MessageHandler(
        Filters.command, 
        lambda u, c: u.message.reply_text("Comando não reconhecido. Use /ajuda para ver os comandos disponíveis.")
    ))
    
    # Registrar handler de erro
    dp.add_error_handler(error_handler)
    
    # Iniciar o bot
    logger.info("Bot iniciado. Pressione Ctrl+C para parar.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='LoL-GPT Betting Assistant')
    parser.add_argument('--train', action='store_true', help='Treinar o modelo antes de iniciar o bot')
    args = parser.parse_args()
    
    # Treinar modelo se solicitado
    if args.train:
        logger.info("Treinando modelo antes de iniciar o bot...")
        train_model()
    
    logger.info("Iniciando LoL-GPT Betting Assistant...")
    main() 