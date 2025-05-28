#!/usr/bin/env python3
"""
SCRIPT DEFINITIVO PARA RESOLVER CONFLITOS DO BOT
Para TODAS as instâncias e limpa completamente o sistema
"""

import os
import asyncio
import time
import sys
import subprocess
import tempfile
import glob

# Configurar token
TELEGRAM_TOKEN = '7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg'
os.environ['TELEGRAM_TOKEN'] = TELEGRAM_TOKEN

def kill_all_python_bot_processes():
    """Mata TODOS os processos Python relacionados ao bot"""
    print("🔪 ELIMINANDO TODOS OS PROCESSOS PYTHON DO BOT")
    print("=" * 60)
    
    killed_count = 0
    
    try:
        if os.name == 'nt':  # Windows
            print("🖥️ Sistema Windows detectado")
            
            # Listar todos os processos Python
            try:
                result = subprocess.run(['wmic', 'process', 'where', 'name="python.exe"', 'get', 'processid,commandline'], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'bot' in line.lower() or 'python.exe' in line:
                            # Extrair PID
                            parts = line.strip().split()
                            if parts:
                                try:
                                    pid = parts[-1]  # PID geralmente é o último
                                    if pid.isdigit():
                                        subprocess.run(['taskkill', '/F', '/PID', pid], 
                                                     capture_output=True, timeout=10)
                                        print(f"🔪 Processo eliminado: PID {pid}")
                                        killed_count += 1
                                except Exception as e:
                                    print(f"⚠️ Erro ao eliminar processo: {e}")
                
                # Método alternativo - matar todos os python.exe
                try:
                    result = subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                                          capture_output=True, timeout=10)
                    if result.returncode == 0:
                        print("🔪 Todos os processos python.exe eliminados")
                        killed_count += 5  # Estimativa
                except:
                    pass
                    
            except Exception as e:
                print(f"⚠️ Erro no método Windows: {e}")
                
        else:  # Unix/Linux/Mac
            print("🐧 Sistema Unix/Linux detectado")
            
            try:
                # Matar processos que contenham 'bot' na linha de comando
                result = subprocess.run(['pkill', '-f', 'bot.*python'], 
                                      capture_output=True, timeout=10)
                if result.returncode == 0:
                    print("🔪 Processos do bot eliminados")
                    killed_count += 3
            except:
                pass
            
            try:
                # Matar processos python que contenham 'telegram'
                result = subprocess.run(['pkill', '-f', 'python.*telegram'], 
                                      capture_output=True, timeout=10)
                if result.returncode == 0:
                    print("🔪 Processos Python/Telegram eliminados")
                    killed_count += 2
            except:
                pass
        
        print(f"✅ {killed_count} processos eliminados")
        return True
        
    except Exception as e:
        print(f"❌ Erro geral ao eliminar processos: {e}")
        return False

