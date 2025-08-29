import requests

class TestUtils:
    @staticmethod
    def create_test_user(base_url, admin_token, user_data):
        """Cria um usuário para testes"""
        response = requests.post(
            f"{base_url}/admin/users",
            headers={'Authorization': f'Bearer {admin_token}'},
            json=user_data
        )
        return response.json().get('user')

    @staticmethod
    def delete_test_user(base_url, admin_token, user_id):
        """Remove um usuário de teste"""
        requests.delete(
            f"{base_url}/admin/users/{user_id}",
            headers={'Authorization': f'Bearer {admin_token}'}
        )

    @staticmethod
    def get_auth_token(base_url, email, password):
        """Obtém token de autenticação"""
        response = requests.post(
            f"{base_url}/login",
            json={"email": email, "password": password}
        )
        return response.json().get("token")