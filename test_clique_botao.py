#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de simulação de clique no botão "Próximas Partidas"
Simula exatamente o que acontece quando o usuário clica no botão
"""

import sys
sys.path.append('.')

class MockUpdate:
    """Mock do objeto Update do Telegram"""
    def __init__(self):
        self.callback_query = MockCallbackQuery()

class MockCallbackQuery:
    """Mock do callback query"""
    def __init__(self):
        self.data = "agenda"  # Simular clique no botão "Próximas Partidas"
        self.message = MockMessage()
        self.edit_message_text_called = False
        self.edit_message_text_args = None
    
    def answer(self):
        """Simular resposta do callback"""
        pass
    
    def edit_message_text(self, text, parse_mode=None, reply_markup=None):
        """Simular edição da mensagem"""
        self.edit_message_text_called = True
        self.edit_message_text_args = {
            'text': text,
            'parse_mode': parse_mode,
            'reply_markup': reply_markup
        }
        print("✅ Mensagem editada com sucesso!")
        return True

class MockMessage:
    """Mock da mensagem"""
    def __init__(self):
        self.chat_id = 12345

def test_clique_proximas_partidas():
    """Simular clique no botão 'Próximas Partidas'"""
    print("🖱️ SIMULAÇÃO DE CLIQUE NO BOTÃO 'PRÓXIMAS PARTIDAS'")
    print("=" * 70)
    
    try:
        from bot_v13_railway import BotLoLV3Railway
        
        # Inicializar bot
        print("🤖 Inicializando bot...")
        bot = BotLoLV3Railway()
        print("✅ Bot inicializado com sucesso")
        
        # Criar mock do update
        print("\n🎯 Simulando clique no botão...")
        mock_update = MockUpdate()
        mock_context = None  # Context não é usado no callback
        
        print(f"📊 Callback data: {mock_update.callback_query.data}")
        
        # Executar o callback handler
        print("🔄 Executando handle_callback...")
        result = bot.handle_callback(mock_update, mock_context)
        
        # Verificar resultado
        if mock_update.callback_query.edit_message_text_called:
            print("✅ Callback executado com sucesso!")
            
            args = mock_update.callback_query.edit_message_text_args
            text = args['text']
            
            print(f"\n📝 CONTEÚDO DA RESPOSTA:")
            print("-" * 50)
            
            # Verificar se contém elementos esperados
            elementos_esperados = [
                "PRÓXIMAS PARTIDAS AGENDADAS",
                "Última atualização",
                "Total de partidas",
                "Horários em Brasília",
                "LIGAS MONITORADAS"
            ]
            
            elementos_encontrados = []
            for elemento in elementos_esperados:
                if elemento in text:
                    elementos_encontrados.append(elemento)
                    print(f"✅ {elemento}")
                else:
                    print(f"❌ {elemento} - NÃO ENCONTRADO")
            
            print(f"\n📊 ANÁLISE DO CONTEÚDO:")
            print(f"✅ Elementos encontrados: {len(elementos_encontrados)}/{len(elementos_esperados)}")
            print(f"📏 Tamanho da mensagem: {len(text)} caracteres")
            
            # Mostrar primeiras linhas da resposta
            linhas = text.split('\n')[:10]
            print(f"\n📄 PRIMEIRAS LINHAS DA RESPOSTA:")
            for i, linha in enumerate(linhas, 1):
                if linha.strip():
                    print(f"  {i}. {linha}")
            
            if len(elementos_encontrados) == len(elementos_esperados):
                print(f"\n🎉 BOTÃO 'PRÓXIMAS PARTIDAS' FUNCIONANDO PERFEITAMENTE!")
                return True
            else:
                print(f"\n⚠️ Botão funciona mas conteúdo incompleto")
                return False
        else:
            print("❌ Callback não executou edit_message_text")
            return False
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_todos_os_botoes():
    """Testar todos os botões do menu principal"""
    print("\n🎮 TESTE DE TODOS OS BOTÕES DO MENU")
    print("=" * 70)
    
    botoes_para_testar = [
        ("📅 Próximas Partidas", "agenda"),
        ("🎮 Ver Partidas", "partidas"),
        ("💰 Value Betting", "value"),
        ("📊 Estatísticas", "stats"),
        ("📈 Portfolio", "portfolio"),
        ("🎯 Sistema Unidades", "units"),
        ("💡 Dicas Pro", "tips"),
        ("🚨 Alertas", "alertas_menu"),
        ("❓ Ajuda", "help")
    ]
    
    try:
        from bot_v13_railway import BotLoLV3Railway
        
        # Inicializar bot
        bot = BotLoLV3Railway()
        
        resultados = []
        
        for nome_botao, callback_data in botoes_para_testar:
            print(f"\n🖱️ Testando: {nome_botao}")
            
            # Criar mock
            mock_update = MockUpdate()
            mock_update.callback_query.data = callback_data
            
            try:
                # Executar callback
                result = bot.handle_callback(mock_update, None)
                
                if mock_update.callback_query.edit_message_text_called:
                    print(f"✅ {nome_botao} - FUNCIONANDO")
                    resultados.append(True)
                else:
                    print(f"❌ {nome_botao} - NÃO FUNCIONANDO")
                    resultados.append(False)
                    
            except Exception as e:
                print(f"❌ {nome_botao} - ERRO: {e}")
                resultados.append(False)
        
        # Resultado final
        funcionando = sum(resultados)
        total = len(resultados)
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"✅ Botões funcionando: {funcionando}/{total}")
        print(f"📈 Taxa de sucesso: {(funcionando/total)*100:.1f}%")
        
        if funcionando == total:
            print(f"\n🎉 TODOS OS BOTÕES ESTÃO FUNCIONANDO!")
            return True
        else:
            print(f"\n⚠️ {total - funcionando} botões com problemas")
            return False
            
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 TESTE DE CLIQUE NOS BOTÕES - BOT LOL V3")
    print("=" * 80)
    
    # Executar testes
    test1 = test_clique_proximas_partidas()
    test2 = test_todos_os_botoes()
    
    # Resultado final
    print("\n📊 RESULTADO FINAL DOS TESTES")
    print("=" * 80)
    print(f"🖱️ Botão 'Próximas Partidas': {'✅ FUNCIONANDO' if test1 else '❌ COM PROBLEMA'}")
    print(f"🎮 Todos os Botões: {'✅ FUNCIONANDO' if test2 else '❌ COM PROBLEMA'}")
    
    if test1 and test2:
        print("\n🎉 CONFIRMADO: TODOS OS BOTÕES ESTÃO FUNCIONANDO!")
        print("✅ O botão 'Próximas Partidas' está operacional")
        print("✅ Todos os outros botões também estão funcionando")
        print("✅ Sistema de callbacks está 100% funcional")
    else:
        print("\n❌ PROBLEMAS DETECTADOS")
        if not test1:
            print("⚠️ Problema específico no botão 'Próximas Partidas'")
        if not test2:
            print("⚠️ Problemas em outros botões")

if __name__ == "__main__":
    main() 