#!/usr/bin/env python3
"""
🧪 TESTE FINAL: Bot Interface Corrigido com Token Válido
Verifica se o problema do NoneType foi resolvido
"""

import os
import asyncio
import sys
import time
from datetime import datetime

# Adiciona o diretório do projeto ao path
sys.path.append('.')

# Mock básico para testes
class MockScheduleManager:
    """Mock do ScheduleManager para testes"""
    def __init__(self):
        self.tips_system = None
        self.telegram_alerts = MockTelegramAlerts()
        self.pandascore_client = None
        self.riot_client = None
    
    async def start_scheduled_tasks(self):
        print("📋 Mock ScheduleManager rodando...")
        await asyncio.sleep(5)  # Simula execução

class MockTelegramAlerts:
    """Mock do TelegramAlertsSystem"""
    def __init__(self):
        self.users = {}

def test_header():
    print("🧪 TESTE FINAL: Bot Interface Corrigido")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🎯 Objetivo: Verificar correções do NoneType")
    print(f"🔑 Token Válido: {token[:25]}...")
    print("")

async def test_bot_initialization():
    """Teste 1: Inicialização do LoLBotV3UltraAdvanced"""
    print("1️⃣ TESTE: Inicialização da Interface")
    print("-" * 40)
    
    try:
        # Mock do schedule manager
        mock_schedule = MockScheduleManager()
        
        # Importa após mock estar pronto
        from bot.telegram_bot.bot_interface import LoLBotV3UltraAdvanced
        
        # Tenta inicializar com token válido
        bot_interface = LoLBotV3UltraAdvanced(
            bot_token=token,
            schedule_manager=mock_schedule,
            admin_user_ids=[8012415611]
        )
        
        # Verifica se application foi criada
        if bot_interface.application is None:
            print("❌ FALHA: Application ainda é None")
            return False
        
        print("✅ SUCESSO: LoLBotV3UltraAdvanced criado")
        print(f"✅ Application: {type(bot_interface.application).__name__}")
        print(f"✅ Handlers configurados: {bot_interface.handlers_configured}")
        print(f"✅ Token válido: {bot_interface.bot_token[:25]}...")
        
        return True, bot_interface
        
    except Exception as e:
        print(f"❌ ERRO na inicialização: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_application_methods():
    """Teste 2: Métodos da Application"""
    print("\n2️⃣ TESTE: Métodos da Application")
    print("-" * 40)
    
    try:
        success, bot_interface = await test_bot_initialization()
        if not success:
            return False
        
        # Testa se método initialize existe
        if hasattr(bot_interface.application, 'initialize'):
            print("✅ Método 'initialize' existe")
        else:
            print("❌ Método 'initialize' não existe")
            return False
        
        # Testa se método start existe
        if hasattr(bot_interface.application, 'start'):
            print("✅ Método 'start' existe")
        else:
            print("❌ Método 'start' não existe")
            return False
        
        # Testa se bot token está correto
        if bot_interface.application.bot.token == token:
            print("✅ Token na application está correto")
        else:
            print("❌ Token na application está incorreto")
            return False
        
        print("✅ SUCESSO: Todos os métodos estão disponíveis")
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao testar methods: {e}")
        return False

def test_webhook_configuration():
    """Teste 3: Configuração de Webhook"""
    print("\n3️⃣ TESTE: Configuração de Webhook")
    print("-" * 40)
    
    try:
        import requests
        
        # Verifica se bot responde
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()['result']
            print(f"✅ Bot respondendo: {bot_info['first_name']}")
            print(f"✅ Username: @{bot_info['username']}")
            print(f"✅ Can join groups: {bot_info.get('can_join_groups', False)}")
            print(f"✅ Can read all messages: {bot_info.get('can_read_all_group_messages', False)}")
            
            # Testa webhook
            webhook_url = "https://predictlol-production.up.railway.app/webhook"
            webhook_response = requests.post(
                f'https://api.telegram.org/bot{token}/setWebhook',
                json={'url': webhook_url},
                timeout=10
            )
            
            if webhook_response.status_code == 200:
                print(f"✅ Webhook configurado: {webhook_url}")
                return True
            else:
                print(f"❌ Erro ao configurar webhook: {webhook_response.status_code}")
                return False
                
        else:
            print(f"❌ Bot não responde: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO no teste webhook: {e}")
        return False

async def test_command_handlers():
    """Teste 4: Handlers de Comandos"""
    print("\n4️⃣ TESTE: Command Handlers")
    print("-" * 40)
    
    try:
        success, bot_interface = await test_bot_initialization()
        if not success:
            return False
        
        # Lista de comandos que devem existir
        expected_commands = [
            'start', 'help', 'status', 'stats', 'subscribe', 
            'unsubscribe', 'mystats', 'activate_group', 
            'admin', 'system', 'force', 'health'
        ]
        
        # Verifica se handlers foram adicionados
        handlers_count = len(bot_interface.application.handlers[0])  # Default group
        print(f"✅ Total de handlers: {handlers_count}")
        
        # Verifica handlers específicos (aproximado)
        if handlers_count >= len(expected_commands):
            print("✅ Quantidade suficiente de handlers")
            print("✅ Handlers provavelmente configurados corretamente")
            return True
        else:
            print(f"❌ Poucos handlers: esperado >= {len(expected_commands)}, encontrado {handlers_count}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO ao testar handlers: {e}")
        return False

async def run_all_tests():
    """Executa todos os testes"""
    print("🚀 INICIANDO BATERIA DE TESTES")
    print("=" * 60)
    
    tests = [
        ("Inicialização", test_bot_initialization),
        ("Application Methods", test_application_methods), 
        ("Webhook Config", test_webhook_configuration),
        ("Command Handlers", test_command_handlers)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 EXECUTANDO: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results.append((test_name, result))
            print(f"{'✅ PASSOU' if result else '❌ FALHOU'}: {test_name}")
            
        except Exception as e:
            print(f"❌ ERRO em {test_name}: {e}")
            results.append((test_name, False))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Bot interface corrigido e funcional")
        print("🚀 Problema do NoneType resolvido")
    else:
        print("⚠️ Alguns testes falharam")
        print("🔧 Correções adicionais podem ser necessárias")

# Configuração
token = "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0"

if __name__ == "__main__":
    test_header()
    asyncio.run(run_all_tests()) 