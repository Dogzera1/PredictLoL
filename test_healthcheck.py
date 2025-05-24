#!/usr/bin/env python3
"""
Teste do sistema de healthcheck do Bot LoL V3
"""

import requests
import time
import sys
import os

def test_healthcheck():
    """Testa o endpoint de healthcheck"""
    url = "http://localhost:5000/health"
    
    print("🔍 Testando healthcheck do Bot LoL V3...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Healthcheck PASSOU - Bot está saudável!")
            return True
        elif response.status_code == 503:
            print("⚠️ Healthcheck FALHOU - Bot não está saudável")
            return False
        else:
            print(f"❌ Status inesperado: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao healthcheck endpoint")
        print("   Verifique se o bot está rodando na porta 5000")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_status_endpoint():
    """Testa o endpoint de status detalhado"""
    url = "http://localhost:5000/status"
    
    print("\n🔍 Testando status endpoint...")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Status endpoint funcionando!")
            print(f"   Bot: {data.get('bot_name', 'Unknown')}")
            print(f"   Versão: {data.get('version', 'Unknown')}")
            print(f"   Saudável: {data.get('healthy', False)}")
            print(f"   Uptime: {data.get('uptime', 0):.2f} segundos")
            return True
        else:
            print(f"❌ Status endpoint falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no status endpoint: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 TESTE DE HEALTHCHECK - Bot LoL V3 Ultra Avançado")
    print("=" * 60)
    
    # Verificar se Flask está disponível
    try:
        import flask
        print("✅ Flask disponível")
    except ImportError:
        print("❌ Flask não encontrado - instale com: pip install flask")
        return False
    
    # Teste 1: Healthcheck
    health_ok = test_healthcheck()
    
    # Teste 2: Status endpoint
    status_ok = test_status_endpoint()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES:")
    print(f"Healthcheck: {'✅ PASSOU' if health_ok else '❌ FALHOU'}")
    print(f"Status:      {'✅ PASSOU' if status_ok else '❌ FALHOU'}")
    
    if health_ok and status_ok:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   O bot está pronto para container com healthcheck")
        return True
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM")
        print("   Verifique se o bot está rodando corretamente")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 