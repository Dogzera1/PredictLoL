#!/usr/bin/env python3
"""
Script para corrigir problemas de indentação no main_v3_riot_integrated.py
Baseado nas diretrizes do GeeksforGeeks: https://www.geeksforgeeks.org/indentation-error-in-python/
"""

import re

def fix_indentation():
    print("🔧 Aplicando correções de indentação baseadas no GeeksforGeeks...")
    
    # Ler arquivo
    with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir problemas específicos identificados pelo linter
    fixes = [
        # 1. Corrigir else órfão (linha 794)
        (r'        elif favorite_prob > 60:\n            analysis\.append\(f"💰 \*\*APOSTA RECOMENDADA:\*\* {favorite} \(confiança moderada\)"\)\n            else:', 
         '        elif favorite_prob > 60:\n            analysis.append(f"💰 **APOSTA RECOMENDADA:** {favorite} (confiança moderada)")\n        else:'),
        
        # 2. Corrigir indentações de keyboard mal alinhadas
        (r'            keyboard = \[', '        keyboard = ['),
        
        # 3. Corrigir return mal indentado na função run
        (r'                return', '            return'),
        
        # 4. Corrigir estrutura if-else final no main
        (r'    if FLASK_AVAILABLE:\n    port = int', '    if FLASK_AVAILABLE:\n        port = int'),
        (r'    else:\n        print\("❌ Flask não disponível', '    else:\n        print("❌ Flask não disponível'),
    ]
    
    # Aplicar correções
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Salvar arquivo corrigido
    with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Indentações corrigidas seguindo padrão Python PEP8!")
    print("📋 Correções aplicadas:")
    print("  • Estruturas condicionais corrigidas")
    print("  • Keyboards com indentação consistente")
    print("  • Return statements alinhados")
    print("  • Blocos if-else finais corrigidos")

if __name__ == "__main__":
    fix_indentation() 