"""
Script para diagnosticar problemas com o webhook do Vercel
"""

import requests
import sys
import os
import json
import argparse

# Configurar argumentos de linha de comando
parser = argparse.ArgumentParser(description="Diagnosticar problemas com webhook do Telegram")
parser.add_argument("webhook_url", nargs="?", help="URL do webhook para testar")
args = parser.parse_args()

# Obter o token do Telegram
try:
    from config import BOT_TOKEN
    token = BOT_TOKEN
except:
    token = None

# Tentar pegar token da variável de ambiente
env_token = os.environ.get("TELEGRAM_TOKEN")
if env_token:
    token = env_token

if not token or token == "SEU_TOKEN_AQUI":
    print("❌ ERRO: Token não encontrado!")
    sys.exit(1)

# URL do webhook no Vercel
if args.webhook_url:
    webhook_url = args.webhook_url
else:
    # URL padrão para fallback
    webhook_url = "https://lol-gpt-apostas-3xkfaf23h-victors-projects-42e6b0fe.vercel.app/api/webhook"

print(f"🔍 Verificando o webhook: {webhook_url}")

# Teste 1: Verificar se o webhook responde a uma requisição GET
try:
    print("\n📝 Teste 1: Verificação GET...")
    response = requests.get(webhook_url)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")
except Exception as e:
    print(f"❌ Erro: {str(e)}")

# Teste 2: Tentar enviar uma mensagem simulada para o webhook
print("\n📝 Teste 2: Envio POST simulado...")
try:
    # Criar um payload simulado de uma mensagem do Telegram
    payload = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Teste",
                "username": "teste_user"
            },
            "chat": {
                "id": 12345,
                "first_name": "Teste",
                "username": "teste_user",
                "type": "private"
            },
            "date": 1621000000,
            "text": "/start"
        }
    }
    
    # Enviar a requisição POST para o webhook
    headers = {
        "Content-Type": "application/json",
        "X-Telegram-Bot-Api-Secret-Token": "lol_gpt_secret_token"
    }
    response = requests.post(webhook_url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")
except Exception as e:
    print(f"❌ Erro: {str(e)}")

# Teste 3: Verificar o status do webhook no Telegram
print("\n📝 Teste 3: Verificação do status do webhook no Telegram...")
try:
    api_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    response = requests.get(api_url)
    data = response.json()
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"❌ Erro: {str(e)}")

# Teste 4: Tentar enviar uma mensagem real usando a API do Telegram
print("\n📝 Teste 4: Envio de mensagem via API...")
try:
    message_url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        "chat_id": 12345,  # Substitua pelo seu ID de chat real
        "text": "🔍 Teste de diagnóstico do webhook"
    }
    response = requests.post(message_url, json=params)
    data = response.json()
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"❌ Erro: {str(e)}")

print("\n✅ Diagnóstico concluído!") 