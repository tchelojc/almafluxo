#!/usr/bin/env python3
"""
TESTE COMPLETO DAS ROTAS STREAMLIT NO FLASK
Este script testa todas as rotas relacionadas ao Streamlit no servidor
"""

import requests
import json
import time
import subprocess
import sys
from urllib.parse import urljoin

class StreamlitRouteTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.token = None
        self.results = {}
    
    def print_header(self, message):
        print(f"\n{'='*60}")
        print(f"🔍 {message}")
        print(f"{'='*60}")
    
    def test_route(self, endpoint, method="GET", data=None, auth_required=False, name=None):
        """Testa uma rota específica"""
        url = f"{self.base_url}{endpoint}"
        name = name or endpoint
        
        try:
            headers = {}
            if auth_required and self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method == "POST":
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, json=data or {}, timeout=5)
            elif method == "OPTIONS":
                response = requests.options(url, headers=headers, timeout=5)
            else:
                return {'error': 'Método não suportado'}
            
            result = {
                'status': '✅ ONLINE' if response.status_code < 400 else '❌ ERRO',
                'status_code': response.status_code,
                'url': url,
                'method': method
            }
            
            # Tenta parsear JSON se possível
            try:
                result['response'] = response.json()
            except:
                result['response'] = response.text[:200] + '...' if len(response.text) > 200 else response.text
            
            print(f"{name}: {result['status']} ({result['status_code']})")
            
            if response.status_code >= 400:
                print(f"   Erro: {result.get('response', 'Sem detalhes')}")
            
            return result
            
        except requests.exceptions.ConnectionError:
            print(f"{name}: ❌ CONNECTION ERROR")
            return {'error': 'Connection refused', 'status': '❌ OFFLINE'}
        except requests.exceptions.Timeout:
            print(f"{name}: ⏰ TIMEOUT")
            return {'error': 'Timeout', 'status': '⏰ TIMEOUT'}
        except Exception as e:
            print(f"{name}: ❌ ERROR - {str(e)}")
            return {'error': str(e), 'status': '❌ ERROR'}
    
    def get_auth_token(self):
        """Obtém token de autenticação para testes"""
        try:
            # Tenta login de teste
            login_data = {
                "email": "admin@fluxon.com",  # Substitua por um email válido
                "password": "admin123"        # Substitua por uma senha válida
            }
            
            response = requests.post(f"{self.base_url}/login", 
                                   json=login_data, 
                                   timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data', {}).get('token'):
                    self.token = data['data']['token']
                    print("✅ Token de autenticação obtido com sucesso")
                    return True
            
            print("⚠️  Não foi possível obter token, testando rotas públicas")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao obter token: {str(e)}")
            return False
    
    def test_all_streamlit_routes(self):
        """Testa todas as rotas relacionadas ao Streamlit"""
        print("🚀 INICIANDO TESTE COMPLETO DAS ROTAS STREAMLIT")
        
        # 1. Testa rotas públicas primeiro
        self.print_header("TESTANDO ROTAS PÚBLICAS")
        
        public_routes = [
            ("/health", "GET", "Health Check"),
            ("/proxy/streamlit/_stcore/health", "GET", "Proxy Streamlit Health"),
            ("/api/streamlit/status", "GET", "Streamlit Status"),
            ("/login", "OPTIONS", "Login Options"),
            ("/admin/server_status", "GET", "Server Status")
        ]
        
        for endpoint, method, name in public_routes:
            self.results[name] = self.test_route(endpoint, method, name=name)
        
        # 2. Tenta obter autenticação
        self.print_header("OBTENDO AUTENTICAÇÃO")
        has_token = self.get_auth_token()
        
        # 3. Testa rotas autenticadas (se tiver token)
        if has_token:
            self.print_header("TESTANDO ROTAS AUTENTICADAS")
            
            auth_routes = [
                ("/api/start_streamlit", "POST", "Start Streamlit", {"action": "start"}),
                ("/api/streamlit/control", "POST", "Streamlit Control", {"action": "status", "platform": "seletor"}),
                ("/api/run/seletor", "POST", "Run Seletor", None),
                ("/hub", "GET", "Hub Redirect", None)
            ]
            
            for endpoint, method, name, data in auth_routes:
                self.results[name] = self.test_route(endpoint, method, data, auth_required=True, name=name)
        
        # 4. Testa rotas com OPTIONS (CORS)
        self.print_header("TESTANDO PREFLIGHT CORS")
        
        cors_routes = [
            "/api/start_streamlit",
            "/api/streamlit/control", 
            "/api/run/seletor",
            "/login",
            "/hub"
        ]
        
        for endpoint in cors_routes:
            self.results[f"OPTIONS {endpoint}"] = self.test_route(endpoint, "OPTIONS", name=f"OPTIONS {endpoint}")
        
        # 5. Resumo final
        self.print_header("📊 RESUMO DOS TESTES")
        
        success_count = sum(1 for result in self.results.values() if result.get('status') == '✅ ONLINE')
        total_count = len(self.results)
        
        print(f"Rotas testadas: {total_count}")
        print(f"Rotas com sucesso: {success_count}")
        print(f"Taxa de sucesso: {(success_count/total_count)*100:.1f}%")
        
        # Mostra rotas com problemas
        problematic_routes = {name: data for name, data in self.results.items() if data.get('status') != '✅ ONLINE'}
        if problematic_routes:
            print(f"\n⚠️  Rotas com problemas ({len(problematic_routes)}):")
            for name, data in problematic_routes.items():
                print(f"   • {name}: {data.get('status_code', 'N/A')} - {data.get('error', 'Sem detalhes')}")
        
        return self.results
    
    def check_streamlit_process(self):
        """Verifica se o Streamlit está rodando"""
        self.print_header("VERIFICANDO PROCESSO STREAMLIT")
        
        try:
            # Verifica se a porta 8501 está em uso
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8501))
            is_running = result == 0
            sock.close()
            
            print(f"Porta 8501: {'✅ EM USO' if is_running else '❌ LIVRE'}")
            
            # Testa health check direto
            try:
                response = requests.get('http://localhost:8501/_stcore/health', timeout=3)
                print(f"Health Check: ✅ {response.status_code}")
            except:
                print("Health Check: ❌ OFFLINE")
            
            return is_running
            
        except Exception as e:
            print(f"Erro na verificação: {str(e)}")
            return False

