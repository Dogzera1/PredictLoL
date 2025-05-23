#!/usr/bin/env python3
"""
Script para corrigir problemas de indentação no main_v3_riot_integrated.py
"""

def fix_indentation():
    # Ler arquivo
    with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Variáveis para controle
    fixed_lines = []
    in_try_block = False
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Problemas específicos identificados
        if line_num == 92:  # def __init__ da classe ChampionAnalyzer
            fixed_lines.append(line.replace('        def __init__(self):', '    def __init__(self):'))
        elif line_num == 882 or 'keyboard = [' in line:
            # Corrigir indentação de keyboard mal alinhado
            if line.strip().startswith('keyboard = ['):
                # Calcular indentação correta baseada no contexto
                indentation = len(line) - len(line.lstrip())
                if indentation == 8:  # 8 espaços, corrigir para 12
                    fixed_lines.append('            keyboard = [\n')
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Escrever arquivo corrigido
    with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ Indentações corrigidas!")

if __name__ == "__main__":
    fix_indentation() 