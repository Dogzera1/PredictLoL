#!/usr/bin/env python3
"""
Versão de teste do main.py com token correto
"""
import os
import sys
import asyncio
import logging

# Força o token correto ANTES de qualquer importação
os.environ["TELEGRAM_BOT_TOKEN"] = "7584060058:AAHiZkgr-TFlbt8Ym1GNFMdvjfVa6oED9l8"
os.environ["TELEGRAM_ADMIN_USER_IDS"] = "8012415611"

print("🔧 Token forçado no início:", os.environ["TELEGRAM_BOT_TOKEN"][:20] + "...")

# Importa apenas após definir as variáveis
from bot.utils.constants import TELEGRAM_CONFIG

# Verifica se está usando o token correto
print("🔍 Token nas constantes:", TELEGRAM_CONFIG["bot_token"][:20] + "...")

# Simula o mesmo processo do main.py original
bot_token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_CONFIG["bot_token"])
print("✅ Token final escolhido:", bot_token[:20] + "...")

# Teste rápido de conexão
async def test_connection():
    try:
        from telegram.ext import Application
        
        app = Application.builder().token(bot_token).build()
        await app.initialize()
        
        # Testa getMe
        bot_info = await app.bot.get_me()
        print(f"🎉 BOT CONECTADO: @{bot_info.username}")
        print(f"📝 Nome: {bot_info.first_name}")
        
        await app.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

# Executa teste
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 TESTANDO CONEXÃO COM TOKEN CORRETO")
    print("="*50)
    
    result = asyncio.run(test_connection())
    
    if result:
        print("\n✅ TOKEN FUNCIONANDO PERFEITAMENTE!")
        print("🔥 Pode iniciar o sistema principal com segurança")
        
        # Pergunta se quer iniciar o sistema completo
        print("\n⚡ Iniciando sistema principal automaticamente em 3 segundos...")
        print("   Pressione Ctrl+C para cancelar")
        
        try:
            import time
            time.sleep(3)
            
            # Remove este arquivo de teste e executa o main real
            print("\n🚀 INICIANDO SISTEMA PRINCIPAL...")
            
            # Importa e executa o sistema completo
            exec(open("main.py").read())
            
        except KeyboardInterrupt:
            print("\n⏹️ Cancelado pelo usuário")
            
    else:
        print("\n❌ PROBLEMA COM O TOKEN!")
        sys.exit(1) 