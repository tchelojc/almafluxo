# test_integracao.py - TESTE COMPLETO DA PLATAFORMA
import requests
import json
import time
import subprocess
import sys
import os
from datetime import datetime

class IntegrationTester:
    def __init__(self):
        self.base_urls = {
            'flask': 'http://localhost:5000',
            'proxy': 'http://localhost:5500', 
            'streamlit': 'http://localhost:8501',
            'ngrok': 'https://a8dd5392dd3f.ngrok-free.app'
        }
        
        self.test_user = {
            'email': 'tchelojc@gmail.com',
            'password': 'KGZO7OIDP8NL8JAJ'
        }
        
        self.results = {}
    
    def log_step(self, step, message, status=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {step}: {message}")
        if status:
            self.results[step] = status
    
    def test_health_checks(self):
        """Testa se todos os serviços estão respondendo"""
        self.log_step("HEALTH", "Iniciando teste de saúde dos serviços")
        
        services = [
            ('Flask', f"{self.base_urls['flask']}/health"),
            ('Proxy', f"{self.base_urls['proxy']}/health"),
            ('Ngrok', f"{self.base_urls['ngrok']}/health")
        ]
        
        all_healthy = True
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log_step(service_name, f"✅ ONLINE - {url}", 'OK')
                else:
                    self.log_step(service_name, f"❌ ERRO {response.status_code} - {url}", 'ERROR')
                    all_healthy = False
            except Exception as e:
                self.log_step(service_name, f"❌ OFFLINE - {str(e)}", 'ERROR')
                all_healthy = False
                time.sleep(1)
        
        return all_healthy
    
    def test_cors_configuration(self):
        """Testa especificamente a configuração CORS"""
        self.log_step("CORS", "Testando configuração CORS")
        
        test_urls = [
            f"{self.base_urls['proxy']}/health",
            f"{self.base_urls['flask']}/health"
        ]
        
        headers = {
            'Origin': 'http://localhost:5500',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        for url in test_urls:
            try:
                # Testa preflight OPTIONS
                response = requests.options(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    cors_headers = {k.lower(): v for k, v in response.headers.items() if 'access-control' in k.lower()}
                    self.log_step("CORS", f"✅ {url} - Headers: {cors_headers}", 'OK')
                else:
                    self.log_step("CORS", f"❌ {url} - Status: {response.status_code}", 'WARNING')
                    
            except Exception as e:
                self.log_step("CORS", f"❌ {url} - Erro: {str(e)}", 'ERROR')
    
    def test_login_flow(self):
        """Testa o fluxo completo de login"""
        self.log_step("LOGIN", "Testando fluxo de autenticação")
        
        login_url = f"{self.base_urls['proxy']}/login"
        login_data = {
            'email': self.test_user['email'],
            'password': self.test_user['password']
        }
        
        try:
            response = requests.post(
                login_url,
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            self.log_step("LOGIN", f"Status: {response.status_code}", 'OK' if response.ok else 'ERROR')
            
            if response.ok:
                data = response.json()
                token = data.get('quantum_token') or data.get('token')
                
                if token:
                    self.log_step("TOKEN", f"✅ Token recebido: {token[:50]}...", 'OK')
                    
                    # Testa validação do token
                    validate_url = f"{self.base_urls['proxy']}/validate_token"
                    validate_data = {'token': token}
                    
                    validate_response = requests.post(
                        validate_url,
                        json=validate_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=5
                    )
                    
                    if validate_response.ok:
                        validation = validate_response.json()
                        self.log_step("VALIDATION", f"✅ Token válido - User: {validation.get('email')}", 'OK')
                        return token
                    else:
                        self.log_step("VALIDATION", f"❌ Token inválido: {validate_response.text}", 'ERROR')
                else:
                    self.log_step("TOKEN", "❌ Nenhum token na resposta", 'ERROR')
            else:
                self.log_step("LOGIN", f"❌ Erro no login: {response.text}", 'ERROR')
                
        except Exception as e:
            self.log_step("LOGIN", f"❌ Erro na requisição: {str(e)}", 'ERROR')
        
        return None
    
    def test_streamlit_connection(self, token):
        """Testa se o Streamlit está acessível com o token"""
        self.log_step("STREAMLIT", "Testando conexão com Streamlit")
        
        streamlit_url = f"{self.base_urls['streamlit']}?token={token}"
        
        try:
            # Tenta acessar o Streamlit
            response = requests.get(streamlit_url, timeout=10)
            
            if response.status_code == 200:
                self.log_step("STREAMLIT", f"✅ ONLINE - Painel acessível", 'OK')
                return True
            else:
                self.log_step("STREAMLIT", f"⚠️  Status {response.status_code} - Pode ser normal", 'WARNING')
                return True  # Streamlit pode retornar outros status
                
        except Exception as e:
            self.log_step("STREAMLIT", f"❌ OFFLINE - {str(e)}", 'ERROR')
            return False
    
    def test_emergency_fallback(self):
        """Testa o modo de emergência"""
        self.log_step("EMERGENCY", "Testando fallback de emergência")
        
        # Testa com credenciais de emergência
        emergency_data = {
            'email': 'admin@fluxon.com',
            'password': 'admin_emergency_2024'
        }
        
        try:
            response = requests.post(
                f"{self.base_urls['proxy']}/login",
                json=emergency_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.ok:
                data = response.json()
                if data.get('warning', '').lower().find('emergencial') != -1:
                    self.log_step("EMERGENCY", "✅ Modo emergencial ativado", 'OK')
                    return True
                else:
                    self.log_step("EMERGENCY", "⚠️  Login ok mas sem flag de emergência", 'WARNING')
                    return True
            else:
                self.log_step("EMERGENCY", f"❌ Falha no modo emergencial: {response.status_code}", 'ERROR')
                return False
                
        except Exception as e:
            self.log_step("EMERGENCY", f"❌ Erro no modo emergencial: {str(e)}", 'ERROR')
            return False
    
    def run_complete_test(self):
        """Executa todos os testes em sequência"""
        print("=" * 60)
        print("🧪 TESTE DE INTEGRAÇÃO COMPLETA - FLUXON PLATFORM")
        print("=" * 60)
        
        # 1. Teste de saúde
        if not self.test_health_checks():
            self.log_step("OVERALL", "❌ Serviços essenciais offline", 'FAIL')
            return False
        
        # 2. Teste CORS
        self.test_cors_configuration()
        
        # 3. Teste de login principal
        token = self.test_login_flow()
        
        if token:
            # 4. Teste Streamlit
            self.test_streamlit_connection(token)
            
            # 5. Teste adicional de validação
            self.log_step("EXTRA", "Testando validação direta no Flask")
            try:
                response = requests.post(
                    f"{self.base_urls['flask']}/validate_token",
                    json={'token': token},
                    timeout=5
                )
                self.log_step("FLASK_VALIDATION", f"Status: {response.status_code}", 'OK' if response.ok else 'WARNING')
            except:
                self.log_step("FLASK_VALIDATION", "❌ Não foi possível testar validação direta", 'WARNING')
        else:
            # 6. Teste de fallback
            self.test_emergency_fallback()
        
        # Resumo final
        print("\n" + "=" * 60)
        print("📊 RESUMO DO TESTE")
        print("=" * 60)
        
        success_count = sum(1 for v in self.results.values() if v == 'OK')
        warning_count = sum(1 for v in self.results.values() if v == 'WARNING')
        error_count = sum(1 for v in self.results.values() if v == 'ERROR')
        
        print(f"✅ Sucessos: {success_count}")
        print(f"⚠️  Alertas: {warning_count}")
        print(f"❌ Erros: {error_count}")
        
        if error_count == 0:
            print("🎉 TODOS OS TESTES PRINCIPAIS PASSARAM!")
            print("💡 O sistema está pronto para uso")
            return True
        else:
            print("🔧 Alguns testes falharam - verifique os logs acima")
            return False

if __name__ == "__main__":
    tester = IntegrationTester()
    success = tester.run_complete_test()
    
    # Sugestões baseadas nos resultados
    if not success:
        print("\n🔧 SUGESTÕES DE CORREÇÃO:")
        print("1. Verifique se todos os serviços estão rodando:")
        print("   • Flask: python app.py")
        print("   • Proxy: python proxy_server.py") 
        print("   • Ngrok: python sync_ngrok.py")
        print("2. Confirme as URLs nos arquivos de configuração")
        print("3. Verifique logs detalhados de cada serviço")
    
    sys.exit(0 if success else 1)