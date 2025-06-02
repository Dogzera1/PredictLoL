#!/usr/bin/env python3

from bot.core_logic.units_system import ProfessionalUnitsSystem
from bot.utils.constants import UNITS_CONFIG

print('🔧 UNITS_CONFIG disponível:')
for nome, config in UNITS_CONFIG.items():
    print(f'  {nome}: conf>={config["min_confidence"]:.3f}, ev>={config["min_ev"]:.3f}, units={config["units"]}')
print()

print('🎯 Testando cálculo de unidades...')
system = ProfessionalUnitsSystem()

# Teste com valores reais do log
confidence = 0.52
ev_percentage = 3.75
tier = 2

print(f'Entrada: confidence={confidence:.3f}, ev_percentage={ev_percentage}%, tier={tier}')

result = system.calculate_units(confidence, ev_percentage, tier)
print('\n📊 Resultado do cálculo:')
for key, value in result.items():
    print(f'  {key}: {value}')

# Teste manual da função _get_units_category
ev_decimal = ev_percentage / 100.0
print(f'\n🔍 Testando _get_units_category manualmente:')
print(f'  confidence: {confidence:.3f}')
print(f'  ev_decimal: {ev_decimal:.4f}')

category = system._get_units_category(confidence, ev_decimal)
print(f'  categoria encontrada: {category}') 