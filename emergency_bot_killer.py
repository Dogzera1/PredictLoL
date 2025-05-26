#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE EMERGÊNCIA: Parar TODAS as instâncias do bot
"""

import os
import requests
import time
from datetime import datetime

TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')

def force_clear_all():
    """Forçar limpeza completa do bot"""
    print("🚨 MODO EMERGÊNCIA: PARANDO TODAS AS INSTÂNCIAS")
    print("=" * 60)
    
    try:
        # 1. Definir webhook vazio para forçar parada de polling
        print("1️⃣ Forçando parada via webhook vazio...")
        url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        data = {'url': ''}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Webhook vazio definido (força parada de polling)")
        else:
            print(f"⚠️ Erro ao definir webhook: {response.status_code}")
        
        time.sleep(3)
        
        # 2. Remover webhook
        print("2️⃣ Removendo webhook...")
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url)
        if response.status_code == 200:
            print("✅ Webhook removido")
        
        time.sleep(3)
        
        # 3. Limpar updates múltiplas vezes
        print("3️⃣ Limpando updates (múltiplas tentativas)...")
        for i in range(5):
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {'offset': -1, 'limit': 100, 'timeout': 1}
            response = requests.get(url, params=params, timeout=5)
            print(f"   Tentativa {i+1}/5: Status {response.status_code}")
            time.sleep(1)
        
        print("✅ Limpeza de emergência concluída")
        
        # 4. Aguardar estabilização
        print("4️⃣ Aguardando estabilização (30 segundos)...")
        for i in range(30, 0, -1):
            print(f"   Aguardando: {i}s", end='\r')
            time.sleep(1)
        print("\n✅ Estabilização concluída")
        
        # 5. Status final
        print("5️⃣ Verificando status final...")
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print(f"🤖 Bot: @{bot_info['username']} - Status: Pronto")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na limpeza de emergência: {e}")
        return False

def check_common_platforms():
    """Verificar plataformas comuns onde o bot pode estar rodando"""
    print("\n🔍 VERIFICAÇÃO DE PLATAFORMAS COMUNS")
    print("=" * 50)
    
    platforms = [
        "🚂 Railway: https://railway.app/dashboard",
        "🟣 Heroku: https://dashboard.heroku.com/apps", 
        "🔵 Render: https://dashboard.render.com/",
        "🟡 Replit: https://replit.com/~",
        "🟠 PythonAnywhere: https://www.pythonanywhere.com/user/dashboard/",
        "☁️ Google Cloud: https://console.cloud.google.com/",
        "🟠 AWS: https://console.aws.amazon.com/",
        "🔴 DigitalOcean: https://cloud.digitalocean.com/",
        "🟢 Vercel: https://vercel.com/dashboard",
        "🔵 Netlify: https://app.netlify.com/"
    ]
    
    print("VERIFIQUE ESTAS PLATAFORMAS E PARE QUALQUER INSTÂNCIA DO BOT:")
    print()
    for platform in platforms:
        print(f"• {platform}")
    
    print()
    print("🎯 AÇÕES NECESSÁRIAS:")
    print("1. Acesse cada plataforma listada acima")
    print("2. Procure por projetos/apps com nomes relacionados ao bot")
    print("3. PAUSE ou DELETE todas as instâncias encontradas")
    print("4. Mantenha apenas UMA instância ativa (Railway)")
    print("5. Aguarde 5 minutos após parar todas as extras")

def main():
    """Função principal de emergência"""
    print("🆘 SCRIPT DE EMERGÊNCIA - CONFLITO DE INSTÂNCIAS")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Executar limpeza de emergência
    if force_clear_all():
        print("\n✅ LIMPEZA DE EMERGÊNCIA CONCLUÍDA")
    else:
        print("\n❌ FALHA NA LIMPEZA DE EMERGÊNCIA")
    
    # Mostrar plataformas para verificar
    check_common_platforms()
    
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANTE: ESTE SCRIPT APENAS LIMPA O TELEGRAM")
    print("⚠️  VOCÊ AINDA PRECISA PARAR AS INSTÂNCIAS EXTRAS MANUALMENTE")
    print("⚠️  VERIFIQUE TODAS AS PLATAFORMAS LISTADAS ACIMA")
    print("=" * 60)

if __name__ == "__main__":
    main() 