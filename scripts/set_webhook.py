"""
Script para configurar o webhook do Telegram no Vercel.

Uso: python set_webhook.py https://seu-app.vercel.app/api/webhook
"""

import argparse
import requests
import sys
import os

# Adicionar o diretório raiz ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_TOKEN

def setup_webhook(webhook_url, allow_self_signed=False, drop_pending=False):
    """Configura o webhook do Telegram."""
    
    # Se o token não estiver no arquivo de configuração, tenta pegar da variável de ambiente
    token = os.environ.get("TELEGRAM_TOKEN", BOT_TOKEN)
    
    if token == "SEU_TOKEN_AQUI" and not os.environ.get("TELEGRAM_TOKEN"):
        print("❌ Erro: Token do Telegram não definido!")
        print("Configure o token no arquivo config.py ou defina a variável de ambiente TELEGRAM_TOKEN")
        return False
    
    # Montar a URL para configurar o webhook
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    # Parâmetros para a requisição
    params = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query", "inline_query"],
        "drop_pending_updates": drop_pending,
        "secret_token": "lol_gpt_secret_token"
    }
    
    # Enviar a requisição para configurar o webhook
    try:
        print(f"Configurando webhook para: {webhook_url}")
        response = requests.post(api_url, json=params)
        result = response.json()
        
        print(f"Resposta completa: {result}")
        
        if result.get("ok"):
            print(f"✅ Webhook configurado com sucesso para: {webhook_url}")
            print(f"Resposta: {result.get('description')}")
            return True
        else:
            print(f"❌ Erro ao configurar webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Erro durante a requisição: {str(e)}")
        return False

def delete_webhook():
    """Remove o webhook atual."""
    
    # Se o token não estiver no arquivo de configuração, tenta pegar da variável de ambiente
    token = os.environ.get("TELEGRAM_TOKEN", BOT_TOKEN)
    
    if token == "SEU_TOKEN_AQUI" and not os.environ.get("TELEGRAM_TOKEN"):
        print("❌ Erro: Token do Telegram não definido!")
        return False
    
    # Montar a URL para remover o webhook
    api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    
    # Enviar a requisição
    try:
        response = requests.get(api_url)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook removido com sucesso!")
            print(f"Resposta: {result.get('description')}")
            return True
        else:
            print(f"❌ Erro ao remover webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Erro durante a requisição: {str(e)}")
        return False

def get_webhook_info():
    """Obtém informações sobre o webhook atual."""
    
    # Se o token não estiver no arquivo de configuração, tenta pegar da variável de ambiente
    token = os.environ.get("TELEGRAM_TOKEN", BOT_TOKEN)
    
    if token == "SEU_TOKEN_AQUI" and not os.environ.get("TELEGRAM_TOKEN"):
        print("❌ Erro: Token do Telegram não definido!")
        return False
    
    # Montar a URL para obter informações do webhook
    api_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    
    # Enviar a requisição
    try:
        response = requests.get(api_url)
        result = response.json()
        
        if result.get("ok"):
            webhook_info = result.get("result", {})
            
            print("\n📊 Informações do Webhook:")
            print(f"URL: {webhook_info.get('url', 'Não definida')}")
            print(f"Personalizado: {webhook_info.get('has_custom_certificate', False)}")
            print(f"Atualizações pendentes: {webhook_info.get('pending_update_count', 0)}")
            
            if webhook_info.get("last_error_date"):
                import datetime
                error_date = datetime.datetime.fromtimestamp(webhook_info.get("last_error_date"))
                print(f"Último erro: {error_date} - {webhook_info.get('last_error_message', 'Desconhecido')}")
            
            return True
        else:
            print(f"❌ Erro ao obter informações: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Erro durante a requisição: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configurar webhook do Telegram para o Vercel")
    parser.add_argument("webhook_url", nargs="?", help="URL do webhook (ex: https://seu-app.vercel.app/api/webhook)")
    parser.add_argument("--info", action="store_true", help="Mostrar informações do webhook atual")
    parser.add_argument("--delete", action="store_true", help="Remover o webhook atual")
    parser.add_argument("--drop-pending", action="store_true", help="Descartar atualizações pendentes")
    
    args = parser.parse_args()
    
    if args.delete:
        delete_webhook()
        get_webhook_info()
    elif args.info:
        get_webhook_info()
    elif args.webhook_url:
        setup_webhook(args.webhook_url, drop_pending=args.drop_pending)
        get_webhook_info()
    else:
        parser.print_help() 