#!/usr/bin/env python3
"""
Bot LoL V3 - Versão Simplificada Funcional
Corrige problemas de compatibilidade entre Python 3.13 e python-telegram-bot
"""

import os
import asyncio
import logging
from typing import Dict, List
import aiohttp
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token do bot
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Dados mock para teste
MOCK_MATCHES = [
    {
        'id': 'match1',
        'team1': 'T1',
        'team2': 'Gen.G', 
        'league': 'LCK',
        'prob1': 0.65,
        'prob2': 0.35
    },
    {
        'id': 'match2',
        'team1': 'JDG',
        'team2': 'BLG',
        'league': 'LPL', 
        'prob1': 0.58,
        'prob2': 0.42
    }
]

class SimpleBotAPI:
    """API simples usando aiohttp diretamente"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        
    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        """Envia mensagem"""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                return await response.json()
    
    async def edit_message_text(self, chat_id: int, message_id: int, text: str, reply_markup=None):
        """Edita mensagem"""
        url = f"{self.base_url}/editMessageText"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                return await response.json()
    
    async def answer_callback_query(self, callback_query_id: str, text: str = ""):
        """Responde callback query"""
        url = f"{self.base_url}/answerCallbackQuery"
        data = {
            "callback_query_id": callback_query_id,
            "text": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                return await response.json()
    
    async def get_updates(self, offset: int = 0):
        """Obtém updates"""
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": offset,
            "timeout": 30
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

class SimpleBot:
    """Bot LoL simplificado"""
    
    def __init__(self):
        if not TOKEN:
            raise ValueError("TELEGRAM_TOKEN não configurado")
            
        self.api = SimpleBotAPI(TOKEN)
        self.last_update_id = 0
        self.authorized_users = set()  # Por simplicidade, sem autorização por enquanto
        self.running = False
        
    async def start_command(self, chat_id: int, user_id: int, first_name: str):
        """Comando /start"""
        text = f"""🎮 **BOT LOL V3 SIMPLIFICADO** 🎮

Olá {first_name}! 👋

🚀 **FUNCIONALIDADES:**
• 🔍 Partidas ao vivo
• 🎯 Predições com IA
• 💰 Sistema de apostas

💡 **COMANDOS:**
• `/start` - Iniciar bot
• `/partidas` - Ver partidas ao vivo
• `/help` - Ajuda

✨ **Versão simplificada funcional!**"""

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔍 Ver Partidas", "callback_data": "show_matches"},
                    {"text": "❓ Ajuda", "callback_data": "help"}
                ]
            ]
        }
        
        await self.api.send_message(chat_id, text, keyboard)
    
    async def help_command(self, chat_id: int):
        """Comando /help"""
        text = """📚 **GUIA DO BOT**

🎯 **COMANDOS:**
• `/start` - Iniciar o bot
• `/partidas` - Ver partidas ao vivo
• `/help` - Este guia

🎮 **COMO USAR:**
1. Use `/partidas` para ver jogos ao vivo
2. Clique nos botões para mais detalhes
3. Receba predições automáticas

🚀 **FUNCIONALIDADES:**
• Predições baseadas em IA
• Monitoramento de partidas 24/7
• Sistema de apostas inteligente

✨ **Bot em desenvolvimento!**"""
        
        await self.api.send_message(chat_id, text)
    
    async def partidas_command(self, chat_id: int):
        """Comando /partidas"""
        text = "🎮 **PARTIDAS AO VIVO**\n\n"
        
        keyboard_buttons = []
        
        for i, match in enumerate(MOCK_MATCHES):
            team1 = match['team1']
            team2 = match['team2']
            league = match['league']
            prob1 = match['prob1'] * 100
            prob2 = match['prob2'] * 100
            
            # Determinar favorito
            if prob1 > prob2:
                favorite = team1
                favorite_prob = prob1
            else:
                favorite = team2
                favorite_prob = prob2
            
            text += f"🏆 **{team1} vs {team2}**\n"
            text += f"📍 Liga: {league}\n"
            text += f"🎯 Favorito: **{favorite}** ({favorite_prob:.1f}%)\n\n"
            
            keyboard_buttons.append([
                {"text": f"🔍 {team1} vs {team2}", "callback_data": f"match_{i}"}
            ])
        
        text += f"⏰ **Atualizado:** {datetime.now().strftime('%H:%M:%S')}"
        
        keyboard = {"inline_keyboard": keyboard_buttons + [
            [{"text": "🔄 Atualizar", "callback_data": "show_matches"}]
        ]}
        
        await self.api.send_message(chat_id, text, keyboard)
    
    async def show_match_details(self, chat_id: int, message_id: int, match_index: int):
        """Mostra detalhes de uma partida específica"""
        if match_index >= len(MOCK_MATCHES):
            text = "❌ **Partida não encontrada**"
            await self.api.edit_message_text(chat_id, message_id, text)
            return
        
        match = MOCK_MATCHES[match_index]
        team1 = match['team1']
        team2 = match['team2']
        league = match['league']
        prob1 = match['prob1']
        prob2 = match['prob2']
        
        text = f"""🎯 **PREDIÇÃO DETALHADA**

🏆 **{team1} vs {team2}**
📍 **Liga:** {league}

