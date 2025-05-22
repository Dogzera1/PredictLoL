from http.server import BaseHTTPRequestHandler
import json
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN", "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        if self.path == '/':
            message = f"Bot LoL funcionando! Token: {'configurado' if TOKEN else 'não configurado'}"
        elif self.path == '/api/webhook':
            message = "Webhook ativo!"
        else:
            message = "Endpoint não encontrado"
            
        self.wfile.write(message.encode())

    def do_POST(self):
        if self.path == '/api/webhook':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