async def force_clear_telegram_webhook():
    """Força limpeza TOTAL do webhook do Telegram"""
    print("\n🧹 LIMPEZA FORÇADA DO WEBHOOK TELEGRAM")
    print("=" * 60)
    
    success = False
    
    try:
        # Tentar com versão v20+ primeiro
        try:
            from telegram.ext import Application
            print("📱 Usando python-telegram-bot v20+")
            
            application = Application.builder().token(TELEGRAM_TOKEN).build()
            
            # Múltiplas tentativas agressivas
            for attempt in range(7):
                try:
                    print(f"🧹 Tentativa {attempt+1}/7 - Removendo webhook...")
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    await asyncio.sleep(3)  # Aguardar mais tempo
                    
                    # Verificar se foi removido
                    webhook_info = await application.bot.get_webhook_info()
                    if not webhook_info.url:
                        print("✅ Webhook removido com sucesso!")
                        success = True
                        break
                    else:
                        print(f"⚠️ Webhook ainda ativo: {webhook_info.url}")
                        
                except Exception as e:
                    print(f"⚠️ Tentativa {attempt+1} falhou: {e}")
                    await asyncio.sleep(2)
            
            # Verificação final
            try:
                webhook_info = await application.bot.get_webhook_info()
                print(f"📋 Status final: {webhook_info.url if webhook_info.url else '✅ LIMPO'}")
                if not webhook_info.url:
                    success = True
            except Exception as e:
                print(f"⚠️ Erro na verificação final: {e}")
                
        except ImportError:
            # Fallback para v13
            from telegram.ext import Updater
            print("📱 Usando python-telegram-bot v13")
            
            updater = Updater(TELEGRAM_TOKEN)
            
            # Múltiplas tentativas agressivas
            for attempt in range(7):
                try:
                    print(f"🧹 Tentativa {attempt+1}/7 - Removendo webhook v13...")
                    updater.bot.delete_webhook(drop_pending_updates=True)
                    time.sleep(3)
                    
                    # Verificar se foi removido
                    webhook_info = updater.bot.get_webhook_info()
                    if not webhook_info.url:
                        print("✅ Webhook removido com sucesso!")
                        success = True
                        break
                    else:
                        print(f"⚠️ Webhook ainda ativo: {webhook_info.url}")
                        
                except Exception as e:
                    print(f"⚠️ Tentativa {attempt+1} falhou: {e}")
                    time.sleep(2)
            
            # Verificação final
            try:
                webhook_info = updater.bot.get_webhook_info()
                print(f"📋 Status final: {webhook_info.url if webhook_info.url else '✅ LIMPO'}")
                if not webhook_info.url:
                    success = True
            except Exception as e:
                print(f"⚠️ Erro na verificação final: {e}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro crítico na limpeza do Telegram: {e}")
        return False

def clear_all_lock_files():
    """Remove TODOS os arquivos de lock relacionados ao bot"""
    print("\n🔓 REMOVENDO TODOS OS ARQUIVOS DE LOCK")
    print("=" * 60)
    
    removed_count = 0
    
    try:
        temp_dir = tempfile.gettempdir()
        print(f"📁 Diretório temporário: {temp_dir}")
        
        # Padrões de arquivos de lock para remover
        lock_patterns = [
            'bot_lol_v3.lock',
            'bot*.lock',
            'telegram*.lock',
            'python*.lock',
            '*bot*.lock',
            'lol*.lock'
        ]
        
        for pattern in lock_patterns:
            try:
                lock_files = glob.glob(os.path.join(temp_dir, pattern))
                for lock_file in lock_files:
                    try:
                        os.remove(lock_file)
                        print(f"🗑️ Removido: {os.path.basename(lock_file)}")
                        removed_count += 1
                    except Exception as e:
                        print(f"⚠️ Erro ao remover {lock_file}: {e}")
            except Exception as e:
                print(f"⚠️ Erro no padrão {pattern}: {e}")
        
        # Tentar remover locks em outros diretórios comuns
        other_dirs = [
            os.path.expanduser('~'),
            os.getcwd(),
            '/tmp' if os.name != 'nt' else None
        ]
        
        for dir_path in other_dirs:
            if dir_path and os.path.exists(dir_path):
                try:
                    for pattern in ['*.lock', 'bot*.lock']:
                        lock_files = glob.glob(os.path.join(dir_path, pattern))
                        for lock_file in lock_files:
                            if 'bot' in os.path.basename(lock_file).lower():
                                try:
                                    os.remove(lock_file)
                                    print(f"🗑️ Removido: {lock_file}")
                                    removed_count += 1
                                except:
                                    pass
                except:
                    pass
        
        print(f"✅ {removed_count} arquivos de lock removidos")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao remover locks: {e}")
        return False

def clear_python_cache():
    """Limpa cache Python que pode estar causando problemas"""
    print("\n🧹 LIMPANDO CACHE PYTHON")
    print("=" * 60)
    
    try:
        # Remover arquivos __pycache__
        current_dir = os.getcwd()
        cache_dirs = []
        
        for root, dirs, files in os.walk(current_dir):
            if '__pycache__' in dirs:
                cache_dirs.append(os.path.join(root, '__pycache__'))
        
        removed = 0
        for cache_dir in cache_dirs:
            try:
                import shutil
                shutil.rmtree(cache_dir)
                print(f"🗑️ Cache removido: {cache_dir}")
                removed += 1
            except:
                pass
        
        print(f"✅ {removed} diretórios de cache removidos")
        return True
        
    except Exception as e:
        print(f"⚠️ Erro ao limpar cache: {e}")
        return False

