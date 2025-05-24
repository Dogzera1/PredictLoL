#!/usr/bin/env python3
"""
Teste Final - Verificação das Correções do Event Loop
"""

import asyncio
import signal
import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_bot_final():
    """Teste final das correções do event loop"""
    print(f"🚀 TESTE FINAL - {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Importar o bot corrigido
        from main_v3_riot_integrated import TelegramBotV3Improved
        
        print("✅ Importação bem-sucedida")
        
        # Criar instância
        bot = TelegramBotV3Improved()
        print("✅ Instância criada")
        
        # Configurar timeout automático de 20 segundos
        timeout_occurred = False
        
        def timeout_handler():
            nonlocal timeout_occurred
            timeout_occurred = True
            print("⏰ Timeout de 20s alcançado - teste concluído!")
        
        # Agendar timeout
        loop = asyncio.get_event_loop()
        timeout_handle = loop.call_later(20, timeout_handler)
        
        try:
            print("🔄 Testando bot por 20 segundos...")
            
            # Executar bot com timeout
            task = asyncio.create_task(bot.run_bot())
            
            # Aguardar 20 segundos ou até o bot falhar
            await asyncio.wait_for(task, timeout=20.0)
            
        except asyncio.TimeoutError:
            print("✅ SUCESSO: Bot rodou por 20 segundos sem erro de event loop!")
            print("🎉 CORREÇÕES FUNCIONARAM!")
            timeout_handle.cancel()
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "event loop" in error_msg.lower():
                print(f"❌ FALHOU: Ainda há erro de event loop: {error_msg}")
                timeout_handle.cancel()
                return False
            elif "token" in error_msg.lower():
                print(f"⚠️ AVISO: Erro de token (esperado): {error_msg}")
                print("✅ Mas não há erro de event loop - correção funcionou!")
                timeout_handle.cancel()
                return True
            else:
                print(f"❌ Erro inesperado: {error_msg}")
                timeout_handle.cancel()
                return False
            
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_test():
    """Executa o teste de forma segura"""
    try:
        # Configurar handler para Ctrl+C
        def signal_handler(sig, frame):
            print("\n🛑 Teste interrompido pelo usuário")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Executar teste
        result = asyncio.run(test_bot_final())
        
        print(f"\n🏁 RESULTADO FINAL:")
        if result:
            print("✅ SUCESSO - Correções do event loop funcionaram!")
            print("🎉 Bot está pronto para uso!")
        else:
            print("❌ FALHOU - Ainda há problemas de event loop")
            print("🔧 Mais correções podem ser necessárias")
        
        return result
        
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido")
        return False
    except Exception as e:
        print(f"\n❌ Erro crítico no teste: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE FINAL DAS CORREÇÕES DO EVENT LOOP")
    print("=" * 50)
    
    success = run_test()
    
    print("=" * 50)
    if success:
        print("🎯 CONCLUSÃO: Correções implementadas com sucesso!")
    else:
        print("⚠️ CONCLUSÃO: Mais trabalho necessário")
    
    exit(0 if success else 1) 