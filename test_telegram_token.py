#!/usr/bin/env python3
"""
Teste simples do token do Telegram
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

async def test_telegram_token():
    """Testa se o token do Telegram está válido"""
    load_dotenv()
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Token não encontrado")
        return False
    
    print(f"🔍 Testando token: {token[:10]}...{token[-10:]}")
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
                if response.status == 200 and data.get('ok'):
                    bot_info = data['result']
                    print(f"✅ Token válido!")
                    print(f"   Bot: @{bot_info.get('username', 'N/A')}")
                    print(f"   Nome: {bot_info.get('first_name', 'N/A')}")
                    print(f"   ID: {bot_info.get('id', 'N/A')}")
                    return True
                else:
                    print(f"❌ Token inválido: {data}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro ao testar token: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_telegram_token()) 
