#!/usr/bin/env python3
"""
Script ULTRA AGRESSIVO para forçar desconexão total
Remove qualquer instância remota e força controle local
"""
import asyncio
import aiohttp
import time
import subprocess
import sys
import os
import psutil

BOT_TOKEN = "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0"

class UltraDisconnectForcer:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
        self.success_count = 0
        self.total_attempts = 0

    async def force_total_disconnection(self):
        """Força desconexão total de qualquer instância"""
        print("🚨 FORÇANDO DESCONEXÃO TOTAL DE INSTÂNCIAS")
        print("=" * 60)
        print("⚡ ATENÇÃO: Modo ultra agressivo ativado")
        print("🔥 Vai fazer 100+ requests para forçar controle")
        print("=" * 60)
        
        # Fase 1: Bombardeio inicial
        await self._phase_1_initial_bombardment()
        
        # Fase 2: Remoção agressiva de webhooks
        await self._phase_2_webhook_destruction()
        
        # Fase 3: Limpeza total de updates
        await self._phase_3_total_cleanup()
        
        # Fase 4: Verificação de controle
        await self._phase_4_control_verification()
        
        # Fase 5: Teste final
        return await self._phase_5_final_test()

    async def _phase_1_initial_bombardment(self):
        """Fase 1: Bombardeio inicial para quebrar qualquer conexão"""
        print("\n🔥 FASE 1: BOMBARDEIO INICIAL")
        print("-" * 40)
        print("📡 Enviando 50 requests simultâneos...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Cria 50 tasks simultâneas
            for i in range(50):
                task = asyncio.create_task(
                    self._aggressive_getUpdates(session, i+1)
                )
                tasks.append(task)
            
            # Executa tudo em paralelo
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success = sum(1 for r in results if r is True)
            print(f"✅ {success}/50 requests bem-sucedidas")
            self.success_count += success
            self.total_attempts += 50

    async def _phase_2_webhook_destruction(self):
        """Fase 2: Destruição agressiva de webhooks"""
        print("\n🔥 FASE 2: DESTRUIÇÃO DE WEBHOOKS")
        print("-" * 40)
        
        async with aiohttp.ClientSession() as session:
            # Múltiplas tentativas de remoção
            for attempt in range(20):
                try:
                    async with session.post(f"{self.base_url}/deleteWebhook") as resp:
                        if resp.status == 200:
                            print(f"   ✅ Webhook removido (tentativa {attempt+1})")
                        else:
                            print(f"   ⚠️ Status {resp.status} (tentativa {attempt+1})")
                except Exception as e:
                    print(f"   ❌ Erro tentativa {attempt+1}: {str(e)[:50]}")
                
                await asyncio.sleep(0.3)
            
            # Verifica se webhook foi realmente removido
            try:
                async with session.post(f"{self.base_url}/getWebhookInfo") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        webhook_url = data.get('result', {}).get('url', '')
                        if webhook_url:
                            print(f"   ❌ WEBHOOK AINDA ATIVO: {webhook_url}")
                        else:
                            print("   ✅ Webhook completamente removido")
            except:
                pass

    async def _phase_3_total_cleanup(self):
        """Fase 3: Limpeza total de updates"""
        print("\n🔥 FASE 3: LIMPEZA TOTAL DE UPDATES")
        print("-" * 40)
        
        async with aiohttp.ClientSession() as session:
            print("📥 Limpando todos os updates pendentes...")
            
            # Várias ondas de limpeza
            for wave in range(5):
                print(f"   Onda {wave+1}/5...")
                
                # 20 requests por onda
                tasks = []
                for i in range(20):
                    task = asyncio.create_task(
                        self._cleanup_updates(session, wave, i)
                    )
                    tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(1)
            
            print("✅ Limpeza total concluída")

    async def _phase_4_control_verification(self):
        """Fase 4: Verificação de controle"""
        print("\n🔥 FASE 4: VERIFICAÇÃO DE CONTROLE")
        print("-" * 40)
        
        async with aiohttp.ClientSession() as session:
            # Testa controle com múltiplas tentativas
            control_tests = 0
            
            for test in range(10):
                try:
                    async with session.post(
                        f"{self.base_url}/getUpdates",
                        json={"timeout": 1, "limit": 1}
                    ) as resp:
                        if resp.status == 200:
                            control_tests += 1
                            print(f"   ✅ Teste {test+1}: Controle OK")
                        elif resp.status == 409:
                            print(f"   ❌ Teste {test+1}: CONFLITO PERSISTENTE")
                        else:
                            print(f"   ⚠️ Teste {test+1}: Status {resp.status}")
                except Exception as e:
                    print(f"   ❌ Teste {test+1}: Erro {str(e)[:30]}")
                
                await asyncio.sleep(0.5)
            
            print(f"📊 Taxa de controle: {control_tests}/10 ({control_tests*10}%)")
            return control_tests >= 7  # 70% de sucesso

    async def _phase_5_final_test(self):
        """Fase 5: Teste final de operação"""
        print("\n🔥 FASE 5: TESTE FINAL")
        print("-" * 30)
        
        await asyncio.sleep(5)  # Aguarda estabilização
        
        try:
            async with aiohttp.ClientSession() as session:
                # Teste de bot info
                async with session.get(f"{self.base_url}/getMe") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        bot_info = data.get('result', {})
                        print(f"✅ Bot verificado: @{bot_info.get('username')}")
                    else:
                        print(f"❌ Bot inacessível: {resp.status}")
                        return False
                
                # Teste de polling
                async with session.post(
                    f"{self.base_url}/getUpdates",
                    json={"timeout": 3, "limit": 1}
                ) as resp:
                    if resp.status == 200:
                        print("✅ Polling 100% funcional")
                        return True
                    elif resp.status == 409:
                        print("❌ CONFLITO AINDA PERSISTE")
                        return False
                    else:
                        print(f"⚠️ Status inesperado: {resp.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Erro no teste final: {e}")
            return False

    async def _aggressive_getUpdates(self, session, attempt_num):
        """Request agressivo de getUpdates"""
        try:
            async with session.post(
                f"{self.base_url}/getUpdates",
                json={"timeout": 0, "limit": 100, "offset": -1}
            ) as resp:
                return resp.status == 200
        except:
            return False

    async def _cleanup_updates(self, session, wave, request_num):
        """Limpeza individual de updates"""
        try:
            # Vários tipos de requests para limpeza
            request_types = [
                {"timeout": 0, "limit": 100},
                {"timeout": 0, "limit": 1, "offset": -1},
                {"timeout": 1, "limit": 50},
            ]
            
            for req_type in request_types:
                async with session.post(
                    f"{self.base_url}/getUpdates",
                    json=req_type
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        updates = data.get('result', [])
                        if updates:
                            # Confirma limpeza com offset
                            last_update_id = updates[-1].get('update_id')
                            if last_update_id:
                                await session.post(
                                    f"{self.base_url}/getUpdates",
                                    json={"offset": last_update_id + 1, "timeout": 0}
                                )
                await asyncio.sleep(0.1)
        except:
            pass

    def kill_local_processes(self):
        """Mata todos os processos Python locais suspeitos"""
        print("\n🔪 MATANDO PROCESSOS LOCAIS")
        print("-" * 30)
        
        killed_count = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        
                        # Não mata o próprio processo
                        if proc.pid == os.getpid():
                            continue
                            
                        if any(keyword in cmdline.lower() for keyword in ['bot', 'telegram', 'main.py', 'schedule']):
                            print(f"   🔪 Matando processo: PID {proc.pid}")
                            proc.terminate()
                            proc.wait(timeout=3)
                            killed_count += 1
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
                    
            print(f"✅ {killed_count} processos eliminados")
            
        except Exception as e:
            print(f"❌ Erro ao matar processos: {e}")

    def show_summary(self, success):
        """Mostra resumo da operação"""
        print("\n📋 RESUMO DA OPERAÇÃO ULTRA AGRESSIVA")
        print("=" * 50)
        
        print(f"📊 Estatísticas:")
        print(f"   • Requests enviados: {self.total_attempts}")
        print(f"   • Sucessos: {self.success_count}")
        print(f"   • Taxa de sucesso: {(self.success_count/self.total_attempts)*100:.1f}%")
        
        if success:
            print("\n🎉 OPERAÇÃO BEM-SUCEDIDA!")
            print("✅ Controle total do bot estabelecido")
            print("🚀 Bot pronto para uso local")
            print("\n💡 Próximos passos:")
            print("   1. Execute: python main.py")
            print("   2. O bot deve iniciar sem conflitos")
        else:
            print("\n⚠️ CONFLITOS PERSISTENTES!")
            print("🔍 Possíveis causas:")
            print("   • Instância em serviço não verificado")
            print("   • Webhook configurado externamente")
            print("   • Cache do Telegram com lag")
            print("\n💡 Soluções alternativas:")
            print("   1. Aguardar 5-10 minutos")
            print("   2. Usar modo webhook local")
            print("   3. Criar bot de teste separado")

async def main():
    print("🚨 ULTRA DISCONNECT FORCER")
    print("=" * 50)
    print("⚡ MODO: Máxima agressividade")
    print("🎯 OBJETIVO: Forçar controle total local")
    print("=" * 50)
    
    forcer = UltraDisconnectForcer()
    
    # Mata processos locais primeiro
    forcer.kill_local_processes()
    
    # Força desconexão total
    success = await forcer.force_total_disconnection()
    
    # Mostra resumo
    forcer.show_summary(success)

if __name__ == "__main__":
    asyncio.run(main()) 
