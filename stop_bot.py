#!/usr/bin/env python3
"""
Script para parar instâncias anteriores do bot via API do Telegram
"""

import os
import asyncio
import aiohttp
import sys
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

async def stop_bot_webhook():
    """Para o bot removendo webhook e cancelando polling"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg")
    
    if not bot_token or bot_token == "BOT_TOKEN_HERE":
        print("❌ Token do bot não configurado")
        return False
    
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🛑 Parando instâncias anteriores do bot...")
            
            # 1. Remove webhook se existir
            print("📡 Removendo webhook...")
            async with session.post(f"{base_url}/deleteWebhook") as resp:
                if resp.status == 200:
                    print("✅ Webhook removido")
                else:
                    print("⚠️ Webhook não existia ou erro ao remover")
            
            # 2. Cancela qualquer polling ativo chamando getUpdates com timeout 0
            print("🔄 Cancelando polling ativo...")
            async with session.post(f"{base_url}/getUpdates", json={"timeout": 0}) as resp:
                if resp.status == 200:
                    print("✅ Polling anterior cancelado")
                else:
                    print("⚠️ Nenhum polling ativo")
            
            # 3. Verifica se bot está operacional
            print("🔍 Verificando status do bot...")
            async with session.get(f"{base_url}/getMe") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        bot_info = data["result"]
                        print(f"✅ Bot @{bot_info['username']} ({bot_info['first_name']}) está pronto")
                        return True
                    else:
                        print("❌ Bot não está operacional")
                        return False
                else:
                    print("❌ Erro ao verificar status do bot")
                    return False
    
    except Exception as e:
        print(f"❌ Erro ao parar bot: {e}")
        return False

async def main():
    """Função principal"""
    print("🧹 LIMPADOR DE BOT - Railway Deploy Helper")
    print("="*50)
    
    success = await stop_bot_webhook()
    
    if success:
        print("\n✅ Bot limpo e pronto para deploy!")
        print("🚀 Agora você pode fazer deploy no Railway sem conflitos")
    else:
        print("\n❌ Falha na limpeza do bot")
        print("⚠️ Pode haver conflitos no deploy")
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main()) 