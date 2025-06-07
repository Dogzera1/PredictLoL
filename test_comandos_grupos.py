#!/usr/bin/env python3
"""
Teste dos Comandos de Grupos - Telegram Bot
Verifica se os comandos /activate_group, /group_status e /deactivate_group funcionam
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_bot.alerts_system import TelegramAlertsSystem, SubscriptionType

class MockBot:
    """Bot mock para testes"""
    async def get_chat_member(self, chat_id, user_id):
        # Simula que o usuário é admin
        member = MagicMock()
        member.status = 'administrator'
        return member

class MockUpdate:
    """Update mock para testes"""
    def __init__(self, chat_type='supergroup', chat_id=-123456789, chat_title='Grupo Teste', user_id=987654321, user_name='TestUser'):
        self.effective_chat = MagicMock()
        self.effective_chat.type = chat_type
        self.effective_chat.id = chat_id
        self.effective_chat.title = chat_title
        
        self.effective_user = MagicMock()
        self.effective_user.id = user_id
        self.effective_user.first_name = user_name
        
        self.message = MagicMock()
        self.message.reply_text = AsyncMock()

class MockContext:
    """Context mock para testes"""
    pass

async def test_group_commands():
    """Testa comandos de grupos"""
    print("🧪 Testando Comandos de Grupos do Telegram")
    print("=" * 60)
    
    try:
        # Configura token de teste
        test_token = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAG0_htf_kVuV_JUzNgMJMuRUOVnJGmeu0o")
        
        # Inicializa sistema
        alerts_system = TelegramAlertsSystem(test_token)
        alerts_system.bot = MockBot()  # Substitui por mock
        
        print(f"✅ Sistema inicializado com token: {test_token[:20]}...")
        
        # Cenário 1: Ativar grupo pela primeira vez
        print("\n1️⃣ Teste: /activate_group (primeira vez)")
        print("-" * 40)
        
        update = MockUpdate()
        context = MockContext()
        
        await alerts_system._handle_activate_group(update, context)
        
        # Verifica se reply_text foi chamado
        if update.message.reply_text.called:
            call_args = update.message.reply_text.call_args
            message_text = call_args[0][0] if call_args[0] else "Mensagem vazia"
            print(f"✅ Resposta enviada:")
            print(f"   {message_text[:100]}...")
        else:
            print("❌ Nenhuma resposta enviada")
        
        # Cenário 2: Verificar status de grupo não registrado
        print("\n2️⃣ Teste: /group_status (grupo não registrado)")
        print("-" * 40)
        
        update2 = MockUpdate()
        await alerts_system._handle_group_status(update2, context)
        
        if update2.message.reply_text.called:
            call_args = update2.message.reply_text.call_args
            message_text = call_args[0][0] if call_args[0] else "Mensagem vazia"
            print(f"✅ Resposta enviada:")
            print(f"   {message_text[:100]}...")
        else:
            print("❌ Nenhuma resposta enviada")
        
        # Cenário 3: Registrar grupo manualmente
        print("\n3️⃣ Teste: Registrar grupo manualmente")
        print("-" * 40)
        
        from bot.telegram_bot.alerts_system import TelegramGroup
        
        test_group = TelegramGroup(
            group_id=-123456789,
            title="Grupo Teste Manual",
            subscription_type=SubscriptionType.ALL_TIPS,
            activated_by=987654321,
            admin_ids=[987654321]
        )
        
        alerts_system.groups[-123456789] = test_group
        print(f"✅ Grupo registrado: {test_group.title}")
        print(f"   • ID: {test_group.group_id}")
        print(f"   • Tipo: {test_group.subscription_type.value}")
        print(f"   • Ativo: {test_group.is_active}")
        
        # Cenário 4: Verificar status de grupo registrado
        print("\n4️⃣ Teste: /group_status (grupo registrado)")
        print("-" * 40)
        
        update3 = MockUpdate()
        await alerts_system._handle_group_status(update3, context)
        
        if update3.message.reply_text.called:
            call_args = update3.message.reply_text.call_args
            message_text = call_args[0][0] if call_args[0] else "Mensagem vazia"
            print(f"✅ Resposta enviada:")
            print(f"   {message_text[:200]}...")
        else:
            print("❌ Nenhuma resposta enviada")
        
        # Cenário 5: Desativar grupo
        print("\n5️⃣ Teste: /deactivate_group")
        print("-" * 40)
        
        update4 = MockUpdate()
        await alerts_system._handle_deactivate_group(update4, context)
        
        if update4.message.reply_text.called:
            call_args = update4.message.reply_text.call_args
            message_text = call_args[0][0] if call_args[0] else "Mensagem vazia"
            print(f"✅ Resposta enviada:")
            print(f"   {message_text[:100]}...")
            
            # Verifica se grupo foi desativado
            if -123456789 in alerts_system.groups:
                is_active = alerts_system.groups[-123456789].is_active
                print(f"   • Grupo ativo: {is_active}")
            
        else:
            print("❌ Nenhuma resposta enviada")
        
        # Cenário 6: Teste em chat individual (deve falhar)
        print("\n6️⃣ Teste: Comando em chat individual (deve falhar)")
        print("-" * 40)
        
        update5 = MockUpdate(chat_type='private')
        await alerts_system._handle_activate_group(update5, context)
        
        if update5.message.reply_text.called:
            call_args = update5.message.reply_text.call_args
            message_text = call_args[0][0] if call_args[0] else "Mensagem vazia"
            print(f"✅ Erro tratado corretamente:")
            print(f"   {message_text[:100]}...")
        else:
            print("❌ Erro não foi tratado")
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📋 RELATÓRIO DOS COMANDOS DE GRUPOS")
        print("=" * 60)
        
        print(f"📊 Grupos registrados: {len(alerts_system.groups)}")
        if alerts_system.groups:
            for group_id, group in alerts_system.groups.items():
                print(f"   • {group.title} (ID: {group_id})")
                print(f"     - Tipo: {group.subscription_type.value}")
                print(f"     - Ativo: {group.is_active}")
                print(f"     - Tips recebidas: {group.tips_received}")
        
        print("\n🔧 PROBLEMAS IDENTIFICADOS:")
        
        # Verifica escape de markdown
        test_text = "Test **bold** and `code` and [link](url)"
        escaped = alerts_system._escape_markdown_v2(test_text)
        print(f"   • Escape Markdown V2: {'✅ OK' if escaped != test_text else '❌ Não funciona'}")
        
        # Verifica handlers registrados
        if hasattr(alerts_system, 'application') and alerts_system.application:
            handlers_count = len(alerts_system.application.handlers.get(0, []))
            print(f"   • Handlers registrados: {handlers_count}")
        else:
            print(f"   • ⚠️ Application não inicializada")
        
        print("\n✅ TESTE CONCLUÍDO!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_group_commands())
        if result:
            print("\n🎉 Teste de comandos de grupos concluído com sucesso!")
        else:
            print("\n⚠️ Teste encontrou problemas")
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}") 
