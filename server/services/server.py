# server.py - ALMA STATIC GATEWAY (VERSÃO CORRIGIDA)
import http.server
import socketserver
import os
import socket
import threading
import webbrowser
import time
import json
import requests
from pathlib import Path
from connection_manager import connection_manager

# Configurações
PORT = 8000
NGROK_CONFIG_PATH = Path(__file__).parent.parent / "server" / ".ngrok_coordinator.json"

def get_ngrok_url():
    """Obtém a URL atual do Ngrok usando o ConnectionManager"""
    return connection_manager.get_current_ngrok_url() or "none"

class AlmaStaticHandler(http.server.SimpleHTTPRequestHandler):
    """Handler para servir arquivos estáticos e redirecionar para Ngrok"""
    
    def do_GET(self):
        # Mapeamento de rotas
        if self.path == '/':
            self.serve_link_alma()
        elif self.path == '/link_alma.html':
            self.serve_static_file('link_alma.html')
        elif self.path == '/health':
            self.serve_health_check()
        elif self.path == '/ngrok-info':
            self.serve_ngrok_info()
        elif self.path == '/redirect':
            self.redirect_to_ngrok()
        else:
            self.serve_static_file(self.path[1:])  # Remove a barra inicial

    def serve_link_alma(self):
        """Serve o link_alma.html com URL dinâmica do Ngrok"""
        try:
            ngrok_url = get_ngrok_url()
            
            # Lê o arquivo link_alma.html
            with open('link_alma.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Substitui a URL estática pela dinâmica do Ngrok
            if ngrok_url and ngrok_url != "none":
                content = content.replace(
                    'http://192.168.99.170:8000/login.html', 
                    f'{ngrok_url}/index_external.html'
                )
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Erro ao processar página: {str(e)}")

    def serve_static_file(self, filename):
        """Serve arquivos estáticos com fallback"""
        try:
            if os.path.exists(filename) and os.path.isfile(filename):
                # Usa a implementação padrão para servir arquivos
                return super().do_GET()
            else:
                self.send_error(404, f"Arquivo não encontrado: {filename}")
        except Exception as e:
            self.send_error(404, f"Erro ao servir arquivo: {filename} - {str(e)}")

    def redirect_to_ngrok(self):
        """Redireciona para a URL atual do Ngrok"""
        ngrok_url = get_ngrok_url()
        
        if ngrok_url and ngrok_url != "none":
            self.send_response(302)
            self.send_header('Location', f'{ngrok_url}/index_external.html')
            self.end_headers()
            
            # HTML de redirecionamento para browsers que não seguem redirects
            html_content = f"""
            <html>
            <head>
                <title>Redirecionando...</title>
                <meta http-equiv="refresh" content="0; url={ngrok_url}/index_external.html">
            </head>
            <body>
                <p>Redirecionando para <a href="{ngrok_url}/index_external.html">{ngrok_url}/index_external.html</a></p>
                <script>window.location.href = "{ngrok_url}/index_external.html";</script>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_error(503, "Ngrok não configurado. Execute: python sync_ngrok.py")

    def serve_health_check(self):
        """Endpoint de health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "healthy",
            "service": "alma_static_gateway",
            "port": PORT,
            "timestamp": time.time(),
            "ngrok_configured": get_ngrok_url() != "none"
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def serve_ngrok_info(self):
        """Informações sobre a configuração do Ngrok"""
        ngrok_url = get_ngrok_url()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "ngrok_configured": ngrok_url != "none",
            "ngrok_url": ngrok_url,
            "static_gateway": f"http://{socket.gethostname()}:{PORT}",
            "shareable_link": f"http://{socket.gethostname()}:{PORT}/link_alma.html",
            "timestamp": time.time()
        }
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

    def log_message(self, format, *args):
        print(f"🌐 STATIC [{self.log_date_time_string()}] {format % args}")

def run_server():
    """Inicia o servidor estático"""
    web_dir = Path(__file__).parent
    os.chdir(web_dir)
    
    print("=" * 60)
    print("🚀 ALMA STATIC GATEWAY")
    print("=" * 60)
    print(f"📂 Diretório: {web_dir}")
    print(f"🌐 Porta: {PORT}")
    
    # Verificar arquivos essenciais
    essential_files = ['link_alma.html', 'index_external.html']
    for file in essential_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (NÃO ENCONTRADO)")
            return  # Para se arquivo essencial não existir
    
    # Obter URL do Ngrok
    ngrok_url = get_ngrok_url()
    
    print(f"\n🔗 Ngrok URL: {ngrok_url if ngrok_url != 'none' else 'Não configurado'}")
    print(f"📱 Link Local: http://localhost:{PORT}/link_alma.html")
    print(f"🌍 Link Rede: http://{socket.gethostbyname(socket.gethostname())}:{PORT}/link_alma.html")
    print("=" * 60)
    
    # Abrir navegador
    def open_browser():
        time.sleep(3)  # Dar tempo para o servidor iniciar
        try:
            webbrowser.open(f"http://localhost:{PORT}/link_alma.html")
            print("🌐 Navegador aberto automaticamente")
        except Exception as e:
            print(f"⚠️ Não foi possível abrir navegador: {e}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Iniciar servidor
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), AlmaStaticHandler) as httpd:
            httpd.allow_reuse_address = True
            print(f"⚡ Servidor rodando em http://0.0.0.0:{PORT}")
            print("⚡ Pressione Ctrl+C para parar")
            print("=" * 60)
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no servidor: {e}")

if __name__ == "__main__":
    run_server()