#!/usr/bin/env python3
"""
DIAGNÓSTICO CORS FLUXON - CLOUD & LOCAL
Testa comunicação entre Cloudflare / Flask / Streamlit e identifica problemas de CORS
"""

import requests
import json
import time

class CloudflareCORSDiagnostic:
    def __init__(self):
        self.base_urls = {
            'cloudflare_login': 'https://fluxon.almafluxo.uk/login',
            'proxy_streamlit': 'http://localhost:5000/proxy/streamlit/_stcore/health',
            'streamlit_direct': 'http://localhost:8501/_stcore/health'
        }
        self.results = {}

    def print_header(self, msg):
        print(f"\n{'='*60}\n🔍 {msg}\n{'='*60}")

    def test_post_login(self, origin):
        """Testa POST /login via Cloudflare"""
        self.print_header("TESTE LOGIN POST (Cloudflare)")
        headers = {
            "Content-Type": "application/json",
            "Origin": origin,
            "Accept": "application/json"
        }
        payload = {"email": "tchelojc@gmail.com", "password": "KGZO7OIDP8NL8JAJ"}

        try:
            response = requests.post(self.base_urls['cloudflare_login'], json=payload, headers=headers, timeout=10)
            self.results['login_post'] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }
            print(f"POST Status: {response.status_code}")
            if 'Access-Control-Allow-Origin' in response.headers:
                print(f"   CORS Origin: {response.headers['Access-Control-Allow-Origin']}")
        except Exception as e:
            print(f"Erro POST /login: {e}")
            self.results['login_post'] = {"error": str(e)}

    def test_preflight(self, origin, target_url):
        """Testa requisição OPTIONS (preflight CORS)"""
        self.print_header(f"TESTE PRE-FLIGHT OPTIONS: {origin} → {target_url}")
        headers = {
            'Origin': origin,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
        try:
            response = requests.options(target_url, headers=headers, timeout=5)
            self.results['preflight'] = {
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
            print(f"OPTIONS Status: {response.status_code}")
            if 'Access-Control-Allow-Origin' in response.headers:
                print(f"   CORS Allow-Origin: {response.headers['Access-Control-Allow-Origin']}")
        except Exception as e:
            print(f"Erro OPTIONS: {e}")
            self.results['preflight'] = {"error": str(e)}

    def test_streamlit_health(self):
        """Testa health check do Streamlit direto e via proxy"""
        self.print_header("TESTE HEALTH STREAMLIT")
        urls = [('Direct', self.base_urls['streamlit_direct']), ('Proxy', self.base_urls['proxy_streamlit'])]
        for name, url in urls:
            try:
                response = requests.get(url, timeout=5)
                self.results[f'health_{name.lower()}'] = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text
                }
                print(f"{name} Status: {response.status_code}")
                if 'Access-Control-Allow-Origin' in response.headers:
                    print(f"   CORS Origin: {response.headers['Access-Control-Allow-Origin']}")
            except Exception as e:
                print(f"{name} health error: {e}")
                self.results[f'health_{name.lower()}'] = {"error": str(e)}

    def run_diagnostic(self):
        """Executa diagnóstico completo"""
        print("🚀 INICIANDO DIAGNÓSTICO CORS CLOUD & LOCAL")
        origin = "https://almafluxo.uk"

        # 1. Teste POST /login
        self.test_post_login(origin)

        # 2. Teste OPTIONS preflight
        self.test_preflight(origin, self.base_urls['cloudflare_login'])

        # 3. Teste Streamlit health
        self.test_streamlit_health()

        # 4. Salva resultados
        with open('cloudflare_cors_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print("\n📁 Resultados salvos em cloudflare_cors_results.json")

if __name__ == "__main__":
    diag = CloudflareCORSDiagnostic()
    diag.run_diagnostic()
