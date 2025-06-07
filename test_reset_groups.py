#!/usr/bin/env python3
"""
🔧 TESTE: Comando /reset_groups
Verificar se o cache de grupos é limpo corretamente
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock
import time

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_bot.alerts_system import TelegramAlertsSystem, TelegramGroup, SubscriptionType

class MockUpdate:
    """Mock do Update do Telegram"""
    def __init__(self, chat_type='supergroup', chat_id=-123456789, chat_title="Grupo Teste", user_id=111, user_name="TestUser"):
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
    """Mock do Context do Telegram"""
    pass

async def test_reset_groups():
    """Testa o comando /reset_groups"""
    print("🧪 TESTE: Comando /reset_groups")
    print("=" * 60)
    
    try:
        # Configura token de teste
        test_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_token")
        
        # Inicializa sistema
        alerts_system = TelegramAlertsSystem(test_token)
        
        # Simula grupos já registrados (antes da limpeza)
        test_groups = {
            -123456789: TelegramGroup(
                group_id=-123456789,
                title="Grupo Teste 1",
                subscription_type=SubscriptionType.ALL_TIPS,
                activated_by=111,
            ),
            -987654321: TelegramGroup(
                group_id=-987654321,
                title="Grupo Teste 2",
                subscription_type=SubscriptionType.HIGH_VALUE,
                activated_by=222,
            )
        }
        
        alerts_system.groups = test_groups.copy()
        alerts_system.blocked_groups = {-555555555}
        
        print(f"📊 Estado inicial:")
        print(f"   • Grupos registrados: {len(alerts_system.groups)}")
        print(f"   • Grupos bloqueados: {len(alerts_system.blocked_groups)}")
        
        # Cenário 1: Reset em grupo específico
        print("\n1️⃣ TESTE: Reset em grupo específico")
        print("-" * 40)
        
        update_group = MockUpdate(
            chat_type='supergroup',
            chat_id=-123456789,
            chat_title="Grupo Teste 1",
            user_id=111,
            user_name="Admin1"
        )
        context = MockContext()
        
        await alerts_system._handle_reset_groups(update_group, context)
        
        # Verifica resultado
        message_sent = update_group.message.reply_text.call_args[0][0] if update_group.message.reply_text.called else "Nenhuma mensagem"
        print(f"✅ Resposta: {message_sent[:50]}...")
        print(f"📊 Grupos restantes: {len(alerts_system.groups)}")
        print(f"   • Grupo específico removido: {-123456789 not in alerts_system.groups}")
        
        # Cenário 2: Reset completo em chat privado
        print("\n2️⃣ TESTE: Reset completo (chat privado)")
        print("-" * 40)
        
        # Restaura grupos para teste
        alerts_system.groups = test_groups.copy()
        alerts_system.blocked_groups = {-555555555}
        
        update_private = MockUpdate(
            chat_type='private',
            chat_id=111,
            chat_title=None,
            user_id=111,
            user_name="Admin"
        )
        
        await alerts_system._handle_reset_groups(update_private, context)
        
        message_sent = update_private.message.reply_text.call_args[0][0] if update_private.message.reply_text.called else "Nenhuma mensagem"
        print(f"✅ Resposta: {message_sent[:100]}...")
        print(f"📊 Resultado:")
        print(f"   • Grupos após reset: {len(alerts_system.groups)}")
        print(f"   • Grupos bloqueados após reset: {len(alerts_system.blocked_groups)}")
        print(f"   • Cache completamente limpo: {len(alerts_system.groups) == 0 and len(alerts_system.blocked_groups) == 0}")
        
        # Cenário 3: Teste da inicialização com limpeza
        print("\n3️⃣ TESTE: Limpeza na inicialização")
        print("-" * 40)
        
        # Simula grupos antigos
        alerts_system.groups = test_groups.copy()
        alerts_system.blocked_groups = {-555555555, -666666666}
        
        print(f"📊 Antes da limpeza:")
        print(f"   • Grupos: {len(alerts_system.groups)}")
        print(f"   • Bloqueados: {len(alerts_system.blocked_groups)}")
        
        # Chama limpeza manual
        alerts_system._clear_groups_cache()
        
        print(f"📊 Depois da limpeza:")
        print(f"   • Grupos: {len(alerts_system.groups)}")
        print(f"   • Bloqueados: {len(alerts_system.blocked_groups)}")
        print(f"   • Limpeza funcionou: {len(alerts_system.groups) == 0 and len(alerts_system.blocked_groups) == 0}")
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS!")
        print("\n📋 INSTRUÇÕES DE USO:")
        print("   • No grupo: /reset_groups - Remove apenas este grupo do cache")
        print("   • Em privado: /reset_groups - Limpa todo o cache (debug)")
        print("   • Automático: Cache limpo a cada inicialização do bot")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_reset_groups())
    if success:
        print("\n🎉 Teste concluído com sucesso!")
    else:
        print("\n💥 Teste falhou!")
        sys.exit(1) 