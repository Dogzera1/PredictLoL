#!/usr/bin/env python3
"""
Diagnóstico específico para Railway
"""

import os
import sys
import time
import requests
from datetime import datetime

def check_environment():
    """Verifica variáveis de ambiente"""
    print("🔍 VERIFICAÇÃO DE AMBIENTE")
    print("=" * 50)
    
    required_vars = ['TELEGRAM_TOKEN', 'PORT']
    optional_vars = ['RAILWAY_ENVIRONMENT_NAME', 'RAILWAY_STATIC_URL', 'RAILWAY_SERVICE_NAME']
    
    print("📋 Variáveis obrigatórias:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: NÃO DEFINIDA")
    
    print("\n📋 Variáveis do Railway:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ⚠️ {var}: Não definida")
    
    # Verificar se é ambiente Railway
    is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT_NAME')) or bool(os.getenv('RAILWAY_STATIC_URL'))
    print(f"\n🚀 Ambiente Railway detectado: {is_railway}")
    
    return is_railway

def check_dependencies():
    """Verifica dependências"""
    print("\n📦 VERIFICAÇÃO DE DEPENDÊNCIAS")
    print("=" * 50)
    
    dependencies = [
        'flask',
        'telegram',
        'requests',
        'aiohttp',
        'numpy'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}: OK")
        except ImportError as e:
            print(f"  ❌ {dep}: ERRO - {e}")

def check_flask_app():
    """Verifica Flask app"""
    print("\n🌐 VERIFICAÇÃO FLASK APP")
    print("=" * 50)
    
    try:
        # Importar sem executar
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Simular variáveis se necessário
        if not os.getenv('TELEGRAM_TOKEN'):
            os.environ['TELEGRAM_TOKEN'] = '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg'
        if not os.getenv('PORT'):
            os.environ['PORT'] = '5800'
        
        from bot_v13_railway import app, PORT
        
        print(f"  ✅ Flask app importado")
        print(f"  ✅ Porta configurada: {PORT}")
        
        # Testar rotas
        with app.test_client() as client:
            # Teste /health
            response = client.get('/health')
            if response.status_code == 200:
                print(f"  ✅ /health: Status {response.status_code}")
                data = response.get_json()
                if data and data.get('status') == 'healthy':
                    print(f"  ✅ Health check retorna 'healthy'")
                else:
                    print(f"  ⚠️ Health check não retorna 'healthy': {data}")
            else:
                print(f"  ❌ /health: Status {response.status_code}")
            
            # Teste /ping
            response = client.get('/ping')
            if response.status_code == 200:
                print(f"  ✅ /ping: Status {response.status_code}")
            else:
                print(f"  ❌ /ping: Status {response.status_code}")
            
            # Teste /
            response = client.get('/')
            if response.status_code == 200:
                print(f"  ✅ /: Status {response.status_code}")
            else:
                print(f"  ❌ /: Status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao verificar Flask: {e}")
        import traceback
        print(f"  📋 Traceback: {traceback.format_exc()}")
        return False

def check_railway_config():
    """Verifica configuração específica do Railway"""
    print("\n🚀 VERIFICAÇÃO CONFIGURAÇÃO RAILWAY")
    print("=" * 50)
    
    # Verificar arquivos de configuração
    config_files = ['railway.json', 'nixpacks.toml', 'requirements.txt', 'Procfile']
    
    for file in config_files:
        if os.path.exists(file):
            print(f"  ✅ {file}: Existe")
            
            # Verificar conteúdo específico
            if file == 'railway.json':
                try:
                    import json
                    with open(file, 'r') as f:
                        config = json.load(f)
                    
                    if 'deploy' in config and 'healthcheckPath' in config['deploy']:
                        health_path = config['deploy']['healthcheckPath']
                        print(f"    📋 Health check path: {health_path}")
                    
                    if 'deploy' in config and 'healthcheckTimeout' in config['deploy']:
                        timeout = config['deploy']['healthcheckTimeout']
                        print(f"    📋 Health check timeout: {timeout}s")
                        
                except Exception as e:
                    print(f"    ⚠️ Erro ao ler {file}: {e}")
            
            elif file == 'requirements.txt':
                try:
                    with open(file, 'r') as f:
                        deps = f.read().strip().split('\n')
                    print(f"    📋 Dependências: {len(deps)} encontradas")
                except Exception as e:
                    print(f"    ⚠️ Erro ao ler {file}: {e}")
        else:
            print(f"  ⚠️ {file}: Não existe")

def generate_railway_tips():
    """Gera dicas para resolver problemas no Railway"""
    print("\n💡 DICAS PARA RAILWAY")
    print("=" * 50)
    
    print("🔧 Se o health check falhar:")
    print("  1. Verifique se a porta 5800 está correta")
    print("  2. Confirme que TELEGRAM_TOKEN está definido")
    print("  3. Verifique logs do Railway para erros de importação")
    print("  4. Teste localmente: python bot_v13_railway.py")
    print("  5. Acesse manualmente: https://SEU_DOMINIO.railway.app/health")
    
    print("\n🚀 Configurações recomendadas no Railway:")
    print("  • PORT=5800")
    print("  • TELEGRAM_TOKEN=seu_token")
    print("  • Health check path: /health")
    print("  • Health check timeout: 300s")
    print("  • Start command: python bot_v13_railway.py")
    
    print("\n🔍 Para debug:")
    print("  • Verifique logs em tempo real no Railway")
    print("  • Teste endpoints manualmente")
    print("  • Confirme que todas as dependências estão instaladas")

if __name__ == "__main__":
    print("🎮 DIAGNÓSTICO RAILWAY - BOT LOL V3")
    print("=" * 60)
    print(f"🕒 Executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Executar verificações
    is_railway = check_environment()
    check_dependencies()
    flask_ok = check_flask_app()
    check_railway_config()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DO DIAGNÓSTICO:")
    print(f"🌐 Flask App: {'✅ OK' if flask_ok else '❌ PROBLEMA'}")
    print(f"🚀 Ambiente Railway: {'✅ Detectado' if is_railway else '⚠️ Local'}")
    
    if flask_ok:
        print("\n🎉 FLASK ESTÁ FUNCIONANDO!")
        print("✅ Health check deve funcionar no Railway")
        print("🔧 Se ainda falhar, verifique variáveis de ambiente no Railway")
    else:
        print("\n💥 PROBLEMAS DETECTADOS!")
        print("🔧 Corrija os erros acima antes de fazer deploy")
    
    generate_railway_tips() 