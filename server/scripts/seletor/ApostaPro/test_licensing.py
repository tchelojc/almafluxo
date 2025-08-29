import unittest
from licensing import LicenseManager
import os
import sqlite3
from datetime import datetime, timedelta
import json
from unittest import mock

class TestLicenseSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_license_file = os.path.abspath("test_license.json")
        cls.test_db = ":memory:"
        
        cls.conn = sqlite3.connect(cls.test_db)
        cls.cursor = cls.conn.cursor()
        cls.cursor.execute('''
            CREATE TABLE licenses (
                key TEXT PRIMARY KEY,
                email TEXT,
                status TEXT DEFAULT 'disponivel',
                device_id TEXT,
                activation_date TEXT,
                expiration_date TEXT
            )
        ''')
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        if os.path.exists(cls.test_license_file):
            os.remove(cls.test_license_file)

    def setUp(self):
        self.cursor.execute("DELETE FROM licenses")
        self.conn.commit()
        if os.path.exists(self.test_license_file):
            os.remove(self.test_license_file)

    def create_test_license(self, key, status, expiration_date):
        self.cursor.execute(
            "INSERT INTO licenses VALUES (?, ?, ?, ?, ?, ?)",
            (key, "test@test.com", status, "test-device-id",
             datetime.now().strftime("%Y-%m-%d"), expiration_date)
        )
        self.conn.commit()

    def test_valid_license(self):
        """Teste com licença válida"""
        test_key = "TEST-VALID-001"
        expiration = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
        # Configura o mock do servidor
        with mock.patch('requests.post') as mock_post:
            # Configura a resposta simulada do servidor
            mock_response = mock.Mock()
            mock_response.json.return_value = {
                'valid': True,
                'status': 'ativada',
                'key': test_key
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response
        
            # Cria licença no banco de dados de teste
            self.create_test_license(test_key, "ativada", expiration)
        
            # Cria arquivo de licença de teste
            with open(self.test_license_file, 'w') as f:
                json.dump({
                    "key": test_key,
                    "status": "ativada",
                    "device_id": "test-device-id",
                    "expiration": expiration,
                    "hash": "mocked-hash-value",
                    "last_check": datetime.now().isoformat()
                }, f)
        
            # Configura o LicenseManager para teste
            manager = LicenseManager()
            manager._test_license_file = self.test_license_file
            manager.base_url = "http://testserver"
            manager.timeout = 5  # Tempo limite reduzido para testes
        
            # Executa a verificação
            result = manager.verify()
        
            # Verificações
            self.assertTrue(result, "Licença válida deveria retornar True")
            mock_post.assert_called_once()  # Garante que o servidor foi chamado

    def test_expired_license(self):
        """Teste com licença expirada"""
        test_key = "TEST-EXPIRED-001"
        expired_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
        with mock.patch('requests.post') as mock_post:
            # Configura resposta de erro do servidor
            mock_response = mock.Mock()
            mock_response.json.return_value = {
                'valid': False,
                'message': 'Licença expirada'
            }
            mock_response.status_code = 403
            mock_post.return_value = mock_response
        
            self.create_test_license(test_key, "ativada", expired_date)
        
            with open(self.test_license_file, 'w') as f:
                json.dump({
                    "key": test_key,
                    "status": "expirada",
                    "device_id": "test-device-id",
                    "expiration": expired_date,
                    "hash": "mocked-hash-value"
                }, f)
        
            manager = LicenseManager()
            manager._test_license_file = self.test_license_file
            manager.base_url = "http://testserver"
        
            result = manager.verify()
            self.assertFalse(result, "Licença expirada deveria retornar False")

if __name__ == '__main__':
    unittest.main()