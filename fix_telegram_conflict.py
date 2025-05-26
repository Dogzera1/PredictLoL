#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para resolver conflito de múltiplas instâncias do Telegram Bot
"""

import os
import requests
import time
from datetime import datetime

# Token do bot
TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')

def clear_webhook():
    """Limpar webhook se existir"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url)
        if response.status_code == 200:
            print("✅ Webhook removido com sucesso")
            return True
        else:
            print(f"⚠️ Erro ao remover webhook: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao limpar webhook: {e}")
        return False

def get_bot_info():
    """Obter informações do bot"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print(f"🤖 Bot: @{bot_info['username']} ({bot_info['first_name']})")
                print(f"🆔 ID: {bot_info['id']}")
                return True
        print(f"❌ Erro ao obter info do bot: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Erro ao conectar com bot: {e}")
        return False

def check_webhook_status():
    """Verificar status do webhook"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                webhook_info = data['result']
                if webhook_info['url']:
                    print(f"🔗 Webhook ativo: {webhook_info['url']}")
                    print(f"📊 Updates pendentes: {webhook_info.get('pending_update_count', 0)}")
                    return True
                else:
                    print("✅ Nenhum webhook configurado")
                    return False
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar webhook: {e}")
        return False

def clear_pending_updates():
    """Limpar updates pendentes"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {'offset': -1, 'limit': 1}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("✅ Updates pendentes limpos")
            return True
        else:
            print(f"⚠️ Erro ao limpar updates: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao limpar updates: {e}")
        return False

def main():
    """Função principal para resolver conflitos"""
    print("🔧 RESOLVENDO CONFLITO DE INSTÂNCIAS DO TELEGRAM BOT")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # 1. Verificar conexão com o bot
    print("1️⃣ Verificando conexão com o bot...")
    if not get_bot_info():
        print("❌ Falha na conexão. Verifique o token.")
        return
    print()
    
    # 2. Verificar webhook
    print("2️⃣ Verificando status do webhook...")
    has_webhook = check_webhook_status()
    print()
    
    # 3. Limpar webhook se existir
    if has_webhook:
        print("3️⃣ Removendo webhook...")
        clear_webhook()
        time.sleep(2)
        print()
    
    # 4. Limpar updates pendentes
    print("4️⃣ Limpando updates pendentes...")
    clear_pending_updates()
    time.sleep(2)
    print()
    
    # 5. Verificar novamente
    print("5️⃣ Verificação final...")
    check_webhook_status()
    print()
    
    print("✅ RESOLUÇÃO CONCLUÍDA!")
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Aguarde 30 segundos")
    print("2. Verifique se apenas UMA instância está rodando:")
    print("   • Railway: Deve estar ativo")
    print("   • Local: Deve estar parado")
    print("   • Outros serviços: Devem estar parados")
    print("3. Teste o bot no Telegram")
    print()
    print("💡 Se o problema persistir:")
    print("   • Pare TODAS as instâncias")
    print("   • Aguarde 5 minutos")
    print("   • Inicie apenas UMA instância")

if __name__ == "__main__":
    main() 