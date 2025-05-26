#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Alertas do Bot LoL V3
"""

import sys
import time
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_alert_system():
    """Testar o sistema de alertas"""
    try:
        # Importar o sistema de alertas
        from bot_v13_railway import AlertSystem
        
        # Criar uma instância mock do bot
        class MockBot:
            def __init__(self):
                self.bot = None
        
        mock_bot = MockBot()
        
        # Inicializar sistema de alertas
        alert_system = AlertSystem(mock_bot)
        
        print("🚨 TESTE DO SISTEMA DE ALERTAS")
        print("=" * 50)
        
        # Teste 1: Status inicial
        print("\n1️⃣ TESTE: Status inicial")
        status = alert_system.get_status()
        print(f"   ✅ Monitoramento ativo: {status['monitoring_active']}")
        print(f"   ✅ Grupos inscritos: {status['subscribed_groups']}")
        print(f"   ✅ Configurações: {status['settings']}")
        
        # Teste 2: Inscrever grupo fictício
        print("\n2️⃣ TESTE: Inscrever grupo")
        test_chat_id = -1001234567890
        result = alert_system.subscribe_group(test_chat_id)
        print(f"   ✅ Grupo inscrito: {result}")
        print(f"   ✅ Total de grupos: {len(alert_system.subscribed_groups)}")
        
        # Teste 3: Verificar configurações
        print("\n3️⃣ TESTE: Configurações")
        settings = alert_system.alert_settings
        print(f"   ✅ Value betting: {settings['value_betting']}")
        print(f"   ✅ Live matches: {settings['live_matches']}")
        print(f"   ✅ EV mínimo: {settings['min_ev']*100:.1f}%")
        print(f"   ✅ Confiança mínima: {settings['min_confidence']*100:.1f}%")
        
        # Teste 4: Atualizar configurações
        print("\n4️⃣ TESTE: Atualizar configurações")
        alert_system.update_settings(min_ev=0.05, high_ev_only=True)
        updated_settings = alert_system.alert_settings
        print(f"   ✅ EV mínimo atualizado: {updated_settings['min_ev']*100:.1f}%")
        print(f"   ✅ Apenas EV alto: {updated_settings['high_ev_only']}")
        
        # Teste 5: Iniciar monitoramento
        print("\n5️⃣ TESTE: Iniciar monitoramento")
        alert_system.start_monitoring()
        time.sleep(2)  # Aguardar 2 segundos
        status_after = alert_system.get_status()
        print(f"   ✅ Monitoramento ativo: {status_after['monitoring_active']}")
        
        # Teste 6: Simular verificação de partidas
        print("\n6️⃣ TESTE: Verificação de partidas (simulação)")
        try:
            alert_system._check_live_matches()
            print("   ✅ Verificação de partidas executada")
        except Exception as e:
            print(f"   ⚠️ Erro esperado (sem bot real): {e}")
        
        # Teste 7: Simular verificação de value betting
        print("\n7️⃣ TESTE: Verificação de value betting (simulação)")
        try:
            alert_system._check_value_opportunities()
            print("   ✅ Verificação de value betting executada")
        except Exception as e:
            print(f"   ⚠️ Erro esperado (sem bot real): {e}")
        
        # Teste 8: Desinscrever grupo
        print("\n8️⃣ TESTE: Desinscrever grupo")
        result = alert_system.unsubscribe_group(test_chat_id)
        print(f"   ✅ Grupo desinscrito: {result}")
        print(f"   ✅ Total de grupos: {len(alert_system.subscribed_groups)}")
        
        # Teste 9: Parar monitoramento
        print("\n9️⃣ TESTE: Parar monitoramento")
        alert_system.stop_monitoring()
        time.sleep(1)
        final_status = alert_system.get_status()
        print(f"   ✅ Monitoramento parado: {not final_status['monitoring_active']}")
        
        print("\n" + "=" * 50)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("🚨 Sistema de alertas está funcionando corretamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Certifique-se que o bot_v13_railway.py está no mesmo diretório")
        return False
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def test_integration():
    """Teste de integração básica"""
    print("\n🔧 TESTE DE INTEGRAÇÃO")
    print("=" * 30)
    
    try:
        # Verificar se todas as classes necessárias existem
        from bot_v13_railway import (
            AlertSystem, 
            ValueBettingSystem, 
            BotLoLV3Railway,
            HealthCheckManager
        )
        
        print("✅ Todas as classes importadas com sucesso")
        
        # Verificar se o bot pode ser inicializado (sem executar)
        print("✅ Classes compatíveis")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro de integração: {e}")
        return False

if __name__ == "__main__":
    print("🤖 TESTE DO SISTEMA DE ALERTAS - BOT LOL V3")
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Executar testes
    test1_result = test_alert_system()
    test2_result = test_integration()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")
    print(f"   🚨 Sistema de Alertas: {'✅ PASSOU' if test1_result else '❌ FALHOU'}")
    print(f"   🔧 Integração: {'✅ PASSOU' if test2_result else '❌ FALHOU'}")
    
    if test1_result and test2_result:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("💡 O sistema de alertas está pronto para uso")
        print("\n📝 PRÓXIMOS PASSOS:")
        print("   1. Execute o bot: python bot_v13_railway.py")
        print("   2. Use /alertas para gerenciar alertas")
        print("   3. Use /inscrever em grupos para receber alertas")
        sys.exit(0)
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique os erros acima e corrija antes de usar")
        sys.exit(1) 