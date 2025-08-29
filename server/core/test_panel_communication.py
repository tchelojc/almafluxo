import sys
import os
import unittest
import requests
import time
from server.config import CONFIG, SECURITY_CONFIG

# Adicione o caminho absoluto do projeto ao PythonPath
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agora importe o database corretamente
try:
    from database import JSONDatabase as Database
except ImportError:
    from flux_on.database import JSONDatabase as Database

class TestPanelCommunication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        cls.base_url = "http://localhost:5000"
        cls.admin_token = SECURITY_CONFIG['ADMIN_TOKEN']
        cls.admin_email = SECURITY_CONFIG['ADMIN_EMAIL']
        cls.admin_password = SECURITY_CONFIG['ADMIN_PASSWORD']
        cls.test_user = {
            "name": "Usuário Teste",
            "email": "teste@fluxon.com",
            "password": "SenhaTeste123",
            "is_admin": False
        }
        cls.test_user_id = None

    def setUp(self):
        """Configuração executada antes de cada teste"""
        # ADICIONE ESTAS LINHAS:
        self.headers = {"Content-Type": "application/json"}
        # Mantenha também as configurações do setUpClass se necessário
        self.base_url = "http://localhost:5000"
        self.admin_email = SECURITY_CONFIG['ADMIN_EMAIL']
        self.admin_password = SECURITY_CONFIG['ADMIN_PASSWORD']
        self.admin_token = SECURITY_CONFIG['ADMIN_TOKEN']

    def test_1_server_connection(self):
        """Testa se o servidor está respondendo"""
        try:
            response = requests.get(f"{self.base_url}/admin/server_status", timeout=5)
            self.assertEqual(response.status_code, 200)
            print("\n✅ Servidor respondendo corretamente")
        except Exception as e:
            self.fail(f"Falha ao conectar ao servidor: {str(e)}")

    def test_2a_direct_admin_token_validation(self):
        """Testa validação do token admin direto"""
        print("Testa validação do token admin direto ...")
        
        # Tenta a rota /admin/verify_token primeiro
        response = requests.post(
            f"{self.base_url}/admin/verify_token",
            json={"token": self.admin_token},
            headers=self.headers  # ← AGORA ESTÁ DEFINIDO!
        )
        
        if response.status_code == 200:
            print(f"✅ Admin token validation: {response.status_code} - {response.text}")
            return
        
        # Se não encontrar, tenta a rota /validate_token como fallback
        print("⚠️  Rota /admin/verify_token não encontrada, tentando /validate_token...")
        
        response = requests.post(
            f"{self.base_url}/validate_token",
            json={"token": self.admin_token},
            headers=self.headers  # ← AGORA ESTÁ DEFINIDO!
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data', {}).get('is_admin'):
                print(f"✅ Admin token validation (fallback): {response.status_code}")
                return
        
        # Se nenhum método funcionar
        self.fail(f"Nenhum método de validação de token admin funcionou. Status: {response.status_code}, Response: {response.text}")
        
    def get_jwt_token(self):
        """Obtém token JWT válido"""
        login_response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.admin_email,
                "password": self.admin_password
            }
        )
        if login_response.status_code == 200:
            return login_response.json()['data']['token']
        raise Exception("Falha ao obter token JWT")

    def test_3a_debug_admin_user(self):
        """Método temporário para debug"""
        db = Database()
        admin = db.get_user_by_email(self.admin_email)
        
        print(f"\nDetalhes do admin:")
        print(f"ID: {admin['id']}")
        print(f"Email: {admin['email']}")
        print(f"Admin: {admin.get('is_admin', False)}")
        print(f"Status: {admin.get('status', 'N/A')}")

    def test_3_admin_login(self):
        """Testa login com credenciais de admin"""
        db = Database()
        admin = db.get_user_by_email(self.admin_email)
        
        if not admin:
            self.fail("Usuário admin não encontrado no banco de dados")
        
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.admin_email,
                "password": self.admin_password
            }
        )
        
        print(f"Resposta completa do login: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('user', response_data['data'])  # Agora verifica dentro de 'data'
        self.assertTrue(response_data['success'])
        
    def test_admin_uniqueness(self):
        """Verify there's only one admin user"""
        db = Database()
        admin_email = SECURITY_CONFIG['ADMIN_EMAIL'].lower()
        admins = [u for u in db.get_all_users() 
                if u['email'].lower() == admin_email and u.get('is_admin')]
        self.assertEqual(len(admins), 1, "Multiple admin users found")

    def create_test_user(self):
        """Cria um usuário temporário para testes"""
        timestamp = int(time.time() * 1000)  # Garante unicidade
        user_data = {
            "name": f"Test User {timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "testpass",
            "status": "Ativo"
        }
        try:
            return self.db.add_user(**user_data)
        except ValueError as e:
            self.logger.error(f"Erro ao criar usuário de teste: {str(e)}")
            raise

    def setUp(self):
        """Configuração inicial para cada teste"""
        self.db = Database()
        # Garante que o UserManager está importado
        from user_manager import UserManager
        self.UserManager = UserManager
    
    # test_panel_communication.py
    def test_update_user_invalid_data(self):
        """Testa atualização com dados inválidos"""
        # Cria usuário de teste
        user = self.create_test_user()
        
        user_manager = self.UserManager(self.db)
        
        # Teste com dados não-dicionário
        with self.assertRaises(ValueError):
            user_manager.update_user(user['id'], "not-a-dict")
        
        # Teste com usuário não existente
        with self.assertRaises(ValueError):
            user_manager.update_user(99999, {'name': 'Invalid'})

    def test_user_manager_validation(self):
        """Testa as validações do UserManager"""
        user_manager = self.UserManager(self.db)
        user = self.create_test_user()
        
        # Teste com dados válidos
        try:
            result = user_manager.update_user(user['id'], {'name': 'New Name'})
            self.assertEqual(result['name'], 'New Name')
        except ValueError as e:
            self.fail(f"Validação falhou inesperadamente: {str(e)}")
        
    def test_4_user_crud_operations(self):
        """Testa completo CRUD de usuários com verificação de persistência"""
        try:
            print("\n🔵 Iniciando teste CRUD de usuários")
            
            # 1. Primeiro faz login como admin para obter token JWT
            login_response = requests.post(
                f"{self.base_url}/login",
                json={
                    "email": self.admin_email,
                    "password": self.admin_password
                }
            )
            
            if login_response.status_code != 200:
                self.fail("Falha no login admin")
                
            token = login_response.json()['data']['token']
            
            # 2. Criar usuário com o token JWT
            user_data = {
                "name": "Test User",
                "email": f"test_user_{int(time.time())}@fluxon.com",
                "password": "TestPass123",
                "status": "Ativo"
            }
            
            create_res = requests.post(
                f"{self.base_url}/admin/users",
                headers={'Authorization': f'Bearer {token}'},
                json=user_data
            )
            
            print(f"📝 Resposta da criação: {create_res.status_code} - {create_res.text}")
            self.assertEqual(create_res.status_code, 201)
            user_id = create_res.json()['data']['user']['id']
            print(f"🆔 ID do usuário criado: {user_id}")
            
            # 3. Atualização
            update_data = {
                "name": "Updated Name", 
                "status": "Ativo",
                "license_expiry": "2030-12-31"
            }
            
            update_res = requests.put(
                f"{self.base_url}/admin/users/{user_id}",
                headers={'Authorization': f'Bearer {token}'},  # Usa o mesmo token JWT
                json=update_data,
                timeout=30
            )
            
            print(f"📝 Resposta da atualização: {update_res.status_code} - {update_res.text}")
            self.assertEqual(update_res.status_code, 200)
            
            # 4. Verificação via GET
            get_res = requests.get(
                f"{self.base_url}/admin/users/{user_id}",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            print(f"📝 Resposta do GET: {get_res.status_code} - {get_res.text}")
            self.assertEqual(get_res.status_code, 200)
            
            user_data = get_res.json()['data']['user']
            self.assertEqual(user_data['name'], "Updated Name")
            
            # 5. Verificação direta no banco
            db = Database()
            db_user = db.get_user_by_id(user_id)
            self.assertIsNotNone(db_user)
            self.assertEqual(db_user['name'], "Updated Name")
            
            # 6. Limpeza
            del_res = requests.delete(
                f"{self.base_url}/admin/users/{user_id}",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            print(f"📝 Resposta da remoção: {del_res.status_code} - {del_res.text}")
            self.assertEqual(del_res.status_code, 200)
            
            print("✅ Teste CRUD concluído com sucesso")
            
        except Exception as e:
            print(f"❌ Falha no CRUD: {str(e)}")
            self.fail(f"Falha no CRUD: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        if cls.test_user_id:
            # Garante que o usuário teste foi removido
            requests.delete(
                f"{cls.base_url}/admin/users/{cls.test_user_id}",
                headers={'Authorization': f'Bearer {cls.admin_token}'},
                timeout=5
            )

if __name__ == '__main__':
    print("\nIniciando testes de comunicação entre panel.py e app.py")
    print("="*60)
    unittest.main(verbosity=2)