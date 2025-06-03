#!/usr/bin/env python3
"""
🧪 TESTE FINAL: Comando /activate_group com token correto
"""

import requests
import time
import json

def test_activate_group_webhook():
    """Testa comando /activate_group via webhook"""
    print("🧪 TESTANDO /activate_group COM TOKEN CORRETO")
    print("=" * 60)
    
    # Simula comando /activate_group em um grupo
    webhook_payload = {
        "update_id": 123456,
        "message": {
            "message_id": 789,
            "from": {
                "id": 8012415611,  # Admin ID
                "username": "testadmin",
                "first_name": "Test Admin"
            },
            "chat": {
                "id": -1001234567890,  # ID de grupo (negativo)
                "type": "supergroup",
                "title": "Grupo de Teste LoL"
            },
            "date": int(time.time()),
            "text": "/activate_group"
        }
    }
    
    print(f"📤 Enviando comando /activate_group...")
    print(f"👤 De: Admin (ID: 8012415611)")
    print(f"👥 Para: Grupo Teste (ID: -1001234567890)")
    
    try:
        url = "https://predictlol-production.up.railway.app/webhook"
        response = requests.post(url, json=webhook_payload, timeout=15)
        
        print(f"\n📊 RESULTADO:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCESSO - Comando processado!")
            try:
                result = response.json()
                print(f"   📋 Resposta JSON: {json.dumps(result, indent=2)}")
            except:
                print(f"   📋 Resposta (texto): {response.text}")
        else:
            print(f"   ❌ ERRO - Status {response.status_code}")
            print(f"   📋 Erro: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ ERRO na requisição: {e}")
        return False

def test_callback_processing():
    """Testa processamento de callback (botões)"""
    print("\n🔘 TESTANDO CALLBACK DE BOTÃO")
    print("=" * 60)
    
    # Simula clique no botão "Todas as Tips"
    callback_payload = {
        "update_id": 123457,
        "callback_query": {
            "id": "callback123",
            "from": {
                "id": 8012415611,
                "username": "testadmin",
                "first_name": "Test Admin"
            },
            "message": {
                "message_id": 790,
                "chat": {
                    "id": -1001234567890,
                    "type": "supergroup",
                    "title": "Grupo de Teste LoL"
                },
                "date": int(time.time())
            },
            "data": "group_all_tips"
        }
    }
    
    print(f"🔘 Simulando clique: 'Todas as Tips'")
    
    try:
        url = "https://predictlol-production.up.railway.app/webhook"
        response = requests.post(url, json=callback_payload, timeout=15)
        
        print(f"\n📊 RESULTADO CALLBACK:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCESSO - Callback processado!")
            try:
                result = response.json()
                print(f"   📋 Resposta: {json.dumps(result, indent=2)}")
            except:
                print(f"   📋 Resposta: {response.text}")
        else:
            print(f"   ❌ ERRO - Status {response.status_code}")
            print(f"   📋 Erro: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ ERRO na requisição: {e}")
        return False

def verify_bot_info():
    """Verifica informações do bot"""
    print("\n🤖 VERIFICANDO BOT INFO")
    print("=" * 60)
    
    token = "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0"
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        
        if response.status_code == 200:
            bot_info = response.json()['result']
            print(f"   ✅ Bot ativo:")
            print(f"      🤖 Nome: {bot_info['first_name']}")
            print(f"      📱 Username: @{bot_info['username']}")
            print(f"      🆔 ID: {bot_info['id']}")
            print(f"      👥 Pode entrar em grupos: {bot_info['can_join_groups']}")
            print(f"      📖 Pode ler mensagens: {bot_info['can_read_all_group_messages']}")
            return True
        else:
            print(f"   ❌ Erro: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    """Função principal"""
    print("🧪 TESTE COMPLETO: /activate_group com Token Correto")
    print("=" * 70)
    print(f"📅 Data/Hora: {time.strftime('%d/%m/%Y %H:%M:%S')}")
    print("🎯 Objetivo: Verificar se comando funciona")
    print("")
    
    # Testes
    results = []
    
    results.append(("Verificação do Bot", verify_bot_info()))
    results.append(("Comando /activate_group", test_activate_group_webhook()))
    results.append(("Callback de Botão", test_callback_processing()))
    
    # Relatório final
    print("\n" + "=" * 70)
    print("📋 RELATÓRIO FINAL")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {status}: {test_name}")
    
    print(f"\n📊 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 COMANDO /activate_group FUNCIONANDO 100%!")
        print("✅ Bot configurado corretamente")
        print("✅ Webhook processando comandos")
        print("✅ Callbacks funcionando")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Adicionar bot a um grupo real")
        print("   2. Testar /activate_group manualmente")
        print("   3. Sistema está pronto para uso!")
    else:
        print("⚠️ Alguns problemas ainda existem")
        print("💡 Verifique os logs acima para detalhes")
    
    print(f"\n🕒 Teste concluído: {time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main() 