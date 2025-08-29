import logging
from datetime import datetime
from werkzeug.security import generate_password_hash

class UserManager:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
    def update_user(self, user_id, update_data):
        """Atualiza um usuário com validações adicionais"""
        try:
            if not isinstance(update_data, dict):
                raise ValueError("Dados de atualização devem ser um dicionário")
                
            self.logger.debug(f"Atualizando usuário {user_id} com dados: {update_data}")
            
            # Verificação otimizada de existência
            user = self.db.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"Usuário {user_id} não encontrado")
            
            # Validação de email único
            if 'email' in update_data:
                existing_user = self.db.get_user_by_email(update_data['email'])
                if existing_user and existing_user['id'] != user_id:
                    raise ValueError("Email já está em uso por outro usuário")
            
            # Hash automático de senha se fornecida
            if 'password' in update_data:
                update_data['password'] = generate_password_hash(update_data['password'])
            
            # Atualização de timestamp
            update_data['updated_at'] = datetime.now().isoformat()
            
            return self.db.update_user(user_id, update_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar usuário {user_id}: {str(e)}", exc_info=True)
            raise

    def create_user(self, user_data):
        """Cria um novo usuário com validações"""
        required_fields = ['name', 'email', 'password']
        if not all(field in user_data for field in required_fields):
            raise ValueError("Campos obrigatórios faltando")
        
        if not isinstance(user_data['password'], str) or len(user_data['password']) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        
        if self.db.get_user_by_email(user_data['email']):
            raise ValueError("Email já cadastrado")
            
        user_data['password'] = generate_password_hash(user_data['password'])
        user_data['created_at'] = datetime.now().isoformat()
        user_data['status'] = user_data.get('status', 'Ativo')
        
        return self.db.add_user(**user_data)