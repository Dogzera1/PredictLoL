#!/usr/bin/env python3
"""
Script avançado para limpar completamente instâncias do bot
e resolver conflitos de getUpdates
"""

import os
import asyncio
import aiohttp
import sys
import time
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class BotCleaner:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    async def force_stop_all_instances(self):
        """Para todas as instâncias do bot de forma agressiva"""
        print("🧹 LIMPEZA COMPLETA DO BOT")
        print("="*50)
        
        if not self.bot_token or self.bot_token == "BOT_TOKEN_HERE":
            print("❌ Token do bot não configurado")
            return False
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # 1. Verifica status inicial
                print("🔍 Verificando status inicial do bot...")
                bot_info = await self._get_bot_info(session)
                if not bot_info:
                    return False
                
                print(f"🤖 Bot: @{bot_info['username']} ({bot_info['first_name']})")
                
                # 2. Remove webhook (se existir)
                print("\n📡 Removendo webhook...")
                await self._remove_webhook(session)
                
                # 3. Para polling de forma agressiva (múltiplas tentativas)
                print("\n🛑 Parando polling ativo (pode demorar)...")
                await self._force_stop_polling(session)
                
                # 4. Limpa updates pendentes
                print("\n🧹 Limpando updates pendentes...")
                await self._clear_pending_updates(session)
                
                # 5. Verifica se limpeza foi bem-sucedida
                print("\n✅ Verificando limpeza...")
                success = await self._verify_cleanup(session)
                
                return success
                
        except Exception as e:
            print(f"❌ Erro durante limpeza: {e}")
            return False
    
    async def _get_bot_info(self, session):
        """Obtém informações do bot"""
        try:
            async with session.get(f"{self.base_url}/getMe") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        return data["result"]
                print("❌ Bot não está acessível")
                return None
        except Exception as e:
            print(f"❌ Erro ao verificar bot: {e}")
            return None
    
    async def _remove_webhook(self, session):
        """Remove webhook se existir"""
        try:
            async with session.post(f"{self.base_url}/deleteWebhook") as resp:
                if resp.status == 200:
                    print("✅ Webhook removido")
                else:
                    print("⚠️ Webhook não existia")
        except Exception as e:
            print(f"⚠️ Erro ao remover webhook: {e}")
    
    async def _force_stop_polling(self, session):
        """Para polling de forma agressiva com múltiplas tentativas"""
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                print(f"🔄 Tentativa {attempt + 1}/{max_attempts}")
                
                # Chama getUpdates com timeout baixo para "roubar" o controle
                async with session.post(
                    f"{self.base_url}/getUpdates", 
                    json={"timeout": 1, "limit": 1},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok"):
                            print(f"✅ Polling interrompido (tentativa {attempt + 1})")
                            break
                    elif resp.status == 409:  # Conflict
                        print(f"⚠️ Conflito detectado (tentativa {attempt + 1})")
                        # Aguarda um pouco antes da próxima tentativa
                        await asyncio.sleep(2)
                        continue
                
            except asyncio.TimeoutError:
                print(f"⏰ Timeout na tentativa {attempt + 1}")
                continue
            except Exception as e:
                print(f"⚠️ Erro na tentativa {attempt + 1}: {e}")
                await asyncio.sleep(1)
                continue
        
        # Aguarda um pouco para garantir que parou
        print("⏳ Aguardando estabilização...")
        await asyncio.sleep(3)
    
    async def _clear_pending_updates(self, session):
        """Limpa todos os updates pendentes"""
        try:
            # Pega todos os updates pendentes e os descarta
            async with session.post(
                f"{self.base_url}/getUpdates", 
                json={"timeout": 0, "limit": 100, "offset": -1}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        updates = data.get("result", [])
                        print(f"🧹 {len(updates)} updates pendentes limpos")
                    else:
                        print("⚠️ Erro ao limpar updates")
                else:
                    print("⚠️ Falha ao acessar updates")
        except Exception as e:
            print(f"⚠️ Erro ao limpar updates: {e}")
    
    async def _verify_cleanup(self, session):
        """Verifica se a limpeza foi bem-sucedida"""
        try:
            # Tenta fazer uma chamada simples de getMe
            async with session.get(f"{self.base_url}/getMe") as resp:
                if resp.status == 200:
                    print("✅ Bot está limpo e acessível")
                    return True
                else:
                    print("❌ Bot não está acessível após limpeza")
                    return False
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            return False

async def main():
    """Função principal"""
    cleaner = BotCleaner()
    
    print("🚀 INICIANDO LIMPEZA COMPLETA DO BOT")
    print("⚠️  Isso pode demorar até 30 segundos...")
    print("="*50)
    
    success = await cleaner.force_stop_all_instances()
    
    print("\n" + "="*50)
    if success:
        print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("🚀 Bot está pronto para deploy no Railway")
        print("💡 Aguarde 10 segundos antes de fazer deploy")
    else:
        print("❌ LIMPEZA FALHOU")
        print("⚠️  Pode ser necessário aguardar alguns minutos")
        print("💡 Ou contatar @BotFather para resetar o bot")
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main()) 