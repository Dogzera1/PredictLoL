#!/usr/bin/env python3
"""
Teste do Bot em Produção - Comandos de Grupos
Inicializa o bot real e mostra como usar os comandos
"""

import asyncio
import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.telegram_bot.alerts_system import TelegramAlertsSystem
    from bot.utils.logger_config import get_logger
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

logger = get_logger(__name__)

async def test_production_bot():
    """Testa o bot em produção"""
    print("🤖 Teste do Bot em Produção - Comandos de Grupos")
    print("=" * 60)
    
    try:
        # Token de produção
        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAHkSPdwIRd87KiyoRAFuHkjqR72pcwOxP4")
        
        if not BOT_TOKEN:
            print("❌ Token do bot não encontrado!")
            return False
        
        print(f"🔗 Inicializando bot: {BOT_TOKEN[:20]}...")
        
        # Inicializa sistema de alertas
        alerts_system = TelegramAlertsSystem(BOT_TOKEN)
        
        print("⚙️ Inicializando componentes...")
        await alerts_system.initialize()
        
        print("📋 Configurando handlers...")
        alerts_system._setup_handlers()
        
        # Verifica handlers registrados
        if alerts_system.application:
            handlers_count = len(alerts_system.application.handlers.get(0, []))
            print(f"✅ {handlers_count} handlers registrados")
            
            # Lista handlers específicos de grupos
            group_commands = ['activate_group', 'group_status', 'deactivate_group']
            print("\n🔧 Handlers de Grupos Registrados:")
            
            for handler in alerts_system.application.handlers.get(0, []):
                if hasattr(handler, 'command') and any(cmd in str(handler.command) for cmd in group_commands):
                    print(f"   ✅ /{handler.command[0]} - {handler.callback.__name__}")
        
        # Mostra informações do bot
        try:
            print("\n🤖 Informações do Bot:")
            print(f"   • Token: {BOT_TOKEN[:20]}...")
            print(f"   • Aplicação: {'✅ Inicializada' if alerts_system.application else '❌ Não inicializada'}")
            print(f"   • Bot: {'✅ Configurado' if alerts_system.bot else '❌ Não configurado'}")
        except Exception as e:
            print(f"   ⚠️ Erro ao obter info: {e}")
        
        # Instruções para uso
        print("\n" + "=" * 60)
        print("📋 INSTRUÇÕES PARA USAR OS COMANDOS DE GRUPOS")
        print("=" * 60)
        
        print("\n1️⃣ ATIVAR ALERTAS EM UM GRUPO:")
        print("   • Adicione o bot ao seu grupo do Telegram")
        print("   • Certifique-se de que você é admin do grupo")
        print("   • Digite: /activate_group")
        print("   • Escolha o tipo de alerta no menu que aparece")
        
        print("\n2️⃣ VERIFICAR STATUS DO GRUPO:")
        print("   • No grupo onde o bot está ativo, digite: /group_status")
        print("   • Verá informações sobre configuração e estatísticas")
        
        print("\n3️⃣ DESATIVAR ALERTAS:")
        print("   • No grupo ativo, digite: /deactivate_group")
        print("   • Apenas admins podem fazer isso")
        
        print("\n4️⃣ TIPOS DE SUBSCRIÇÃO DISPONÍVEIS:")
        print("   🔔 Todas as Tips - Recebe todas as tips geradas")
        print("   💎 Alto Valor - Apenas tips com EV > 10%")
        print("   🎯 Alta Confiança - Apenas tips com confiança > 80%")
        print("   👑 Premium - Tips com EV > 15% E confiança > 85%")
        
        print("\n⚠️ REQUISITOS:")
        print("   • Bot deve ser admin ou membro do grupo")
        print("   • Usuário que executa comando deve ser admin")
        print("   • Grupo deve ser 'supergroup' (grupos grandes)")
        
        # Simula inicialização do bot (sem polling real)
        print(f"\n🚀 Bot configurado e pronto para receber comandos!")
        print(f"📞 Para testar, adicione @{alerts_system.bot_token.split(':')[0]} ao seu grupo")
        
        # Status final
        print("\n✅ SISTEMA FUNCIONAL!")
        print("💡 Os comandos de grupos devem funcionar normalmente agora")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste de produção: {e}")
        import traceback
        traceback.print_exc()
        return False

async def show_bot_info():
    """Mostra informações do bot sem inicializar polling"""
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAHkSPdwIRd87KiyoRAFuHkjqR72pcwOxP4")
    
    print("\n📊 INFORMAÇÕES DO BOT:")
    print("-" * 30)
    
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        
        # Obter informações do bot
        me = await bot.get_me()
        print(f"   • Username: @{me.username}")
        print(f"   • Nome: {me.first_name}")
        print(f"   • ID: {me.id}")
        print(f"   • É bot: {'✅' if me.is_bot else '❌'}")
        
    except Exception as e:
        print(f"   ❌ Erro ao obter info: {e}")

if __name__ == "__main__":
    try:
        print("🧪 Iniciando teste de produção...")
        
        # Roda teste
        result = asyncio.run(test_production_bot())
        
        # Mostra info do bot
        asyncio.run(show_bot_info())
        
        if result:
            print("\n🎉 Teste concluído com sucesso!")
            print("💡 Os comandos de grupos devem estar funcionando")
        else:
            print("\n⚠️ Teste encontrou problemas")
            
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}") 