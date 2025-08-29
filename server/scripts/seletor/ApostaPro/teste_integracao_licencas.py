from datetime import datetime
import unittest
import uuid
import os
from licensing import LicenseManager
from quantum_licensing import QuantumLicenseManager
from servidor.servidor_licencas import app, atualizar_esquema_banco

class TesteIntegracaoLicencas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuração inicial dos testes"""
        # Atualiza esquema do banco antes dos testes
        atualizar_esquema_banco()
        
        cls.client = app.test_client()
        cls.client.testing = True
        
        # Configurações básicas
        cls.app_name = "OperadorConquistador"
        cls.license_key = "TEST-KEY-123"
        cls.device_id = f"TEST-DEVICE-{uuid.uuid4().hex[:8]}"
        
        # Configura chaves de ambiente
        os.environ['SECRET_KEY'] = "sua-chave-secreta-muito-longa-e-complexa-aqui"
        os.environ['LICENSE_SECRET_KEY'] = os.environ['SECRET_KEY']
        
    def test_00_time_sync(self):
        """Verifica sincronização de tempo com servidor"""
        response = self.client.get('/api/time')
        server_time = datetime.fromisoformat(response.json()['server_time'])
        time_diff = (datetime.now() - server_time).total_seconds() / 60
        self.assertLess(abs(time_diff), 5, f"Diferença de tempo muito grande: {time_diff} minutos")

    def test_01_servidor_online(self):
        """Testa conexão com o servidor"""
        response = self.client.get('/api/time')
        self.assertEqual(response.status_code, 200)
        self.assertIn('server_time', response.json)

    def test_02_licenca_manager(self):
        """Testa o LicenseManager básico"""
        manager = LicenseManager()
        result = manager.verify()
        self.assertIsInstance(result, bool)

    def test_03_quantum_license_manager(self):
        """Testa o QuantumLicenseManager"""
        qmanager = QuantumLicenseManager(self.app_name)
    
        # Garante que a licença de teste está disponível
        self._reset_test_license()
    
        # Ativação com parâmetros diretos
        activation = qmanager.activate_license(self.license_key, self.device_id)
        self.assertTrue(activation and activation.get('success', False), 
                       f"Falha na ativação: {activation}")
    
        # Verificação
        verification = qmanager.verify_license(
            license_key=self.license_key,
            device_id=self.device_id
        )
        self.assertTrue(verification and verification.get('valid', False), 
                       f"Falha na verificação: {verification}")
        
    def test_04_editor_licencas(self):
        """Testa funções do editor de licenças"""
        from editar_licenca import QuantumTimeAdjuster
        adjuster = QuantumTimeAdjuster()
        is_valid = adjuster.validate_quantum_time(datetime.now())
        self.assertIsInstance(is_valid, bool)

    def _reset_test_license(self):
        """Reseta a licença de teste para estado disponível"""
        with app.app_context():
            conn = sqlite3.connect('licenses.db')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE licenses 
                SET status = 'disponivel', 
                    device_id = NULL 
                WHERE key = ?
            """, (self.license_key,))
            conn.commit()
            conn.close()
            
if __name__ == '__main__':
    unittest.main()