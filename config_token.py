#!/usr/bin/env python3
"""
Script para forçar o token correto no sistema
"""
import os

# Define o token correto
CORRECT_TOKEN = "7584060058:AAHiZkgr-TFlbt8Ym1GNFMdvjfVa6oED9l8"

# Define as variáveis de ambiente
os.environ["TELEGRAM_BOT_TOKEN"] = CORRECT_TOKEN
os.environ["TELEGRAM_ADMIN_USER_IDS"] = "8012415611"

print(f"✅ Token configurado: {CORRECT_TOKEN[:20]}...{CORRECT_TOKEN[-10:]}")
print(f"✅ Admin configurado: {os.environ['TELEGRAM_ADMIN_USER_IDS']}")
print("✅ Variáveis de ambiente definidas!")

# Verifica se foi aplicado
if os.getenv("TELEGRAM_BOT_TOKEN") == CORRECT_TOKEN:
    print("🔥 TOKEN CORRETO APLICADO!")
else:
    print("❌ Erro: token não foi aplicado") 