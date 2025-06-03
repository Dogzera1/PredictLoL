#!/usr/bin/env python3
"""
Debug do token - rastreia exatamente onde o token está sendo usado
"""
import os
import sys

# Força o token correto NO INÍCIO
os.environ["TELEGRAM_BOT_TOKEN"] = "7584060058:AAHiZkgr-TFlbt8Ym1GNFMdvjfVa6oED9l8"
os.environ["TELEGRAM_ADMIN_USER_IDS"] = "8012415611"

print("=" * 60)
print("🔍 DEBUG DO TOKEN - RASTREAMENTO COMPLETO")
print("=" * 60)

# 1. Verifica variável de ambiente
print(f"1️⃣ ENVIRONMENT: {os.getenv('TELEGRAM_BOT_TOKEN', 'NÃO DEFINIDO')[:20]}...")

# 2. Verifica constants.py
try:
    from bot.utils.constants import TELEGRAM_CONFIG
    print(f"2️⃣ CONSTANTS.PY: {TELEGRAM_CONFIG['bot_token'][:20]}...")
except Exception as e:
    print(f"2️⃣ CONSTANTS.PY: ERRO - {e}")

# 3. Simula o main.py
print(f"3️⃣ MAIN.PY SIMULATION:")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_CONFIG["bot_token"])
print(f"   Token escolhido: {bot_token[:20]}...")

# 4. Testa criação da aplicação diretamente
try:
    print(f"4️⃣ TESTE APLICAÇÃO TELEGRAM:")
    from telegram.ext import Application
    
    app = Application.builder().token(bot_token).build()
    print(f"   ✅ Aplicação criada com token: {bot_token[:20]}...")
    
    # 5. Testa conexão real
    import asyncio
    import aiohttp
    
    async def test_token():
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    if data.get('ok'):
                        bot_info = data['result']
                        print(f"   ✅ TOKEN VÁLIDO! Bot: @{bot_info.get('username')}")
                        print(f"   📝 Nome: {bot_info.get('first_name')}")
                        return True
                    else:
                        print(f"   ❌ TOKEN INVÁLIDO: {data}")
                        return False
        except Exception as e:
            print(f"   ❌ ERRO NO TESTE: {e}")
            return False
    
    result = asyncio.run(test_token())
    
    if result:
        print("\n🎉 TOKEN CORRETO CONFIRMADO!")
    else:
        print("\n❌ PROBLEMA COM O TOKEN!")

except Exception as e:
    print(f"4️⃣ ERRO NA APLICAÇÃO: {e}")

print("=" * 60)
print("🔧 PRÓXIMO PASSO: Iniciar sistema com este token")
print("=" * 60) 