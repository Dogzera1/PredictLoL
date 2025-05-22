# Instruções para Deploy no Vercel

Este guia explica como fazer o deploy do bot LoL-GPT no Vercel e configurar o webhook do Telegram.

## Pré-requisitos

- [Node.js](https://nodejs.org/) instalado
- [Vercel CLI](https://vercel.com/docs/cli) instalado (`npm install -g vercel`)
- Uma conta no [Vercel](https://vercel.com/)

## Passo a Passo para Deploy Manual

### 1) Estrutura do Projeto

Certifique-se de que seu projeto tem a seguinte estrutura:

```
lol-gpt-apostas/
├── api/
│   └── webhook.py
├── backend/
├── telegram_bot/
├── scripts/
├── vercel.json
└── requirements.txt
```

### 2) Arquivo Vercel.json

O arquivo `vercel.json` na raiz deve conter:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/webhook.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/webhook",
      "methods": ["POST","GET"],
      "dest": "api/webhook.py"
    }
  ]
}
```

### 3) Arquivo Requirements.txt

O arquivo `requirements.txt` na raiz deve conter:

```
python-telegram-bot==13.15
requests
```

### 4) Deploy usando o Script Automatizado

Para facilitar o deploy, você pode usar o script PowerShell fornecido:

```powershell
# Na raiz do projeto
./scripts/deploy_vercel.ps1
```

Este script irá:
1. Verificar se o Vercel CLI está instalado
2. Fazer o deploy do projeto
3. Configurar o webhook do Telegram automaticamente

### 5) Deploy Manual

Se preferir fazer o deploy manualmente:

```powershell
# Na raiz do projeto
vercel --prod --yes
```

Após o deploy, configure o webhook do Telegram:

```powershell
$token = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo" 
$url = "https://lol-gpt-apostas-YYYYYYYYYYYY.vercel.app/api/webhook"

Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/setWebhook" -Method Post -Body @{ url = $url }
```

Substitua `YYYYYYYYYYYY` pelo ID gerado pelo Vercel.

## Solução de Problemas

### Erro de "Function Runtimes"

Se você encontrar o erro "Function Runtimes", verifique:

1. Se o arquivo `webhook.py` está no diretório `api/` e não em outro lugar
2. Se não há blocos `functions` no arquivo `vercel.json`, apenas `builds` e `routes`
3. Se o `requirements.txt` está na raiz do projeto

### Webhook não funciona

Se o webhook não estiver funcionando:

1. Verifique se o URL está correto em `setWebhook`
2. Teste o endpoint com uma chamada GET para verificar se está online
3. Verifique os logs no painel do Vercel para identificar erros
4. Certifique-se de que o token do bot está correto

## Verificação do Status

Para verificar se o webhook está configurado corretamente:

```powershell
$token = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getWebhookInfo"
```

Isso mostrará o URL atual do webhook e seu status. 