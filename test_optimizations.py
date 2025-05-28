#!/usr/bin/env python3
"""
Script para testar as otimizações implementadas no bot
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

async def test_optimizations():
    """Testa as otimizações implementadas"""
    print("🧪 TESTE DE OTIMIZAÇÕES - BOT LOL V3")
    print("=" * 50)
    
    initial_memory = get_memory_usage()
    print(f"💾 Memória inicial: {initial_memory:.2f} MB")
    
    try:
        # Importar bot otimizado
        print("\n🔄 Importando bot otimizado...")
        from bot_v13_railway import LoLBotV3UltraAdvanced
        
        import_memory = get_memory_usage()
        print(f"💾 Memória após import: {import_memory:.2f} MB (+{import_memory - initial_memory:.2f} MB)")
        
        # Inicializar bot
        print("\n🤖 Inicializando bot...")
        start_time = time.time()
        bot = LoLBotV3UltraAdvanced()
        init_time = time.time() - start_time
        
        init_memory = get_memory_usage()
        print(f"⏱️ Tempo de inicialização: {init_time:.2f}s")
        print(f"💾 Memória após inicialização: {init_memory:.2f} MB (+{init_memory - import_memory:.2f} MB)")
        
        # Testar lazy loading
        print("\n🔄 Testando lazy loading...")
        
        # Tips system
        print("  📊 Acessando tips_system...")
        tips_start = time.time()
        tips_system = bot.tips_system
        tips_time = time.time() - tips_start
        tips_memory = get_memory_usage()
        print(f"    ⏱️ Tempo: {tips_time:.2f}s | 💾 Memória: {tips_memory:.2f} MB")
        
        # Schedule manager
        print("  📅 Acessando schedule_manager...")
        schedule_start = time.time()
        schedule_manager = bot.schedule_manager
        schedule_time = time.time() - schedule_start
        schedule_memory = get_memory_usage()
        print(f"    ⏱️ Tempo: {schedule_time:.2f}s | 💾 Memória: {schedule_memory:.2f} MB")
        
        # Prediction system
        print("  🔮 Acessando prediction_system...")
        pred_start = time.time()
        prediction_system = bot.prediction_system
        pred_time = time.time() - pred_start
        pred_memory = get_memory_usage()
        print(f"    ⏱️ Tempo: {pred_time:.2f}s | 💾 Memória: {pred_memory:.2f} MB")
        
        # Alerts system
        print("  📢 Acessando alerts_system...")
        alerts_start = time.time()
        alerts_system = bot.alerts_system
        alerts_time = time.time() - alerts_start
        alerts_memory = get_memory_usage()
        print(f"    ⏱️ Tempo: {alerts_time:.2f}s | 💾 Memória: {alerts_memory:.2f} MB")
        
        final_memory = get_memory_usage()
        total_memory_used = final_memory - initial_memory
        
        print("\n📊 RESUMO DOS TESTES:")
        print("=" * 30)
        print(f"💾 Memória total usada: {total_memory_used:.2f} MB")
        print(f"⏱️ Tempo total: {time.time() - start_time:.2f}s")
        
        # Verificar se está dentro dos limites aceitáveis
        if total_memory_used < 100:  # Menos de 100MB
            print("✅ OTIMIZAÇÃO BEM-SUCEDIDA - Uso de memória baixo")
        elif total_memory_used < 200:  # Menos de 200MB
            print("⚠️ OTIMIZAÇÃO PARCIAL - Uso de memória moderado")
        else:
            print("❌ OTIMIZAÇÃO INSUFICIENTE - Uso de memória alto")
        
        # Testar monitoramento otimizado
        print("\n🔍 Testando sistema de monitoramento otimizado...")
        monitoring_status = tips_system.get_monitoring_status()
        print(f"  📊 Status: {monitoring_status}")
        
        print("\n✅ TESTES CONCLUÍDOS!")
        
    except Exception as e:
        print(f"❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimizations()) 