#!/usr/bin/env python3
"""
Teste rápido para verificar se a correção do event loop funcionou
"""

import asyncio
import signal
import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_bot_quick():
    """Teste rápido do bot com timeout automático"""
    print(f"🚀 Iniciando teste rápido do bot - {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Importar o bot
        from main_v3_riot_integrated import TelegramBotV3Improved
        
        print("✅ Importação do bot bem-sucedida")
        
        # Criar instância
        bot = TelegramBotV3Improved()
        print("✅ Instância do bot criada")
        
        # Configurar timeout automático
        def timeout_handler():
            print("⏰ Timeout alcançado - teste concluído com sucesso!")
            # Não usar sys.exit() em async context
            return
        
        # Agendar timeout
        loop = asyncio.get_event_loop()
        timeout_handle = loop.call_later(15, timeout_handler)  # 15 segundos
        
        try:
            print("🚀 Iniciando bot (teste de 15 segundos)...")
            
            # Executar o bot com timeout
            task = asyncio.create_task(bot.run_bot())
            
            # Aguardar 15 segundos ou até o bot falhar
            await asyncio.wait_for(task, timeout=15.0)
            
        except asyncio.TimeoutError:
            print("✅ TESTE CONCLUÍDO: Bot funcionou por 15 segundos sem erro!")
            print("🎉 CORREÇÃO DO EVENT LOOP FUNCIONOU!")
            timeout_handle.cancel()
            return True
        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
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

if __name__ == "__main__":
    try:
        result = asyncio.run(test_bot_quick())
        print(f"\n🏁 Resultado final: {'✅ SUCESSO' if result else '❌ FALHOU'}")
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido pelo usuário")
        exit(0)
    except Exception as e:
        print(f"\n❌ Erro crítico no teste: {e}")
        exit(1) 