#!/usr/bin/env python3
"""
🔧 DIAGNÓSTICO COMPLETO - Comando /activate_group
Identifica e resolve todos os problemas do comando de grupos
"""

import os
import requests
import json
import time
from datetime import datetime

def print_header():
    print("🔧 DIAGNÓSTICO COMPLETO: Comando /activate_group")
    print("=" * 70)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("🎯 Objetivo: Identificar e corrigir problemas")
    print("")

def test_telegram_token():
    """Testa o token do Telegram"""
    print("🔑 TESTANDO TOKEN DO TELEGRAM")
    print("=" * 50)
    
    # Tokens para testar
    tokens_to_test = [
        "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0",  # Token atual válido
        os.getenv("TELEGRAM_BOT_TOKEN"),  # Token do ambiente
    ]
    
    for i, token in enumerate(tokens_to_test, 1):
        if not token:
            print(f"   ❌ Token {i}: Não encontrado")
            continue
            
        print(f"   🔍 Testando Token {i}: {token[:20]}...")
        
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                print(f"   ✅ Token {i}: VÁLIDO")
                print(f"      🤖 Bot: @{bot_info['result']['username']}")
                print(f"      📝 Nome: {bot_info['result']['first_name']}")
                print(f"      🆔 ID: {bot_info['result']['id']}")
                return token
            else:
                print(f"   ❌ Token {i}: Status {response.status_code}")
                print(f"      📝 Erro: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Token {i}: Erro na conexão - {e}")
    
    print("\n🚨 NENHUM TOKEN VÁLIDO ENCONTRADO!")
    return None

def test_railway_deployment():
    """Testa deployment no Railway"""
    print("\n🚀 TESTANDO RAILWAY DEPLOYMENT")
    print("=" * 50)
    
    base_url = "https://predictlol-production.up.railway.app"
    
    endpoints = [
        ("/", "Root"),
        ("/health", "Health Check"),
        ("/status", "Status"),
        ("/webhook", "Webhook"),
        ("/dashboard", "Dashboard")
    ]
    
    railway_working = True
    
    for endpoint, name in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            if endpoint == "/webhook":
                # Webhook deve aceitar POST
                response = requests.post(url, json={"test": True}, timeout=10)
            else:
                response = requests.get(url, timeout=10)
            
            if response.status_code in [200, 400, 405]:  # 405 = Method not allowed (normal para webhook GET)
                print(f"   ✅ {name}: OK ({response.status_code})")
            else:
                print(f"   ⚠️ {name}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {name}: Erro - {e}")
            railway_working = False
    
    return railway_working

