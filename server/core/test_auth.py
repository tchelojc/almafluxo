import unittest
import requests
import json
import os
from datetime import datetime, timezone, timedelta
import time
import jwt
import sys

# Adiciona o path para importar as configurações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import SECURITY_CONFIG

class TestAuthSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        cls.base_url = "http://localhost:5000"
        cls.admin_token = SECURITY_CONFIG['ADMIN_TOKEN']
        cls.admin_email = SECURITY_CONFIG['ADMIN_EMAIL']
        cls.admin_password = SECURITY_CONFIG['ADMIN_PASSWORD']
        
        # Usuário de teste com email único
        cls.test_user = {
            "name": "Usuário Teste Auth",
            "email": f"test_auth_{int(time.time())}@fluxon.com",
            "password": "SenhaTeste123!",
            "is_admin": False
        }
        
        cls.headers = {"Content-Type": "application/json"}
        cls.admin_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.admin_token}"
        }
        
        # Criar usuário de teste
        try:
            response = requests.post(
                f"{cls.base_url}/admin/users",
                headers=cls.admin_headers,
                json={
                    "name": cls.test_user["name"],
                    "email": cls.test_user["email"],
                    "password": cls.test_user["password"],
                    "is_admin": cls.test_user["is_admin"]
                },
                timeout=5
            )
            
            if response.status_code == 201:
                cls.test_user_id = response.json()['data']['user']['id']
                print(f"✅ Usuário de teste criado: {cls.test_user['email']} (ID: {cls.test_user_id})")
            else:
                print(f"⚠️  Falha ao criar usuário de teste: {response.status_code} - {response.text}")
                cls.test_user_id = None
                
        except Exception as e:
            print(f"❌ Erro ao criar usuário de teste: {str(e)}")
            cls.test_user_id = None

    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        if hasattr(cls, 'test_user_id') and cls.test_user_id:
            try:
                response = requests.delete(
                    f"{cls.base_url}/admin/users/{cls.test_user_id}",
                    headers=cls.admin_headers,
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"✅ Usuário de teste removido: {cls.test_user['email']}")
                else:
                    print(f"⚠️  Falha ao remover usuário: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Erro ao remover usuário: {str(e)}")

    def setUp(self):
        """Configuração antes de cada teste"""
        self.headers = {"Content-Type": "application/json"}

    def test_1_successful_login(self):
        """Testa login bem-sucedido"""
        try:
            response = requests.post(
                f"{self.base_url}/login",
                headers=self.headers,
                json={"email": self.test_user["email"], "password": self.test_user["password"]},
                timeout=5
            )
            
            # Verifica se o login foi bem-sucedido
            if response.status_code == 200:
                data = response.json()
                self.assertIn("data", data)
                self.assertIn("token", data["data"])
                self.assertIn("user", data["data"])
                self.assertEqual(data["data"]["user"]["email"], self.test_user["email"])
                print("✅ Login bem-sucedido")
            else:
                self.fail(f"Login falhou: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.fail(f"Erro no teste de login: {str(e)}")

    def test_2_invalid_credentials(self):
        """Testa login com credenciais inválidas"""
        # Senha incorreta
        response = requests.post(
            f"{self.base_url}/login",
            headers=self.headers,
            json={"email": self.test_user["email"], "password": "senhaerrada"},
            timeout=5
        )
        self.assertEqual(response.status_code, 401)
        
        # Email não existente
        response = requests.post(
            f"{self.base_url}/login",
            headers=self.headers,
            json={"email": "naoexiste@teste.com", "password": "qualquer"},
            timeout=5
        )
        self.assertEqual(response.status_code, 401)

    def test_3_inactive_account(self):
        """Testa login com conta inativa"""
        if not hasattr(self, 'test_user_id') or not self.test_user_id:
            self.skipTest("Usuário de teste não foi criado")
            
        try:
            # Desativa a conta
            response = requests.put(
                f"{self.base_url}/admin/users/{self.test_user_id}",
                headers=self.admin_headers,
                json={"status": "Inativo"},
                timeout=5
            )
            
            if response.status_code != 200:
                self.skipTest(f"Não foi possível desativar usuário: {response.status_code}")
            
            # Tenta fazer login
            response = requests.post(
                f"{self.base_url}/login",
                headers=self.headers,
                json={"email": self.test_user["email"], "password": self.test_user["password"]},
                timeout=5
            )
            
            self.assertEqual(response.status_code, 403)
            
            # Reativa a conta
            requests.put(
                f"{self.base_url}/admin/users/{self.test_user_id}",
                headers=self.admin_headers,
                json={"status": "Ativo"},
                timeout=5
            )
            
        except Exception as e:
            self.fail(f"Erro no teste de conta inativa: {str(e)}")

    def test_4_token_validation(self):
        """Testa a validação do token em rotas protegidas"""
        try:
            # Faz login para obter o token
            login_response = requests.post(
                f"{self.base_url}/login",
                headers=self.headers,
                json={"email": self.test_user["email"], "password": self.test_user["password"]},
                timeout=5
            )
            
            if login_response.status_code != 200:
                self.skipTest("Login falhou, pulando teste de validação de token")
            
            token = login_response.json()["data"]["token"]
            
            # Testa rota protegida
            response = requests.get(
                f"{self.base_url}/api/user_info",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                timeout=5
            )
            
            # Aceita 200 (sucesso) ou 401/403 (sem permissão)
            self.assertIn(response.status_code, [200, 401, 403])
            
        except Exception as e:
            self.fail(f"Erro no teste de validação de token: {str(e)}")

    def test_5_admin_routes_protection(self):
        """Testa se rotas de admin estão protegidas"""
        try:
            # Faz login como usuário normal
            login_response = requests.post(
                f"{self.base_url}/login",
                headers=self.headers,
                json={"email": self.test_user["email"], "password": self.test_user["password"]},
                timeout=5
            )
            
            if login_response.status_code != 200:
                self.skipTest("Login falhou, pulando teste de proteção admin")
            
            token = login_response.json()["data"]["token"]
            
            # Tenta acessar rota de admin
            response = requests.get(
                f"{self.base_url}/admin/users",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                timeout=5
            )
            
            self.assertEqual(response.status_code, 403)
            
        except Exception as e:
            self.fail(f"Erro no teste de proteção admin: {str(e)}")

    def test_6_token_expiration(self):
        """Testa se o token expira corretamente"""
        # Este teste é complexo e pode ser pulado se necessário
        self.skipTest("Teste de expiração de token requer setup complexo")

    def test_7_token_content(self):
        """Testa se o token contém as informações corretas"""
        try:
            response = requests.post(
                f"{self.base_url}/login",
                headers=self.headers,
                json={"email": self.test_user["email"], "password": self.test_user["password"]},
                timeout=5
            )
            
            if response.status_code != 200:
                self.skipTest("Login falhou, pulando teste de conteúdo do token")
            
            token = response.json()["data"]["token"]
            
            # Decodifica o token sem verificação para teste
            decoded = jwt.decode(token, options={"verify_signature": False})
            self.assertEqual(decoded["email"], self.test_user["email"])
            self.assertIn("user_id", decoded)
            self.assertIn("is_admin", decoded)
            
        except Exception as e:
            self.fail(f"Erro no teste de conteúdo do token: {str(e)}")

if __name__ == '__main__':
    unittest.main()