#!/usr/bin/env python3

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

async def test_telegram_token():
    """Testa se o token do Telegram está válido"""
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN não encontrado no .env")
        return False
    
    print(f"🔍 Testando token: {token[:10]}...")
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        bot_info = data.get("result", {})
                        print("✅ TOKEN VÁLIDO!")
                        print(f"   Nome do bot: {bot_info.get('first_name')}")
                        print(f"   Username: @{bot_info.get('username')}")
                        print(f"   ID: {bot_info.get('id')}")
                        return True
                    else:
                        print(f"❌ Erro na resposta: {data}")
                        return False
                else:
                    print(f"❌ Status HTTP: {response.status}")
                    error_text = await response.text()
                    print(f"   Erro: {error_text}")
                    return False
    
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Testando configuração do bot Telegram...")
    result = asyncio.run(test_telegram_token())
    
    if result:
        print("\n✅ Bot configurado corretamente!")
    else:
        print("\n❌ Bot precisa ser reconfigurado.")
        print("\n🔧 Para corrigir:")
        print("1. Vá ao @BotFather no Telegram")
        print("2. Use /newbot para criar um novo bot")
        print("3. Copie o token fornecido")
        print("4. Atualize TELEGRAM_BOT_TOKEN no arquivo .env") 