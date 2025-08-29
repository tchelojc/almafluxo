import http.server
import socketserver
import json
from pathlib import Path
import time
import socket
from datetime import datetime

REDIRECT_PORT = 5001
DOMINIO_PRINCIPAL = "almafluxo.uk"

class AlmaRedirectHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.client_address[0]} -> {self.path}")
        
        try:
            # Health check
            if self.path == '/health':
                self.send_health_response()
                return
                
            # Página principal - LINK_ALMA.HTML
            if self.path == '/':
                self.serve_file('link_alma.html', 'text/html')
                return
            
            # Página de login - INDEX_EXTERNAL.HTML (apenas GET → mostra HTML)
            if self.path == '/login':
                self.serve_file('index_external.html', 'text/html')
                return
            
            # Redirecionamento para aplicação principal
            if self.path.startswith('/app/'):
                self.redirect_to_app()
                return
            
            # Servir arquivos estáticos
            if self.path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
                self.serve_static_file()
                return
            
            # Para qualquer outra rota, mostra página não encontrada
            self.send_error(404, "Página não encontrada")
                
        except Exception as e:
            print(f"Erro: {e}")
            self.send_error(500, "Erro interno do servidor")

    def do_POST(self):
        """
        🔴 Nunca processa POST aqui, para não atrapalhar o login.
        POST /login deve ir para o Flask (fluxon.almafluxo.uk)
        """
        self.send_response(405)  # Method Not Allowed
        self.end_headers()

    def serve_file(self, filename, content_type):
        """Serve arquivos HTML"""
        try:
            file_path = Path(__file__).parent / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self.send_error(404, f"Arquivo {filename} não encontrado")
        except Exception as e:
            self.send_error(500, f"Erro ao ler {filename}")

    def send_health_response(self):
        """Resposta de health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "healthy",
            "service": "alma_redirect",
            "domain": DOMINIO_PRINCIPAL,
            "port": REDIRECT_PORT,
            "timestamp": datetime.now().isoformat(),
            "endpoints": ["/", "/login", "/health"]
        }
        
        self.wfile.write(json.dumps(response).encode())

    def redirect_to_app(self):
        """Redireciona para a aplicação principal"""
        app_url = "http://localhost:5001"
        self.send_response(302)
        self.send_header('Location', app_url)
        self.end_headers()

    def serve_static_file(self):
        """Serve arquivos estáticos"""
        try:
            file_path = Path(__file__).parent / 'static' / self.path[1:]
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Determina tipo de conteúdo
                content_types = {
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.ico': 'image/x-icon'
                }
                
                content_type = content_types.get(file_path.suffix, 'application/octet-stream')
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Arquivo não encontrado")
        except Exception as e:
            self.send_error(500, "Erro ao servir arquivo")

    def log_message(self, format, *args):
        """Log simplificado"""
        message = format % args
        if not self.path.startswith('/health'):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def run_server():
    """Inicia o servidor de redirecionamento"""
    with socketserver.TCPServer(("0.0.0.0", REDIRECT_PORT), AlmaRedirectHandler) as httpd:
        print("=" * 50)
        print("🌐 SERVIDOR ALMA - REDIRECIONAMENTO")
        print("=" * 50)
        print(f"📍 Porta: {REDIRECT_PORT}")
        print(f"🌍 Domínio: {DOMINIO_PRINCIPAL}")
        print(f"🔗 Local: http://localhost:{REDIRECT_PORT}")
        print(f"🚀 Global: https://{DOMINIO_PRINCIPAL}")
        print("📁 Servindo:")
        print("   • /          → link_alma.html")
        print("   • /login     → index_external.html")
        print("   • /health    → Status do servidor")
        print("=" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor parado pelo usuário")

if __name__ == "__main__":
    run_server()