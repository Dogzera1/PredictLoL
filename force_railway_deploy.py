#!/usr/bin/env python3
"""
Script para resetar webhook e forçar o Railway a detectar as mudanças
"""

import requests
import json
import time

BOT_TOKEN = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
WEBHOOK_URL = "https://spectacular-wonder-production-4fb2.up.railway.app/webhook"
HEALTH_URL = "https://spectacular-wonder-production-4fb2.up.railway.app/health"

def delete_webhook():
    """Remove o webhook atual"""
    print("🗑️ REMOVENDO WEBHOOK ATUAL...")
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print("✅ Webhook removido com sucesso")
                return True
            else:
                print(f"❌ Erro da API: {data}")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def set_webhook():
    """Configura o webhook novamente"""
    print("📡 CONFIGURANDO WEBHOOK...")
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        payload = {"url": WEBHOOK_URL}
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print("✅ Webhook configurado com sucesso")
                return True
            else:
                print(f"❌ Erro da API: {data}")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def check_version():
    """Verifica a versão do bot"""
    print("🔍 VERIFICANDO VERSÃO DO BOT...")
    
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            version = data.get('version', 'unknown')
            background_thread = data.get('background_thread', False)
            loop_status = data.get('loop', 'unknown')
            
            print(f"📊 Versão: {version}")
            print(f"🔄 Loop: {loop_status}")
            print(f"🧵 Background Thread: {background_thread}")
            
            if version == "2025.05.23-event-loop-fix":
                print("✅ VERSÃO ATUALIZADA DETECTADA!")
                return True
            else:
                print("❌ VERSÃO ANTIGA OU DESCONHECIDA")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def send_test_message():
    """Envia mensagem de teste"""
    print("📨 ENVIANDO MENSAGEM DE TESTE...")
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": "@BETLOLGPT_bot",  # Para o próprio bot
            "text": "🤖 Teste de funcionamento - Railway atualizado!"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print("✅ Mensagem de teste enviada")
                return True
            else:
                print(f"❌ Erro da API: {data}")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 SCRIPT DE FORÇA PARA ATUALIZAÇÃO RAILWAY")
    print("=" * 60)
    
    # Aguardar um pouco para Railway processar
    print("⏳ Aguardando Railway processar mudanças (30s)...")
    time.sleep(30)
    
    # Verificar versão atual
    updated = check_version()
    
    if updated:
        print("\n✅ BOT JÁ ESTÁ ATUALIZADO!")
        return
    
    print("\n🔄 TENTANDO FORÇAR ATUALIZAÇÃO...")
    
    # Reset webhook
    deleted = delete_webhook()
    if deleted:
        time.sleep(5)
        set_webhook()
        time.sleep(10)
        
        # Verificar novamente
        if check_version():
            print("\n✅ SUCESSO! Bot atualizado após reset do webhook")
        else:
            print("\n❌ Ainda na versão antiga após reset")
    
    print("\n📋 RESUMO:")
    print(f"   🤖 Bot URL: {WEBHOOK_URL}")
    print(f"   🏥 Health: {HEALTH_URL}")
    print(f"   💡 Se ainda estiver com problemas, verifique o painel do Railway")

if __name__ == "__main__":
    main() 