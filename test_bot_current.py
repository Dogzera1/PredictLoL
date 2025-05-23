#!/usr/bin/env python3
"""
Script para testar o bot atual no Railway e verificar se o erro persiste
"""

import requests
import json
import time

# Configurações
BOT_TOKEN = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
WEBHOOK_URL = "https://spectacular-wonder-production-4fb2.up.railway.app/webhook"
HEALTH_URL = "https://spectacular-wonder-production-4fb2.up.railway.app/health"

def test_bot_health():
    """Testa a saúde do bot"""
    print("🏥 TESTANDO SAÚDE DO BOT")
    print("=" * 40)
    
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status', 'unknown')}")
            print(f"🤖 Bot: {data.get('bot', 'unknown')}")
            print(f"🔧 Inicializado: {data.get('initialized', False)}")
            print(f"🔑 Token: {data.get('token', 'unknown')}")
            
            # Verificar se tem campo 'loop' (versão nova)
            if 'loop' in data:
                print(f"🔄 Loop: {data.get('loop', 'unknown')}")
                print("✅ VERSÃO ATUALIZADA DETECTADA!")
                return True
            else:
                print("❌ VERSÃO ANTIGA - FALTA CAMPO 'loop'")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def send_test_message():
    """Envia mensagem de teste via API do Telegram"""
    print("\n📨 ENVIANDO MENSAGEM DE TESTE")
    print("=" * 40)
    
    # Usar meu chat_id (precisa ser descoberto, vou usar um método geral)
    test_payload = {
        "update_id": 999999,
        "message": {
            "message_id": 1001,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": int(time.time()),
            "text": "/start"
        }
    }
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Webhook respondeu OK")
            print(f"📄 Response: {response.text}")
            return True
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def check_telegram_updates():
    """Verifica updates pendentes no Telegram"""
    print("\n📬 VERIFICANDO UPDATES PENDENTES")
    print("=" * 40)
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                updates = data['result']
                print(f"📊 Total de updates: {len(updates)}")
                
                if updates:
                    last_update = updates[-1]
                    print(f"🔢 Último update_id: {last_update.get('update_id')}")
                    print(f"📅 Última mensagem: {last_update.get('message', {}).get('text', 'N/A')}")
                else:
                    print("✅ Nenhum update pendente")
                    
                return True
            else:
                print(f"❌ Erro da API: {data}")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Função principal"""
    print("🔍 TESTE COMPLETO DO BOT RAILWAY")
    print("=" * 50)
    print(f"🤖 Bot: @BETLOLGPT_bot")
    print(f"🌐 URL: {WEBHOOK_URL}")
    print()
    
    # Teste 1: Saúde do bot
    health_ok = test_bot_health()
    
    # Teste 2: Updates pendentes
    updates_ok = check_telegram_updates()
    
    # Teste 3: Webhook (apenas se saúde estiver OK)
    if health_ok:
        webhook_ok = send_test_message()
    else:
        webhook_ok = False
        print("\n⚠️ Pulando teste de webhook - bot não saudável")
    
    # Resultado final
    print("\n" + "=" * 50)
    print("📋 RESULTADO DOS TESTES:")
    print(f"   🏥 Saúde: {'✅' if health_ok else '❌'}")
    print(f"   📬 Updates: {'✅' if updates_ok else '❌'}")
    print(f"   📨 Webhook: {'✅' if webhook_ok else '❌'}")
    
    if health_ok and not('loop' in requests.get(HEALTH_URL).json()):
        print("\n🚨 CONCLUSÃO: BOT ESTÁ FUNCIONANDO MAS COM VERSÃO ANTIGA")
        print("💡 NECESSÁRIO FORÇAR REDEPLOY NO RAILWAY")
    elif health_ok:
        print("\n✅ CONCLUSÃO: BOT ATUALIZADO E FUNCIONANDO")
    else:
        print("\n❌ CONCLUSÃO: BOT COM PROBLEMAS")

if __name__ == "__main__":
    main() 