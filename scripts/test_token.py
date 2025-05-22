"""
Script para testar se o token do Telegram está funcionando corretamente
"""

import os
import sys
import requests
import json
import traceback

# Adicione esta linha no início do script test_polling.py
sys.modules['imghdr'] = type('', (), {})

print("🔄 Iniciando teste de token do Telegram...")

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f"📂 Diretório raiz adicionado ao path: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")

# Tentar importar token do config.py
print("🔍 Tentando importar token do config.py...")
try:
    from config import BOT_TOKEN
    token = BOT_TOKEN
    print(f"📝 Token encontrado no config.py: {BOT_TOKEN[:5]}...")
except Exception as e:
    token = None
    print(f"⚠️ Erro ao importar token do config.py: {str(e)}")
    print(traceback.format_exc())

# Tentar pegar token da variável de ambiente
print("🔍 Tentando obter token da variável de ambiente...")
env_token = os.environ.get("TELEGRAM_TOKEN")
if env_token:
    token = env_token
    print(f"📝 Token encontrado na variável de ambiente: {env_token[:5]}...")
else:
    print("⚠️ Token não encontrado na variável de ambiente")

if not token or token == "SEU_TOKEN_AQUI":
    print("❌ ERRO: Token não encontrado ou inválido!")
    print("Configure o token no arquivo config.py ou defina a variável de ambiente TELEGRAM_TOKEN")
    sys.exit(1)

print(f"🔑 Testando token: {token[:5]}...")

# Testar o token fazendo uma requisição simples
try:
    print(f"🌐 Fazendo requisição para getMe...")
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)
    data = response.json()
    
    print("\n📊 Resposta completa:")
    print(json.dumps(data, indent=2))
    
    if data.get("ok"):
        bot_info = data.get("result", {})
        print("\n✅ Token válido!")
        print(f"Nome do bot: {bot_info.get('first_name')}")
        print(f"Username: @{bot_info.get('username')}")
        print(f"ID: {bot_info.get('id')}")
        
        # Testar envio de mensagem para o bot
        print("\n📨 Tentando obter as atualizações recentes...")
        updates_url = f"https://api.telegram.org/bot{token}/getUpdates?limit=5"
        updates_response = requests.get(updates_url)
        updates_data = updates_response.json()
        
        if updates_data.get("ok"):
            updates = updates_data.get("result", [])
            if updates:
                print(f"Recebidas {len(updates)} atualizações recentes:")
                for update in updates:
                    update_id = update.get("update_id")
                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    text = message.get("text", "")
                    
                    print(f"- Update ID: {update_id}, Chat ID: {chat_id}, Mensagem: {text[:30]}")
                    
                    # Tentar responder à mensagem mais recente
                    if chat_id:
                        send_url = f"https://api.telegram.org/bot{token}/sendMessage"
                        send_params = {
                            "chat_id": chat_id,
                            "text": "✅ Teste do token realizado com sucesso! O bot está funcionando corretamente."
                        }
                        send_response = requests.post(send_url, json=send_params)
                        send_data = send_response.json()
                        
                        if send_data.get("ok"):
                            print(f"✅ Mensagem enviada com sucesso para o chat {chat_id}")
                        else:
                            print(f"❌ Erro ao enviar mensagem: {send_data.get('description')}")
                        
                        break  # Responder apenas ao chat mais recente
            else:
                print("❌ Nenhuma atualização recente encontrada. Envie uma mensagem para o bot e tente novamente.")
        else:
            print(f"❌ Erro ao obter atualizações: {updates_data.get('description')}")
    else:
        print("\n❌ Token inválido!")
        print(f"Erro: {data.get('description')}")
except Exception as e:
    print(f"\n❌ Erro ao testar o token: {str(e)}")
    print(traceback.format_exc()) 