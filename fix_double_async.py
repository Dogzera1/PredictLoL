#!/usr/bin/env python3
"""
Script para corrigir async duplicado no tips_system.py
"""

def fix_double_async():
    file_path = "bot/systems/tips_system.py"
    
    # Lê o arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrige o async duplicado
    content = content.replace(
        "async async def _filter_suitable_matches",
        "async def _filter_suitable_matches"
    )
    
    # Escreve o arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Async duplicado corrigido!")

if __name__ == "__main__":
    fix_double_async() 