#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação contínua de conflito - Detecta quando o problema é resolvido
"""

import os
import requests
import time
from datetime import datetime

TOKEN = os.getenv('TELEGRAM_TOKEN', '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg')

def check_bot_status():
    """Verificar se há conflito ativo"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {'limit': 1, 'timeout': 2}
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=5)
        end_time = time.time()
        
        if response.status_code == 200:
            return True, f"✅ OK ({end_time - start_time:.1f}s)"
        elif response.status_code == 409:
            return False, "❌ CONFLITO DETECTADO"
        else:
            return False, f"⚠️ Erro {response.status_code}"
            
    except Exception as e:
        return False, f"❌ Erro: {str(e)[:50]}"

def monitor_conflict():
    """Monitorar conflito em tempo real"""
    print("🔍 MONITOR DE CONFLITO EM TEMPO REAL")
    print("=" * 60)
    print("Verificando a cada 10 segundos...")
    print("Pressione Ctrl+C para parar")
    print()
    
    conflict_count = 0
    success_count = 0
    
    try:
        while True:
            timestamp = datetime.now().strftime('%H:%M:%S')
            is_ok, status = check_bot_status()
            
            if is_ok:
                success_count += 1
                conflict_count = 0  # Reset contador de conflito
                print(f"[{timestamp}] {status} (Sucessos consecutivos: {success_count})")
                
                if success_count >= 3:
                    print("\n🎉 CONFLITO RESOLVIDO!")
                    print("✅ Bot funcionando normalmente por 30+ segundos")
                    print("✅ Pode testar no Telegram agora")
                    break
                    
            else:
                conflict_count += 1
                success_count = 0  # Reset contador de sucesso
                print(f"[{timestamp}] {status} (Conflitos consecutivos: {conflict_count})")
                
                if conflict_count == 1:
                    print("⚠️  AINDA HÁ INSTÂNCIAS EXTRAS RODANDO!")
                    print("⚠️  Continue verificando as plataformas...")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n📊 RELATÓRIO FINAL:")
        print(f"• Conflitos detectados: {conflict_count > 0}")
        print(f"• Status atual: {'✅ Funcionando' if success_count > 0 else '❌ Em conflito'}")

def quick_platforms_check():
    """Lista rápida de plataformas para verificar"""
    print("\n🎯 VERIFICAÇÃO RÁPIDA DE PLATAFORMAS")
    print("=" * 50)
    
    platforms = [
        ("🚂 Railway", "https://railway.app/dashboard", "PRIORITÁRIO - Verifique múltiplos projetos"),
        ("🟣 Heroku", "https://dashboard.heroku.com/apps", "Procure apps ativas do bot"),
        ("🔵 Render", "https://dashboard.render.com/", "Verifique web services"),
        ("🟡 Replit", "https://replit.com/~", "Pare repls em execução")
    ]
    
    for name, url, action in platforms:
        print(f"{name}")
        print(f"   URL: {url}")
        print(f"   AÇÃO: {action}")
        print()

def main():
    """Função principal"""
    print("🚨 VERIFICAÇÃO URGENTE DE CONFLITO")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Verificação inicial
    print("1️⃣ Verificação inicial...")
    is_ok, status = check_bot_status()
    print(f"   Status: {status}")
    
    if not is_ok:
        print("\n❌ CONFLITO CONFIRMADO!")
        quick_platforms_check()
        print("🔄 Iniciando monitoramento contínuo...")
        print("   (O monitor parará automaticamente quando o conflito for resolvido)")
        print()
        monitor_conflict()
    else:
        print("\n✅ NENHUM CONFLITO DETECTADO!")
        print("✅ Bot parece estar funcionando normalmente")

if __name__ == "__main__":
    main() 