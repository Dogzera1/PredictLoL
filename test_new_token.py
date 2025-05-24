#!/usr/bin/env python3
import asyncio
import aiohttp
import os

async def test_token():
    token = os.environ.get('TELEGRAM_TOKEN')
    print(f"🔍 Token: {token[:15]}...{token[-10:] if token else 'None'}")
    
    if not token:
        print("❌ Token não encontrado")
        return False
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    bot_info = data.get('result', {})
                    print(f"✅ Token válido!")
                    print(f"🤖 Bot: @{bot_info.get('username', 'N/A')}")
                    print(f"📛 Nome: {bot_info.get('first_name', 'N/A')}")
                    return True
                else:
                    print(f"❌ Token inválido (Status: {response.status})")
                    return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_token())
    exit(0 if result else 1) 