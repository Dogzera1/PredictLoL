#!/usr/bin/env python3
"""
Script para testar /activate_group com token correto
Substitua TOKEN_AQUI pelo token válido
"""

import requests
import time

def test_activate_group():
    # SUBSTITUA PELO TOKEN CORRETO
    bot_token = "TOKEN_AQUI"
    
    # 1. Primeiro, configura webhook
    webhook_url = "https://predictlol-production.up.railway.app/webhook"
    set_webhook_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    print("🔧 Configurando webhook...")
    response = requests.post(set_webhook_url, json={"url": webhook_url})
    print(f"Webhook: {response.status_code} - {response.json()}")
    
    # 2. Simula comando em grupo
    webhook_payload = {
        "update_id": 123456,
        "message": {
            "message_id": 789,
            "from": {
                "id": 8012415611,
                "username": "admin",
                "first_name": "Admin"
            },
            "chat": {
                "id": -1001234567890,
                "type": "supergroup",
                "title": "Grupo Teste"
            },
            "date": int(time.time()),
            "text": "/activate_group"
        }
    }
    
    print("📨 Enviando comando /activate_group...")
    response = requests.post(webhook_url, json=webhook_payload)
    print(f"Comando: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_activate_group()
