#!/usr/bin/env python3
import asyncio

async def test():
    try:
        print("🔍 TESTE RÁPIDO: VERIFICANDO TIPS")
        
        # 1. Testar API
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        pandascore = PandaScoreAPIClient()
        partidas = await pandascore.get_lol_live_matches()
        print(f"📊 Partidas encontradas: {len(partidas)}")
        
        # 2. Se não há partidas, esse é o motivo
        if len(partidas) == 0:
            print("❌ MOTIVO: Nenhuma partida ao vivo detectada")
            print("   - Isso é normal quando não há jogos profissionais")
            print("   - LEC/LCS/LCK podem estar em pausa")
            print("   - Fim de semana ou período entre splits")
        else:
            print("✅ Partidas encontradas - sistema deveria gerar tips")
            for p in partidas[:3]:
                print(f"   - {p.get('name', 'Unknown')}")
        
        await pandascore.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test())