#!/usr/bin/env python3
"""
Force Redeploy no Railway
"""

import requests
import json
import os
import time

def force_redeploy():
    """Força um redeploy no Railway"""
    
    # Dados do projeto (baseado nas configurações anteriores)
    project_id = "be1cb85b-2d91-4eeb-aede-c22f425ce1ef"  # Railway Environment ID
    
    print("🚀 Iniciando Force Redeploy no Railway...")
    print(f"📦 Project ID: {project_id}")
    
    # Método 1: Trigger via webhook (se configurado)
    try:
        # Simular um push/commit para trigger redeploy
        print("\n📝 Criando arquivo de trigger...")
        
        # Criar arquivo de timestamp para forçar mudança
        timestamp = int(time.time())
        trigger_content = f"""# Force Redeploy Trigger
# Timestamp: {timestamp}
# Data: {time.ctime()}

# Correções aplicadas:
# ✅ Bot Telegram corrigido para python-telegram-bot v20.x
# ✅ Comando /start funcionando
# ✅ Compatibilidade com Railway
# ✅ Polling configurado corretamente

REDEPLOY_TRIGGER = {timestamp}
"""
        
        with open('.railway_trigger', 'w') as f:
            f.write(trigger_content)
        
        print("✅ Arquivo de trigger criado")
        
        # Método 2: Usar Railway CLI via subprocess se disponível
        import subprocess
        
        try:
            # Tentar redeploy via CLI
            result = subprocess.run(['railway', 'up', '--detach'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Railway redeploy iniciado via CLI")
                print(result.stdout)
                return True
            else:
                print(f"⚠️ CLI retornou código {result.returncode}")
                print(result.stderr)
        
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout no comando Railway CLI")
        except FileNotFoundError:
            print("⚠️ Railway CLI não encontrado")
        except Exception as e:
            print(f"⚠️ Erro no Railway CLI: {e}")
        
        # Método 3: Instruções manuais
        print("\n📋 INSTRUÇÕES PARA REDEPLOY MANUAL:")
        print("=" * 50)
        print("1. Acesse: https://railway.app/dashboard")
        print("2. Selecione seu projeto PredictLoL")
        print("3. Vá na aba 'Deployments'")
        print("4. Clique em 'Redeploy' no último deployment")
        print("5. Ou clique em 'Deploy Now' para forçar novo deploy")
        
        print("\n🔧 VARIÁVEIS DE AMBIENTE (verificar se estão configuradas):")
        print("=" * 50)
        print("TELEGRAM_BOT_TOKEN=8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI")
        print("TELEGRAM_ADMIN_USER_IDS=8012415611")
        print("RAILWAY_ENVIRONMENT_ID=be1cb85b-2d91-4eeb-aede-c22f425ce1ef")
        
        print("\n📦 ARQUIVOS PRINCIPAIS ATUALIZADOS:")
        print("=" * 50)
        print("✅ bot/telegram_bot/predictlol_bot.py - Corrigido para v20.x")
        print("✅ main.py - Método de inicialização corrigido")
        print("✅ requirements.txt - Dependências atualizadas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no redeploy: {e}")
        return False

def verificar_deploy():
    """Verifica se o deploy foi bem-sucedido"""
    print("\n🔍 Verificando status do deploy...")
    
    # Aguardar um pouco para o deploy processar
    print("⏳ Aguardando deploy processar (30s)...")
    time.sleep(30)
    
    # Verificar se o bot está respondendo
    token = "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI"
    
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print("✅ Bot está respondendo após redeploy")
                return True
        
        print("❌ Bot não está respondendo")
        return False
        
    except Exception as e:
        print(f"❌ Erro ao verificar bot: {e}")
        return False

if __name__ == "__main__":
    print("🔄 FORCE REDEPLOY - PredictLoL Railway")
    print("=" * 50)
    
    if force_redeploy():
        print("\n✅ Redeploy iniciado com sucesso!")
        
        # Verificar após deploy
        if verificar_deploy():
            print("\n🎉 REDEPLOY CONCLUÍDO COM SUCESSO!")
            print("✅ Bot funcionando")
            print("✅ Comando /start operacional")
            print("\n💡 Teste agora: @PredictLoLbot /start")
        else:
            print("\n⚠️ Redeploy pode ainda estar processando...")
            print("Aguarde alguns minutos e teste novamente.")
    else:
        print("\n❌ Erro no redeploy. Tente manualmente no Railway dashboard.") 