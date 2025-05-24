# 🤖 Configuração do Token Telegram - Bot LoL V3

## ❌ PROBLEMA IDENTIFICADO

```
ERROR: The token `7897326299:AAFkX7lF4j_aQYPP70xfAkNyNON6-ZBbMcE` was rejected by the server.
telegram.error.InvalidToken: Unauthorized
```

**Causa:** O token atual está inválido ou foi revogado.

## 🔧 SOLUÇÕES

### 📋 **OPÇÃO 1: Configurar Novo Token (Recomendado)**

1. **Abra o Telegram** e procure por `@BotFather`
2. **Digite `/start`** para iniciar
3. **Digite `/newbot`** para criar um novo bot
4. **Siga as instruções:**
   - Nome do bot: `Seu Bot LoL Predictor`
   - Username: `seu_bot_lol_bot` (deve terminar com "bot")
5. **Copie o token** fornecido (formato: `1234567890:ABCDEF...`)

### 📋 **OPÇÃO 2: Recuperar Token Existente**

1. **No @BotFather, digite `/token`**
2. **Selecione seu bot** da lista
3. **Copie o token** fornecido

### 📋 **OPÇÃO 3: Usar Script Automático**

```bash
python setup_token.py
```

## ⚙️ CONFIGURAÇÃO DO TOKEN

### 🖥️ **Windows:**
```cmd
setx TELEGRAM_TOKEN "SEU_TOKEN_AQUI"
```

### 🐧 **Linux/Mac:**
```bash
export TELEGRAM_TOKEN="SEU_TOKEN_AQUI"
echo 'export TELEGRAM_TOKEN="SEU_TOKEN_AQUI"' >> ~/.bashrc
source ~/.bashrc
```

### 🐳 **Docker/Container:**
```bash
docker run -e TELEGRAM_TOKEN="SEU_TOKEN_AQUI" seu_bot
```

### ☁️ **Railway/Deploy:**
Adicione a variável `TELEGRAM_TOKEN` no painel de configuração.

## 🧪 TESTAR TOKEN

### **Método 1: Script de Teste**
```bash
python setup_token.py
# Escolha opção 2 para testar
```

### **Método 2: Teste Manual**
```python
import asyncio
import aiohttp

async def test_token(token):
    url = f"https://api.telegram.org/bot{token}/getMe"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Token válido: @{data['result']['username']}")
            else:
                print("❌ Token inválido")

# Execute: asyncio.run(test_token("SEU_TOKEN"))
```

## 🚀 EXECUTAR BOT APÓS CONFIGURAÇÃO

```bash
# Verificar se token está configurado
echo $TELEGRAM_TOKEN

# Executar bot
python main_v3_riot_integrated.py
```

## ⚠️ PROBLEMAS COMUNS

### **Token não encontrado:**
```
⚠️ TELEGRAM_TOKEN não configurado - usando modo teste
```
**Solução:** Configure a variável de ambiente `TELEGRAM_TOKEN`

### **Token inválido:**
```
ERROR: InvalidToken: Unauthorized
```
**Solução:** Obtenha novo token do @BotFather

### **Bot não responde:**
```
ERROR: 'TelegramBotV3Improved' object has no attribute 'application'
```
**Solução:** Atualização já implementada no código

## 🔒 SEGURANÇA

- ❌ **NUNCA** compartilhe seu token
- ❌ **NUNCA** commite tokens no Git
- ✅ **USE** variáveis de ambiente
- ✅ **REVOGUE** tokens antigos no @BotFather

## 📞 SUPORTE

Se os problemas persistirem:

1. **Verifique logs:** `logs/bot.log`
2. **Execute teste:** `python test_bot_startup.py`
3. **Token válido:** Formato `1234567890:ABC-DEF1234...`

## ✅ CHECKLIST FINAL

- [ ] Token obtido do @BotFather
- [ ] Variável TELEGRAM_TOKEN configurada
- [ ] Token testado e válido
- [ ] Bot executa sem erros
- [ ] Sistema de autorização ativo

---

**🎯 Com token válido configurado, o bot funcionará perfeitamente!** 