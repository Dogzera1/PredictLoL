#!/usr/bin/env python3
"""
Verifica se o bot está funcionando
"""

import requests
import time

def verificar_bot():
    """Verifica se o bot está respondendo"""
    token = "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI"
    
    try:
        # Verificar se o bot está ativo
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print("✅ Bot Status: ATIVO")
                print(f"📱 Nome: {bot_info['first_name']}")
                print(f"🔗 Username: @{bot_info['username']}")
                print(f"🆔 ID: {bot_info['id']}")
                return True
            else:
                print("❌ Bot Status: ERRO na resposta")
                return False
        else:
            print(f"❌ Bot Status: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar bot: {e}")
        return False

def verificar_updates():
    """Verifica se há updates/mensagens recentes"""
    token = "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI"
    
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                updates = data['result']
                print(f"📨 Updates recentes: {len(updates)}")
                
                if updates:
                    last_update = updates[-1]
                    if 'message' in last_update:
                        msg = last_update['message']
                        print(f"🗨️ Última mensagem: '{msg.get('text', 'N/A')}'")
                        print(f"👤 De: {msg['from']['first_name']}")
                        print(f"📅 Em: {time.ctime(msg['date'])}")
                
                return True
            else:
                print("❌ Erro ao obter updates")
                return False
        else:
            print(f"❌ HTTP {response.status_code} ao obter updates")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar updates: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verificando status do bot...")
    print("=" * 50)
    
    if verificar_bot():
        print("\n🔍 Verificando mensagens recentes...")
        print("=" * 50)
        verificar_updates()
        
        print("\n💡 INSTRUÇÕES:")
        print("1. Abra o Telegram")
        print("2. Procure por @PredictLoLbot")
        print("3. Digite /start")
        print("4. Você deve receber uma mensagem de boas-vindas")
        print("\nSe não funcionar, verifique se o processo main.py está rodando.")
    else:
        print("\n❌ Bot não está funcionando corretamente!") 