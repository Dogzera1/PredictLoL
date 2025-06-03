#!/usr/bin/env python3
"""
Script para configurar webhook no Railway
"""
import asyncio
import aiohttp
import os

# Token correto
TOKEN = "7584060058:AAHiZkgr-TFlbt8Ym1GNFMdvjfVa6oED9l8"

async def configure_railway_webhook():
    """
    Configura webhook para Railway
    """
    print("🌐 CONFIGURANDO WEBHOOK PARA RAILWAY")
    print("=" * 60)
    
    # URL do Railway (você precisa fornecer a URL real do seu deploy)
    railway_url = input("🔗 Digite a URL do seu Railway (ex: https://seu-app.up.railway.app): ").strip()
    
    if not railway_url:
        print("❌ URL não fornecida!")
        return False
    
    if not railway_url.startswith("http"):
        railway_url = f"https://{railway_url}"
    
    webhook_url = f"{railway_url}/webhook"
    
    print(f"🎯 Webhook URL: {webhook_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            base_url = f"https://api.telegram.org/bot{TOKEN}"
            
            # 1. Remove webhook atual (se houver)
            print("🧹 Removendo webhook anterior...")
            async with session.post(f"{base_url}/deleteWebhook") as resp:
                if resp.status == 200:
                    print("✅ Webhook anterior removido")
                else:
                    print(f"⚠️ Aviso: {resp.status}")
            
            # 2. Configura novo webhook
            print("🔧 Configurando novo webhook...")
            webhook_data = {
                "url": webhook_url,
                "drop_pending_updates": True,
                "allowed_updates": ["message", "callback_query"]
            }
            
            async with session.post(f"{base_url}/setWebhook", json=webhook_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('ok'):
                        print("✅ WEBHOOK CONFIGURADO COM SUCESSO!")
                        print(f"   URL: {webhook_url}")
                        
                        # 3. Verifica configuração
                        print("\n🔍 Verificando configuração...")
                        async with session.get(f"{base_url}/getWebhookInfo") as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                webhook_info = data.get('result', {})
                                
                                print(f"📊 STATUS:")
                                print(f"   URL: {webhook_info.get('url', 'N/A')}")
                                print(f"   Pending Updates: {webhook_info.get('pending_update_count', 0)}")
                                print(f"   Last Error: {webhook_info.get('last_error_message', 'Nenhum')}")
                                
                                if webhook_info.get('url') == webhook_url:
                                    print("\n🎉 CONFIGURAÇÃO CONFIRMADA!")
                                    return True
                                else:
                                    print("\n❌ Configuração não confirmada")
                                    return False
                    else:
                        print(f"❌ Erro na API: {data}")
                        return False
                else:
                    print(f"❌ Erro HTTP: {resp.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

async def test_webhook_connectivity():
    """
    Testa se o webhook está acessível
    """
    print("\n🔬 TESTANDO CONECTIVIDADE DO WEBHOOK")
    print("=" * 60)
    
    railway_url = input("🔗 URL do Railway novamente: ").strip()
    if not railway_url.startswith("http"):
        railway_url = f"https://{railway_url}"
    
    webhook_url = f"{railway_url}/webhook"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📡 Testando: {webhook_url}")
            
            # Testa se o endpoint responde
            async with session.get(railway_url) as resp:
                if resp.status == 200:
                    print("✅ Railway app está respondendo")
                else:
                    print(f"⚠️ Railway app: status {resp.status}")
            
            # Testa webhook específico (pode dar 404, mas deve conectar)
            try:
                async with session.post(webhook_url, 
                                      json={"test": "connectivity"}, 
                                      timeout=10) as resp:
                    print(f"📊 Webhook endpoint: status {resp.status}")
                    if resp.status in [200, 404, 405]:  # 404/405 são OK para teste
                        print("✅ Webhook endpoint é acessível")
                    else:
                        print(f"⚠️ Status inesperado: {resp.status}")
            except asyncio.TimeoutError:
                print("❌ Timeout - webhook pode estar inacessível")
            except Exception as e:
                print(f"⚠️ Erro no teste: {e}")
                
    except Exception as e:
        print(f"❌ Erro geral: {e}")

async def main():
    print("🚀 CONFIGURADOR DE WEBHOOK RAILWAY")
    print("=" * 60)
    print("Este script configura o webhook do Telegram para o Railway")
    print("Isso elimina conflitos com polling local")
    print("=" * 60)
    
    # 1. Configura webhook
    success = await configure_railway_webhook()
    
    if success:
        # 2. Testa conectividade
        test = input("\n🧪 Quer testar conectividade? (y/n): ").lower()
        if test == 'y':
            await test_webhook_connectivity()
        
        print("\n" + "=" * 60)
        print("✅ WEBHOOK CONFIGURADO!")
        print("🎯 Próximos passos:")
        print("  1. Faça deploy do código no Railway")
        print("  2. O bot funcionará via webhook (sem conflitos)")
        print("  3. Localmente rode apenas: python main.py")
        print("     (Será apenas sistema de tips, sem Telegram)")
        print("=" * 60)
    else:
        print("\n❌ Falha na configuração do webhook")
        print("💡 Verifique se a URL do Railway está correta")

if __name__ == "__main__":
    asyncio.run(main()) 