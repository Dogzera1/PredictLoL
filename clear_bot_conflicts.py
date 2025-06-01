#!/usr/bin/env python3
"""
Script para limpar conflitos do Bot Telegram - Solução Definitiva
"""
import asyncio
import aiohttp
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"

async def force_clear_bot_conflicts():
    """Força limpeza completa de conflitos"""
    logger.info("🧹 Iniciando limpeza forçada de conflitos...")
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Múltiplas tentativas de getUpdates para "roubar" controle
            logger.info("📡 Fazendo múltiplas requisições getUpdates...")
            for i in range(10):
                try:
                    async with session.post(
                        f"{base_url}/getUpdates", 
                        json={"timeout": 1, "offset": -1}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            logger.info(f"✅ Requisição {i+1}/10 - {len(data.get('result', []))} updates limpos")
                        await asyncio.sleep(0.5)
                except Exception as e:
                    logger.debug(f"Tentativa {i+1}: {e}")
            
            # 2. Remove webhook se existir
            logger.info("🔗 Removendo webhook...")
            try:
                async with session.post(f"{base_url}/deleteWebhook") as resp:
                    if resp.status == 200:
                        logger.info("✅ Webhook removido com sucesso")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao remover webhook: {e}")
            
            # 3. Aguarda estabilização
            logger.info("⏳ Aguardando estabilização (10s)...")
            await asyncio.sleep(10)
            
            # 4. Teste final
            logger.info("🧪 Testando conectividade...")
            try:
                async with session.post(f"{base_url}/getMe") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        bot_info = data.get('result', {})
                        logger.info(f"✅ Bot limpo: @{bot_info.get('username')} ({bot_info.get('first_name')})")
                    else:
                        logger.error(f"❌ Erro no teste: {resp.status}")
            except Exception as e:
                logger.error(f"❌ Erro no teste final: {e}")
            
            logger.info("🎉 Limpeza de conflitos concluída!")
            
        except Exception as e:
            logger.error(f"❌ Erro durante limpeza: {e}")

async def main():
    await force_clear_bot_conflicts()
    
    # Aguarda um pouco antes de finalizar
    logger.info("✅ Script finalizado. Agora pode iniciar o bot normalmente.")

if __name__ == "__main__":
    asyncio.run(main()) 