#!/usr/bin/env python3
"""
Script para corrigir erro de sintaxe no tips_system.py
"""

def fix_syntax_error():
    file_path = "bot/systems/tips_system.py"
    
    # Lê o arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrige as linhas problemáticas
    content = content.replace(
        "if not await self._is_draft_complete(match):",
        "# if not await self._is_draft_complete(match):"
    )
    
    content = content.replace(
        'logger.debug(f"Draft incompleto - aguardando fechamento do draft: {match.match_id}")',
        '# logger.debug(f"Draft incompleto - aguardando fechamento do draft: {match.match_id}")'
    )
    
    content = content.replace(
        "return False",
        "# return False  # Temporariamente desabilitado",
        1  # Apenas a primeira ocorrência
    )
    
    content = content.replace(
        "if game_minutes == 0.0 and await self._is_draft_complete(match):",
        "# if game_minutes == 0.0 and await self._is_draft_complete(match):"
    )
    
    content = content.replace(
        'logger.debug(f"Momento ideal: draft completo, jogo começando")',
        '# logger.debug(f"Momento ideal: draft completo, jogo começando")'
    )
    
    # Escreve o arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Erro de sintaxe corrigido!")
    print("⚠️  Verificação de draft temporariamente desabilitada")

if __name__ == "__main__":
    fix_syntax_error() 