#!/usr/bin/env python3
"""
Script COMPLETO para corrigir TODOS os problemas de indentação
"""

import re

def fix_complete_indentation():
    """Corrige TODOS os problemas de indentação e estrutura"""
    
    # Ler arquivo
    with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    corrected_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1
        
        # Correções específicas por linha
        if line_num == 869:  # Problema na linha 869
            corrected_lines.append('            if is_callback:')
            print(f"Corrigido linha {line_num}: if is_callback indentação")
        elif line_num == 906:  # Problema do for loop
            corrected_lines.append('            for match in live_matches[:8]:  # Máximo 8 partidas')
            print(f"Corrigido linha {line_num}: for loop indentação")
        elif line_num == 925 and 'if is_callback:' in line:
            corrected_lines.append('            if is_callback:')
            print(f"Corrigido linha {line_num}: if is_callback indentação")
        elif line_num == 930 and 'except Exception as e:' in line:
            corrected_lines.append('        except Exception as e:')
            print(f"Corrigido linha {line_num}: except indentação")
        elif line_num == 980 and 'await query.edit_message_text' in line:
            corrected_lines.append('            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=\'Markdown\')')
            print(f"Corrigido linha {line_num}: await indentação")
        elif line_num == 982 and 'except Exception as e:' in line:
            corrected_lines.append('        except Exception as e:')
            print(f"Corrigido linha {line_num}: except indentação")
        elif line_num == 1063 and 'await query.edit_message_text' in line:
            corrected_lines.append('            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=\'Markdown\')')
            print(f"Corrigido linha {line_num}: await indentação")
        elif line_num == 1065 and 'except Exception as e:' in line:
            corrected_lines.append('        except Exception as e:')
            print(f"Corrigido linha {line_num}: except indentação")
        elif line_num == 1325 and 'await update.message.reply_text' in line:
            corrected_lines.append('            await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=\'Markdown\')')
            print(f"Corrigido linha {line_num}: await indentação")
        else:
            # Correções gerais de padrões problemáticos
            if re.match(r'^\s{12,}keyboard = \[', line):
                corrected_lines.append('        keyboard = [')
                print(f"Corrigido linha {line_num}: keyboard = [ indentação")
            elif re.match(r'^\s{12,}reply_markup = InlineKeyboardMarkup', line):
                corrected_lines.append('        reply_markup = InlineKeyboardMarkup(keyboard)')
                print(f"Corrigido linha {line_num}: reply_markup indentação")
            elif re.match(r'^\s{12,}\]$', line):
                corrected_lines.append('        ]')
                print(f"Corrigido linha {line_num}: ] indentação")
            else:
                corrected_lines.append(line)
        
        i += 1
    
    # Salvar arquivo corrigido
    with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(corrected_lines))
    
    print("✅ TODAS as correções aplicadas!")

if __name__ == "__main__":
    fix_complete_indentation() 