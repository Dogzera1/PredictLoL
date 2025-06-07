#!/usr/bin/env python3
"""
Script para testar especificamente o comando /start
"""

import asyncio
import os
import logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler

# Token do bot
BOT_TOKEN = "7584060058:AAG0_htf_kVuV_JUzNgMJMuRUOVnJGmeu0o"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def handle_start(update: Update, context) -> None:
    """Handler simplificado para /start"""
    user = update.effective_user
    
    message = f"""🚀 **TESTE - Bot LoL V3 Ultra Avançado!**

Olá, {user.first_name}! 

✅ O comando /start está funcionando!

Este é um teste básico."""
    
    logger.info(f"📤 Enviando resposta para {user.first_name} ({user.id})")
    
    await update.message.reply_text(message)
    logger.info("✅ Resposta enviada com sucesso!")

async def test_bot():
    """Teste básico do bot"""
    try:
        logger.info("🤖 TESTE DO COMANDO /start")
        logger.info("=" * 50)
        
        # Cria application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Adiciona handler
        application.add_handler(CommandHandler("start", handle_start))
        
        logger.info("✅ Handler /start registrado")
        
        # Testa conexão com bot
        bot = Bot(BOT_TOKEN)
        bot_info = await bot.get_me()
        
        logger.info(f"🔗 Bot conectado: @{bot_info.username} ({bot_info.first_name})")
        
        # Inicia polling
        await application.initialize()
        await application.start()
        
        logger.info("🎯 Bot iniciado! Teste o comando /start no Telegram")
        logger.info("📱 Bot: @BETLOLGPT_bot")
        logger.info("🛑 Pressione Ctrl+C para parar")
        
        # Polling
        await application.updater.start_polling(
            allowed_updates=["message"],
            drop_pending_updates=True
        )
        
        # Mantém rodando
        await application.updater.idle()
        
    except KeyboardInterrupt:
        logger.info("🛑 Parando teste...")
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        raise
    finally:
        if 'application' in locals():
            await application.stop()
            await application.shutdown()
        logger.info("✅ Teste finalizado")

if __name__ == "__main__":
    asyncio.run(test_bot()) 