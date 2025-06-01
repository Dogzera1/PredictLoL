#!/usr/bin/env python3
"""
Script diagnóstico e correção para conflitos de polling/webhook
Detecta instâncias remotas e garante operação limpa
"""
import asyncio
import aiohttp
import subprocess
import sys
import os
import psutil
import time
from pathlib import Path

BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"

class ConflictDiagnostic:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
        self.issues_found = []
        self.solutions_applied = []

    async def run_full_diagnostic(self):
        """Executa diagnóstico completo e aplicação de soluções"""
        print("🔍 DIAGNÓSTICO COMPLETO DE CONFLITOS")
        print("=" * 50)
        
        # 1. Verificar status atual do bot
        await self._check_bot_status()
        
        # 2. Detectar instâncias locais do Python
        self._check_local_python_instances()
        
        # 3. Verificar webhook status
        await self._check_webhook_status()
        
        # 4. Testar capacidade de polling
        await self._test_polling_capability()
        
        # 5. Verificar instâncias remotas
        await self._detect_remote_instances()
        
        # 6. Aplicar soluções
        await self._apply_solutions()
        
        # 7. Verificação final
        await self._final_verification()
        
        self._show_summary()

    async def _check_bot_status(self):
        """Verifica status básico do bot"""
        print("\n🤖 VERIFICANDO STATUS DO BOT")
        print("-" * 30)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/getMe") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        bot_info = data.get('result', {})
                        print(f"✅ Bot ativo: @{bot_info.get('username')}")
                        print(f"   ID: {bot_info.get('id')}")
                        print(f"   Nome: {bot_info.get('first_name')}")
                    else:
                        print(f"❌ Bot inacessível: Status {resp.status}")
                        self.issues_found.append("Bot inacessível")
        except Exception as e:
            print(f"❌ Erro ao verificar bot: {e}")
            self.issues_found.append(f"Erro de conectividade: {e}")

    def _check_local_python_instances(self):
        """Verifica instâncias locais do Python rodando"""
        print("\n🐍 VERIFICANDO INSTÂNCIAS PYTHON LOCAIS")
        print("-" * 40)
        
        try:
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if any(keyword in cmdline.lower() for keyword in ['bot', 'telegram', 'main.py', 'schedule']):
                            python_processes.append({
                                'pid': proc.info['pid'],
                                'cmd': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if python_processes:
                print(f"⚠️ {len(python_processes)} processos Python relacionados encontrados:")
                for proc in python_processes:
                    print(f"   PID {proc['pid']}: {proc['cmd']}")
                self.issues_found.append(f"{len(python_processes)} processos Python ativos")
            else:
                print("✅ Nenhum processo Python suspeito encontrado")
                
        except Exception as e:
            print(f"❌ Erro ao verificar processos: {e}")

    async def _check_webhook_status(self):
        """Verifica status do webhook"""
        print("\n🔗 VERIFICANDO STATUS DO WEBHOOK")
        print("-" * 35)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/getWebhookInfo") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        webhook_info = data.get('result', {})
                        
                        webhook_url = webhook_info.get('url', '')
                        if webhook_url:
                            print(f"⚠️ WEBHOOK ATIVO DETECTADO!")
                            print(f"   URL: {webhook_url}")
                            print(f"   Pending: {webhook_info.get('pending_update_count', 0)}")
                            print(f"   Última erro: {webhook_info.get('last_error_message', 'Nenhum')}")
                            self.issues_found.append("Webhook ativo conflitando com polling")
                        else:
                            print("✅ Nenhum webhook ativo")
                    else:
                        print(f"❌ Erro ao verificar webhook: Status {resp.status}")
        except Exception as e:
            print(f"❌ Erro ao verificar webhook: {e}")

    async def _test_polling_capability(self):
        """Testa capacidade de polling"""
        print("\n📞 TESTANDO CAPACIDADE DE POLLING")
        print("-" * 35)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Teste simples de getUpdates
                async with session.post(
                    f"{self.base_url}/getUpdates",
                    json={"timeout": 1, "limit": 1}
                ) as resp:
                    if resp.status == 200:
                        print("✅ Polling funcional")
                    elif resp.status == 409:
                        response_text = await resp.text()
                        if "conflict" in response_text.lower():
                            print("❌ CONFLITO DETECTADO: Outra instância fazendo polling")
                            self.issues_found.append("Conflito de polling ativo")
                        else:
                            print(f"⚠️ Erro 409 não relacionado a conflito: {response_text}")
                    else:
                        print(f"❌ Erro no polling: Status {resp.status}")
                        response_text = await resp.text()
                        print(f"   Resposta: {response_text[:200]}")
        except Exception as e:
            print(f"❌ Erro ao testar polling: {e}")

    async def _detect_remote_instances(self):
        """Tenta detectar instâncias remotas"""
        print("\n🌐 DETECTANDO INSTÂNCIAS REMOTAS")
        print("-" * 35)
        
        # Verifica se há updates sendo processados rapidamente
        try:
            async with aiohttp.ClientSession() as session:
                print("   Testando reatividade do bot...")
                
                # Faz múltiplos requests rápidos para ver se alguém mais está consumindo
                start_time = time.time()
                requests_success = 0
                
                for i in range(5):
                    try:
                        async with session.post(
                            f"{self.base_url}/getUpdates",
                            json={"timeout": 0, "limit": 1, "offset": -1}
                        ) as resp:
                            if resp.status == 200:
                                requests_success += 1
                            elif resp.status == 409:
                                print(f"   ❌ Conflito na tentativa {i+1}")
                            await asyncio.sleep(0.5)
                    except:
                        pass
                
                end_time = time.time()
                response_time = (end_time - start_time) / 5
                
                if requests_success < 3:
                    print("⚠️ POSSÍVEL INSTÂNCIA REMOTA ATIVA")
                    print("   Indicadores:")
                    print(f"   - Baixa taxa de sucesso: {requests_success}/5")
                    print(f"   - Tempo médio: {response_time:.2f}s")
                    print("   - Possíveis locais: Railway, Heroku, VPS")
                    self.issues_found.append("Possível instância remota ativa")
                else:
                    print("✅ Nenhuma instância remota detectada")
                    
        except Exception as e:
            print(f"❌ Erro na detecção remota: {e}")

    async def _apply_solutions(self):
        """Aplica soluções para os problemas encontrados"""
        print("\n🛠️ APLICANDO SOLUÇÕES")
        print("-" * 25)
        
        if not self.issues_found:
            print("✅ Nenhum problema encontrado, nada a corrigir")
            return
        
        # Solução 1: Remover webhook se existir
        if any("webhook" in issue.lower() for issue in self.issues_found):
            print("🔧 Removendo webhook...")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.base_url}/deleteWebhook") as resp:
                        if resp.status == 200:
                            print("   ✅ Webhook removido")
                            self.solutions_applied.append("Webhook removido")
                        else:
                            print(f"   ❌ Falha ao remover webhook: {resp.status}")
            except Exception as e:
                print(f"   ❌ Erro ao remover webhook: {e}")
        
        # Solução 2: Forçar limpeza de getUpdates
        if any("conflito" in issue.lower() for issue in self.issues_found):
            print("🔧 Forçando limpeza de conflitos...")
            try:
                async with aiohttp.ClientSession() as session:
                    # Múltiplas tentativas agressivas
                    for i in range(10):
                        async with session.post(
                            f"{self.base_url}/getUpdates",
                            json={"timeout": 0, "limit": 100, "offset": -1}
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                updates_count = len(data.get('result', []))
                                if updates_count > 0:
                                    print(f"   📥 Limpou {updates_count} updates")
                        await asyncio.sleep(0.5)
                    
                    self.solutions_applied.append("Conflitos de getUpdates limpos")
                    print("   ✅ Limpeza de conflitos concluída")
            except Exception as e:
                print(f"   ❌ Erro na limpeza: {e}")
        
        # Solução 3: Parar processos Python locais
        if any("processos python" in issue.lower() for issue in self.issues_found):
            print("🔧 Sugestão: Parar processos Python suspeitos")
            print("   Execute: python stop_all_bots.py")
            self.solutions_applied.append("Sugestão para parar processos locais")

    async def _final_verification(self):
        """Verificação final após aplicação de soluções"""
        print("\n🧪 VERIFICAÇÃO FINAL")
        print("-" * 20)
        
        await asyncio.sleep(3)  # Aguarda estabilização
        
        try:
            async with aiohttp.ClientSession() as session:
                # Teste final de polling
                async with session.post(
                    f"{self.base_url}/getUpdates",
                    json={"timeout": 2, "limit": 1}
                ) as resp:
                    if resp.status == 200:
                        print("✅ Polling operacional")
                    elif resp.status == 409:
                        print("❌ Conflitos persistem - possível instância remota")
                    else:
                        print(f"⚠️ Status inesperado: {resp.status}")
        except Exception as e:
            print(f"❌ Erro na verificação final: {e}")

    def _show_summary(self):
        """Mostra resumo do diagnóstico"""
        print("\n📋 RESUMO DO DIAGNÓSTICO")
        print("=" * 30)
        
        print(f"\n🔍 Problemas encontrados ({len(self.issues_found)}):")
        for issue in self.issues_found:
            print(f"   ❌ {issue}")
        
        print(f"\n🛠️ Soluções aplicadas ({len(self.solutions_applied)}):")
        for solution in self.solutions_applied:
            print(f"   ✅ {solution}")
        
        if not self.issues_found:
            print("\n🎉 SISTEMA LIMPO!")
            print("💡 Execute: python main.py")
        elif len(self.solutions_applied) >= len(self.issues_found):
            print("\n✅ PROBLEMAS RESOLVIDOS!")
            print("💡 Aguarde 30s e execute: python main.py")
        else:
            print("\n⚠️ PROBLEMAS PERSISTENTES!")
            print("💡 Possíveis ações:")
            print("   1. Verificar instâncias remotas (Railway, Heroku)")
            print("   2. Aguardar mais tempo para estabilização")
            print("   3. Executar stop_all_bots.py")

async def main():
    print("🔍 DIAGNÓSTICO E CORREÇÃO DE CONFLITOS")
    print("=" * 50)
    print("⚡ Detectando conflitos polling/webhook")
    print("🌐 Verificando instâncias remotas")
    print("🛠️ Aplicando correções automáticas")
    print("=" * 50)
    
    diagnostic = ConflictDiagnostic()
    await diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    asyncio.run(main()) 