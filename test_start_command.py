#!/usr/bin/env python3
"""
Teste simples do comando /start - Bot LoL V3
"""
import asyncio
import logging
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token do bot
BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"
ADMIN_ID = 8012415611

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler simples para /start"""
    user = update.effective_user
    logger.info(f"Comando /start recebido de {user.first_name} (ID: {user.id})")
    
    is_admin = user.id == ADMIN_ID
    admin_text = " 👑 **ADMIN**" if is_admin else ""
    
    message = f"""🚀 **Bot LoL V3 Ultra Avançado** 🚀{admin_text}

Olá, {user.first_name}\\! 

✅ **Comando /start funcionando perfeitamente\\!**

🎯 Sistema operacional:
• Bot respondendo normalmente
• Handlers configurados
• Token válido
• Conexão estável

📋 **Comandos disponíveis:**
• `/help` \\- Ajuda completa
• `/status` \\- Status do sistema

🔥 **Bot testado e funcionando\\!**"""
    
    await update.message.reply_text(
        message,
        parse_mode='MarkdownV2'
    )

async def handle_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando de teste"""
    await update.message.reply_text("✅ Comando de teste funcionando!")

async def test_start_command():
    """Testa apenas o comando /start"""
    try:
        logger.info("🧪 Testando comando /start...")
        
        # Cria aplicação
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Adiciona handlers de teste
        app.add_handler(CommandHandler("start", handle_start))
        app.add_handler(CommandHandler("test", handle_test))
        
        # Inicializa
        await app.initialize()
        logger.info("✅ Bot inicializado")
        
        # Inicia
        await app.start()
        logger.info("✅ Bot iniciado")
        
        # Polling
        logger.info("🔄 Iniciando polling...")
        logger.info(f"👥 Bot: @{app.bot.username}")
        logger.info("📱 Envie /start para testar")
        logger.info("⏹️ Ctrl+C para parar")
        
        await app.updater.start_polling()
        
        # Aguarda indefinidamente
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("🛑 Interrompido pelo usuário")
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
    finally:
        # Cleanup
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            logger.info("✅ Bot parado com sucesso")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_start_command()) 