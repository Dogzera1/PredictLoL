#!/usr/bin/env python3
"""
Script para configurar o webhook do Telegram com a URL atual do Vercel
"""

import requests
from config import BOT_TOKEN

def set_webhook():
    """Configura o webhook do Telegram"""
    webhook_url = "https://lol-gpt-apostas-hvcx2icbm-victors-projects-42e6b0fe.vercel.app/api/webhook"
    
    print(f"🔗 Configurando webhook: {webhook_url}")
    
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    
    data = {
        "url": webhook_url,
        "secret_token": "lol_gpt_secret_token"
    }
    
    try:
        response = requests.post(telegram_url, json=data)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook configurado com sucesso!")
            print(f"Descrição: {result.get('description', 'N/A')}")
            return True
        else:
            print(f"❌ Erro ao configurar webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def get_webhook_info():
    """Verifica informações do webhook"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            webhook_info = data.get("result", {})
            webhook_url = webhook_info.get("url", "Não configurado")
            pending_updates = webhook_info.get("pending_update_count", 0)
            last_error = webhook_info.get("last_error_message", "Nenhum")
            
            print(f"🔗 URL do webhook: {webhook_url}")
            print(f"📊 Updates pendentes: {pending_updates}")
            print(f"⚠️ Último erro: {last_error}")
            
            return True
        else:
            print(f"❌ Erro: {data.get('description', 'Erro desconhecido')}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔗 CONFIGURAÇÃO DO WEBHOOK")
    print("=" * 60)
    
    print("📋 Status atual:")
    get_webhook_info()
    print()
    
    print("🔄 Configurando novo webhook...")
    if set_webhook():
        print()
        print("📋 Status após configuração:")
        get_webhook_info()
    
    print("\n" + "=" * 60)
    print("✅ CONFIGURAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print("🌐 Nova URL: https://lol-gpt-apostas-hvcx2icbm-victors-projects-42e6b0fe.vercel.app")
    print("📱 Teste seu bot enviando /start no Telegram") 