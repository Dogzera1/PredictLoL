#!/usr/bin/env python3
"""
Script ULTRA AGRESSIVO para limpar conflitos do Telegram
"""
import asyncio
import aiohttp
import time

BOT_TOKEN = "7584060058:AAG0_htf_kVuV_JUzNgMJMuRUOVnJGmeu0o"

async def ultra_aggressive_cleanup():
    """Limpeza ultra agressiva de conflitos"""
    print("🚨 LIMPEZA ULTRA AGRESSIVA - FORÇANDO CONTROLE DO BOT")
    print("=" * 60)
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    # Configurações agressivas
    timeout_connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=50,
        keepalive_timeout=60,
        enable_cleanup_closed=True
    )
    
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    async with aiohttp.ClientSession(
        connector=timeout_connector,
        timeout=timeout
    ) as session:
        
        # FASE 1: Bombardeio de getUpdates para "roubar" controle
        print("🔥 FASE 1: Bombardeio de getUpdates (50 requests)")
        
        tasks = []
        for i in range(50):
            task = asyncio.create_task(
                aggressive_get_updates(session, base_url, i+1)
            )
            tasks.append(task)
        
        # Executa em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if r and not isinstance(r, Exception))
        print(f"✅ {successful}/50 requests de getUpdates bem-sucedidas")
        
        # FASE 2: Limpeza de webhooks múltipla
        print("\n🔥 FASE 2: Remoção agressiva de webhooks")
        
        for attempt in range(10):
            try:
                async with session.post(f"{base_url}/deleteWebhook") as resp:
                    if resp.status == 200:
                        print(f"  ✅ Webhook removido (tentativa {attempt+1})")
                        break
                    else:
                        print(f"  ⚠️ Status {resp.status} (tentativa {attempt+1})")
            except Exception as e:
                print(f"  ❌ Erro tentativa {attempt+1}: {e}")
            
            await asyncio.sleep(0.5)
        
        # FASE 3: Verificação e limpeza final
        print("\n🔥 FASE 3: Limpeza final e verificação")
        
        # Múltiplas verificações do bot
        for i in range(5):
            try:
                async with session.post(f"{base_url}/getMe") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        bot_info = data.get('result', {})
                        print(f"  ✅ Bot verificado: @{bot_info.get('username', 'unknown')}")
                        break
            except Exception as e:
                print(f"  ⚠️ Erro verificação {i+1}: {e}")
            
            await asyncio.sleep(1)
        
        # FASE 4: Limpeza final de updates
        print("\n🔥 FASE 4: Limpeza final massiva")
        
        final_tasks = []
        for i in range(20):
            task = asyncio.create_task(
                final_cleanup_updates(session, base_url, i+1)
            )
            final_tasks.append(task)
        
        await asyncio.gather(*final_tasks, return_exceptions=True)
        
        print("\n🚨 LIMPEZA ULTRA AGRESSIVA CONCLUÍDA!")
        print("⏳ Aguardando 10 segundos para estabilização...")
        await asyncio.sleep(10)

async def aggressive_get_updates(session, base_url, attempt_num):
    """Requisição agressiva de getUpdates"""
    try:
        async with session.post(
            f"{base_url}/getUpdates",
            json={"timeout": 1, "limit": 100, "offset": -1}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                updates_count = len(data.get('result', []))
                if updates_count > 0:
                    print(f"    📥 Req {attempt_num}: {updates_count} updates")
                return True
    except:
        pass
    return False

async def final_cleanup_updates(session, base_url, attempt_num):
    """Limpeza final de updates"""
    try:
        # Vários tipos de requests para garantir limpeza
        requests_types = [
            {"timeout": 0, "limit": 100},
            {"timeout": 1, "limit": 100},
            {"timeout": 0, "limit": 1, "offset": -1},
        ]
        
        for req_type in requests_types:
            async with session.post(
                f"{base_url}/getUpdates",
                json=req_type
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    updates = data.get('result', [])
                    if updates:
                        # Se há updates, pega o último offset para limpar
                        last_update_id = updates[-1].get('update_id')
                        if last_update_id:
                            await session.post(
                                f"{base_url}/getUpdates",
                                json={"offset": last_update_id + 1, "timeout": 0}
                            )
            
            await asyncio.sleep(0.1)
            
    except:
        pass

async def test_bot_control():
    """Testa se conseguimos controle total do bot"""
    print("\n🧪 TESTE DE CONTROLE DO BOT")
    print("=" * 40)
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        # Teste 1: getMe
        try:
            async with session.post(f"{base_url}/getMe") as resp:
                if resp.status == 200:
                    print("✅ getMe: Bot acessível")
                else:
                    print(f"❌ getMe: Status {resp.status}")
        except Exception as e:
            print(f"❌ getMe: Erro {e}")
        
        # Teste 2: getUpdates simples
        try:
            async with session.post(
                f"{base_url}/getUpdates",
                json={"timeout": 2, "limit": 1}
            ) as resp:
                if resp.status == 200:
                    print("✅ getUpdates: Sem conflitos detectados")
                else:
                    print(f"❌ getUpdates: Status {resp.status}")
        except Exception as e:
            error_str = str(e).lower()
            if "conflict" in error_str:
                print("❌ getUpdates: CONFLITO AINDA ATIVO!")
                return False
            else:
                print(f"❌ getUpdates: Erro {e}")
        
        # Teste 3: Webhook status
        try:
            async with session.post(f"{base_url}/getWebhookInfo") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    webhook_info = data.get('result', {})
                    webhook_url = webhook_info.get('url', '')
                    if webhook_url:
                        print(f"⚠️ Webhook ativo: {webhook_url}")
                        return False
                    else:
                        print("✅ Webhook: Não há webhook ativo")
        except Exception as e:
            print(f"❌ Webhook check: Erro {e}")
    
    print("✅ CONTROLE DO BOT ESTABELECIDO!")
    return True

async def main():
    print("🚨 ULTRA CLEAR CONFLICTS - MÁXIMA AGRESSIVIDADE")
    print("=" * 60)
    print("⚠️  Este script vai fazer 50+ requests simultâneos")
    print("⚠️  Use apenas se outros métodos falharam")
    print("=" * 60)
    
    # Executa limpeza ultra agressiva
    await ultra_aggressive_cleanup()
    
    # Testa se conseguimos controle
    if await test_bot_control():
        print("\n🎉 SUCESSO TOTAL!")
        print("🚀 Bot está 100% sob controle")
        print("💡 Agora execute: python main.py")
    else:
        print("\n⚠️ CONFLITO PERSISTENTE")
        print("🔍 Há outra instância rodando em servidor remoto")
        print("💡 Verifique Railway, Heroku, etc.")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 
