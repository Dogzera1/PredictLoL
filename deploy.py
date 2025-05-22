#!/usr/bin/env python3
"""
Script para fazer deploy do bot LoL no Vercel

Este script automatiza o processo de deploy e configuração do webhook.
"""

import os
import sys
import json
import subprocess
import requests
from config import BOT_TOKEN

def run_command(command):
    """Executa um comando e retorna o resultado"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_vercel_cli():
    """Verifica se o Vercel CLI está instalado"""
    success, _, _ = run_command("vercel --version")
    return success

def deploy_to_vercel():
    """Faz o deploy para o Vercel"""
    print("🚀 Iniciando deploy para o Vercel...")
    
    if not check_vercel_cli():
        print("❌ Vercel CLI não encontrado. Instale com: npm i -g vercel")
        return False
    
    # Deploy
    success, output, error = run_command("vercel --prod")
    
    if success:
        print("✅ Deploy realizado com sucesso!")
        # Extrair URL do output
        lines = output.split('\n')
        for line in lines:
            if 'https://' in line and 'vercel.app' in line:
                return line.strip()
        return True
    else:
        print(f"❌ Erro no deploy: {error}")
        return False

def set_webhook(url):
    """Configura o webhook no Telegram"""
    webhook_url = f"{url}/api/webhook"
    
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
            return True
        else:
            print(f"❌ Erro ao configurar webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def check_bot_status(url):
    """Verifica o status do bot"""
    try:
        response = requests.get(f"{url}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ Bot está funcionando corretamente!")
                return True
        
        print("⚠️ Bot pode não estar funcionando corretamente")
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 DEPLOY DO BOT LOL PARA VERCEL")
    print("=" * 60)
    
    # Verificar token
    if not BOT_TOKEN or BOT_TOKEN == "seu_token_aqui":
        print("❌ Token do bot não configurado!")
        print("Configure a variável TELEGRAM_TOKEN ou edite config.py")
        return
    
    # Deploy
    result = deploy_to_vercel()
    if not result:
        return
    
    # Extrair URL se for string
    if isinstance(result, str):
        url = result
    else:
        # Tentar obter URL do projeto
        success, output, _ = run_command("vercel ls")
        if success:
            lines = output.split('\n')
            for line in lines:
                if '.vercel.app' in line:
                    parts = line.split()
                    for part in parts:
                        if '.vercel.app' in part:
                            url = f"https://{part}"
                            break
                    break
            else:
                print("❌ Não foi possível obter a URL do projeto")
                return
        else:
            print("❌ Não foi possível obter a URL do projeto")
            return
    
    print(f"🌐 URL do projeto: {url}")
    
    # Configurar webhook
    if set_webhook(url):
        # Verificar status
        print("\n⏳ Aguardando alguns segundos...")
        import time
        time.sleep(5)
        check_bot_status(url)
    
    print("\n" + "=" * 60)
    print("✅ DEPLOY CONCLUÍDO!")
    print("=" * 60)
    print(f"🌐 Bot URL: {url}")
    print(f"🔗 Webhook: {url}/api/webhook")
    print(f"💊 Health Check: {url}/health")
    print("\n📱 Teste seu bot no Telegram enviando /start")

if __name__ == "__main__":
    main() 