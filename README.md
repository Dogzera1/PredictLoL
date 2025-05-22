# LoL-GPT Betting Assistant

Bot do Telegram para acompanhamento de partidas de League of Legends e assistência para apostas.

## 📋 Funcionalidades

- 🎮 **Partidas ao vivo**: Acompanhe partidas em andamento com estatísticas em tempo real
- 📊 **Previsões**: Obtenha análises de probabilidade e odds justas para apostas
- 🔍 **Análise detalhada**: Veja análises aprofundadas de composições e situação atual da partida
- 📅 **Próximas partidas**: Veja a agenda de partidas futuras
- 🤖 **IA avançada**: Modelo preditivo treinado com dados históricos de 2023-2025

## 🚀 Instalação

### Pré-requisitos

- Python 3.7+
- pip (gerenciador de pacotes Python)
- Token de bot do Telegram (obtenha com [@BotFather](https://t.me/BotFather))
- Chave de API da Riot (opcional, para funcionalidades completas)

### Passos para instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/lol-gpt-apostas.git
   cd lol-gpt-apostas
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Configure as credenciais:
   - Abra `config.py`
   - Substitua `SEU_TOKEN_AQUI` pelo token do seu bot do Telegram
   - Substitua `SUA_CHAVE_API_AQUI` pela sua chave de API da Riot (opcional)

4. Testar o modelo localmente:
   ```
   python simple_test.py
   ```

5. Execute o bot localmente:
   ```
   python bot.py
   ```

### Implantação no Vercel

1. Instale a CLI do Vercel:
   ```
   npm install -g vercel
   ```

2. Faça login e configure o projeto:
   ```
   vercel login
   vercel link
   ```

3. Configure as variáveis de ambiente:
   ```
   vercel env add TELEGRAM_TOKEN
   ```

4. Implante o bot:
   ```
   vercel deploy
   ```

5. Configure o webhook do Telegram:
   ```
   curl -F "url=https://seu-novo-projeto.vercel.app/api/webhook" -F "secret_token=lol_gpt_secret_token" https://api.telegram.org/bot<SEU_TOKEN>/setWebhook
   ```

### Testar Localmente com o Webhook

Para testar o webhook localmente, use:

```
python local_webhook.py
```

Então use uma ferramenta como ngrok para expor seu servidor local:

```
ngrok http 8000
```

Configure o webhook do Telegram com o URL fornecido pelo ngrok:

```
curl -F "url=https://seu-tunnel-ngrok.io/api/webhook" -F "secret_token=lol_gpt_secret_token" https://api.telegram.org/bot<SEU_TOKEN>/setWebhook
```

## 📝 Comandos do Bot

- `/start` - Inicia o bot e mostra o menu principal
- `/ajuda` - Mostra lista de comandos disponíveis
- `/ao_vivo` - Mostra partidas que estão acontecendo agora
- `/proximas` - Mostra próximas partidas agendadas
- `/partida [id]` - Mostra detalhes de uma partida específica
- `/sobre` - Informações sobre o bot

## 💡 Uso da API

O bot utiliza a API oficial da Riot Games para LoL Esports. Para funcionalidade completa, é recomendado obter uma chave de API no [Portal de Desenvolvedores da Riot](https://developer.riotgames.com/).

## 📊 Modelo de Previsão

O serviço de previsão utiliza um algoritmo avançado de machine learning treinado com dados históricos de 2023-2025. O modelo considera:

- Histórico completo dos times em torneios recentes
- Composição (champions selecionados)
- Estatísticas em tempo real (ouro, kills, dragões, etc.)
- Fase do jogo (early, mid, late game)
- Tendências e padrões de comportamento dos times

Os palpites são atualizados em tempo real conforme a partida progride, utilizando tanto dados históricos quanto a situação atual para oferecer previsões mais precisas.

### Treinamento do Modelo

O modelo é treinado utilizando:

- Random Forest Classifier para previsão de resultados
- Normalização de features com StandardScaler
- Validação cruzada para garantir precisão
- Features derivadas de mais de 1000 partidas profissionais

## ⚠️ Solução de Problemas

### Problema de Features do Modelo
Se você encontrar o erro "X has 18 features, but StandardScaler is expecting 13 features as input.", o problema foi corrigido no arquivo `services/model_trainer.py`. O código agora ajusta automaticamente o número de features para 13, garantindo compatibilidade com o modelo treinado.

### Problemas com o Webhook
Se o bot não estiver respondendo no Telegram após a implantação no Vercel:

1. Verifique os logs do Vercel:
   ```
   vercel logs
   ```

2. Confirme que o webhook está configurado corretamente:
   ```
   curl https://api.telegram.org/bot<SEU_TOKEN>/getWebhookInfo
   ```

3. Verifique se a variável de ambiente TELEGRAM_TOKEN está configurada no Vercel

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## 📜 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## ⚠️ Aviso Legal

Este bot foi desenvolvido apenas para fins educacionais e de entretenimento. As previsões não devem ser consideradas conselhos financeiros ou garantia de resultados em apostas. Aposte com responsabilidade. 