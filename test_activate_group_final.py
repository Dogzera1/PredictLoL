#!/usr/bin/env python3
"""
🧪 TESTE ESPECÍFICO: Comando /activate_group CORRIGIDO
"""

import requests
import time
from datetime import datetime

token = "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0"

def test_activate_group():
    """Testa o comando /activate_group"""
    print("🧪 TESTE: Comando /activate_group")
    print("=" * 50)
    
    # 1. Verifica se bot responde
    print("1️⃣ Testando bot...")
    try:
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        if response.status_code == 200:
            bot_info = response.json()['result']
            print(f"✅ Bot: {bot_info['first_name']} (@{bot_info['username']})")
        else:
            print(f"❌ Bot não responde: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro bot: {e}")
        return False
    
    # 2. Verifica Railway
    print("\n2️⃣ Testando Railway...")
    try:
        response = requests.get('https://predictlol-production.up.railway.app/status', timeout=10)
        if response.status_code == 200:
            print("✅ Railway online")
        else:
            print(f"❌ Railway erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro Railway: {e}")
        return False
    
    # 3. Testa comando via webhook
    print("\n3️⃣ Testando /activate_group...")
    try:
        webhook_payload = {
            "update_id": int(time.time()),
            "message": {
                "message_id": int(time.time()),
                "from": {
                    "id": 8012415611,
                    "username": "testadmin",
                    "first_name": "Test Admin"
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
        
        response = requests.post(
            'https://predictlol-production.up.railway.app/webhook',
            json=webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print(f"📨 Comando enviado")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ /activate_group FUNCIONANDO!")
            return True
        else:
            print(f"❌ Erro webhook: {response.status_code}")
            print(f"📝 Resposta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Erro webhook: {e}")
        return False

if __name__ == "__main__":
    print(f"🔑 Token: {token[:25]}...")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("")
    
    success = test_activate_group()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 COMANDO /activate_group FUNCIONANDO!")
        print("✅ Correções aplicadas com sucesso")
        print("🚀 Bot operacional no Railway")
    else:
        print("❌ Problemas identificados")
        print("🔧 Investigação adicional necessária") 