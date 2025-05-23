#!/usr/bin/env python3
"""
Script para monitorar status do deploy no Railway
Verifica periodicamente se o auto-deploy foi ativado
"""

import requests
import time
import json
from datetime import datetime

# URLs para monitorar
HEALTH_URL = "https://betlolgpt-bot-production.up.railway.app/health"
ROOT_URL = "https://betlolgpt-bot-production.up.railway.app/"

def check_endpoint(url, name):
    """Verifica um endpoint específico"""
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        
        if status_code == 200:
            try:
                data = response.json()
                return {"status": "success", "code": status_code, "data": data}
            except:
                return {"status": "success", "code": status_code, "data": response.text}
        else:
            return {"status": "error", "code": status_code, "data": response.text}
            
    except requests.exceptions.RequestException as e:
        return {"status": "connection_error", "error": str(e)}

def monitor_deployment():
    """Monitora o status do deployment"""
    
    print("🔍 MONITORANDO DEPLOY DO RAILWAY")
    print("=" * 50)
    
    check_count = 0
    last_status = None
    
    while check_count < 20:  # Máximo 20 checks (10 minutos)
        check_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] Check #{check_count}")
        
        # Verificar health endpoint
        health_result = check_endpoint(HEALTH_URL, "health")
        print(f"🏥 Health: {health_result['status']} ({health_result.get('code', 'N/A')})")
        
        # Verificar root endpoint
        root_result = check_endpoint(ROOT_URL, "root")
        print(f"🏠 Root: {root_result['status']} ({root_result.get('code', 'N/A')})")
        
        # Analisar mudanças
        current_status = {
            "health": health_result,
            "root": root_result
        }
        
        if last_status is None:
            print("📝 Status inicial capturado")
        elif current_status != last_status:
            print("🚨 MUDANÇA DETECTADA!")
            print(f"   Health: {last_status['health']['status']} → {health_result['status']}")
            print(f"   Root: {last_status['root']['status']} → {root_result['status']}")
        
        # Verificar se deploy foi bem-sucedido
        if health_result['status'] == 'success' and 'version' in str(health_result.get('data', '')):
            print("✅ DEPLOY DETECTADO - Bot atualizado!")
            
            if 'data' in health_result and isinstance(health_result['data'], dict):
                version = health_result['data'].get('version', 'unknown')
                print(f"🚀 Nova versão: {version}")
            
            break
        
        last_status = current_status
        
        # Aguardar antes do próximo check
        if check_count < 20:
            print("⏳ Aguardando 30 segundos...")
            time.sleep(30)
    
    print(f"\n📊 Monitoramento concluído após {check_count} checks")

if __name__ == "__main__":
    monitor_deployment() 