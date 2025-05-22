# 🚂 Variáveis Railway - Configure no Painel

No painel do Railway, vá em **Variables** e adicione:

## 🔧 **Variáveis Nixpacks (Força Detecção)**
```
NIXPACKS_PYTHON_VERSION = 3.11
NIXPACKS_BUILD_CMD = pip install -r requirements.txt
NIXPACKS_START_CMD = python main.py
```

## 🔧 **Variáveis Buildpack (Alternativo)**
```
BUILDPACK_URL = heroku/python
```

## 🔧 **Variáveis da Aplicação**
```
PORT = 8080
PYTHONPATH = /app
PYTHONUNBUFFERED = 1
```

## 🔧 **Variável do Bot (Opcional - só após funcionar)**
```
TELEGRAM_TOKEN = 7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo
```

## 📋 **Ordem de Teste:**

### 1. Configure apenas PORT primeiro
### 2. Redeploy e veja se funciona
### 3. Se não, adicione NIXPACKS_* variables
### 4. Se ainda não, adicione BUILDPACK_URL
### 5. Último recurso: use Dockerfile 