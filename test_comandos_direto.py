#!/usr/bin/env python3
"""
Teste direto dos comandos do bot via API Telegram
"""
import asyncio
import aiohttp
import json
import time

BOT_TOKEN = "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0"
USER_ID = 8012415611  # Seu ID de usuário

async def test_bot_commands():
    """Testa comandos do bot via API"""
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        
        print("🧪 Testando comandos do bot...")
        print("=" * 50)
        
        # 1. Verifica se bot está rodando
        async with session.get(f"{base_url}/getMe") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Bot ativo: @{data['result']['username']}")
            else:
                print(f"❌ Bot não encontrado: {resp.status}")
                return
        
        # 2. Testa comando /start
        print("\n📤 Enviando comando /start...")
        message_data = {
            "chat_id": USER_ID,
            "text": "/start"
        }
        
        async with session.post(f"{base_url}/sendMessage", data=message_data) as resp:
            result = await resp.json()
            if result.get("ok"):
                print("✅ Comando /start enviado com sucesso")
            else:
                print(f"❌ Erro ao enviar /start: {result}")
        
        # Aguarda resposta
        await asyncio.sleep(3)
        
        # 3. Busca atualizações (respostas do bot)
        print("\n📥 Buscando respostas do bot...")
        async with session.get(f"{base_url}/getUpdates?offset=-1") as resp:
            if resp.status == 200:
                data = await resp.json()
                updates = data.get("result", [])
                
                if updates:
                    last_update = updates[-1]
                    message = last_update.get("message", {})
                    
                    if message.get("from", {}).get("is_bot"):
                        print("✅ Bot respondeu:")
                        print(f"📝 Mensagem: {message.get('text', 'Sem texto')[:100]}...")
                        
                        # Verifica se tem botões
                        reply_markup = message.get("reply_markup", {})
                        if reply_markup.get("inline_keyboard"):
                            print(f"🎛️ Botões: {len(reply_markup['inline_keyboard'])} linhas")
                    else:
                        print("⚠️ Não há resposta recente do bot")
                else:
                    print("⚠️ Nenhuma atualização encontrada")
            else:
                print(f"❌ Erro ao buscar atualizações: {resp.status}")
        
        # 4. Testa outros comandos principais
        comandos_teste = ["/help", "/status", "/ping"]
        
        for comando in comandos_teste:
            print(f"\n📤 Testando {comando}...")
            
            message_data = {
                "chat_id": USER_ID,
                "text": comando
            }
            
            async with session.post(f"{base_url}/sendMessage", data=message_data) as resp:
                result = await resp.json()
                if result.get("ok"):
                    print(f"✅ {comando} enviado")
                else:
                    print(f"❌ Erro {comando}: {result.get('description', 'Desconhecido')}")
            
            await asyncio.sleep(2)  # Evita rate limit
        
        print("\n" + "=" * 50)
        print("🎯 Teste de comandos concluído!")
        print("💡 Verifique seu Telegram para ver as respostas")

if __name__ == "__main__":
    asyncio.run(test_bot_commands()) 
