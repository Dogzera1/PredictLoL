#!/usr/bin/env python3
"""
Script para configurar o webhook no Railway
Execute após o deploy estar funcionando
"""

import requests
import sys

# Token do bot (você vai inserir manualmente)
TOKEN = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"

def set_webhook(railway_url):
    """Configura o webhook do Telegram para apontar para o Railway"""
    webhook_url = f"{railway_url}/webhook"
    
    print(f"🔗 Configurando webhook para: {webhook_url}")
    
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    
    data = {
        "url": webhook_url,
        "secret_token": "lol_gpt_secret_token"
    }
    
    try:
        response = requests.post(telegram_url, json=data)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook configurado com sucesso!")
            print(f"📝 Descrição: {result.get('description', 'N/A')}")
            return True
        else:
            print(f"❌ Erro ao configurar webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_railway_app(railway_url):
    """Testa se a aplicação está funcionando no Railway"""
    try:
        print(f"🧪 Testando aplicação: {railway_url}")
        response = requests.get(railway_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Aplicação funcionando!")
            print(f"📄 Conteúdo: {response.text[:100]}...")
            return True
        else:
            print(f"❌ Aplicação retornou status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar aplicação: {e}")
        return False

def check_webhook_info():
    """Verifica o status do webhook"""
    url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
    
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

def main():
    print("=" * 60)
    print("🚂 CONFIGURAÇÃO DO BOT NO RAILWAY")
    print("=" * 60)
    
    # Solicitar URL do Railway
    if len(sys.argv) > 1:
        railway_url = sys.argv[1].rstrip('/')
    else:
        railway_url = input("Digite a URL do seu projeto no Railway (ex: https://app-name.up.railway.app): ").strip().rstrip('/')
    
    if not railway_url.startswith('http'):
        print("❌ URL inválida! Deve começar com http:// ou https://")
        return
    
    print(f"\n🎯 URL do projeto: {railway_url}")
    
    # Testar aplicação
    print("\n📋 Etapa 1: Testando aplicação...")
    if not test_railway_app(railway_url):
        print("❌ Aplicação não está respondendo. Verifique o deploy.")
        return
    
    # Configurar webhook
    print("\n📋 Etapa 2: Configurando webhook...")
    if set_webhook(railway_url):
        print("\n📋 Etapa 3: Verificando configuração...")
        check_webhook_info()
        
        print("\n" + "=" * 60)
        print("🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("=" * 60)
        print(f"🌐 App URL: {railway_url}")
        print(f"🔗 Webhook: {railway_url}/webhook")
        print(f"🤖 Bot: @BETLOLGPT_bot")
        print("\n📱 Teste agora enviando /start para o bot!")
    else:
        print("\n❌ Falha na configuração do webhook.")

if __name__ == "__main__":
    main() 