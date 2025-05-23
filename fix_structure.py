#!/usr/bin/env python3
"""
Script para corrigir a estrutura try/except quebrada
"""

def fix_structure():
    """Corrige a estrutura do código que está quebrada"""
    
    # Ler arquivo
    with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Correção da função show_all_live_matches que está com estrutura quebrada
    old_broken_section = '''    async def show_all_live_matches(self, update_or_query, is_callback=False):
        """Mostra todas as partidas ao vivo com botões funcionais"""
        try:
            # Mostrar loading
            if is_callback:
                await update_or_query.edit_message_text("🔄 Buscando TODAS as partidas ao vivo...")
            else:
                loading_msg = await update_or_query.message.reply_text("🔄 Buscando TODAS as partidas ao vivo...")
            
            # Buscar partidas ao vivo
            live_matches = await self.riot_api.get_all_live_matches()
            
            if not live_matches:
                text = """🔴 **PARTIDAS AO VIVO**

Não há partidas acontecendo neste momento.

✨ O bot monitora constantemente:
• 🇰🇷 LCK (Coreia)
• 🇨🇳 LPL (China)
• 🇪🇺 LEC (Europa)
• 🇺🇸 LCS (América do Norte)
• 🌍 Torneios internacionais
• 🏆 Ligas regionais menores

🔄 Atualize em alguns minutos!"""
                
        keyboard = [
                    [InlineKeyboardButton("🔄 Atualizar", callback_data="live_matches_all")],
                    [InlineKeyboardButton("🏠 Menu Principal", callback_data="start")]
        ]
                
        reply_markup = InlineKeyboardMarkup(keyboard)
                
            if is_callback:
                    await update_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await loading_msg.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                return'''
    
    new_correct_section = '''    async def show_all_live_matches(self, update_or_query, is_callback=False):
        """Mostra todas as partidas ao vivo com botões funcionais"""
        try:
            # Mostrar loading
            if is_callback:
                await update_or_query.edit_message_text("🔄 Buscando TODAS as partidas ao vivo...")
            else:
                loading_msg = await update_or_query.message.reply_text("🔄 Buscando TODAS as partidas ao vivo...")
            
            # Buscar partidas ao vivo
            live_matches = await self.riot_api.get_all_live_matches()
            
            if not live_matches:
                text = """🔴 **PARTIDAS AO VIVO**

Não há partidas acontecendo neste momento.

✨ O bot monitora constantemente:
• 🇰🇷 LCK (Coreia)
• 🇨🇳 LPL (China)
• 🇪🇺 LEC (Europa)
• 🇺🇸 LCS (América do Norte)
• 🌍 Torneios internacionais
• 🏆 Ligas regionais menores

🔄 Atualize em alguns minutos!"""
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Atualizar", callback_data="live_matches_all")],
                    [InlineKeyboardButton("🏠 Menu Principal", callback_data="start")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if is_callback:
                    await update_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await loading_msg.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                return'''
    
    # Aplicar correção
    content = content.replace(old_broken_section, new_correct_section)
    
    # Salvar arquivo
    with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Estrutura corrigida!")

if __name__ == "__main__":
    fix_structure() 