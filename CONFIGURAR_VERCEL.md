# Como Configurar o Bot no Vercel - Guia Completo

## 🚨 Problema Identificado

O bot está configurado, mas o Vercel está retornando erro 401 para o webhook. Isso significa que o token não está sendo encontrado como variável de ambiente.

## ✅ Solução Passo a Passo

### 1. Configurar Variável de Ambiente no Vercel

1. Acesse: https://vercel.com/dashboard
2. Clique no seu projeto `lol-gpt-apostas`
3. Vá em **Settings** (Configurações)
4. Clique em **Environment Variables** (Variáveis de Ambiente)
5. Clique em **Add New** (Adicionar Nova)
6. Configure:
   - **Name**: `TELEGRAM_TOKEN`
   - **Value**: `7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo`
   - **Environments**: Marque todas (Production, Preview, Development)
7. Clique em **Save** (Salvar)

### 2. Fazer Redeploy

Após configurar a variável de ambiente:

1. Vá em **Deployments** (Implantações)
2. Clique nos três pontos (...) do último deploy
3. Selecione **Redeploy** (Reimplantar)
4. Aguarde o deploy terminar

### 3. Testar o Bot

Execute este comando para testar:
```bash
python test_bot.py
```

## 🔧 Comandos Úteis

### Deploy manual:
```bash
vercel --prod
```

### Configurar webhook automaticamente:
```bash
python deploy.py
```

### Testar bot:
```bash
python test_bot.py
```

## 📱 URLs Importantes

- **Bot URL**: https://lol-gpt-apostas-m1j08tcnh-victors-projects-42e6b0fe.vercel.app
- **Webhook**: https://lol-gpt-apostas-m1j08tcnh-victors-projects-42e6b0fe.vercel.app/api/webhook
- **Painel Vercel**: https://vercel.com/dashboard

## 🐛 Problemas Comuns

### Erro 401 Unauthorized
- **Causa**: Token não configurado como variável de ambiente
- **Solução**: Seguir passo 1 acima

### Updates pendentes no webhook
- **Causa**: Bot não consegue processar mensagens
- **Solução**: Corrigir erro 401 primeiro

### Bot não responde
- **Causa**: Webhook não configurado ou com erro
- **Solução**: Executar `python deploy.py` novamente

## ✅ Status Esperado

Após configurar corretamente, os testes devem mostrar:
- 🌐 Endpoint webhook: ✅ OK
- 🤖 Bot Telegram: ✅ OK  
- 🔗 Webhook configurado: ✅ OK

## 🎯 Próximos Passos

1. Configure a variável de ambiente
2. Faça o redeploy
3. Execute os testes
4. Teste o bot enviando `/start` no Telegram

O bot está quase funcionando! Só falta configurar a variável de ambiente no Vercel. 