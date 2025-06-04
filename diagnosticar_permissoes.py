#!/usr/bin/env python3
"""
Diagnóstico de Permissões - Bot Telegram
Identifica problemas com verificação de permissões em grupos
"""

import asyncio
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from telegram import Bot
    from telegram.error import TelegramError, Forbidden, BadRequest
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

async def diagnose_bot_permissions():
    """Diagnóstica problemas de permissões do bot"""
    print("🔍 Diagnóstico de Permissões do Bot")
    print("=" * 50)
    
    try:
        # Token do bot
        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0")
        
        if not BOT_TOKEN:
            print("❌ Token não encontrado!")
            return False
        
        # Inicializa bot
        bot = Bot(token=BOT_TOKEN)
        
        # Testa conexão básica
        print("🤖 Testando conexão do bot...")
        try:
            me = await bot.get_me()
            print(f"✅ Bot conectado: @{me.username} ({me.first_name})")
            print(f"   • ID: {me.id}")
            print(f"   • Pode se juntar a grupos: {me.can_join_groups}")
            print(f"   • Pode ler mensagens de grupos: {me.can_read_all_group_messages}")
            print(f"   • Suporta comandos inline: {me.supports_inline_queries}")
        except Exception as e:
            print(f"❌ Erro ao conectar bot: {e}")
            return False
        
        # Instruções para o usuário testar
        print("\n" + "=" * 50)
        print("📋 COMO TESTAR PERMISSÕES EM UM GRUPO:")
        print("=" * 50)
        
        print("\n1️⃣ ADICIONE O BOT AO SEU GRUPO:")
        print(f"   • Vá ao seu grupo no Telegram")
        print(f"   • Adicione @{me.username}")
        print(f"   • O bot deve aparecer na lista de membros")
        
        print("\n2️⃣ TORNE O BOT ADMINISTRADOR (IMPORTANTE!):")
        print("   • Vá em configurações do grupo")
        print("   • Escolha 'Administradores'")
        print("   • Adicione o bot como admin")
        print("   • Dê pelo menos essas permissões:")
        print("     ✓ Ver mensagens")
        print("     ✓ Enviar mensagens")
        print("     ✓ Ver lista de membros")
        
        print("\n3️⃣ TESTE O COMANDO:")
        print("   • Digite /activate_group no grupo")
        print("   • Se ainda der erro, use o script de teste abaixo")
        
        # Script de teste personalizado
        print("\n" + "=" * 50)
        print("🛠️ SCRIPT DE TESTE AVANÇADO:")
        print("=" * 50)
        
        print("""
Para testar permissões específicas, use este código Python:

```python
import asyncio
from telegram import Bot

async def test_group_permissions():
    bot = Bot(token="{}")
    
    # Substitua por ID real do seu grupo (negativo)
    GROUP_ID = -1001234567890  # Exemplo
    USER_ID = 123456789        # Seu ID de usuário
    
    try:
        # Testa obter informações do chat
        chat = await bot.get_chat(GROUP_ID)
        print(f"✅ Chat encontrado: {{chat.title}}")
        
        # Testa obter membro específico
        member = await bot.get_chat_member(GROUP_ID, USER_ID)
        print(f"✅ Membro encontrado: {{member.user.first_name}}")
        print(f"   Status: {{member.status}}")
        
        # Testa obter admins
        admins = await bot.get_chat_administrators(GROUP_ID)
        print(f"✅ {{len(admins)}} administradores encontrados")
        
        # Verifica se bot é admin
        bot_member = await bot.get_chat_member(GROUP_ID, bot.id)
        print(f"✅ Status do bot: {{bot_member.status}}")
        
    except Exception as e:
        print(f"❌ Erro: {{e}}")

asyncio.run(test_group_permissions())
```""".format(BOT_TOKEN))
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_common_group_scenarios():
    """Testa cenários comuns de problemas em grupos"""
    print("\n🔧 CENÁRIOS COMUNS DE PROBLEMAS:")
    print("-" * 40)
    
    scenarios = [
        {
            "problema": "Bot não é administrador",
            "sintoma": "Erro ao verificar permissões",
            "solucao": "Tornar bot admin no grupo"
        },
        {
            "problema": "Grupo é privado demais",
            "sintoma": "Forbidden: bot can't access chat", 
            "solucao": "Ajustar configurações de privacidade"
        },
        {
            "problema": "Bot foi removido",
            "sintoma": "Chat not found",
            "solucao": "Adicionar bot novamente ao grupo"
        },
        {
            "problema": "Permissões insuficientes",
            "sintoma": "BadRequest: not enough rights",
            "solucao": "Dar mais permissões ao bot"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['problema']}")
        print(f"   💥 Sintoma: {scenario['sintoma']}")
        print(f"   🔧 Solução: {scenario['solucao']}")

if __name__ == "__main__":
    try:
        print("🧪 Iniciando diagnóstico de permissões...")
        
        result = asyncio.run(diagnose_bot_permissions())
        asyncio.run(test_common_group_scenarios())
        
        if result:
            print("\n✅ Diagnóstico concluído!")
            print("💡 Siga as instruções acima para resolver o problema")
        else:
            print("\n⚠️ Problemas encontrados no diagnóstico")
            
    except KeyboardInterrupt:
        print("\n🛑 Diagnóstico interrompido")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}") 
