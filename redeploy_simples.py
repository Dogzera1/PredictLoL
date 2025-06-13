#!/usr/bin/env python3
"""
Redeploy simples no Railway
"""

import time
import subprocess
import sys

def criar_trigger():
    """Cria arquivo de trigger para forcar redeploy"""
    timestamp = int(time.time())
    
    trigger_content = f"""# Force Redeploy Trigger
# Timestamp: {timestamp}
# Data: {time.ctime()}

# Correcoes aplicadas:
# Bot Telegram corrigido para python-telegram-bot v20.x
# Comando /start funcionando
# Compatibilidade com Railway
# Polling configurado corretamente

REDEPLOY_TRIGGER = {timestamp}
"""
    
    try:
        with open('.railway_trigger', 'w', encoding='utf-8') as f:
            f.write(trigger_content)
        print("Arquivo de trigger criado")
        return True
    except Exception as e:
        print(f"Erro ao criar trigger: {e}")
        return False

def tentar_railway_cli():
    """Tenta usar Railway CLI"""
    try:
        print("Tentando Railway CLI...")
        result = subprocess.run(['railway', 'up', '--detach'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("Railway redeploy iniciado via CLI")
            print(result.stdout)
            return True
        else:
            print(f"CLI retornou codigo {result.returncode}")
            if result.stderr:
                print(f"Erro: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print("Timeout no comando Railway CLI")
        return False
    except FileNotFoundError:
        print("Railway CLI nao encontrado")
        return False
    except Exception as e:
        print(f"Erro no Railway CLI: {e}")
        return False

def main():
    print("FORCE REDEPLOY - PredictLoL Railway")
    print("=" * 50)
    
    # Criar arquivo de trigger
    if criar_trigger():
        print("Trigger criado com sucesso")
    
    # Tentar Railway CLI
    if tentar_railway_cli():
        print("\nRedeploy iniciado com sucesso!")
        print("Aguarde alguns minutos para o deploy completar.")
        print("Teste o bot: @PredictLoLbot /start")
        return
    
    # Instruções manuais
    print("\nINSTRUCOES PARA REDEPLOY MANUAL:")
    print("=" * 50)
    print("1. Acesse: https://railway.app/dashboard")
    print("2. Selecione seu projeto PredictLoL")
    print("3. Va na aba 'Deployments'")
    print("4. Clique em 'Redeploy' no ultimo deployment")
    print("5. Ou clique em 'Deploy Now' para forcar novo deploy")
    
    print("\nVARIAVEIS DE AMBIENTE (verificar se estao configuradas):")
    print("=" * 50)
    print("TELEGRAM_BOT_TOKEN=8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI")
    print("TELEGRAM_ADMIN_USER_IDS=8012415611")
    print("RAILWAY_ENVIRONMENT_ID=be1cb85b-2d91-4eeb-aede-c22f425ce1ef")
    
    print("\nARQUIVOS PRINCIPAIS ATUALIZADOS:")
    print("=" * 50)
    print("bot/telegram_bot/predictlol_bot.py - Corrigido para v20.x")
    print("main.py - Metodo de inicializacao corrigido")
    print("requirements.txt - Dependencias atualizadas")

if __name__ == "__main__":
    main() 