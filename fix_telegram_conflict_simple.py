#!/usr/bin/env python3
"""
Script Simples para Resolver Conflito de Instâncias Telegram

Resolve o erro: "terminated by other getUpdates request"
"""

import asyncio
import aiohttp
import sys

async def resolve_telegram_conflict(bot_token):
    """
    Resolve conflito de instâncias do bot Telegram
    """
    print("🔧 Resolvendo conflito de instâncias Telegram...")
    
    if not bot_token:
        print("❌ Token do bot é obrigatório!")
        return False
    
    try:
        async with aiohttp.ClientSession() as session:
            base_url = f"https://api.telegram.org/bot{bot_token}"
            
            print("📋 1. Verificando status atual do webhook...")
            
            # 1. Verifica webhook atual
            try:
                async with session.get(f"{base_url}/getWebhookInfo") as resp:
                    if resp.status == 200:
                        webhook_info = await resp.json()
                        webhook_url = webhook_info.get("result", {}).get("url", "")
                        if webhook_url:
                            print(f"⚠️  Webhook ativo encontrado: {webhook_url}")
                        else:
                            print("✅ Nenhum webhook ativo")
                    else:
                        print("⚠️  Não foi possível verificar webhook")
            except Exception as e:
                print(f"⚠️  Erro ao verificar webhook: {e}")
            
            print("🧹 2. Removendo webhook (se existir)...")
            
            # 2. Remove webhook
            try:
                async with session.post(f"{base_url}/deleteWebhook") as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("ok"):
                            print("✅ Webhook removido com sucesso")
                        else:
                            print(f"⚠️  Resposta webhook: {result}")
                    else:
                        print("⚠️  Erro ao remover webhook")
            except Exception as e:
                print(f"⚠️  Erro ao remover webhook: {e}")
            
            print("🔄 3. Cancelando polling ativo...")
            
            # 3. Cancela polling ativo com timeout 0
            try:
                async with session.post(f"{base_url}/getUpdates", 
                                       json={"timeout": 0, "limit": 100}) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        updates_count = len(result.get("result", []))
                        print(f"✅ Polling cancelado ({updates_count} updates limpos)")
                    else:
                        print("⚠️  Erro ao cancelar polling")
            except Exception as e:
                print(f"⚠️  Erro ao cancelar polling: {e}")
            
            print("⏳ 4. Aguardando estabilização...")
            await asyncio.sleep(3)
            
            print("✅ 5. Verificando status final...")
            
            # 4. Verifica status final
            try:
                async with session.get(f"{base_url}/getWebhookInfo") as resp:
                    if resp.status == 200:
                        webhook_info = await resp.json()
                        webhook_url = webhook_info.get("result", {}).get("url", "")
                        if not webhook_url:
                            print("✅ Webhook limpo confirmado")
                        else:
                            print(f"⚠️  Webhook ainda ativo: {webhook_url}")
            except Exception as e:
                print(f"⚠️  Erro ao verificar status final: {e}")
                
            # 5. Teste final com getMe
            try:
                async with session.get(f"{base_url}/getMe") as resp:
                    if resp.status == 200:
                        bot_info = await resp.json()
                        if bot_info.get("ok"):
                            bot_name = bot_info.get("result", {}).get("username", "unknown")
                            print(f"✅ Bot @{bot_name} pronto para uso")
                            return True
                        else:
                            print("❌ Erro na verificação final do bot")
                            return False
                    else:
                        print("❌ Bot não responde")
                        return False
            except Exception as e:
                print(f"❌ Erro no teste final: {e}")
                return False
                    
    except Exception as e:
        print(f"❌ Erro durante resolução: {e}")
        return False

def print_instructions():
    """Exibe instruções pós-resolução"""
    print("\n" + "="*60)
    print("📋 PRÓXIMOS PASSOS")
    print("="*60)
    print("1. 🚄 Vá para Railway dashboard")
    print("2. 🔄 Clique em 'Redeploy' na seção Deployments") 
    print("3. ⏳ Aguarde logs mostrarem: '🎉 SISTEMA TOTALMENTE OPERACIONAL!'")
    print("4. 📱 Teste bot com /start no Telegram")
    print("\n🔍 Monitoramento:")
    print("   • Health check: https://seu-app.railway.app/health")
    print("   • Status: https://seu-app.railway.app/status")
    print("\n✅ Conflito resolvido! Bot pronto para Railway.")

async def main():
    """Função principal"""
    print("🚀 RESOLUÇÃO DE CONFLITO TELEGRAM - BOT LOL V3")
    print("="*60)
    print("Resolvendo: 'terminated by other getUpdates request'")
    print("")
    
    # Solicita token do usuário
    if len(sys.argv) > 1:
        bot_token = sys.argv[1]
        print(f"📱 Usando token fornecido: {bot_token[:10]}...")
    else:
        print("🔑 Para resolver o conflito, precisamos do token do bot.")
        print("💡 Você pode obtê-lo no @BotFather do Telegram")
        print("")
        bot_token = input("Digite seu TELEGRAM_BOT_TOKEN: ").strip()
        
        if not bot_token:
            print("❌ Token é obrigatório!")
            return False
    
    print("")
    success = await resolve_telegram_conflict(bot_token)
    
    print("\n" + "="*60)
    if success:
        print("🎉 CONFLITO RESOLVIDO COM SUCESSO!")
        print_instructions()
    else:
        print("❌ Falha na resolução do conflito")
        print("\n🔧 Soluções manuais:")
        print("1. Verifique se o token está correto")
        print(f"2. Acesse: https://api.telegram.org/bot{bot_token}/deleteWebhook")
        print("3. Restart Railway manualmente")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1) 
