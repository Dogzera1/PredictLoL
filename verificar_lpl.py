#!/usr/bin/env python3

from bot.utils.constants import SUPPORTED_LEAGUES, LEAGUE_TIERS

print("🏆 VERIFICAÇÃO LPL (Liga Profissional da China)")
print("=" * 60)

# Verifica se LPL está nas ligas suportadas
lpl_supported = 'LPL' in SUPPORTED_LEAGUES
print(f"✅ LPL nas ligas suportadas: {'SIM' if lpl_supported else 'NÃO'}")

# Verifica tier da LPL
lpl_tier = LEAGUE_TIERS.get('LPL', 'N/A')
print(f"🎯 Tier da LPL: {lpl_tier}")

if lpl_tier == 1:
    print("🌟 LPL é considerada TIER 1 (Liga Principal)")
elif lpl_tier == 2:
    print("⭐ LPL é considerada TIER 2 (Liga Regional)")
else:
    print("❓ LPL não encontrada nos tiers")

print("\n📋 Ligas Tier 1 (principais):")
tier1_leagues = [liga for liga, tier in LEAGUE_TIERS.items() if tier == 1]
for liga in tier1_leagues:
    emoji = "🇨🇳" if liga == "LPL" else "🏆"
    print(f"   {emoji} {liga}")

print(f"\n🔍 Total de ligas Tier 1: {len(tier1_leagues)}")

# Busca por variantes da LPL
print(f"\n🔍 Buscando variantes LPL na lista completa ({len(SUPPORTED_LEAGUES)} ligas):")
lpl_variants = [l for l in SUPPORTED_LEAGUES if 'lpl' in l.lower() or 'china' in l.lower()]

if lpl_variants:
    print("🇨🇳 Variantes LPL encontradas:")
    for variant in lpl_variants:
        print(f"   • {variant}")
else:
    print("❌ Nenhuma variante LPL encontrada")

# Status final
print("\n" + "=" * 60)
if lpl_supported and lpl_tier == 1:
    print("✅ STATUS: LPL ESTÁ SENDO MONITORADA")
    print("🎯 Prioridade: ALTA (Tier 1)")
    print("📊 O sistema detectará partidas LPL automaticamente")
    print("⚡ Tips serão geradas para jogos LPL ao vivo")
elif lpl_supported:
    print("⚠️ STATUS: LPL está suportada mas com prioridade menor")
else:
    print("❌ STATUS: LPL NÃO está sendo monitorada")
    print("🔧 Seria necessário adicionar à lista")

print(f"\n🌍 Resumo das ligas principais monitoradas:")
print(f"   🇨🇳 LPL (China): {'✅' if 'LPL' in tier1_leagues else '❌'}")
print(f"   🇰🇷 LCK (Coreia): {'✅' if 'LCK' in tier1_leagues else '❌'}")
print(f"   🇪🇺 LEC (Europa): {'✅' if 'LEC' in tier1_leagues else '❌'}")
print(f"   🇺🇸 LCS (América do Norte): {'✅' if 'LCS' in tier1_leagues else '❌'}")
print(f"   🇧🇷 CBLOL (Brasil): {'✅' if 'CBLOL' in tier1_leagues else '❌'}") 
