#!/usr/bin/env python3
"""
Script para testar o bot no Vercel
"""

import requests
import json
from config import BOT_TOKEN

def test_webhook_endpoint():
    """Testa o endpoint do webhook"""
    url = "https://lol-gpt-apostas-hvcx2icbm-victors-projects-42e6b0fe.vercel.app/api/webhook"
    
    try:
        print("🔍 Testando endpoint do webhook...")
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_telegram_bot():
    """Testa se o bot está ativo no Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        print("🤖 Testando bot no Telegram...")
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            bot_info = data.get("result", {})
            print(f"✅ Bot ativo: @{bot_info.get('username', 'N/A')}")
            print(f"Nome: {bot_info.get('first_name', 'N/A')}")
            return True
        else:
            print(f"❌ Erro: {data.get('description', 'Erro desconhecido')}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def check_webhook_info():
    """Verifica informações do webhook"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        print("🔗 Verificando webhook configurado...")
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            webhook_info = data.get("result", {})
            webhook_url = webhook_info.get("url", "Não configurado")
            pending_updates = webhook_info.get("pending_update_count", 0)
            last_error = webhook_info.get("last_error_message", "Nenhum")
            
            print(f"URL do webhook: {webhook_url}")
            print(f"Updates pendentes: {pending_updates}")
            print(f"Último erro: {last_error}")
            
            return webhook_url != ""
        else:
            print(f"❌ Erro: {data.get('description', 'Erro desconhecido')}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 TESTE DO BOT LOL NO VERCEL")
    print("=" * 60)
    
    # Teste 1: Endpoint do webhook
    webhook_ok = test_webhook_endpoint()
    print()
    
    # Teste 2: Bot no Telegram
    bot_ok = test_telegram_bot()
    print()
    
    # Teste 3: Informações do webhook
    webhook_info_ok = check_webhook_info()
    print()
    
    print("=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    print(f"🌐 Endpoint webhook: {'✅ OK' if webhook_ok else '❌ FALHOU'}")
    print(f"🤖 Bot Telegram: {'✅ OK' if bot_ok else '❌ FALHOU'}")
    print(f"🔗 Webhook configurado: {'✅ OK' if webhook_info_ok else '❌ FALHOU'}")
    
    if all([webhook_ok, bot_ok, webhook_info_ok]):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("📱 Seu bot deve estar funcionando. Teste enviando /start no Telegram.")
    else:
                print("\n⚠️ ALGUNS TESTES FALHARAM")        print("📋 Verifique as mensagens de erro acima para resolver os problemas.")        print("\n🔗 URLs úteis:")    print("• Bot URL: https://lol-gpt-apostas-hvcx2icbm-victors-projects-42e6b0fe.vercel.app")    print("• Webhook: https://lol-gpt-apostas-hvcx2icbm-victors-projects-42e6b0fe.vercel.app/api/webhook")

if __name__ == "__main__":
    main() 