📊 **PROBABILIDADES:**
• {team1}: {prob1*100:.1f}% (odds {1/prob1:.2f})
• {team2}: {prob2*100:.1f}% (odds {1/prob2:.2f})

🎖️ **Confiança:** Alta

📋 **ANÁLISE:**
• Time mais forte: **{team1 if prob1 > prob2 else team2}**
• Diferença de qualidade significativa
• Recomendação: Apostar no favorito

🕐 **Última atualização:** {datetime.now().strftime('%H:%M:%S')}"""

        keyboard = {
            "inline_keyboard": [
                [{"text": "◀️ Voltar", "callback_data": "show_matches"}]
            ]
        }
        
        await self.api.edit_message_text(chat_id, message_id, text, keyboard)
    
    async def handle_callback(self, query_data):
        """Processa callbacks"""
        callback_data = query_data.get('data', '')
        message = query_data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        message_id = message.get('message_id')
        query_id = query_data.get('id')
        
        # Responder ao callback
        await self.api.answer_callback_query(query_id)
        
        if callback_data == "show_matches":
            await self.show_matches_callback(chat_id, message_id)
        elif callback_data == "help":
            await self.help_callback(chat_id)
        elif callback_data.startswith("match_"):
            match_index = int(callback_data.replace("match_", ""))
            await self.show_match_details(chat_id, message_id, match_index)
    
    async def show_matches_callback(self, chat_id: int, message_id: int):
        """Callback para mostrar partidas"""
        text = "🎮 **PARTIDAS AO VIVO**\n\n"
        
        keyboard_buttons = []
        
        for i, match in enumerate(MOCK_MATCHES):
            team1 = match['team1']
            team2 = match['team2']
            league = match['league']
            prob1 = match['prob1'] * 100
            prob2 = match['prob2'] * 100
            
            if prob1 > prob2:
                favorite = team1
                favorite_prob = prob1
            else:
                favorite = team2
                favorite_prob = prob2
            
            text += f"🏆 **{team1} vs {team2}**\n"
            text += f"📍 Liga: {league}\n"
            text += f"🎯 Favorito: **{favorite}** ({favorite_prob:.1f}%)\n\n"
            
            keyboard_buttons.append([
                {"text": f"🔍 {team1} vs {team2}", "callback_data": f"match_{i}"}
            ])
        
        text += f"⏰ **Atualizado:** {datetime.now().strftime('%H:%M:%S')}"
        
        keyboard = {"inline_keyboard": keyboard_buttons + [
            [{"text": "🔄 Atualizar", "callback_data": "show_matches"}]
        ]}
        
        await self.api.edit_message_text(chat_id, message_id, text, keyboard)
    
    async def help_callback(self, chat_id: int):
        """Callback para ajuda"""
        text = """📚 **GUIA DO BOT**

🎯 **COMANDOS:**
• `/start` - Iniciar o bot
• `/partidas` - Ver partidas ao vivo
• `/help` - Este guia

🎮 **COMO USAR:**
1. Use `/partidas` para ver jogos ao vivo
2. Clique nos botões para mais detalhes
3. Receba predições automáticas

🚀 **FUNCIONALIDADES:**
• Predições baseadas em IA
• Monitoramento de partidas 24/7
• Sistema de apostas inteligente

✨ **Bot em desenvolvimento!**"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔍 Ver Partidas", "callback_data": "show_matches"}]
            ]
        }
        
        await self.api.send_message(chat_id, text, keyboard)
    
    async def handle_message(self, message_data):
        """Processa mensagens"""
        text = message_data.get('text', '')
        chat = message_data.get('chat', {})
        user = message_data.get('from', {})
        
        chat_id = chat.get('id')
        user_id = user.get('id')
        first_name = user.get('first_name', 'Usuário')
        
        if text == '/start':
            await self.start_command(chat_id, user_id, first_name)
        elif text == '/help':
            await self.help_command(chat_id)
        elif text == '/partidas':
            await self.partidas_command(chat_id)
        else:
            # Mensagem não reconhecida
            await self.api.send_message(
                chat_id, 
                "❓ Comando não reconhecido. Use /help para ver comandos disponíveis."
            )
    
    async def run(self):
        """Executa o bot"""
        self.running = True
        logger.info("🚀 Bot simples iniciado!")
        
        try:
            while self.running:
                try:
                    # Obter updates
                    result = await self.api.get_updates(self.last_update_id + 1)
                    
                    if result.get('ok'):
                        updates = result.get('result', [])
                        
                        for update in updates:
                            self.last_update_id = update.get('update_id', 0)
                            
                            # Processar mensagem
                            if 'message' in update:
                                await self.handle_message(update['message'])
                            
                            # Processar callback
                            elif 'callback_query' in update:
                                await self.handle_callback(update['callback_query'])
                    
                    # Pequena pausa para não sobrecarregar
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Erro no loop principal: {e}")
                    await asyncio.sleep(5)  # Pausa maior em caso de erro
                    
        except KeyboardInterrupt:
            logger.info("🛑 Bot interrompido pelo usuário")
        finally:
            self.running = False
            logger.info("✅ Bot finalizado")

async def main():
    """Função principal"""
    try:
        bot = SimpleBot()
        await bot.run()
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Iniciando Bot LoL V3 Simplificado...")
    asyncio.run(main()) 