#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final do bot - Verificar se está funcionando após resolver conflito
"""

import os
import requests
import time
from datetime import datetime

TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')

def test_bot_functionality():
    """Testar funcionalidades básicas do bot"""
    print("🧪 TESTE FINAL DO BOT")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    tests = []
    
    # Teste 1: Conectividade básica
    print("1️⃣ Testando conectividade básica...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print(f"   ✅ Bot conectado: @{bot_info['username']}")
                print(f"   ✅ Nome: {bot_info['first_name']}")
                print(f"   ✅ ID: {bot_info['id']}")
                tests.append(("Conectividade", True))
            else:
                print(f"   ❌ Erro na resposta: {data}")
                tests.append(("Conectividade", False))
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            tests.append(("Conectividade", False))
    except Exception as e:
        print(f"   ❌ Erro de conexão: {e}")
        tests.append(("Conectividade", False))
    
    print()
    
    # Teste 2: Verificar updates (sem conflito)
    print("2️⃣ Testando recebimento de updates...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {'limit': 1, 'timeout': 3}
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=5)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"   ✅ Updates OK (tempo: {end_time - start_time:.1f}s)")
            tests.append(("Updates", True))
        elif response.status_code == 409:
            print(f"   ❌ CONFLITO AINDA DETECTADO!")
            tests.append(("Updates", False))
        else:
            print(f"   ⚠️ Status inesperado: {response.status_code}")
            tests.append(("Updates", False))
    except Exception as e:
        print(f"   ❌ Erro ao buscar updates: {e}")
        tests.append(("Updates", False))
    
    print()
    
    # Teste 3: Webhook status
    print("3️⃣ Verificando status do webhook...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                webhook_info = data['result']
                if webhook_info['url']:
                    print(f"   ⚠️ Webhook ativo: {webhook_info['url']}")
                    print(f"   ⚠️ Isso pode causar problemas com polling")
                    tests.append(("Webhook", False))
                else:
                    print(f"   ✅ Nenhum webhook configurado (correto para polling)")
                    tests.append(("Webhook", True))
            else:
                print(f"   ❌ Erro na resposta: {data}")
                tests.append(("Webhook", False))
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            tests.append(("Webhook", False))
    except Exception as e:
        print(f"   ❌ Erro ao verificar webhook: {e}")
        tests.append(("Webhook", False))
    
    print()
    
    # Relatório final
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"• {test_name}: {status}")
        if result:
            passed += 1
    
    print()
    print(f"📈 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Bot está funcionando perfeitamente")
        print("✅ Pode usar no Telegram agora")
        return True
    else:
        print("⚠️ Alguns testes falharam")
        print("⚠️ Verifique os problemas acima")
        return False

def main():
    """Função principal"""
    success = test_bot_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("🎯 PRÓXIMOS PASSOS:")
        print("1. Abra o Telegram")
        print("2. Procure por @BETLOLGPT_bot")
        print("3. Envie /start")
        print("4. Teste os comandos /agenda e /partidas")
        print("5. Verifique se a API da Riot está funcionando")
    else:
        print("🔧 AÇÕES NECESSÁRIAS:")
        print("1. Verifique os erros acima")
        print("2. Se houver conflito, pare outras instâncias")
        print("3. Se houver webhook, remova-o")
        print("4. Execute este teste novamente")

if __name__ == "__main__":
    main() 