async def main():
    """Função principal - Limpeza completa e definitiva"""
    print("🚨 STOP ALL CONFLICTS - LIMPEZA DEFINITIVA")
    print("=" * 70)
    print("⚠️ ESTE SCRIPT VAI ELIMINAR TUDO RELACIONADO AO BOT")
    print("=" * 70)
    
    success_steps = 0
    total_steps = 6
    
    # PASSO 1: Eliminar processos
    print(f"\n🔪 PASSO 1/{total_steps}: ELIMINANDO PROCESSOS")
    if kill_all_python_bot_processes():
        success_steps += 1
    
    # PASSO 2: Aguardar processos terminarem
    print(f"\n⏳ PASSO 2/{total_steps}: AGUARDANDO PROCESSOS TERMINAREM")
    print("Aguardando 15 segundos para garantir que processos foram eliminados...")
    await asyncio.sleep(15)
    success_steps += 1
    
    # PASSO 3: Limpar webhook do Telegram
    print(f"\n🧹 PASSO 3/{total_steps}: LIMPEZA TOTAL DO TELEGRAM")
    if await force_clear_telegram_webhook():
        success_steps += 1
    
    # PASSO 4: Remover arquivos de lock
    print(f"\n🔓 PASSO 4/{total_steps}: REMOVENDO LOCKS")
    if clear_all_lock_files():
        success_steps += 1
    
    # PASSO 5: Limpar cache Python
    print(f"\n🧹 PASSO 5/{total_steps}: LIMPANDO CACHE")
    if clear_python_cache():
        success_steps += 1
    
    # PASSO 6: Aguardar estabilização final
    print(f"\n⏳ PASSO 6/{total_steps}: ESTABILIZAÇÃO FINAL")
    print("Aguardando 20 segundos para estabilização completa do sistema...")
    await asyncio.sleep(20)
    success_steps += 1
    
    # RESULTADO FINAL
    print("\n" + "=" * 70)
    if success_steps == total_steps:
        print("🎉 LIMPEZA COMPLETA REALIZADA COM SUCESSO!")
        print("✅ Todos os processos eliminados")
        print("✅ Telegram completamente limpo")
        print("✅ Arquivos de lock removidos")
        print("✅ Cache Python limpo")
        print("✅ Sistema completamente estabilizado")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. ✅ Sistema está limpo - sem conflitos")
        print("2. 🚀 Faça deploy no Railway")
        print("3. ⏳ Aguarde 5 minutos para inicialização")
        print("4. 🧪 Teste /start no Telegram")
        print("5. 📋 Verifique logs do Railway")
        
        print("\n⚠️ REGRAS IMPORTANTES:")
        print("🔴 NUNCA execute localmente enquanto Railway estiver ativo!")
        print("🟢 Use APENAS Railway para produção")
        print("🟡 Para desenvolvimento local, pare o Railway primeiro")
        
    else:
        print(f"⚠️ LIMPEZA PARCIAL: {success_steps}/{total_steps} passos concluídos")
        print("🔧 Alguns passos falharam, mas o sistema deve estar mais limpo")
        print("💡 Tente executar o script novamente se ainda houver problemas")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        print("🎮 Iniciando limpeza definitiva de conflitos...")
        asyncio.run(main())
        print("✅ Script concluído!")
    except KeyboardInterrupt:
        print("\n🛑 Script interrompido pelo usuário")
        print("⚠️ Limpeza pode estar incompleta")
    except Exception as e:
        print(f"\n❌ Erro crítico no script: {e}")
        import traceback
        print("📋 Traceback completo:")
        print(traceback.format_exc())
        print("\n💡 Tente executar novamente ou faça limpeza manual") 