def test_webhook_processing():
    """Testa processamento de webhook para activate_group"""
    print("\n📨 TESTANDO PROCESSAMENTO DO WEBHOOK")
    print("=" * 50)
    
    # Simula comando /activate_group em um grupo
    webhook_payload = {
        "update_id": 123456,
        "message": {
            "message_id": 789,
            "from": {
                "id": 8012415611,  # Admin ID
                "username": "testuser",
                "first_name": "Test"
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
    
    try:
        url = "https://predictlol-production.up.railway.app/webhook"
        response = requests.post(url, json=webhook_payload, timeout=15)
        
        print(f"   📤 Payload enviado: /activate_group")
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Webhook processado com sucesso")
            try:
                result = response.json()
                print(f"   📋 Resposta: {result}")
            except:
                print(f"   📋 Resposta (text): {response.text}")
        else:
            print(f"   ❌ Erro no webhook: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erro ao testar webhook: {e}")

def check_health_check_implementation():
    """Verifica implementação do health_check.py"""
    print("\n🔍 VERIFICANDO IMPLEMENTAÇÃO NO HEALTH_CHECK.PY")
    print("=" * 50)
    
    try:
        with open("health_check.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verifica se activate_group está implementado
        checks = [
            ("'/activate_group'", "Comando activate_group"),
            ("_send_activate_group_response", "Função de resposta"),
            ("_handle_callback", "Handler de callback"),
            ("group_all_tips", "Callback de grupo"),
            ("_process_group_subscription", "Processamento de grupo")
        ]
        
        missing = []
        
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}: Encontrado")
            else:
                print(f"   ❌ {description}: FALTANDO")
                missing.append(description)
        
        if missing:
            print(f"\n   🚨 PROBLEMAS ENCONTRADOS: {len(missing)} itens faltando")
            return False
        else:
            print(f"\n   ✅ IMPLEMENTAÇÃO COMPLETA")
            return True
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar arquivo: {e}")
        return False

def suggest_fixes():
    """Sugere correções para os problemas encontrados"""
    print("\n🔧 CORREÇÕES SUGERIDAS")
    print("=" * 50)
    
    print("1. 🔑 PROBLEMA DO TOKEN:")
    print("   • O token atual está retornando 401 Unauthorized")
    print("   • Possível solução: Renovar token no @BotFather")
    print("   • Comando: /newbot ou /token no @BotFather")
    print("   • Atualizar variável TELEGRAM_BOT_TOKEN no Railway")
    
    print("\n2. 🌐 CONFIGURAÇÃO DO WEBHOOK:")
    print("   • Verificar se webhook está configurado")
    print("   • URL: https://predictlol-production.up.railway.app/webhook")
    print("   • Comando: setWebhook no Telegram API")
    
    print("\n3. 📱 TESTANDO MANUALMENTE:")
    print("   • Adicione o bot a um grupo de teste")
    print("   • Digite /activate_group")
    print("   • Verifique se aparece menu de botões")
    
    print("\n4. 🔄 RESTART DO RAILWAY:")
    print("   • Às vezes é necessário restart após mudanças")
    print("   • Verificar logs do Railway para erros")

def create_test_webhook_script():
    """Cria script para testar webhook com token válido"""
    print("\n📝 CRIANDO SCRIPT DE TESTE")
    print("=" * 50)
    
    test_script = '''#!/usr/bin/env python3
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
'''
    
    with open("test_webhook_token.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("   ✅ Script criado: test_webhook_token.py")
    print("   📝 Substitua TOKEN_AQUI pelo token correto")

def main():
    """Função principal"""
    print_header()
    
    # Testa token
    valid_token = test_telegram_token()
    
    # Testa Railway
    railway_ok = test_railway_deployment()
    
    # Testa webhook
    test_webhook_processing()
    
    # Verifica implementação
    implementation_ok = check_health_check_implementation()
    
    # Cria script de teste
    create_test_webhook_script()
    
    # Sugere correções
    suggest_fixes()
    
    # Relatório final
    print("\n" + "=" * 70)
    print("📋 RELATÓRIO FINAL DE DIAGNÓSTICO")
    print("=" * 70)
    
    issues = []
    
    if not valid_token:
        issues.append("🔑 Token do Telegram inválido")
    
    if not railway_ok:
        issues.append("🚀 Problemas no Railway")
        
    if not implementation_ok:
        issues.append("🔧 Implementação incompleta")
    
    if issues:
        print("❌ PROBLEMAS IDENTIFICADOS:")
        for issue in issues:
            print(f"   • {issue}")
        
        print("\n🔧 PRÓXIMOS PASSOS:")
        print("1. Renovar token do Telegram no @BotFather")
        print("2. Atualizar TELEGRAM_BOT_TOKEN no Railway")
        print("3. Configurar webhook com token correto")
        print("4. Testar /activate_group em grupo real")
        
    else:
        print("✅ NENHUM PROBLEMA CRÍTICO ENCONTRADO")
        print("🎯 O comando /activate_group deve estar funcionando")
        print("💡 Se ainda não funciona, o problema pode ser:")
        print("   • Webhook não configurado")
        print("   • Bot não adicionado ao grupo")
        print("   • Permissões do bot no grupo")
    
    print(f"\n📅 Diagnóstico concluído: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main() 