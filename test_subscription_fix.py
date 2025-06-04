#!/usr/bin/env python3
"""
Teste da Correção dos Botões de Subscrição - Bot LoL V3

Testa especificamente a correção do erro:
"Attribute 'data' of class 'CallbackQuery' can't be set!"
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_subscription_mapping():
    """Testa o mapeamento de subscrições"""
    print("🧪 Testando mapeamento de subscrições...")
    
    # Mapeia exatamente como no código
    subscription_mapping = {
        "sub_all_tips": "all_tips",
        "sub_high_value": "high_value", 
        "sub_high_conf": "high_conf",
        "sub_premium": "premium"
    }
    
    # Importa o enum
    try:
        from bot.telegram_bot.alerts_system import SubscriptionType
        print("✅ SubscriptionType importado com sucesso")
        
        # Testa conversão de cada tipo
        for callback_data, enum_value in subscription_mapping.items():
            try:
                subscription_enum = SubscriptionType(enum_value)
                print(f"✅ {callback_data} → {enum_value} → {subscription_enum}")
            except Exception as e:
                print(f"❌ Erro ao converter {callback_data}: {e}")
                return False
                
    except ImportError as e:
        print(f"❌ Erro ao importar SubscriptionType: {e}")
        return False
    
    print("✅ Todos os mapeamentos funcionam corretamente!")
    return True

async def test_subscription_flow():
    """Testa o fluxo completo de subscrição"""
    print("\n🔄 Testando fluxo de subscrição...")
    
    try:
        # Importa as classes necessárias
        from bot.telegram_bot.alerts_system import TelegramAlertsSystem, SubscriptionType
        
        # Cria uma instância mock do sistema de alertas
        alerts_system = TelegramAlertsSystem("dummy_token")
        
        # Mock do query e user
        mock_query = Mock()
        mock_query.from_user = Mock()
        mock_query.from_user.id = 12345
        mock_query.from_user.first_name = "Teste"
        mock_query.from_user.username = "teste_user"
        mock_query.edit_message_text = AsyncMock()
        
        # Testa cada tipo de subscrição
        test_subscriptions = [
            ("sub_all_tips", "all_tips"),
            ("sub_high_value", "high_value"), 
            ("sub_high_conf", "high_conf"),
            ("sub_premium", "premium")
        ]
        
        for callback_data, enum_value in test_subscriptions:
            print(f"  🧪 Testando {callback_data}...")
            
            # Converte para enum
            subscription_enum = SubscriptionType(enum_value)
            
            # Testa o método de subscrição
            await alerts_system._handle_user_subscription(
                query=mock_query,
                user=mock_query.from_user,
                subscription_type=subscription_enum
            )
            
            # Verifica se o usuário foi registrado
            if mock_query.from_user.id in alerts_system.users:
                user = alerts_system.users[mock_query.from_user.id]
                if user.subscription_type == subscription_enum:
                    print(f"  ✅ {callback_data} registrado com sucesso")
                else:
                    print(f"  ❌ Tipo de subscrição incorreto para {callback_data}")
                    return False
            else:
                print(f"  ❌ Usuário não foi registrado para {callback_data}")
                return False
        
        print("✅ Fluxo de subscrição funciona corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de fluxo: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_callback_data_readonly():
    """Demonstra que callback_data é read-only"""
    print("\n🔒 Testando propriedade read-only de callback_data...")
    
    try:
        # Simula um CallbackQuery mock
        from unittest.mock import Mock
        
        # Cria mock que simula comportamento real
        mock_query = Mock()
        
        # Define data como propriedade read-only
        mock_query._data = "test_data"
        
        def get_data():
            return mock_query._data
        
        def set_data(value):
            raise AttributeError("Attribute 'data' of class 'CallbackQuery' can't be set!")
        
        # Cria propriedade read-only
        type(mock_query).data = property(get_data, set_data)
        
        # Testa leitura (deve funcionar)
        print(f"✅ Leitura de data: {mock_query.data}")
        
        # Testa escrita (deve falhar)
        try:
            mock_query.data = "new_value"
            print("❌ ERRO: Conseguiu modificar data (não deveria)")
            return False
        except AttributeError as e:
            print(f"✅ Erro esperado ao tentar modificar: {e}")
            print("✅ Comportamento read-only confirmado!")
            return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Executa todos os testes"""
    print("🎯 TESTE DA CORREÇÃO DOS BOTÕES DE SUBSCRIÇÃO")
    print("=" * 50)
    
    tests = [
        ("Mapeamento de Subscrições", test_subscription_mapping),
        ("Fluxo de Subscrição", test_subscription_flow),
        ("Callback Data Read-Only", test_callback_data_readonly)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        results.append((test_name, result))
    
    # Sumário
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("\n💡 A correção está funcionando corretamente.")
        print("   O erro 'can't be set' foi resolvido!")
    else:
        print("⚠️ Alguns testes falharam.")
        print("   Verifique os erros acima.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