# Função para testar com diferentes URLs
def test_multiple_servers():
    """Testa em múltiplos servidores possíveis"""
    servers = [
        "http://localhost:5000",
        "http://127.0.0.1:5000", 
        "http://192.168.99.170:5000",
        "https://1ac41472cd64.ngrok-free.app"
    ]
    
    results = {}
    
    for server in servers:
        print(f"\n🎯 Testando servidor: {server}")
        try:
            tester = StreamlitRouteTester(server)
            result = tester.test_route("/health", "GET", name="Health Check")
            
            if result.get('status') == '✅ ONLINE':
                print(f"✅ Servidor ativo: {server}")
                # Testa todas as rotas neste servidor
                full_results = tester.test_all_streamlit_routes()
                results[server] = full_results
                break
            else:
                print(f"❌ Servidor offline: {server}")
                
        except Exception as e:
            print(f"❌ Erro ao testar {server}: {str(e)}")
    
    return results

if __name__ == "__main__":
    # Testa o servidor local primeiro
    tester = StreamlitRouteTester()
    
    # 1. Verifica processo Streamlit
    tester.check_streamlit_process()
    
    # 2. Testa todas as rotas
    results = tester.test_all_streamlit_routes()
    
    # 3. Se local falhar, testa outros servidores
    if not any(result.get('status') == '✅ ONLINE' for result in results.values()):
        print("\n🔍 Nenhum servidor local respondendo, testando alternativas...")
        test_multiple_servers()
    
    # 4. Salva resultados
    with open('streamlit_routes_test.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Resultados salvos em: streamlit_routes_test.json")