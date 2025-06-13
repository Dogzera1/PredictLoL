#!/usr/bin/env python3
"""
Bot Telegram simples para testar o comando /start
"""

import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotSimples:
    def __init__(self, token: str):
        self.token = token
        self.app = None
        
    async def initialize(self):
        """Inicializa o bot"""
        self.app = Application.builder().token(self.token).build()
        
        # Registrar comando /start
        self.app.add_handler(CommandHandler("start", self.start_command))
        
        logger.info("✅ Bot simples inicializado")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user = update.effective_user
        
        message = f"""
🎯 **PredictLoL - Sistema de Apostas**

Olá {user.first_name}! 

✅ Bot funcionando perfeitamente!
✅ Comando /start operacional!

Funcionalidades disponíveis:
• 💰 Gestão de Bankroll
• 📊 Análise de Value  
• 📈 Tracker de Apostas
• 🎮 Previsões Pós-Draft

Use /help para mais informações.
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Bot OK!", callback_data="bot_ok")],
            [InlineKeyboardButton("📊 Menu", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info(f"✅ /start executado para {user.first_name}")
    
    async def run(self):
        """Executa o bot"""
        try:
            await self.initialize()
            
            # Executar polling
            await self.app.run_polling(
                poll_interval=1.0,
                timeout=10,
                read_timeout=10,
                write_timeout=10,
                connect_timeout=10
            )
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")

async def main():
    """Função principal"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI")
    
    bot = BotSimples(token)
    await bot.run()

if __name__ == "__main__":
    print("🤖 Iniciando bot simples para teste...")
    print("Teste o comando /start no @PredictLoLbot")
    asyncio.run(main()) 