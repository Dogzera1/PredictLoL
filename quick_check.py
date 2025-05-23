#!/usr/bin/env python3
"""
Quick check para ver se versão integrada foi deployed
"""
import requests
import json

# Nova URL
NEW_URL = "https://spectacular-wonder-production-4fb2.up.railway.app"

def check_version():
    """Verifica se é a versão integrada"""
    
    print("🔍 VERIFICANDO VERSÃO DEPLOYADA")
    print("=" * 40)
    
    try:
        # Verificar health endpoint
        health_response = requests.get(f"{NEW_URL}/health", timeout=10)
        print(f"💚 Health Status: {health_response.status_code}")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"📊 Health Data: {json.dumps(health_data, indent=2)}")
            
            # Verificar se tem as chaves da versão integrada
            if 'version' in health_data and 'prediction_system' in health_data:
                print("✅ VERSÃO INTEGRADA DETECTADA!")
                return True
        
        # Verificar root endpoint
        root_response = requests.get(NEW_URL, timeout=10)
        content = root_response.text
        
        if 'integrated' in content.lower() or 'prediction' in content.lower():
            print("✅ Palavras-chave da versão integrada encontradas!")
            return True
        else:
            print("⚠️ Ainda mostrando versão anterior")
            print(f"📄 Conteúdo: {content[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    is_integrated = check_version()
    
    if is_integrated:
        print("\n🎉 SUCESSO! Versão integrada deployada!")
    else:
        print("\n⏳ Aguardando deploy da versão integrada...") 