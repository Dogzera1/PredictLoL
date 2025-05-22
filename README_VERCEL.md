# Implantação do LoL-GPT Bot no Vercel

Este guia explica como implantar o bot de apostas LoL-GPT no Vercel para mantê-lo online 24/7.

## Pré-requisitos

1. Ter uma conta no [Vercel](https://vercel.com)
2. Ter o [Vercel CLI](https://vercel.com/docs/cli) instalado
3. Token do bot do Telegram (obtido do @BotFather)

## Configuração

### 1. Configurar o token do bot

Você pode configurar o token do bot de duas maneiras:

**Opção 1 - Arquivo config.py:**
Edite o arquivo `config.py` e substitua "SEU_TOKEN_AQUI" pelo seu token real:

```python
BOT_TOKEN = "seu_token_real_aqui"  # Substitua pelo seu token
```

**Opção 2 - Variável de ambiente (recomendado):**
Configure o token como variável de ambiente no Vercel:

```bash
vercel env add TELEGRAM_TOKEN
```

### 2. Login no Vercel

Execute o login na CLI do Vercel:

```bash
vercel login
```

### 3. Implantação para o Vercel

Execute o comando de implantação:

```bash
vercel
```

Responda as perguntas quando solicitado. Certifique-se de selecionar o diretório apropriado como diretório raiz do projeto.

### 4. Configurar o webhook do Telegram

Depois que o projeto estiver implantado, você precisará configurar o webhook do Telegram para apontar para o endpoint do Vercel.

Use o script de configuração incluído:

```bash
python scripts/set_webhook.py https://seu-app.vercel.app/api/webhook
```

Substitua `https://seu-app.vercel.app` pelo URL real da sua aplicação no Vercel.

Para verificar o status atual do webhook:

```bash
python scripts/set_webhook.py --info
```

## Resolução de problemas

### Erro: "Token do Telegram não definido"

Certifique-se de que o token do bot esteja configurado corretamente, seja no arquivo `config.py` ou como variável de ambiente no Vercel:

```bash
vercel env add TELEGRAM_TOKEN
```

### Webhook não funciona

Verifique as informações do webhook:

```bash
python scripts/set_webhook.py --info
```

Se houver erros, reconfigure o webhook:

```bash
python scripts/set_webhook.py https://seu-app.vercel.app/api/webhook
```

### Verificando logs no Vercel

Para verificar os logs da sua aplicação no Vercel:

```bash
vercel logs seu-app.vercel.app
```

## Atualizando o bot

Para atualizar o bot após fazer alterações:

```bash
vercel --prod
```

## Limitações no plano gratuito do Vercel

- Tempo de execução máximo de 10 segundos por função
- Tempo limite de inatividade
- Recursos de processamento limitados

Para usos mais intensivos, considere atualizar para um plano pago. 