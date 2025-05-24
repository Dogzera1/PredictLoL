#!/usr/bin/env python3
"""
Script para corrigir especificamente as linhas 973, 975, 979 com problemas de indentação
"""

def fix_specific_lines():
    print("🔧 Corrigindo linhas específicas com problemas de indentação...")
    
    # Ler arquivo
    with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Corrigir linhas específicas
    # Linha 973: reply_markup = InlineKeyboardMarkup(keyboard)
    if len(lines) > 972:
        lines[972] = "            reply_markup = InlineKeyboardMarkup(keyboard)\n"
    
    # Linha 975: if is_callback:
    if len(lines) > 974:
        lines[974] = "            if is_callback:\n"
    
    # Linha 979: return
    if len(lines) > 978:
        lines[978] = "            return\n"
    
    # Verificar e corrigir outras linhas se necessário
    for i, line in enumerate(lines):
        # Corrigir indentações incorretas específicas
        if 'reply_markup = InlineKeyboardMarkup(keyboard)' in line and line.startswith('               '):
            lines[i] = line.replace('               ', '            ')
        elif 'if is_callback:' in line and line.startswith('                '):
            lines[i] = line.replace('                ', '            ')
        elif line.strip() == 'return' and line.startswith('            ') and i > 970 and i < 985:
            lines[i] = "            return\n"
    
    # Salvar arquivo corrigido
    with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Linhas específicas corrigidas!")
    print("📋 Correções aplicadas:")
    print("  • Linha 973: reply_markup indentação corrigida")
    print("  • Linha 975: if is_callback indentação corrigida")
    print("  • Linha 979: return indentação corrigida")

if __name__ == "__main__":
    fix_specific_lines() 