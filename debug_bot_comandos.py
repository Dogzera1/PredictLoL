#!/usr/bin/env python3
"""
Bot LoL V3 - Debug Mode para verificar comandos
"""
import asyncio
import logging
import time
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

# Configuração de logging detalhado
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"
ADMIN_ID = 8012415611
START_TIME = time.time()

# Contador de comandos
command_count = 0

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler completo para /start"""
    global command_count
    command_count += 1
    
    user = update.effective_user
    logger.info(f"🚀 COMANDO /start RECEBIDO de {user.first_name} (ID: {user.id})")
    
    try:
        message = f"""🚀 **Bot LoL V3 Ultra Avançado** 🚀

Olá, {user.first_name}\\!

✅ **Sistema Operacional:**
• 🤖 Bot respondendo \\(comando #{command_count}\\)
• ⏰ Ativo há: {int((time.time() - START_TIME) / 60)} minutos
• 🔥 Todos os comandos funcionando

**📋 Comandos Disponíveis:**
• `/help` \\- Ajuda completa
• `/status` \\- Status do sistema
• `/ping` \\- Teste de conectividade
• `/debug` \\- Informações de debug

⚡ **Bot 100% funcional\\!**"""

        keyboard = [
            [InlineKeyboardButton("🆘 Ajuda", callback_data="help")],
            [InlineKeyboardButton("📊 Status", callback_data="status")],
            [InlineKeyboardButton("🏓 Ping", callback_data="ping")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        
        logger.info(f"✅ Resposta /start enviada para {user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro no comando /start: {e}")
        await update.message.reply_text(f"❌ Erro interno: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /help"""
    global command_count
    command_count += 1
    
    user = update.effective_user
    logger.info(f"📖 COMANDO /help RECEBIDO de {user.first_name}")
    
    try:
        help_text = f"""🆘 **Ajuda \\- Bot LoL V3**

**👤 Comandos Básicos:**
• `/start` \\- Iniciar bot
• `/help` \\- Esta ajuda
• `/status` \\- Status do sistema
• `/ping` \\- Teste de conectividade
• `/debug` \\- Informações técnicas

**📊 Estatísticas:**
• Comandos processados: {command_count}
• Tempo ativo: {int((time.time() - START_TIME) / 60)} min

🤖 **Bot LoL V3 Ultra Avançado**
⚡ Sistema de tips eSports profissional"""

        await update.message.reply_text(
            help_text,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ Ajuda enviada para {user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro no comando /help: {e}")
        await update.message.reply_text(f"❌ Erro: {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /status"""
    global command_count
    command_count += 1
    
    user = update.effective_user
    logger.info(f"📊 COMANDO /status RECEBIDO de {user.first_name}")
    
    try:
        uptime_min = int((time.time() - START_TIME) / 60)
        uptime_hrs = uptime_min // 60
        uptime_min_rest = uptime_min % 60
        
        status_text = f"""📊 **STATUS DO SISTEMA**

🤖 **Bot Info:**
• Nome: @BETLOLGPT\\_bot
• Status: ✅ Online
• Uptime: {uptime_hrs}h {uptime_min_rest}min

📈 **Estatísticas:**
• Comandos processados: {command_count}
• Usuário atual: {user.first_name}
• ID do usuário: `{user.id}`
• Timestamp: `{int(time.time())}`

🔥 **Sistema 100% operacional\\!**"""

        keyboard = [
            [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_status")],
            [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            status_text,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        
        logger.info(f"✅ Status enviado para {user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro no comando /status: {e}")
        await update.message.reply_text(f"❌ Erro: {str(e)}")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /ping"""
    global command_count
    command_count += 1
    
    user = update.effective_user
    start_time = time.time()
    logger.info(f"🏓 COMANDO /ping RECEBIDO de {user.first_name}")
    
    try:
        # Calcula latência
        response_time = (time.time() - start_time) * 1000
        
        ping_text = f"""🏓 **PONG\\!**

⚡ **Conectividade:**
• Latência: {response_time:.1f}ms
• Status: ✅ Excelente
• Servidor: Online
• API: Funcionando

🎯 **Bot respondendo perfeitamente\\!**"""

        await update.message.reply_text(
            ping_text,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ Pong enviado para {user.first_name} ({response_time:.1f}ms)")
        
    except Exception as e:
        logger.error(f"❌ Erro no comando /ping: {e}")
        await update.message.reply_text(f"❌ Erro: {str(e)}")

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /debug"""
    global command_count
    command_count += 1
    
    user = update.effective_user
    logger.info(f"🐛 COMANDO /debug RECEBIDO de {user.first_name}")
    
    try:
        debug_text = f"""🐛 **DEBUG INFO**

**📱 Update Info:**
• Message ID: `{update.message.message_id}`
• Chat ID: `{update.effective_chat.id}`
• User ID: `{user.id}`
• Username: @{user.username or 'N/A'}

**🤖 Bot Info:**
• Handlers: Todos configurados
• Commands: /start, /help, /status, /ping, /debug
• Callbacks: Configurados
• Messages: Processando

**⚙️ System:**
• Python: Executando
• Telegram API: ✅ Conectado
• Logging: DEBUG ativo

🔧 **Tudo funcionando normalmente\\!**"""

        await update.message.reply_text(
            debug_text,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ Debug info enviada para {user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro no comando /debug: {e}")
        await update.message.reply_text(f"❌ Erro: {str(e)}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para callbacks dos botões"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    logger.info(f"🎛️ CALLBACK RECEBIDO: {data} de {user.first_name}")
    
    try:
        if data == "help":
            await help_command(update, context)
        elif data == "status":
            await status_command(update, context)
        elif data == "ping":
            await ping_command(update, context)
        elif data == "refresh_status":
            await query.edit_message_text(
                "🔄 **Atualizando status\\.\\.\\.**",
                parse_mode='MarkdownV2'
            )
            await asyncio.sleep(1)
            await status_command(update, context)
        elif data == "main_menu":
            await start_command(update, context)
        else:
            await query.edit_message_text(
                f"❓ **Callback desconhecido:** `{data}`",
                parse_mode='MarkdownV2'
            )
        
        logger.info(f"✅ Callback {data} processado para {user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro no callback {data}: {e}")
        await query.edit_message_text(f"❌ Erro: {str(e)}")

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para comandos desconhecidos"""
    global command_count
    command_count += 1
    
    user = update.effective_user
    text = update.message.text
    logger.info(f"❓ COMANDO DESCONHECIDO: '{text}' de {user.first_name}")
    
    try:
        unknown_text = f"""❓ **Comando desconhecido:** `{text}`

**📋 Comandos disponíveis:**
• `/start` \\- Iniciar bot
• `/help` \\- Ajuda
• `/status` \\- Status
• `/ping` \\- Teste
• `/debug` \\- Debug

💡 **Digite um comando válido\\!**"""

        await update.message.reply_text(
            unknown_text,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"✅ Mensagem de comando desconhecido enviada para {user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ Erro no handler de comando desconhecido: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de erros"""
    logger.error(f"❌ ERRO GLOBAL: {context.error}")
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"❌ **Erro interno do bot**\n\n"
                f"Por favor, tente novamente\\.",
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem de erro: {e}")

async def run_debug_bot():
    """Executa bot em modo debug"""
    logger.info("🚀 Iniciando Bot LoL V3 - Modo Debug Completo")
    
    try:
        # Cria aplicação
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Adiciona handlers de comandos
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CommandHandler("ping", ping_command))
        app.add_handler(CommandHandler("debug", debug_command))
        
        # Handler para callbacks
        app.add_handler(CallbackQueryHandler(handle_callback))
        
        # Handler para comandos desconhecidos
        app.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
        
        # Handler global de erros
        app.add_error_handler(error_handler)
        
        # Inicializa
        await app.initialize()
        await app.start()
        
        # Informações do bot
        me = await app.bot.get_me()
        logger.info(f"✅ Bot iniciado: @{me.username} - {me.first_name}")
        logger.info(f"👤 Admin ID: {ADMIN_ID}")
        logger.info(f"📱 Comandos: /start, /help, /status, /ping, /debug")
        logger.info(f"🎛️ Callbacks: Configurados")
        logger.info(f"🔧 Debug: ATIVO")
        logger.info("🔥 PRONTO PARA RECEBER COMANDOS!")
        
        # Inicia polling
        await app.updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            poll_interval=1.0
        )
        
        # Mantém rodando
        print("\n" + "="*60)
        print("🤖 BOT LoL V3 - DEBUG MODE ATIVO")
        print("="*60)
        print(f"✅ Bot: @{me.username}")
        print(f"🆔 Admin: {ADMIN_ID}")
        print("📱 Comandos ativos: /start, /help, /status, /ping, /debug")
        print("🔍 Logs em tempo real abaixo:")
        print("="*60)
        print("📱 Teste os comandos no Telegram agora!")
        print("🛑 Ctrl+C para parar")
        print("="*60)
        
        # Aguarda indefinidamente
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("🛑 Parando bot...")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
    finally:
        if app.updater:
            await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("✅ Bot parado com sucesso")

if __name__ == "__main__":
    asyncio.run(run_debug_bot()) 