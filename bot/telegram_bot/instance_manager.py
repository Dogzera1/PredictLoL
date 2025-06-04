"""
Bot Instance Manager
Gerencia instâncias do bot para evitar conflitos
"""

import os
import sys
import psutil
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class BotInstanceManager:
    """Gerenciador de instâncias do bot"""
    
    def __init__(self, lock_file: str = "/tmp/lol_bot_v3.lock"):
        self.lock_file = lock_file
        self.pid = os.getpid()
        
    async def check_instance(self) -> bool:
        """
        Verifica se já existe uma instância rodando
        Returns:
            bool: True se pode continuar, False se deve parar
        """
        try:
            if os.path.exists(self.lock_file):
                try:
                    with open(self.lock_file, 'r') as f:
                        old_pid = int(f.read().strip())
                    
                    # Verifica se o processo ainda existe
                    if psutil.pid_exists(old_pid):
                        logger.error(f"❌ Outra instância do bot já está rodando (PID: {old_pid})")
                        return False
                    else:
                        # Processo morto, remove arquivo
                        os.remove(self.lock_file)
                except (ValueError, FileNotFoundError):
                    # Arquivo inválido ou já removido
                    if os.path.exists(self.lock_file):
                        os.remove(self.lock_file)
            
            # Cria arquivo de lock
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
            
            logger.info(f"✅ Lock de instância adquirido: {self.lock_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar instância: {e}")
            return False
    
    async def release(self) -> None:
        """Libera o lock da instância"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                logger.info("✅ Lock de instância liberado")
        except Exception as e:
            logger.error(f"❌ Erro ao liberar lock: {e}")
    
    @staticmethod
    async def stop_all_instances() -> None:
        """Para todas as instâncias do bot"""
        try:
            current_pid = os.getpid()
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Pula o processo atual
                    if proc.pid == current_pid:
                        continue
                    
                    # Verifica se é um processo Python
                    if proc.name().lower().startswith('python'):
                        cmdline = proc.cmdline()
                        # Verifica se é nosso bot
                        if any('main.py' in cmd for cmd in cmdline):
                            logger.info(f"🛑 Parando instância: PID {proc.pid}")
                            proc.terminate()
                            try:
                                proc.wait(timeout=5)
                            except psutil.TimeoutExpired:
                                proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Remove arquivo de lock
            lock_file = "/tmp/lol_bot_v3.lock"
            if os.path.exists(lock_file):
                os.remove(lock_file)
            
            logger.info("✅ Todas as instâncias paradas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar instâncias: {e}")
    
    @staticmethod
    def create_stop_script() -> None:
        """Cria script para parar todas as instâncias"""
        script = """#!/usr/bin/env python3
import os
import sys
import psutil
import time

def stop_all_bots():
    print("🔍 Procurando instâncias do bot...")
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
        print(f"✅ {stopped} instâncias paradas com sucesso!")
    else:
        print("ℹ️ Nenhuma instância do bot encontrada")

if __name__ == "__main__":
    stop_all_bots()
"""
        
        # Cria script
        script_path = "stop_all_bots.py"
        with open(script_path, 'w') as f:
            f.write(script)
        
        # Torna executável em sistemas Unix
        if sys.platform != "win32":
            os.chmod(script_path, 0o755)
        
        logger.info(f"✅ Script de parada criado: {script_path}") 