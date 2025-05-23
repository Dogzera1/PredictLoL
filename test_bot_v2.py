#!/usr/bin/env python3
"""
Script para testar o Bot LoL V2 com arquitetura robusta
"""

import requests
import json
import time

# Configurações
BOT_TOKEN = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
WEBHOOK_URL = "https://spectacular-wonder-production-4fb2.up.railway.app/webhook"
HEALTH_URL = "https://spectacular-wonder-production-4fb2.up.railway.app/health"
ROOT_URL = "https://spectacular-wonder-production-4fb2.up.railway.app/"

def test_v2_deployment():
    """Testa se a versão V2 foi deployada"""
    print("🔍 TESTANDO VERSÃO V2 ROBUSTA")
    print("=" * 40)
    
    try:
        # Testar health endpoint
        print("🏥 Testando Health Endpoint...")
        response = requests.get(HEALTH_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status Code: {response.status_code}")
            print(f"📊 Response: {json.dumps(data, indent=2)}")
            
            # Verificar se é V2
            if "version" in data and "2.0" in str(data["version"]):
                print("🎯 VERSÃO V2 DETECTADA!")
                return True, data
            else:
                print("⚠️ Ainda é a versão antiga")
                return False, data
        else:
            print(f"❌ Status Code: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False, None

def test_root_endpoint():
    """Testa endpoint raiz"""
    print("\n🌐 Testando Root Endpoint...")
    
    try:
        response = requests.get(ROOT_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root Response: {json.dumps(data, indent=2)}")
            
            # Verificar se contém mensagem V2
            if "V2" in str(data.get("message", "")):
                print("🎯 ROOT ENDPOINT V2 CONFIRMADO!")
                return True
        else:
            print(f"❌ Root Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro no root: {e}")
        
    return False

def send_test_message():
    """Envia mensagem de teste para o bot"""
    print("\n📤 Testando Envio de Mensagem...")
    
    try:
        # Simular um update do Telegram
        test_update = {
            "update_id": 999999,
            "message": {
                "message_id": 999,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Tester",
                    "username": "tester"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Tester",
                    "username": "tester",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/status"
            }
        }
        
        response = requests.post(
            WEBHOOK_URL, 
            json=test_update,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Webhook Response: {response.status_code}")
            print(f"📝 Content: {response.text}")
            return True
        else:
            print(f"❌ Webhook Error: {response.status_code}")
            print(f"📝 Content: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return False

def monitor_deployment():
    """Monitora o deployment da V2"""
    print("⏳ MONITORANDO DEPLOYMENT DA V2...")
    print("=" * 50)
    
    max_attempts = 10
    interval = 30  # segundos
    
    for attempt in range(max_attempts):
        print(f"\n🔄 Tentativa {attempt + 1}/{max_attempts}")
        
        is_v2, health_data = test_v2_deployment()
        
        if is_v2:
            print("🎉 VERSÃO V2 DEPLOYADA COM SUCESSO!")
            
            # Testes adicionais
            test_root_endpoint()
            send_test_message()
            
            print("\n✅ TESTES CONCLUÍDOS - V2 FUNCIONANDO!")
            return True
        
        if attempt < max_attempts - 1:
            print(f"⏳ Aguardando {interval}s para próxima tentativa...")
            time.sleep(interval)
    
    print("\n❌ V2 não foi deployada no tempo esperado")
    return False

def main():
    """Função principal"""
    print("🤖 TESTADOR DO BOT LOL V2")
    print("=" * 30)
    print("🎯 Verifica se a versão robusta foi deployada")
    print("🔧 Testa arquitetura sem problemas de event loop")
    print()
    
    # Verificar estado atual
    is_v2, current_data = test_v2_deployment()
    
    if is_v2:
        print("🎉 V2 JÁ ESTÁ ATIVA!")
        test_root_endpoint()
        send_test_message()
    else:
        print("⏳ V2 ainda não deployada, iniciando monitoramento...")
        monitor_deployment()

if __name__ == "__main__":
    main() 