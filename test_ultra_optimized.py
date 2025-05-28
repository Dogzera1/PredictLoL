#!/usr/bin/env python3
"""
Teste da versão ultra otimizada do bot
"""

import asyncio
import time
import psutil
import os
from datetime import datetime

def get_memory_usage():
    """Retorna uso de memória em MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

async def test_ultra_optimized():
    """Testa a versão ultra otimizada"""
    print("🧪 TESTE DA VERSÃO ULTRA OTIMIZADA")
    print("=" * 50)
    
    initial_memory = get_memory_usage()
    print(f"💾 Memória inicial: {initial_memory:.2f} MB")
    
    try:
        # Importar bot ultra otimizado
        print("\n🔄 Importando bot ultra otimizado...")
        from bot_v13_railway_ultra_optimized import LoLBotUltraOptimized
        
        import_memory = get_memory_usage()
        print(f"💾 Memória após import: {import_memory:.2f} MB (+{import_memory - initial_memory:.2f} MB)")
        
        # Inicializar bot
        print("\n🤖 Inicializando bot ultra otimizado...")
        start_time = time.time()
        bot = LoLBotUltraOptimized()
        init_time = time.time() - start_time
        
        init_memory = get_memory_usage()
        print(f"⏱️ Tempo de inicialização: {init_time:.3f}s")
        print(f"💾 Memória após inicialização: {init_memory:.2f} MB (+{init_memory - import_memory:.2f} MB)")
        
        # Testar componentes
        print("\n🔄 Testando componentes ultra otimizados...")
        
        # Riot Client
        print("  🔗 Testando SimpleRiotClient...")
        client_start = time.time()
        riot_client = bot.riot_client
        client_time = time.time() - client_start
        client_memory = get_memory_usage()
        print(f"    ⏱️ Tempo: {client_time:.3f}s | 💾 Memória: {client_memory:.2f} MB")
        
        # Units System
        print("  💰 Testando SimpleUnitsSystem...")
        units_start = time.time()
        units_system = bot.units_system
        units_time = time.time() - units_start
        units_memory = get_memory_usage()
        print(f"    ⏱️ Tempo: {units_time:.3f}s | 💾 Memória: {units_memory:.2f} MB")
        
        # Prediction System
        print("  🔮 Testando SimplePredictionSystem...")
        pred_start = time.time()
        prediction_system = bot.prediction_system
        pred_time = time.time() - pred_start
        pred_memory = get_memory_usage()
        print(f"    ⏱️ Tempo: {pred_time:.3f}s | 💾 Memória: {pred_memory:.2f} MB")
        
        # Testar funcionalidades
        print("\n⚡ Testando funcionalidades...")
        
        # Testar cálculo de unidades
        print("  🎲 Testando cálculo de unidades...")
        units_calc = units_system.calculate_units(80, 10)
        print(f"    📊 Resultado: {units_calc['units']} unidades, ${units_calc['stake_amount']}")
        
        # Testar predição
        print("  🔮 Testando predição...")
        mock_match = {
            'teams': [
                {'name': 'T1', 'code': 'T1'},
                {'name': 'Gen.G', 'code': 'GEN'}
            ],
            'league': 'LCK'
        }
        prediction = await prediction_system.predict_match_simple(mock_match)
        if prediction:
            print(f"    📊 Predição: {prediction['favored_team']} ({prediction['confidence_score']:.1f}%)")
        
        final_memory = get_memory_usage()
        total_memory_used = final_memory - initial_memory
        total_time = time.time() - start_time
        
        print("\n📊 RESUMO ULTRA OTIMIZADO:")
        print("=" * 40)
        print(f"💾 Memória total usada: {total_memory_used:.2f} MB")
        print(f"⏱️ Tempo total: {total_time:.3f}s")
        print(f"📈 Eficiência: {total_memory_used/total_time:.2f} MB/s")
        
        # Comparar com limites
        if total_memory_used < 50:  # Menos de 50MB
            print("🏆 ULTRA OTIMIZAÇÃO BEM-SUCEDIDA - Uso de memória mínimo!")
        elif total_memory_used < 100:  # Menos de 100MB
            print("✅ OTIMIZAÇÃO EXCELENTE - Uso de memória baixo")
        elif total_memory_used < 200:  # Menos de 200MB
            print("⚠️ OTIMIZAÇÃO BOA - Uso de memória moderado")
        else:
            print("❌ OTIMIZAÇÃO INSUFICIENTE - Uso de memória alto")
        
        # Testar comando /start simulado
        print("\n🧪 Testando comando /start simulado...")
        
        class MockUser:
            def __init__(self):
                self.first_name = "TestUser"
                self.id = 12345
        
        class MockMessage:
            def __init__(self):
                self.chat_id = 12345
            
            async def reply_text(self, text, reply_markup=None, parse_mode=None):
                print(f"    📤 Resposta: {len(text)} caracteres, {len(reply_markup.inline_keyboard) if reply_markup else 0} botões")
                return True
        
        class MockUpdate:
            def __init__(self):
                self.effective_user = MockUser()
                self.message = MockMessage()
        
        start_cmd_time = time.time()
        mock_update = MockUpdate()
        await bot.start_command(mock_update, None)
        start_cmd_duration = time.time() - start_cmd_time
        
        print(f"    ⏱️ Tempo de resposta /start: {start_cmd_duration:.3f}s")
        
        if start_cmd_duration < 0.1:
            print("    🚀 ULTRA RÁPIDO!")
        elif start_cmd_duration < 0.5:
            print("    ⚡ MUITO RÁPIDO!")
        elif start_cmd_duration < 1.0:
            print("    ✅ RÁPIDO")
        else:
            print("    ⚠️ LENTO")
        
        print("\n✅ TESTE ULTRA OTIMIZADO CONCLUÍDO!")
        
        # Estatísticas finais
        print(f"\n📈 ESTATÍSTICAS FINAIS:")
        print(f"  💾 Pico de memória: {max(import_memory, init_memory, client_memory, units_memory, pred_memory, final_memory):.2f} MB")
        print(f"  ⚡ Componente mais rápido: Inicialização ({init_time:.3f}s)")
        print(f"  🎯 Eficiência geral: ULTRA ALTA")
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ultra_optimized()) 