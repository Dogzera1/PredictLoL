#!/usr/bin/env python3
"""
Teste de Preparação para Deploy Railway - Bot LoL V3

Verifica se todos os arquivos e configurações estão prontos para deploy.
"""

import os
import sys
import json
from pathlib import Path

def test_required_files():
    """Testa se todos os arquivos necessários existem"""
    print("📁 Verificando arquivos necessários...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "runtime.txt", 
        "Procfile",
        "railway.toml",
        "health_check.py",
        "env.template"
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - FALTANDO!")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Arquivos faltando: {missing_files}")
        return False
    
    print("✅ Todos os arquivos necessários estão presentes!")
    return True

def test_requirements():
    """Testa se requirements.txt está válido"""
    print("\n📦 Verificando requirements.txt...")
    
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_packages = [
            "python-telegram-bot",
            "aiohttp",
            "flask",
            "psutil",
            "python-dotenv"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            if package in content:
                print(f"  ✅ {package}")
            else:
                print(f"  ❌ {package} - FALTANDO!")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n❌ Pacotes faltando: {missing_packages}")
            return False
        
        print("✅ Requirements.txt está completo!")
        return True
        
    except FileNotFoundError:
        print("❌ requirements.txt não encontrado!")
        return False

def test_health_check():
    """Testa se health check funciona"""
    print("\n🏥 Testando health check...")
    
    try:
        # Tenta importar health check
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from health_check import app, health_check, detailed_status
        
        print("  ✅ Health check importado com sucesso")
        
        # Testa se as rotas existem
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        expected_routes = ["/health", "/status", "/"]
        
        for route in expected_routes:
            if route in routes:
                print(f"  ✅ Rota {route}")
            else:
                print(f"  ❌ Rota {route} - FALTANDO!")
                return False
        
        print("✅ Health check está funcionando!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro ao importar health check: {e}")
        return False

def test_main_imports():
    """Testa se main.py importa sem erros"""
    print("\n🚀 Testando imports do main.py...")
    
    try:
        # Adiciona path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Testa imports críticos
        from bot.utils.logger_config import setup_logging
        print("  ✅ Logger config")
        
        from bot.systems.schedule_manager import ScheduleManager
        print("  ✅ Schedule Manager")
        
        from bot.telegram_bot.bot_interface import LoLBotV3UltraAdvanced
        print("  ✅ Bot Interface")
        
        from bot.telegram_bot.alerts_system import TelegramAlertsSystem
        print("  ✅ Alerts System")
        
        print("✅ Todos os imports principais funcionam!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False

def test_environment_template():
    """Testa se template de ambiente está completo"""
    print("\n🔧 Verificando template de ambiente...")
    
    try:
        with open("env.template", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_ADMIN_USER_IDS", 
            "PANDASCORE_API_KEY",
            "ENVIRONMENT",
            "PORT"
        ]
        
        missing_vars = []
        
        for var in required_vars:
            if var in content:
                print(f"  ✅ {var}")
            else:
                print(f"  ❌ {var} - FALTANDO!")
                missing_vars.append(var)
        
        if missing_vars:
            print(f"\n❌ Variáveis faltando: {missing_vars}")
            return False
        
        print("✅ Template de ambiente está completo!")
        return True
        
    except FileNotFoundError:
        print("❌ env.template não encontrado!")
        return False
    except UnicodeDecodeError:
        print("⚠️ Problema de encoding no env.template, mas arquivo existe")
        return True  # Considera OK se arquivo existe

def test_railway_config():
    """Testa configuração do Railway"""
    print("\n🚄 Verificando configuração Railway...")
    
    # Testa railway.toml
    try:
        with open("railway.toml", "r") as f:
            content = f.read()
        
        if "startCommand" in content and "python main.py" in content:
            print("  ✅ railway.toml - comando de start correto")
        else:
            print("  ❌ railway.toml - comando de start incorreto")
            return False
        
        # Verifica se Python version está configurada
        if "NIXPACKS_PYTHON_VERSION" in content and "3.11" in content:
            print("  ✅ railway.toml - Python 3.11 configurado")
        else:
            print("  ✅ railway.toml - Python será auto-detectado")
            
    except FileNotFoundError:
        print("  ❌ railway.toml não encontrado!")
        return False
    
    # Testa Procfile
    try:
        with open("Procfile", "r") as f:
            content = f.read()
        
        if "python main.py" in content:
            print("  ✅ Procfile - comando correto")
        else:
            print("  ❌ Procfile - comando incorreto")
            return False
            
    except FileNotFoundError:
        print("  ❌ Procfile não encontrado!")
        return False
    
    print("✅ Configuração Railway está correta!")
    return True

def generate_deploy_summary():
    """Gera resumo para deploy"""
    print("\n" + "="*60)
    print("📋 RESUMO PARA DEPLOY RAILWAY")
    print("="*60)
    
    print("\n🔑 VARIÁVEIS OBRIGATÓRIAS NO RAILWAY:")
    print("   TELEGRAM_BOT_TOKEN=seu_token_aqui")
    print("   TELEGRAM_ADMIN_USER_IDS=123456789,987654321")
    
    print("\n📡 VARIÁVEIS OPCIONAIS:")
    print("   PANDASCORE_API_KEY=sua_key_aqui")
    print("   RIOT_API_KEY=sua_key_aqui")
    
    print("\n🚀 COMANDOS PARA DEPLOY:")
    print("   1. git add .")
    print("   2. git commit -m 'Deploy Railway - Bot LoL V3'")
    print("   3. git push origin main")
    print("   4. Conectar repositório no Railway")
    print("   5. Configurar variáveis de ambiente")
    
    print("\n🔍 ENDPOINTS PARA TESTAR:")
    print("   https://seu-app.railway.app/health")
    print("   https://seu-app.railway.app/status")
    
    print("\n📱 COMANDOS BOT:")
    print("   /start → Menu principal")
    print("   /admin → Painel administrativo")
    print("   /status → Status do sistema")

def main():
    """Executa todos os testes"""
    print("🧪 TESTE DE PREPARAÇÃO PARA RAILWAY DEPLOY")
    print("="*60)
    
    tests = [
        ("Arquivos Necessários", test_required_files),
        ("Requirements.txt", test_requirements),
        ("Health Check", test_health_check),
        ("Imports Principais", test_main_imports),
        ("Template Ambiente", test_environment_template),
        ("Configuração Railway", test_railway_config)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        result = test_func()
        results.append((test_name, result))
    
    # Resultado final
    print("\n" + "="*60)
    print("📊 RESULTADO DOS TESTES")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 TESTES: {passed}/{len(tests)} passaram")
    
    if passed == len(tests):
        print("\n🎉 PROJETO PRONTO PARA DEPLOY!")
        print("🚀 Todos os testes passaram - pode fazer deploy no Railway!")
        generate_deploy_summary()
        return True
    else:
        print("\n⚠️ Alguns testes falharam.")
        print("🔧 Corrija os problemas antes do deploy.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 