#!/usr/bin/env python3
import requests
import json

# URL do webhook
webhook_url = "https://spectacular-wonder-production-4fb2.up.railway.app/webhook"

# Simular um update do Telegram com comando /start
test_update = {
    "update_id": 999999,
    "message": {
        "message_id": 1,
        "from": {
            "id": 123456789,
            "is_bot": False,
            "first_name": "TestUser",
            "username": "testuser"
        },
        "chat": {
            "id": 123456789,
            "type": "private"
        },
        "date": 1621234567,
        "text": "/start",
        "entities": [
            {
                "type": "bot_command",
                "offset": 0,
                "length": 6
            }
        ]
    }
}

print(f"🔷 Testando webhook: {webhook_url}")
print(f"🔷 Enviando update simulado: {json.dumps(test_update, indent=2)}")

try:
    response = requests.post(
        webhook_url,
        json=test_update,
        headers={
            "Content-Type": "application/json"
        },
        timeout=10
    )
    
    print(f"🔷 Status Code: {response.status_code}")
    print(f"🔷 Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Webhook respondeu com sucesso!")
    else:
        print("❌ Webhook retornou erro!")
        
except Exception as e:
    print(f"❌ Erro ao testar webhook: {e}") 