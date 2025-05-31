#!/usr/bin/env python3
"""
Teste simples do Bot Telegram - Bot LoL V3
"""
import asyncio
import logging
import os
from telegram.ext import Application

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token do bot
BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"

async def test_simple_bot():
    """Teste básico do bot"""
    try:
        logger.info("🧪 Testando Bot Telegram simples...")
        
        # Cria aplicação
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Inicializa
        await app.initialize()
        logger.info("✅ Bot inicializado")
        
        # Inicia
        await app.start()
        logger.info("✅ Bot iniciado")
        
        # Testa me
        me = await app.bot.get_me()
        logger.info(f"✅ Bot info: @{me.username} - {me.first_name}")
        
        # Para
        await app.stop()
        await app.shutdown()
        logger.info("✅ Bot parado com sucesso")
        
        logger.info("🎉 Teste do bot passou!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_simple_bot())
    if result:
        print("\n✅ Bot funcionando corretamente!")
    else:
        print("\n❌ Bot com problemas!") 