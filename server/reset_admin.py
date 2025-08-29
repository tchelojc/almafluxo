import os
import json
from werkzeug.security import generate_password_hash

def reset_admin():
    db_path = os.path.join(os.path.dirname(__file__), 'fluxon.json')
    
    with open(db_path, 'r+') as f:
        data = json.load(f)
        
        # Garante que existe pelo menos um usuário admin
        if not any(user['email'] == 'admin@fluxon.com' for user in data['users']):
            data['users'].append({
                "id": 1,
                "name": "Admin Fluxon",
                "email": "admin@fluxon.com",
                "password": generate_password_hash("nova_senha_segura123"),
                "is_admin": True,
                "status": "Ativo",
                "created_at": "2025-08-15T00:00:00"
            })
        else:
            # Atualiza a senha do admin existente
            for user in data['users']:
                if user['email'] == 'admin@fluxon.com':
                    user['password'] = generate_password_hash("nova_senha_segura123")
                    user['status'] = "Ativo"
                    break
        
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    print("✅ Admin resetado com sucesso!")
    print("Email: admin@fluxon.com")
    print("Senha: nova_senha_segura123")

if __name__ == '__main__':
    reset_admin()