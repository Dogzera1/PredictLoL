#!/usr/bin/env python3
"""
Teste específico para o comando /start do bot
"""

import os
import asyncio
import logging
from pathlib import Path
import sys

# Adicionar o diretório do bot ao path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def teste_start_command():
    """Teste do comando /start"""
    print("🧪 Testando comando /start do bot...")
    
    try:
        # 1. Verificar token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN não encontrado!")
            print("Defina: export TELEGRAM_BOT_TOKEN='seu_token_aqui'")
            return False
        
        print(f"✅ Token encontrado: {bot_token[:10]}...")
        
        # 2. Criar bot
        from bot.telegram_bot.predictlol_bot import PredictLoLTelegramBot
        
        bot = PredictLoLTelegramBot(token=bot_token)
        print("✅ Bot criado")
        
        # 3. Inicializar
        await bot.initialize()
        print("✅ Bot inicializado")
        
        # 4. Verificar se handlers estão registrados
        if bot.app and bot.app.handlers:
            handlers_count = len(bot.app.handlers[0])  # Group 0 handlers
            print(f"✅ {handlers_count} handlers registrados")
            
            # Procurar handler do /start
            start_handler_found = False
            for handler in bot.app.handlers[0]:
                if hasattr(handler, 'command') and 'start' in handler.command:
                    start_handler_found = True
                    break
                elif hasattr(handler, 'callback') and 'start' in str(handler.callback):
                    start_handler_found = True
                    break
            
            if start_handler_found:
                print("✅ Handler /start encontrado")
            else:
                print("❌ Handler /start NÃO encontrado")
                return False
        else:
            print("❌ Nenhum handler registrado")
            return False
        
        # 5. Testar método _start_command diretamente
        try:
            # Criar mock do update e context
            class MockUser:
                first_name = "TestUser"
            
            class MockMessage:
                async def reply_text(self, text, **kwargs):
                    print(f"📝 Resposta do bot:\n{text}")
                    return True
            
            class MockUpdate:
                effective_user = MockUser()
                message = MockMessage()
            
            class MockContext:
                pass
            
            mock_update = MockUpdate()
            mock_context = MockContext()
            
            # Testar método diretamente
            await bot._start_command(mock_update, mock_context)
            print("✅ Método _start_command executado com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao executar _start_command: {e}")
            return False
        
        print("\n🎯 DIAGNÓSTICO COMPLETO:")
        print("✅ Token configurado")
        print("✅ Bot inicializado")
        print("✅ Handlers registrados")
        print("✅ Comando /start funcional")
        print("\n💡 O bot deveria estar funcionando!")
        print("\nSe ainda não funciona, pode ser:")
        print("1. Bot não está rodando (execute: python main.py)")
        print("2. Token expirado (crie novo bot no @BotFather)")
        print("3. Bot não foi iniciado no Telegram (@PredictLoLbot)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("Verifique se todos os módulos estão instalados")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

if __name__ == "__main__":
    # Configurar token de teste
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("⚠️  Configurando token padrão para teste...")
        os.environ["TELEGRAM_BOT_TOKEN"] = "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI"
    
    asyncio.run(teste_start_command()) 