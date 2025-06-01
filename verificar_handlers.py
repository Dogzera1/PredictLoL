#!/usr/bin/env python3
"""
Verificação dos Handlers do Bot
Lista todos os handlers registrados para identificar problemas
"""

import asyncio
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.telegram_bot.alerts_system import TelegramAlertsSystem
    from telegram.ext import CommandHandler
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

async def check_handlers():
    """Verifica handlers registrados"""
    print("🔍 Verificação dos Handlers do Bot")
    print("=" * 50)
    
    try:
        # Token
        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAHkSPdwIRd87KiyoRAFuHkjqR72pcwOxP4")
        
        # Inicializa sistema
        alerts_system = TelegramAlertsSystem(BOT_TOKEN)
        await alerts_system.initialize()
        alerts_system._setup_handlers()
        
        print(f"✅ Sistema inicializado")
        
        if alerts_system.application:
            # Lista TODOS os handlers
            all_handlers = alerts_system.application.handlers.get(0, [])
            print(f"\n📊 Total de handlers: {len(all_handlers)}")
            
            print("\n📋 LISTA COMPLETA DE HANDLERS:")
            print("-" * 40)
            
            for i, handler in enumerate(all_handlers, 1):
                handler_type = type(handler).__name__
                
                if isinstance(handler, CommandHandler):
                    commands = handler.commands if hasattr(handler, 'commands') else []
                    callback_name = handler.callback.__name__ if handler.callback else "None"
                    
                    print(f"{i:2d}. CommandHandler")
                    print(f"    • Comandos: {commands}")
                    print(f"    • Callback: {callback_name}")
                    
                    # Identifica comandos de grupos
                    group_commands = ['activate_group', 'group_status', 'deactivate_group']
                    is_group_command = any(cmd in commands for cmd in group_commands)
                    if is_group_command:
                        print(f"    🎯 COMANDO DE GRUPO!")
                    
                else:
                    print(f"{i:2d}. {handler_type}")
                    if hasattr(handler, 'callback'):
                        print(f"    • Callback: {handler.callback.__name__}")
                
                print()
            
            # Busca especificamente comandos de grupos
            print("\n🎯 COMANDOS DE GRUPOS ENCONTRADOS:")
            print("-" * 40)
            
            group_handlers_found = []
            
            for handler in all_handlers:
                if isinstance(handler, CommandHandler):
                    commands = handler.commands if hasattr(handler, 'commands') else []
                    
                    if 'activate_group' in commands:
                        group_handlers_found.append(f"✅ /activate_group -> {handler.callback.__name__}")
                    elif 'group_status' in commands:
                        group_handlers_found.append(f"✅ /group_status -> {handler.callback.__name__}")
                    elif 'deactivate_group' in commands:
                        group_handlers_found.append(f"✅ /deactivate_group -> {handler.callback.__name__}")
            
            if group_handlers_found:
                for handler_info in group_handlers_found:
                    print(f"   {handler_info}")
            else:
                print("   ❌ NENHUM COMANDO DE GRUPO ENCONTRADO!")
                
                # Verifica se métodos existem na classe
                print("\n🔍 VERIFICANDO MÉTODOS NA CLASSE:")
                print("-" * 40)
                
                methods = [
                    '_handle_activate_group',
                    '_handle_group_status', 
                    '_handle_deactivate_group'
                ]
                
                for method_name in methods:
                    if hasattr(alerts_system, method_name):
                        method = getattr(alerts_system, method_name)
                        print(f"   ✅ {method_name} - {method}")
                    else:
                        print(f"   ❌ {method_name} - Não encontrado")
        
        print("\n" + "=" * 50)
        print("📋 DIAGNÓSTICO:")
        
        if not group_handlers_found:
            print("❌ PROBLEMA: Comandos de grupos não estão sendo registrados!")
            print("🔧 POSSÍVEIS CAUSAS:")
            print("   • Erro no método _setup_handlers()")
            print("   • Métodos dos handlers não existem")
            print("   • Problema na importação CommandHandler")
            
            print("\n🛠️ VERIFICANDO _setup_handlers()...")
            
            # Vamos verificar o código do _setup_handlers manualmente
            import inspect
            setup_code = inspect.getsource(alerts_system._setup_handlers)
            
            if 'activate_group' in setup_code:
                print("   ✅ activate_group está no código de _setup_handlers")
            else:
                print("   ❌ activate_group NÃO está no código")
            
            if 'group_status' in setup_code:
                print("   ✅ group_status está no código de _setup_handlers")
            else:
                print("   ❌ group_status NÃO está no código")
                
        else:
            print("✅ COMANDOS DE GRUPOS REGISTRADOS CORRETAMENTE!")
        
        return len(group_handlers_found) > 0
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(check_handlers())
        if result:
            print("\n🎉 Handlers de grupos funcionando!")
        else:
            print("\n⚠️ Problema com handlers de grupos identificado")
    except Exception as e:
        print(f"\n❌ Erro: {e}") 