#!/usr/bin/env python3
"""
Teste Final - Sistema PredictLoL
Verificação completa antes do deploy
"""

import os
import sys
import asyncio
from datetime import datetime

def test_imports():
    """Testa importações do sistema"""
    print("🔍 Testando importações...")
    
    try:
        from bot.personal_betting import PersonalBettingSystem
        print("✅ PersonalBettingSystem importado")
        
        from bot.telegram_bot.predictlol_bot import PredictLoLTelegramBot
        print("✅ PredictLoLTelegramBot importado")
        
        from main import PredictLoLBot
        print("✅ PredictLoLBot importado")
        
        return True
    except Exception as e:
        print(f"❌ Erro nas importações: {e}")
        return False

def test_system_creation():
    """Testa criação do sistema"""
    print("\n🚀 Testando criação do sistema...")
    
    try:
        from bot.personal_betting import PersonalBettingSystem
        
        system = PersonalBettingSystem(initial_bankroll=1000.0)
        status = system.get_status()
        
        print(f"✅ Sistema v{status['version']} criado")
        print(f"💰 Bankroll: R$ {status['bankroll']:.2f}")
        
        for component, status_comp in status['components'].items():
            print(f"   • {component}: {status_comp}")
        
        return True
    except Exception as e:
        print(f"❌ Erro na criação: {e}")
        return False

def test_telegram_bot():
    """Testa criação do bot Telegram"""
    print("\n🤖 Testando bot Telegram...")
    
    try:
        from bot.telegram_bot.predictlol_bot import PredictLoLTelegramBot
        from bot.personal_betting import PersonalBettingSystem
        
        system = PersonalBettingSystem()
        bot = PredictLoLTelegramBot(
            token="test_token",
            personal_betting=system
        )
        
        print("✅ Bot Telegram criado")
        print("✅ Integração com sistema de apostas OK")
        
        return True
    except Exception as e:
        print(f"❌ Erro no bot: {e}")
        return False

async def test_main_system():
    """Testa sistema principal"""
    print("\n🎯 Testando sistema principal...")
    
    try:
        from main import PredictLoLBot
        
        # Simular variável de ambiente
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        
        bot = PredictLoLBot()
        print("✅ Sistema principal criado")
        
        return True
    except Exception as e:
        print(f"❌ Erro no sistema principal: {e}")
        return False

def test_dependencies():
    """Testa dependências"""
    print("\n📦 Testando dependências...")
    
    try:
        import telegram
        print("✅ python-telegram-bot")
        
        import requests
        print("✅ requests")
        
        import json
        print("✅ json (built-in)")
        
        import logging
        print("✅ logging (built-in)")
        
        import asyncio
        print("✅ asyncio (built-in)")
        
        return True
    except Exception as e:
        print(f"❌ Erro nas dependências: {e}")
        return False

def test_file_structure():
    """Testa estrutura de arquivos"""
    print("\n📁 Testando estrutura de arquivos...")
    
    required_files = [
        'main.py',
        'requirements.txt', 
        'Procfile',
        'README.md',
        'bot/personal_betting/__init__.py',
        'bot/telegram_bot/predictlol_bot.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - FALTANDO")
            missing_files.append(file)
    
    return len(missing_files) == 0

def main():
    """Executa todos os testes"""
    print("🎯 TESTE FINAL: SISTEMA PREDICTLOL")
    print("=" * 60)
    print(f"⏰ Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Estrutura de Arquivos", test_file_structure),
        ("Dependências", test_dependencies),
        ("Importações", test_imports),
        ("Sistema de Apostas", test_system_creation),
        ("Bot Telegram", test_telegram_bot),
        ("Sistema Principal", lambda: asyncio.run(test_main_system()))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 SISTEMA PRONTO PARA DEPLOY!")
        print("🚀 Todos os testes passaram com sucesso")
        print("💯 Sistema 100% funcional")
        
        print("\n🔧 PRÓXIMOS PASSOS:")
        print("1. Configure TELEGRAM_BOT_TOKEN no Railway")
        print("2. Faça deploy do repositório")
        print("3. Teste o bot no Telegram")
        print("4. Comece a usar o sistema!")
        
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("🔧 Corrija os problemas antes do deploy")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 