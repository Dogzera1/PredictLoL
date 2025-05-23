#!/usr/bin/env python3
"""
Script para testar o bot localmente e identificar problemas antes do deploy
"""

import os
import sys
import requests
import time
from datetime import datetime

def test_telegram_token():
    """Testa se o token do Telegram é válido"""
    print("🔍 Testando token do Telegram...")
    
    # Token do ambiente ou hardcoded para teste
    token = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print(f"✅ Token válido!")
                print(f"   🤖 Nome: {bot_info['first_name']}")
                print(f"   🆔 Username: @{bot_info['username']}")
                print(f"   🔢 ID: {bot_info['id']}")
                return True
            else:
                print(f"❌ Token inválido: {data.get('description', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_webhook_setup():
    """Testa configuração do webhook"""
    print("\n🔍 Testando configuração do webhook...")
    
    token = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
    
    try:
        # Verificar webhook atual
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                webhook_info = data['result']
                print(f"📡 URL do webhook: {webhook_info.get('url', 'Não configurado')}")
                print(f"📊 Updates pendentes: {webhook_info.get('pending_update_count', 0)}")
                
                last_error = webhook_info.get('last_error_message')
                if last_error:
                    print(f"⚠️ Último erro: {last_error}")
                    print(f"📅 Data do erro: {webhook_info.get('last_error_date', 'N/A')}")
                else:
                    print("✅ Nenhum erro no webhook")
                
                return True
            else:
                print(f"❌ Erro ao obter info do webhook: {data.get('description')}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_railway_url():
    """Testa se a URL do Railway está respondendo"""
    print("\n🔍 Testando URL do Railway...")
    
    railway_url = "https://spectacular-wonder-production-4fb2.up.railway.app"
    
    try:
        # Testar página inicial
        print("   🏠 Testando página inicial...")
        response = requests.get(railway_url, timeout=15)
        
        if response.status_code == 200:
            print(f"   ✅ Página inicial OK (200)")
            if "Bot LoL" in response.text:
                print("   ✅ Conteúdo correto detectado")
            else:
                print("   ⚠️ Conteúdo pode estar incorreto")
        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            
        # Testar endpoint de saúde
        print("   🏥 Testando endpoint de saúde...")
        health_response = requests.get(f"{railway_url}/health", timeout=15)
        
        if health_response.status_code == 200:
            print(f"   ✅ Health check OK (200)")
            try:
                health_data = health_response.json()
                print(f"   📊 Status: {health_data.get('status', 'unknown')}")
                print(f"   🤖 Bot: {health_data.get('bot', 'unknown')}")
            except:
                print("   ⚠️ Resposta não é JSON válido")
        else:
            print(f"   ❌ Health check falhou ({health_response.status_code})")
            
        # Testar webhook
        print("   📡 Testando webhook...")
        webhook_response = requests.get(f"{railway_url}/webhook", timeout=15)
        
        if webhook_response.status_code == 200:
            print(f"   ✅ Webhook endpoint OK (200)")
        else:
            print(f"   ❌ Webhook falhou ({webhook_response.status_code})")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erro de conexão com Railway: {e}")
        return False

def test_dependencies():
    """Testa se todas as dependências estão instaladas"""
    print("\n🔍 Testando dependências...")
    
    required_modules = [
        'telegram',
        'flask', 
        'requests'
    ]
    
    all_ok = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} - não instalado")
            all_ok = False
    
    return all_ok

def main():
    print("🤖 TESTE COMPLETO DO BOT LoL")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests_results = []
    
    # Executar testes
    tests_results.append(("Token Telegram", test_telegram_token()))
    tests_results.append(("Webhook Info", test_webhook_setup()))
    tests_results.append(("Railway URL", test_railway_url()))
    tests_results.append(("Dependências", test_dependencies()))
    
    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = sum(1 for _, result in tests_results if result)
    total = len(tests_results)
    
    for test_name, result in tests_results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:.<20} {status}")
    
    print(f"\n📈 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("💡 O bot deveria estar funcionando. Se ainda há problemas no Railway:")
        print("   1. Verifique as variáveis de ambiente no dashboard")
        print("   2. Verifique os logs de deployment no Railway")
        print("   3. Tente fazer redeploy manual")
    else:
        print(f"\n⚠️ {total - passed} TESTE(S) FALHARAM")
        print("💡 Corrija os problemas identificados antes de fazer o deploy")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        exit(1) 