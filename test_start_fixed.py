#!/usr/bin/env python3
"""
Teste do comando /start com sistema corrigido
"""

import asyncio
import os
import sys

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.abspath('.'))

from bot.telegram_bot.alerts_system import TelegramAlertsSystem

async def test_start_system():
    """Teste do sistema de alertas"""
    try:
        print("🔧 TESTE DO SISTEMA DE ALERTAS")
        print("=" * 50)
        
        # Token do bot
        token = "7584060058:AAG0_htf_kVuV_JUzNgMJMuRUOVnJGmeu0o"
        
        # Inicializa sistema
        print("📱 Inicializando TelegramAlertsSystem...")
        alerts_system = TelegramAlertsSystem(bot_token=token)
        
        print("🔄 Inicializando bot...")
        await alerts_system.initialize()
        
        print("🚀 Iniciando bot...")
        await alerts_system.start_bot()
        
        print("✅ Bot iniciado com sucesso!")
        print("📱 Teste o comando /start no @BETLOLGPT_bot")
        print("🛑 Pressione Ctrl+C para parar")
        
        # Mantém rodando
        while True:
            await asyncio.sleep(10)
            print("🔄 Sistema ativo... (teste /start)")
        
    except KeyboardInterrupt:
        print("\n🛑 Parando teste...")
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise
    finally:
        if 'alerts_system' in locals():
            try:
                await alerts_system.stop_bot()
                print("✅ Bot parado")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(test_start_system()) 