#!/usr/bin/env python3
"""
Verificação Final para Deploy Railway - Bot LoL V3
Script de validação completa antes do deploy
"""

import os
import sys
from pathlib import Path

def check_files():
    """Verifica arquivos essenciais"""
    print("📋 VERIFICANDO ARQUIVOS ESSENCIAIS...")
    
    required_files = [
        "main_railway.py",
        "simple_health_check.py", 
        "railway.toml",
        "requirements.txt",
        "bot/utils/constants.py",
        "bot/telegram_bot/alerts_system.py",
        "bot/systems/schedule_manager.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"   ✅ {file}")
    
    if missing_files:
        print(f"   ❌ Arquivos faltando: {missing_files}")
        return False
    
    print("   ✅ Todos os arquivos essenciais presentes!")
    return True

def check_imports():
    """Verifica imports críticos"""
    print("\n🔧 VERIFICANDO IMPORTS CRÍTICOS...")
    
    try:
        # Teste do constants.py
        from bot.utils.constants import TELEGRAM_ADMIN_USER_IDS, TELEGRAM_BOT_TOKEN
        print("   ✅ Constants.py - TELEGRAM_ADMIN_USER_IDS OK")
        
        # Teste do alerts_system
        from bot.telegram_bot.alerts_system import TelegramAlertsSystem
        print("   ✅ TelegramAlertsSystem OK")
        
        # Teste do schedule_manager  
        from bot.systems.schedule_manager import ScheduleManager
        print("   ✅ ScheduleManager OK")
        
        # Teste do health check
        from simple_health_check import app
        print("   ✅ SimpleHealthCheck OK")
        
        print("   ✅ Todos os imports funcionando!")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro de import: {e}")
        return False

def check_environment():
    """Verifica variáveis de ambiente"""
    print("\n🌍 VERIFICANDO VARIÁVEIS DE AMBIENTE...")
    
    required_vars = {
        "TELEGRAM_BOT_TOKEN": "Token do bot Telegram",
        "TELEGRAM_ADMIN_USER_IDS": "IDs dos administradores"
    }
    
    all_ok = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {description} ({'*' * (len(value)-4) + value[-4:] if len(value) > 4 else '***'})")
        else:
            print(f"   ⚠️ {var}: {description} - NÃO CONFIGURADA (será necessária no Railway)")
            all_ok = False
    
    # Variáveis opcionais
    optional_vars = {
        "PORT": os.getenv("PORT", "5000"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "production"),
        "RAILWAY_ENVIRONMENT_ID": os.getenv("RAILWAY_ENVIRONMENT_ID", "não definida")
    }
    
    print("\n   📋 Variáveis opcionais:")
    for var, value in optional_vars.items():
        print(f"      {var}: {value}")
    
    return all_ok

def check_railway_config():
    """Verifica configuração do Railway"""
    print("\n🚂 VERIFICANDO CONFIGURAÇÃO RAILWAY...")
    
    try:
        with open("railway.toml", "r") as f:
            content = f.read()
        
        checks = {
            "startCommand = \"python main_railway.py\"": "Comando de início correto",
            "healthcheckPath = \"/health\"": "Health check configurado",
            "numReplicas = 1": "Instância única configurada",
            "ENVIRONMENT = \"production\"": "Ambiente de produção"
        }
        
        all_ok = True
        for check, description in checks.items():
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - NÃO ENCONTRADO")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"   ❌ Erro ao ler railway.toml: {e}")
        return False

def final_summary(file_ok, import_ok, env_ok, railway_ok):
    """Resumo final"""
    print("\n" + "="*60)
    print("📊 RESUMO FINAL DA VERIFICAÇÃO")
    print("="*60)
    
    total_checks = 4
    passed_checks = sum([file_ok, import_ok, env_ok, railway_ok])
    
    status_emoji = "✅" if passed_checks == total_checks else "⚠️"
    
    print(f"\n{status_emoji} **RESULTADO GERAL: {passed_checks}/{total_checks} verificações passaram**")
    
    print(f"\n📋 **DETALHES:**")
    print(f"   {'✅' if file_ok else '❌'} Arquivos Essenciais")
    print(f"   {'✅' if import_ok else '❌'} Imports Críticos") 
    print(f"   {'✅' if env_ok else '⚠️'} Variáveis de Ambiente")
    print(f"   {'✅' if railway_ok else '❌'} Configuração Railway")
    
    if passed_checks == total_checks:
        print(f"\n🎉 **SISTEMA PRONTO PARA DEPLOY!**")
        print(f"✅ Todos os componentes verificados")
        print(f"🚀 Pode fazer deploy no Railway com segurança")
        
        print(f"\n📋 **PRÓXIMOS PASSOS:**")
        print(f"   1. git push origin main")
        print(f"   2. Conectar repositório no Railway")
        print(f"   3. Configurar variáveis TELEGRAM no Railway:")
        print(f"      - TELEGRAM_BOT_TOKEN=seu_token")
        print(f"      - TELEGRAM_ADMIN_USER_IDS=8012415611")
        print(f"   4. Aguardar deploy e testar /health endpoint")
        
    else:
        print(f"\n⚠️ **DEPLOY COM PROBLEMAS**")
        print(f"🔧 Corrija os itens marcados com ❌ antes do deploy")
        
        if not import_ok:
            print(f"   • Verifique imports no código")
        if not file_ok:
            print(f"   • Verifique arquivos faltando")
        if not railway_ok:
            print(f"   • Verifique railway.toml")

def main():
    """Função principal"""
    print("🔍 VERIFICAÇÃO FINAL PARA RAILWAY DEPLOY")
    print("🤖 Bot LoL V3 Ultra Avançado")
    print("="*60)
    
    # Executa verificações
    file_ok = check_files()
    import_ok = check_imports()
    env_ok = check_environment()
    railway_ok = check_railway_config()
    
    # Resumo final
    final_summary(file_ok, import_ok, env_ok, railway_ok)

if __name__ == "__main__":
    main() 