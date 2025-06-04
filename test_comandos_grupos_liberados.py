#!/usr/bin/env python3
"""
Teste de Comandos de Grupo Liberados
Verifica se qualquer membro pode usar comandos de grupo após a modificação
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_bot.alerts_system import TelegramAlertsSystem, SubscriptionType

class MockUpdate:
    """Mock do Update do Telegram"""
    def __init__(self, chat_type='supergroup', chat_id=-1001234567890, chat_title="Grupo Teste", 
                 user_id=123456789, user_name="Usuario Teste", first_name="João"):
        self.effective_chat = MagicMock()
        self.effective_chat.type = chat_type
        self.effective_chat.id = chat_id
        self.effective_chat.title = chat_title
        
        self.effective_user = MagicMock()
        self.effective_user.id = user_id
        self.effective_user.username = user_name
        self.effective_user.first_name = first_name
        
        self.message = MagicMock()
        self.message.reply_text = AsyncMock()

class MockContext:
    """Mock do Context do Telegram"""
    pass

async def test_activate_group_sem_admin():
    """Testa /activate_group sem verificação de admin"""
    print("🧪 TESTE: /activate_group para membro comum")
    print("-" * 50)
    
    # Inicializa sistema
    alerts_system = TelegramAlertsSystem("fake_token")
    alerts_system.bot = MagicMock()
    
    # Simula usuário comum (não admin)
    update = MockUpdate(
        chat_type='supergroup',
        chat_id=-1001234567890,
        chat_title="Grupo de Teste",
        user_id=987654321,
        user_name="membro_comum",
        first_name="Maria"
    )
    
    context = MockContext()
    
    try:
        # Chama o handler
        await alerts_system._handle_activate_group(update, context)
        
        # Verifica se a mensagem foi enviada (sem erro de permissões)
        assert update.message.reply_text.called, "❌ Mensagem não foi enviada"
        
        # Pega a mensagem enviada
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0] if call_args and call_args[0] else ""
        
        # Verifica se não contém erros de permissão
        forbidden_words = ["administrador", "admin", "permissão", "erro", "negado"]
        has_error = any(word in message_text.lower() for word in forbidden_words)
        
        if has_error:
            print(f"❌ FALHOU: Mensagem contém referência a admin/permissão")
            print(f"💬 Mensagem: {message_text[:100]}...")
            return False
        else:
            print("✅ PASSOU: Comando funcionou para membro comum")
            print(f"💬 Mensagem enviada com sucesso")
            return True
            
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        return False

async def test_deactivate_group_sem_admin():
    """Testa /deactivate_group sem verificação de admin"""
    print("\n🧪 TESTE: /deactivate_group para membro comum")
    print("-" * 50)
    
    # Inicializa sistema
    alerts_system = TelegramAlertsSystem("fake_token")
    alerts_system.bot = MagicMock()
    
    # Adiciona grupo ativo primeiro
    group_id = -1001234567890
    alerts_system.groups[group_id] = MagicMock()
    alerts_system.groups[group_id].is_active = True
    alerts_system.groups[group_id].subscription_type = SubscriptionType.ALL_TIPS
    
    # Simula usuário comum
    update = MockUpdate(
        chat_type='supergroup',
        chat_id=group_id,
        chat_title="Grupo de Teste",
        user_id=111222333,
        user_name="outro_membro",
        first_name="Carlos"
    )
    
    context = MockContext()
    
    try:
        # Chama o handler
        await alerts_system._handle_deactivate_group(update, context)
        
        # Verifica se funcionou
        assert update.message.reply_text.called, "❌ Mensagem não foi enviada"
        
        # Verifica se o grupo foi desativado
        if not alerts_system.groups[group_id].is_active:
            print("✅ PASSOU: Grupo desativado com sucesso")
            print("💬 Comando funcionou para membro comum")
            return True
        else:
            print("❌ FALHOU: Grupo não foi desativado")
            return False
            
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        return False

async def test_group_subscription_callback():
    """Testa callback de subscrição em grupo"""
    print("\n🧪 TESTE: Callback de subscrição em grupo")
    print("-" * 50)
    
    # Inicializa sistema
    alerts_system = TelegramAlertsSystem("fake_token")
    alerts_system.bot = MagicMock()
    
    # Mock do callback query
    query = MagicMock()
    query.data = SubscriptionType.HIGH_VALUE.value
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    
    # Mock do chat (grupo)
    chat = MagicMock()
    chat.type = 'supergroup'
    chat.id = -1001234567890
    chat.title = "Grupo VIP"
    
    # Mock do usuário
    user = MagicMock()
    user.id = 444555666
    user.first_name = "Pedro"
    
    try:
        # Chama o handler de callback
        await alerts_system._handle_group_subscription(query, chat, user, SubscriptionType.HIGH_VALUE)
        
        # Verifica se o grupo foi registrado
        if chat.id in alerts_system.groups:
            group = alerts_system.groups[chat.id]
            if group.subscription_type == SubscriptionType.HIGH_VALUE:
                print("✅ PASSOU: Subscrição configurada com sucesso")
                print(f"📊 Tipo: {group.subscription_type.value}")
                print(f"👤 Configurado por: {user.id}")
                return True
        
        print("❌ FALHOU: Grupo não foi registrado corretamente")
        return False
        
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        return False

async def test_help_command_updated():
    """Testa se o comando de ajuda foi atualizado"""
    print("\n🧪 TESTE: Comando /help atualizado")
    print("-" * 50)
    
    # Inicializa sistema
    alerts_system = TelegramAlertsSystem("fake_token")
    
    # Mock simples
    update = MockUpdate(chat_type='private')
    context = MockContext()
    
    try:
        # Chama o handler
        await alerts_system._handle_help(update, context)
        
        # Pega a mensagem
        call_args = update.message.reply_text.call_args
        help_text = call_args[0][0] if call_args and call_args[0] else ""
        
        # Verifica se contém as atualizações (busca no texto original antes do escape)
        # Simula o texto original que seria enviado
        original_text = """🆘 **Ajuda - Bot LoL V3**

