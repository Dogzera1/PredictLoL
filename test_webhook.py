#!/usr/bin/env python3
"""
Teste da rota /webhook simulando mensagem do Telegram
"""
import requests
import json

def test_webhook():
    """Testa a rota /webhook simulando mensagem do Telegram"""
    
    # Simula mensagem /start do Telegram
    webhook_data = {
        "message": {
            "message_id": 123,
            "from": {
                "id": 8012415611,
                "username": "test_user",
                "first_name": "Test"
            },
            "chat": {
                "id": 8012415611,
                "type": "private"
            },
            "date": 1640995200,
            "text": "/start"
        }
    }
    
    try:
        print("🧪 Testando webhook com comando /start...")
        
        # Testa localmente primeiro
        try:
            response = requests.post(
                "http://localhost:8080/webhook",
                json=webhook_data,
                timeout=10
            )
            
            print(f"LOCAL Status: {response.status_code}")
            print(f"LOCAL Response: {response.text}")
            
        except Exception as e:
            print(f"❌ LOCAL falhou: {e}")
        
        # Testa Railway
        try:
            response = requests.post(
                "https://predictlol-production.up.railway.app/webhook",
                json=webhook_data,
                timeout=10
            )
            
            print(f"RAILWAY Status: {response.status_code}")
            print(f"RAILWAY Response: {response.text}")
            
        except Exception as e:
            print(f"❌ RAILWAY falhou: {e}")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    test_webhook() 