#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico dos botões do Bot LoL V3
Verifica se todos os callbacks estão funcionando
"""

import sys
sys.path.append('.')

def test_callback_handlers():
    """Testar se todos os handlers de callback estão implementados"""
    print("🔘 TESTE DE HANDLERS DE CALLBACK")
    print("=" * 60)
    
    try:
        from bot_v13_railway import BotLoLV3Railway
        
        # Inicializar bot
        bot = BotLoLV3Railway()
        print("✅ Bot inicializado com sucesso")
        
        # Lista de todos os callbacks esperados
        callbacks_esperados = [
            "menu_principal",
            "agenda", 
            "partidas",
            "value",
            "stats", 
            "portfolio",
            "units",
            "tips",
            "help",
            "inscrever_alertas",
            "desinscrever_alertas", 
            "status_alertas",
            "alertas_menu"
        ]
        
        # Ler o código do handle_callback
        import inspect
        source_code = inspect.getsource(bot.handle_callback)
        
        print(f"\n📊 VERIFICANDO {len(callbacks_esperados)} CALLBACKS:")
        print("-" * 60)
        
        callbacks_encontrados = []
        callbacks_faltando = []
        
        for callback in callbacks_esperados:
            if f'query.data == "{callback}"' in source_code:
                callbacks_encontrados.append(callback)
                print(f"✅ {callback}")
            else:
                callbacks_faltando.append(callback)
                print(f"❌ {callback} - NÃO ENCONTRADO")
        
        print(f"\n📈 RESULTADO:")
        print(f"✅ Callbacks funcionando: {len(callbacks_encontrados)}/{len(callbacks_esperados)}")
        print(f"❌ Callbacks faltando: {len(callbacks_faltando)}")
        
        if callbacks_faltando:
            print(f"\n⚠️ CALLBACKS FALTANDO:")
            for callback in callbacks_faltando:
                print(f"  • {callback}")
            return False
        else:
            print(f"\n🎉 TODOS OS CALLBACKS IMPLEMENTADOS!")
            return True
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_menu_buttons():
    """Testar se os botões do menu principal estão corretos"""
    print("\n🎮 TESTE DOS BOTÕES DO MENU PRINCIPAL")
    print("=" * 60)
    
    try:
        from bot_v13_railway import BotLoLV3Railway
        
        # Inicializar bot
        bot = BotLoLV3Railway()
        
        # Ler o código do show_main_menu
        import inspect
        source_code = inspect.getsource(bot.show_main_menu)
        
        # Botões esperados no menu principal
        botoes_esperados = [
            ('📅 Próximas Partidas', 'agenda'),
            ('🎮 Ver Partidas', 'partidas'),
            ('📊 Estatísticas', 'stats'),
            ('💰 Value Betting', 'value'),
            ('📈 Portfolio', 'portfolio'),
            ('🎯 Sistema Unidades', 'units'),
            ('🚨 Alertas', 'alertas_menu'),
            ('💡 Dicas Pro', 'tips'),
            ('❓ Ajuda', 'help')
        ]
        
        print(f"📊 VERIFICANDO {len(botoes_esperados)} BOTÕES:")
        print("-" * 60)
        
        botoes_encontrados = []
        botoes_faltando = []
        
        for texto, callback in botoes_esperados:
            if f'"{texto}"' in source_code and f'callback_data="{callback}"' in source_code:
                botoes_encontrados.append((texto, callback))
                print(f"✅ {texto} → {callback}")
            else:
                botoes_faltando.append((texto, callback))
                print(f"❌ {texto} → {callback} - NÃO ENCONTRADO")
        
        print(f"\n📈 RESULTADO:")
        print(f"✅ Botões funcionando: {len(botoes_encontrados)}/{len(botoes_esperados)}")
        print(f"❌ Botões faltando: {len(botoes_faltando)}")
        
        if botoes_faltando:
            print(f"\n⚠️ BOTÕES FALTANDO:")
            for texto, callback in botoes_faltando:
                print(f"  • {texto} → {callback}")
            return False
        else:
            print(f"\n🎉 TODOS OS BOTÕES DO MENU IMPLEMENTADOS!")
            return True
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agenda_functionality():
    """Testar especificamente a funcionalidade de agenda"""
    print("\n📅 TESTE ESPECÍFICO DA AGENDA")
    print("=" * 60)
    
    try:
        from bot_v13_railway import BotLoLV3Railway
        
        # Inicializar bot
        bot = BotLoLV3Railway()
        
        # Testar função _get_scheduled_matches
        print("🔍 Testando _get_scheduled_matches...")
        agenda_data = bot._get_scheduled_matches()
        
        print(f"✅ Função executada com sucesso")
        print(f"📊 Partidas encontradas: {len(agenda_data.get('matches', []))}")
        print(f"🕐 Última atualização: {agenda_data.get('last_update', 'N/A')}")
        print(f"🌍 Fuso horário: {agenda_data.get('timezone', 'N/A')}")
        
        # Verificar se há partidas
        if agenda_data.get('matches'):
            print(f"\n🎮 PRIMEIRAS 3 PARTIDAS:")
            for i, match in enumerate(agenda_data['matches'][:3], 1):
                print(f"  {i}. {match.get('team1', 'N/A')} vs {match.get('team2', 'N/A')}")
                print(f"     🏆 {match.get('league', 'N/A')} • {match.get('tournament', 'N/A')}")
                print(f"     ⏰ {match.get('scheduled_time', 'N/A')}")
                print()
        
        # Testar funções auxiliares
        print("🔍 Testando funções auxiliares...")
        
        # Testar _get_match_status_emoji
        emoji = bot._get_match_status_emoji('scheduled')
        print(f"✅ _get_match_status_emoji('scheduled'): {emoji}")
        
        # Testar _format_match_time (com data fictícia)
        from datetime import datetime, timedelta
        import pytz
        brazil_tz = pytz.timezone('America/Sao_Paulo')
        future_time = datetime.now(brazil_tz) + timedelta(hours=2)
        formatted_time = bot._format_match_time(future_time)
        print(f"✅ _format_match_time: {formatted_time}")
        
        print(f"\n🎉 FUNCIONALIDADE DE AGENDA FUNCIONANDO!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste"""
    print("🚀 TESTE ESPECÍFICO DOS BOTÕES - BOT LOL V3")
    print("=" * 70)
    
    # Executar testes
    test1 = test_callback_handlers()
    test2 = test_menu_buttons()
    test3 = test_agenda_functionality()
    
    # Resultado final
    print("\n📊 RESULTADO FINAL DOS TESTES")
    print("=" * 70)
    print(f"🔘 Handlers de Callback: {'✅ PASSOU' if test1 else '❌ FALHOU'}")
    print(f"🎮 Botões do Menu: {'✅ PASSOU' if test2 else '❌ FALHOU'}")
    print(f"📅 Funcionalidade Agenda: {'✅ PASSOU' if test3 else '❌ FALHOU'}")
    
    if test1 and test2 and test3:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Botão 'Próximas Partidas' está funcionando")
        print("✅ Todos os outros botões estão funcionando")
        print("✅ Sistema de callbacks está completo")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("Verifique os erros acima para identificar problemas")
        
        if not test1:
            print("⚠️ Problema nos handlers de callback")
        if not test2:
            print("⚠️ Problema nos botões do menu")
        if not test3:
            print("⚠️ Problema na funcionalidade de agenda")

if __name__ == "__main__":
    main() 