#!/usr/bin/env python3
"""
Script final para corrigir TODOS os problemas de indentação
"""

def fix_all_indentation():
    """Corrige todos os problemas de indentação"""
    
    # Ler arquivo
    with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Correções específicas para problemas conhecidos
    corrections = [
        # Linha com keyboard mal indentada
        ('            keyboard = [', '        keyboard = ['),
        ('            ]', '        ]'),
        ('            reply_markup = InlineKeyboardMarkup(keyboard)', '        reply_markup = InlineKeyboardMarkup(keyboard)'),
        
        # Corrigir o bloco mal estruturado do text_message_handler
        ('💡 **Dica:** Use a interface com botões para melhor experiência!"""\n                \n                keyboard = [', 
         '💡 **Dica:** Use a interface com botões para melhor experiência!"""\n            \n            keyboard = ['),
        ('                [InlineKeyboardButton("🔴 PARTIDAS AO VIVO", callback_data="live_matches_all")],\n                [InlineKeyboardButton("🏠 Menu Principal", callback_data="start")]\n                ]\n                \n                reply_markup = InlineKeyboardMarkup(keyboard)',
         '            [InlineKeyboardButton("🔴 PARTIDAS AO VIVO", callback_data="live_matches_all")],\n            [InlineKeyboardButton("🏠 Menu Principal", callback_data="start")]\n        ]\n        \n        reply_markup = InlineKeyboardMarkup(keyboard)')
    ]
    
    # Aplicar correções
    for old, new in corrections:
        content = content.replace(old, new)
    
    # Salvar arquivo corrigido
    with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Todas as correções aplicadas!")

if __name__ == "__main__":
    fix_all_indentation() 