#!/usr/bin/env python3
"""
Script para limpar conflitos do Telegram apenas
"""
import asyncio
import aiohttp
import time

BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"

async def clear_telegram_conflicts():
    """Limpa conflitos do Telegram via API"""
    print("🧹 Limpando conflitos do Telegram...")
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Múltiplas requisições getUpdates para limpar
            print("📡 Limpando updates pendentes...")
            for i in range(10):
                try:
                    async with session.post(f"{base_url}/getUpdates", 
                                          json={"timeout": 1, "limit": 100}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            updates_count = len(data.get('result', []))
                            if updates_count > 0:
                                print(f"  📥 {updates_count} updates limpos")
                except Exception as e:
                    print(f"  ⚠️ Erro na tentativa {i+1}: {e}")
                
                await asyncio.sleep(0.5)
            
            # 2. Remove webhook
            print("🔗 Removendo webhook...")
            try:
                async with session.post(f"{base_url}/deleteWebhook") as resp:
                    if resp.status == 200:
                        print("✅ Webhook removido")
            except Exception as e:
                print(f"⚠️ Erro ao remover webhook: {e}")
            
            # 3. Verifica bot
            print("🤖 Verificando bot...")
            try:
                async with session.post(f"{base_url}/getMe") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        bot_info = data.get('result', {})
                        print(f"✅ Bot OK: @{bot_info.get('username', 'unknown')}")
            except Exception as e:
                print(f"❌ Erro no bot: {e}")
            
            print("✅ Conflitos limpos!")
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")

async def main():
    print("🚀 Limpeza de Conflitos do Telegram")
    print("=" * 40)
    
    await clear_telegram_conflicts()
    
    print("=" * 40)
    print("🎯 Pronto para iniciar o bot!")

if __name__ == "__main__":
    asyncio.run(main()) 