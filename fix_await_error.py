#!/usr/bin/env python3
"""
Script para corrigir erro de await no tips_system.py
"""

def fix_await_error():
    file_path = "bot/systems/tips_system.py"
    
    # Lê o arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrige a linha problemática
    content = content.replace(
        "suitable_matches = self._filter_suitable_matches(live_matches)",
        "suitable_matches = await self._filter_suitable_matches(live_matches)"
    )
    
    # Também corrige o método _filter_suitable_matches para ser async
    content = content.replace(
        "def _filter_suitable_matches(self, matches: List[MatchData]) -> List[MatchData]:",
        "async def _filter_suitable_matches(self, matches: List[MatchData]) -> List[MatchData]:"
    )
    
    # Escreve o arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Erro de await corrigido!")
    print("✅ Método _filter_suitable_matches agora é async")

if __name__ == "__main__":
    fix_await_error() 