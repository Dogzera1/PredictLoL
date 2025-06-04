#!/usr/bin/env python3
"""
Script para parar todas as instâncias do bot
"""

import os
import sys
import psutil
import time

def stop_all_bots():
    """Para todas as instâncias do bot"""
    print("\n🔍 Procurando instâncias do bot...")
    current_pid = os.getpid()
    stopped = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.pid == current_pid:
                continue
            
            if proc.name().lower().startswith('python'):
                cmdline = proc.cmdline()
                if any('main.py' in cmd for cmd in cmdline):
                    print(f"🛑 Parando bot: PID {proc.pid}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                        stopped += 1
                    except psutil.TimeoutExpired:
                        print(f"⚠️ Forçando parada: PID {proc.pid}")
                        proc.kill()
                        stopped += 1
        except:
            continue
    
    # Remove arquivo de lock
    lock_file = "/tmp/lol_bot_v3.lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)
        print("🗑️ Lock removido")
    
    if stopped > 0:
        print(f"\n✅ {stopped} instâncias paradas com sucesso!")
    else:
        print("\nℹ️ Nenhuma instância do bot encontrada")

if __name__ == "__main__":
    try:
        stop_all_bots()
    except KeyboardInterrupt:
        print("\n🛑 Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    finally:
        print("\n💡 Para iniciar o bot novamente, use: python main.py") 
