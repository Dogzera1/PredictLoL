#!/usr/bin/env python3
"""
Kill ALL Python processes and clear bot conflicts DEFINITIVELY
"""
import subprocess
import asyncio
import aiohttp
import time
import sys
import os

BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"

def kill_all_python():
    """Mata todos os processos Python"""
    print("🔪 Matando TODOS os processos Python...")
    
    try:
        # Windows
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                      capture_output=True, check=False)
        subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], 
                      capture_output=True, check=False)
        subprocess.run(["taskkill", "/F", "/T", "/FI", "IMAGENAME eq python*"], 
                      capture_output=True, check=False)
        print("✅ Processos Python terminados")
    except Exception as e:
        print(f"⚠️ Erro ao matar processos: {e}")

async def aggressive_cleanup():
    """Limpeza agressiva"""
    print("🧨 Iniciando limpeza AGRESSIVA...")
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        # 1. Remove webhook múltiplas vezes
        for i in range(5):
            try:
                async with session.post(f"{base_url}/deleteWebhook") as resp:
                    print(f"🔗 Webhook delete {i+1}/5: {resp.status}")
            except:
                pass
            await asyncio.sleep(1)
        
        # 2. Get updates agressivo
        for i in range(20):
            try:
                async with session.post(
                    f"{base_url}/getUpdates", 
                    json={"timeout": 1, "offset": -1}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        updates_count = len(data.get('result', []))
                        print(f"🔄 Cleanup {i+1}/20: {updates_count} updates limpos")
                    await asyncio.sleep(0.3)
            except Exception as e:
                print(f"⚠️ Tentativa {i+1}: {e}")
                await asyncio.sleep(0.5)
        
        # 3. Set empty webhook
        try:
            async with session.post(
                f"{base_url}/setWebhook",
                json={"url": ""}
            ) as resp:
                print(f"🔗 Webhook vazio definido: {resp.status}")
        except:
            pass
        
        # 4. Teste final
        try:
            async with session.post(f"{base_url}/getMe") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    bot_info = data.get('result', {})
                    print(f"✅ Bot livre: @{bot_info.get('username')}")
                else:
                    print(f"❌ Erro teste: {resp.status}")
        except Exception as e:
            print(f"❌ Erro final: {e}")

async def main():
    """Main destrutivo"""
    print("💀 LIMPEZA TOTAL INICIADA!")
    print("⚠️ Isso vai MATAR todos os processos Python!")
    
    # Passo 1: Mata todos os processos
    kill_all_python()
    await asyncio.sleep(3)
    
    # Passo 2: Limpeza via API
    await aggressive_cleanup()
    
    # Passo 3: Aguarda estabilização
    print("⏳ Aguardando 15s para estabilização total...")
    await asyncio.sleep(15)
    
    print("🎉 LIMPEZA TOTAL CONCLUÍDA!")
    print("✅ Agora pode rodar qualquer bot SEM conflitos!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}") 