#!/usr/bin/env python3
"""
Teste do novo token do Telegram
"""
import asyncio
import aiohttp
import sys

async def testar_token():
    """Testa se o token está funcionando"""
    TOKEN = "7584060058:AAHiZkgr-TFlbt8Ym1GNFMdvjfVa6oED9l8"
    
    print("🔍 TESTANDO NOVO TOKEN DO TELEGRAM...")
    print("=" * 50)
    print(f"Token: {TOKEN[:20]}...")
    
    try:
        # Teste 1: Verificar se o token é válido
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
                if data.get('ok'):
                    bot_info = data['result']
                    print(f"\n✅ TOKEN VÁLIDO!")
                    print(f"🤖 Bot: @{bot_info['username']}")
                    print(f"📛 Nome: {bot_info['first_name']}")
                    print(f"🆔 ID: {bot_info['id']}")
                    
                    # Teste 2: Tentar limpar webhook
                    webhook_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
                    async with session.post(webhook_url) as webhook_resp:
                        webhook_data = await webhook_resp.json()
                        if webhook_data.get('ok'):
                            print("✅ Webhook limpo com sucesso")
                        else:
                            print("⚠️ Problema ao limpar webhook")
                    
                    print("\n🚀 TOKEN PRONTO PARA USO!")
                    return True
                    
                else:
                    print(f"\n❌ TOKEN INVÁLIDO!")
                    print(f"Erro: {data.get('description', 'Desconhecido')}")
                    return False
                    
    except Exception as e:
        print(f"\n❌ ERRO na conexão: {e}")
        return False

if __name__ == "__main__":
    resultado = asyncio.run(testar_token())
    if resultado:
        print("\n✅ Pode usar o bot com confiança!")
    else:
        print("\n❌ Token não está funcionando!")
    sys.exit(0 if resultado else 1) 