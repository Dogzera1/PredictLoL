#!/usr/bin/env python3
"""
Script para parar instância do Railway que está causando conflito
"""
import asyncio
import aiohttp
import os
import time

# Token correto
TOKEN = "7584060058:AAHiZkgr-TFlbt8Ym1GNFMdvjfVa6oED9l8"

async def force_stop_conflicting_instances():
    """
    Força parar instâncias conflitantes usando webhook
    """
    print("🚨 DETECTADO: Conflito de instâncias (Railway + Local)")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            base_url = f"https://api.telegram.org/bot{TOKEN}"
            
            # 1. Verifica webhook atual
            print("🔍 Verificando webhook atual...")
            async with session.get(f"{base_url}/getWebhookInfo") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    webhook_info = data.get('result', {})
                    webhook_url = webhook_info.get('url', '')
                    
                    if webhook_url:
                        print(f"🌐 WEBHOOK ATIVO: {webhook_url}")
                        print("   ↳ Isso confirma que há instância no Railway!")
                        
                        # 2. Remove webhook para parar Railway
                        print("\n🛑 Removendo webhook do Railway...")
                        async with session.post(f"{base_url}/deleteWebhook", 
                                              json={"drop_pending_updates": True}) as resp:
                            if resp.status == 200:
                                print("✅ Webhook removido com sucesso!")
                                print("   ↳ Instância do Railway foi desconectada")
                            else:
                                print(f"❌ Erro ao remover webhook: {resp.status}")
                    else:
                        print("ℹ️ Nenhum webhook configurado")
            
            # 3. Força limpeza de updates pendentes
            print("\n🧹 Limpando updates pendentes...")
            async with session.post(f"{base_url}/getUpdates", 
                                  json={"offset": -1, "timeout": 1}) as resp:
                if resp.status == 200:
                    print("✅ Updates limpos")
                else:
                    print(f"⚠️ Aviso na limpeza: {resp.status}")
            
            # 4. Verifica se consegue conectar sem conflito
            print("\n🔬 Testando conexão sem conflito...")
            async with session.get(f"{base_url}/getMe") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('ok'):
                        bot_info = data['result']
                        print(f"🎉 SUCESSO! Bot: @{bot_info.get('username')}")
                        print("✅ Conflito resolvido - pode iniciar local")
                        return True
                else:
                    print(f"❌ Ainda há problemas: {resp.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

async def test_local_start():
    """
    Testa se pode iniciar localmente sem conflito
    """
    print("\n" + "=" * 60)
    print("🚀 TESTANDO INÍCIO LOCAL SEM CONFLITO")
    print("=" * 60)
    
    try:
        from telegram.ext import Application
        
        # Cria aplicação
        app = Application.builder().token(TOKEN).build()
        await app.initialize()
        
        # Testa polling por 5 segundos
        print("⏱️ Testando polling por 5 segundos...")
        
        # Inicia polling em background
        await app.start()
        
        polling_task = asyncio.create_task(
            app.updater.start_polling(drop_pending_updates=True)
        )
        
        # Aguarda 5 segundos
        await asyncio.sleep(5)
        
        # Para polling
        app.updater.stop()
        await app.stop()
        await app.shutdown()
        
        print("✅ TESTE PASSOU! Sem conflitos detectados")
        print("🔥 Pode iniciar o sistema principal com segurança")
        return True
        
    except Exception as e:
        if "conflict" in str(e).lower():
            print(f"❌ AINDA HÁ CONFLITO: {e}")
            print("💡 Pode ser necessário aguardar alguns minutos")
        else:
            print(f"❌ Outro erro: {e}")
        return False

async def main():
    print("🔧 RESOLVEDOR DE CONFLITOS RAILWAY/LOCAL")
    print("=" * 60)
    
    # 1. Para instâncias conflitantes
    success = await force_stop_conflicting_instances()
    
    if success:
        # 2. Aguarda um pouco para garantir
        print("\n⏳ Aguardando 10 segundos para garantir...")
        await asyncio.sleep(10)
        
        # 3. Testa se pode iniciar local
        local_ok = await test_local_start()
        
        if local_ok:
            print("\n" + "=" * 60)
            print("🎉 PROBLEMA RESOLVIDO!")
            print("✅ Pode iniciar o sistema principal agora")
            print("=" * 60)
            
            # Oferece iniciar automaticamente
            print("\n⚡ Quer iniciar o sistema principal agora? (5s)")
            print("   Pressione Ctrl+C para cancelar")
            
            try:
                await asyncio.sleep(5)
                print("\n🚀 INICIANDO SISTEMA PRINCIPAL...")
                
                # Inicia o main.py
                import subprocess
                subprocess.Popen(["python", "main.py"], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                
                print("✅ Sistema iniciado em nova janela!")
                
            except KeyboardInterrupt:
                print("\n⏹️ Cancelado - você pode iniciar manualmente")
        else:
            print("\n❌ Ainda há conflitos - verifique Railway dashboard")
    else:
        print("\n❌ Não foi possível resolver automaticamente")
        print("💡 Verifique o Railway dashboard manualmente")

if __name__ == "__main__":
    asyncio.run(main()) 