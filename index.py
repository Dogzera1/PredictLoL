from api.webhook import app

# Exportar a aplicação Flask para o Vercel
# O Vercel procura por arquivos na raiz ou na pasta api/
if __name__ == "__main__":
    app.run(debug=True, port=5000) 