#!/usr/bin/env python3
"""
Script simples e rápido para limpeza de conflitos
"""
import asyncio
import aiohttp
import time

BOT_TOKEN = "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0"

async def simple_clear():
    print("🧹 LIMPEZA SIMPLES E RÁPIDA")
    print("=" * 40)
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Remove webhook
            print("🔗 Removendo webhook...")
            async with session.post(f"{base_url}/deleteWebhook") as resp:
                if resp.status == 200:
                    print("✅ Webhook removido")
                else:
                    print(f"⚠️ Status webhook: {resp.status}")
            
            # 2. Limpeza rápida de updates
            print("📥 Limpando updates...")
            for i in range(10):
                async with session.post(f"{base_url}/getUpdates", 
                                      json={"timeout": 0, "limit": 100, "offset": -1}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        updates_count = len(data.get('result', []))
                        if updates_count > 0:
                            print(f"   Limpou {updates_count} updates")
                        elif i == 0:
                            print("   Nenhum update pendente")
                await asyncio.sleep(0.5)
            
            # 3. Teste final
            print("🧪 Testando controle...")
            await asyncio.sleep(2)
            
            async with session.post(f"{base_url}/getUpdates", 
                                  json={"timeout": 1, "limit": 1}) as resp:
                if resp.status == 200:
                    print("✅ SUCESSO! Bot sob controle")
                    print("🚀 Execute: python main.py")
                    return True
                elif resp.status == 409:
                    print("❌ Conflito ainda persiste")
                    print("💡 Aguarde 5 minutos ou verifique instâncias remotas")
                    return False
                else:
                    print(f"⚠️ Status inesperado: {resp.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(simple_clear())
    print("=" * 40)
    if result:
        print("🎉 LIMPEZA CONCLUÍDA COM SUCESSO!")
    else:
        print("⚠️ Problemas persistem") 
