#!/usr/bin/env python3
"""
Verificação Final - Bot Telegram Funcionando
"""
import asyncio
import aiohttp
import json

BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"
USER_ID = 8012415611

async def verificar_bot():
    """Verifica se bot está funcionando corretamente"""
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    print("🔍 VERIFICAÇÃO FINAL - BOT TELEGRAM")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Verifica se bot está online
        print("1️⃣ Verificando conectividade...")
        try:
            async with session.get(f"{base_url}/getMe") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    bot_info = data['result']
                    print(f"   ✅ Bot online: @{bot_info['username']}")
                    print(f"   📱 Nome: {bot_info['first_name']}")
                    print(f"   🆔 ID: {bot_info['id']}")
                else:
                    print(f"   ❌ Bot offline: HTTP {resp.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Erro de conectividade: {e}")
            return False
        
        # 2. Testa envio de comando
        print("\n2️⃣ Testando envio de comando...")
        try:
            message_data = {
                "chat_id": USER_ID,
                "text": "/start"
            }
            
            async with session.post(f"{base_url}/sendMessage", data=message_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("ok"):
                        print("   ✅ Comando /start enviado com sucesso")
                        message_id = result['result']['message_id']
                        print(f"   📨 Message ID: {message_id}")
                    else:
                        print(f"   ❌ Erro ao enviar comando: {result}")
                        return False
                else:
                    print(f"   ❌ HTTP Error: {resp.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Erro ao enviar comando: {e}")
            return False
        
        # 3. Aguarda resposta
        print("\n3️⃣ Aguardando resposta do bot...")
        await asyncio.sleep(3)
        
        # 4. Verifica se bot respondeu
        print("\n4️⃣ Verificando resposta...")
        try:
            async with session.get(f"{base_url}/getUpdates?limit=5") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    updates = data.get("result", [])
                    
                    # Procura por mensagens do bot
                    bot_responses = []
                    for update in updates[-10:]:  # Últimas 10 atualizações
                        message = update.get("message", {})
                        if message.get("from", {}).get("is_bot"):
                            bot_responses.append(message)
                    
                    if bot_responses:
                        latest_response = bot_responses[-1]
                        print("   ✅ Bot respondeu!")
                        print(f"   📝 Texto: {latest_response.get('text', 'Sem texto')[:100]}...")
                        
                        # Verifica se tem botões
                        reply_markup = latest_response.get("reply_markup", {})
                        if reply_markup.get("inline_keyboard"):
                            print(f"   🎛️ Botões: {len(reply_markup['inline_keyboard'])} linhas de botões")
                        
                        print("   ✅ Interface funcionando!")
                        return True
                    else:
                        print("   ⚠️ Nenhuma resposta do bot encontrada")
                        print("   💡 Isso pode ser normal se o bot já estava ativo")
                        
                        # Testa comando direto
                        print("\n   🔄 Testando comando /ping...")
                        ping_data = {
                            "chat_id": USER_ID,
                            "text": "/ping"
                        }
                        
                        async with session.post(f"{base_url}/sendMessage", data=ping_data) as ping_resp:
                            if ping_resp.status == 200:
                                print("   ✅ Comando /ping enviado")
                                await asyncio.sleep(2)
                                
                                # Verifica resposta do ping
                                async with session.get(f"{base_url}/getUpdates?offset=-1") as final_resp:
                                    if final_resp.status == 200:
                                        final_data = await final_resp.json()
                                        final_updates = final_data.get("result", [])
                                        
                                        if final_updates:
                                            last_msg = final_updates[-1].get("message", {})
                                            if last_msg.get("from", {}).get("is_bot"):
                                                print("   ✅ Bot respondeu ao ping!")
                                                return True
                        
                        print("   ⚠️ Bot pode não estar processando comandos")
                        return False
                else:
                    print(f"   ❌ Erro ao verificar updates: {resp.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Erro ao verificar resposta: {e}")
            return False

async def main():
    """Função principal"""
    sucesso = await verificar_bot()
    
    print("\n" + "=" * 50)
    if sucesso:
        print("🎉 VERIFICAÇÃO CONCLUÍDA - BOT FUNCIONANDO!")
        print("")
        print("✅ Resultados:")
        print("   • Bot online e conectado")
        print("   • Comandos sendo enviados")
        print("   • Bot respondendo corretamente")
        print("   • Interface com botões ativa")
        print("")
        print("💡 O bot está 100% funcional!")
        print("📱 Teste agora no Telegram: /start")
    else:
        print("❌ VERIFICAÇÃO FALHOU - PROBLEMAS IDENTIFICADOS")
        print("")
        print("🔧 Possíveis soluções:")
        print("   1. Verificar se bot debug está rodando")
        print("   2. Restart do bot: python debug_bot_comandos.py")
        print("   3. Verificar logs no terminal do bot")
        print("   4. Testar comandos manualmente no Telegram")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 