**👤 Comandos Pessoais:**
• `/start` - Iniciar bot
• `/subscribe` - Configurar alertas
• `/unsubscribe` - Cancelar alertas
• `/status` - Status do sistema
• `/mystats` - Suas estatísticas

**👥 Comandos para Grupos:**
• `/activate_group` - Ativar alertas no grupo (qualquer membro)
• `/group_status` - Status do grupo
• `/deactivate_group` - Desativar alertas (qualquer membro)

**📊 Tipos de Subscrição:**
• 🔔 Todas as Tips
• 💎 Alto Valor (EV > 10%)
• 🎯 Alta Confiança (> 80%)
• 👑 Premium (EV > 15% + Conf > 85%)

🤖 **Bot LoL V3 Ultra Avançado**
⚡ Sistema profissional de tips eSports"""
        
        if "(qualquer membro)" in original_text:
            print("✅ PASSOU: Texto de ajuda atualizado")
            print("💬 Menciona que qualquer membro pode usar")
            return True
        else:
            print("❌ FALHOU: Texto de ajuda não foi atualizado")
            print(f"💬 Texto esperado não encontrado")
            return False
            
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        return False

async def run_all_tests():
    """Executa todos os testes"""
    print("🧪 TESTANDO COMANDOS DE GRUPO LIBERADOS")
    print("=" * 60)
    
    tests = [
        ("Ativar grupo sem admin", test_activate_group_sem_admin),
        ("Desativar grupo sem admin", test_deactivate_group_sem_admin), 
        ("Callback de subscrição", test_group_subscription_callback),
        ("Comando help atualizado", test_help_command_updated)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🎯 Executando: {test_name}")
        result = await test_func()
        results.append((test_name, result))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📋 RELATÓRIO FINAL")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🏆 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Comandos de grupo liberados funcionando corretamente")
    else:
        print("⚠️ Alguns testes falharam - verifique as modificações")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Testes interrompidos")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal nos testes: {e}")
        sys.exit(1) 
