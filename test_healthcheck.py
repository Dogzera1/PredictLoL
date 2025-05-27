#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Health Check
Verifica se o endpoint /health está funcionando corretamente
"""

import requests
import time
import threading
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_health_endpoint():
    """Testa o endpoint /health"""
    print("🏥 TESTE DO HEALTH CHECK")
    print("=" * 40)
    
    try:
        # Importar e iniciar o Flask app
        from bot_v13_railway import app, PORT
        print(f"✅ Flask app importado, porta: {PORT}")
        
        # Iniciar servidor em thread separada
        def run_server():
            app.run(host='0.0.0.0', port=PORT, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        print("🌐 Servidor Flask iniciado em thread separada")
        
        # Aguardar servidor iniciar
        time.sleep(3)
        
        # Testar endpoint /health
        print("\n🔍 Testando endpoint /health...")
        try:
            response = requests.get(f'http://localhost:{PORT}/health', timeout=10)
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Health check respondeu com sucesso!")
                print(f"📋 Resposta: {data}")
                
                # Verificar campos obrigatórios
                required_fields = ['status', 'timestamp', 'service']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    print("✅ Todos os campos obrigatórios presentes")
                    return True
                else:
                    print(f"❌ Campos faltando: {missing_fields}")
                    return False
            else:
                print(f"❌ Health check falhou com status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def test_root_endpoint():
    """Testa o endpoint raiz /"""
    print("\n🏠 TESTE DO ENDPOINT RAIZ")
    print("=" * 40)
    
    try:
        from bot_v13_railway import PORT
        
        print("🔍 Testando endpoint /...")
        response = requests.get(f'http://localhost:{PORT}/', timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint raiz respondeu com sucesso!")
            print(f"📋 Resposta: {data}")
            return True
        else:
            print(f"❌ Endpoint raiz falhou com status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal"""
    print("🏥 TESTE COMPLETO DO HEALTH CHECK")
    print("🕒 Iniciado em:", time.strftime('%d/%m/%Y %H:%M:%S'))
    print()
    
    # Teste 1: Health check
    health_ok = test_health_endpoint()
    
    # Teste 2: Endpoint raiz
    root_ok = test_root_endpoint()
    
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES:")
    print(f"✅ Health Check: {'OK' if health_ok else 'FALHOU'}")
    print(f"✅ Endpoint Raiz: {'OK' if root_ok else 'FALHOU'}")
    
    if health_ok and root_ok:
        print("\n🎯 HEALTH CHECK FUNCIONANDO PERFEITAMENTE!")
        print("✅ O Railway pode fazer health check do bot")
        print("✅ Endpoints /health e / estão respondendo")
        print("✅ JSON válido sendo retornado")
    else:
        print("\n⚠️ Alguns testes falharam")
        print("🔧 Verifique se:")
        print("   • O Flask está configurado corretamente")
        print("   • A porta está disponível")
        print("   • Não há conflitos de dependências")
    
    return health_ok and root_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 