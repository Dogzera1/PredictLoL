# Configuração de Variáveis de Ambiente no Vercel

Para que o bot funcione corretamente no Vercel, você precisa configurar as seguintes variáveis de ambiente:

## Obrigatórias

### TELEGRAM_TOKEN
- **Descrição**: Token do seu bot do Telegram
- **Valor atual**: `7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo`
- **Como configurar no Vercel**:
  1. Acesse seu projeto no dashboard do Vercel
  2. Vá em "Settings" > "Environment Variables"
  3. Adicione uma nova variável com nome `TELEGRAM_TOKEN`
  4. Cole o token acima como valor

## Opcionais

### RIOT_API_KEY
- **Descrição**: Chave da API da Riot Games
- **Valor**: `RGAPI-25f07e53-9e17-474b-a357-4e416d985311`

### SECRET_TOKEN
- **Descrição**: Token secreto para validação do webhook
- **Valor padrão**: `lol_gpt_secret_token`

### MODEL_CONFIDENCE_THRESHOLD
- **Descrição**: Limite de confiança do modelo de previsão
- **Valor padrão**: `0.65`

### UPDATE_INTERVAL
- **Descrição**: Intervalo de atualização em segundos
- **Valor padrão**: `60`

## Como Configurar no Vercel

1. Acesse [vercel.com](https://vercel.com)
2. Faça login em sua conta
3. Selecione seu projeto
4. Vá em "Settings" > "Environment Variables"
5. Para cada variável:
   - Clique em "Add New"
   - Digite o nome da variável
   - Cole o valor
   - Selecione "Production", "Preview" e "Development"
   - Clique em "Save"

## Depois de Configurar

Após adicionar as variáveis de ambiente, você precisa fazer um novo deploy:
1. Vá em "Deployments"
2. Clique nos três pontos (...) do último deploy
3. Selecione "Redeploy"

## Verificação

Você pode verificar se o bot está funcionando acessando:
- `https://seu-projeto.vercel.app/health` - Status do bot
- `https://seu-projeto.vercel.app/api/webhook` - Endpoint do webhook 