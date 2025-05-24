#!/usr/bin/env python3
"""
Teste mínimo para isolar o problema do Application do Telegram
"""

import asyncio
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_app_minimal():
    """Teste mínimo do Application do Telegram"""
    try:
        print("🔍 Testando Application do Telegram...")
        
        # Importar apenas o necessário
        from telegram.ext import Application
        
        print("✅ Import do Application bem-sucedido")
        
        # Obter token
        token = os.environ.get('TELEGRAM_TOKEN')
        if not token:
            print("❌ Token não encontrado")
            return False
        
        print(f"✅ Token encontrado: {token[:15]}...{token[-10:]}")
        
        # Criar application simples
        print("🏗️ Criando Application...")
        app = Application.builder().token(token).build()
        print("✅ Application criado com sucesso")
        
        # Testar bot
        print("🤖 Testando bot...")
        bot_info = await app.bot.get_me()
        print(f"✅ Bot: @{bot_info.username}")
        
        # Testar run_polling por alguns segundos
        print("🚀 Testando run_polling por 5 segundos...")
        
        # Executar com timeout
        task = asyncio.create_task(
            app.run_polling(
                poll_interval=2.0,
                timeout=5,
                drop_pending_updates=True
            )
        )
        
        await asyncio.wait_for(task, timeout=5.0)
        
        return True
        
    except asyncio.TimeoutError:
        print("✅ Timeout alcançado - teste bem-sucedido!")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_telegram_app_minimal())
        print(f"\n🏁 Resultado: {'✅ SUCESSO' if result else '❌ FALHOU'}")
        exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        exit(1) 