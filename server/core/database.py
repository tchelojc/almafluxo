# database.py CORRIGIDO
import time
from datetime import datetime
import json
import os
import threading
from werkzeug.security import generate_password_hash
from server.config import CONFIG, SECURITY_CONFIG
import logging

# Configuração do logger para database.py
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Formato dos logs
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Handler para console
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Handler para arquivo
fh = logging.FileHandler('database_debug.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

class JSONDatabase:
    def __init__(self, db_file=None):
        self.DB_FILE = db_file or os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'fluxon.json')
        )
        self.LOCK = threading.RLock()
        self.logger = logging.getLogger(__name__ + '.JSONDatabase')  # Adicionando logger
        self._initialize_database()

    def _initialize_database(self):
        """Verifica e cria a estrutura do banco de dados se não existir"""
        if not os.path.exists(self.DB_FILE):
            self._create_initial_database()
        else:
            self._validate_database_structure()
            self._cleanup_duplicate_admins()  # Add this line
            
    def _create_initial_database(self):
        """
        Cria o banco de dados inicial com:
        - 1 usuário admin padrão
        - 1 script básico
        - Permissões iniciais
        - Estrutura completa
        """
        initial_data = {
            "users": [self._create_admin_user()],
            "scripts": [self._create_default_script()],
            "permissions": [{
                "user_id": 1,
                "script_id": 1
            }],
            "access_logs": [],
            "execution_logs": [],
            "blocked_ips": []
        }
        self._write(initial_data)
        
    def clear_access_logs(self):
        """Limpa logs com backup automático"""
        try:
            # Cria backup automático
            backup_data = self._read()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_access_logs_{timestamp}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data['access_logs'], f)
            
            # Limpa os logs
            data = self._read()
            data['access_logs'] = []
            self._write(data)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar logs: {str(e)}")
            return False
        
    def clear_execution_logs(self):
        """Limpa todos os registros de execução de scripts"""
        data = self._read()
        data['execution_logs'] = []
        self._write(data)
        
    def clear_all_logs(self):
        """Limpa todos os registros de acesso e execução"""
        data = self._read()
        data['access_logs'] = []
        data['execution_logs'] = []
        self._write(data)

    # No método _create_admin_user() em database.py
    def _create_admin_user(self):
        """Cria o usuário administrador padrão"""
        return {
            "id": 1,
            "name": "Admin",
            "email": SECURITY_CONFIG['ADMIN_EMAIL'],  # admin@fluxon.com
            "password": generate_password_hash(SECURITY_CONFIG['ADMIN_PASSWORD']),  # senha_admin_segura
            "is_admin": True,
            "license_expiry": "2030-12-31",
            "status": "Ativo",
            "created_at": datetime.now().isoformat()
        }

    def _create_default_script(self):
        """Cria o script padrão da plataforma"""
        return {
            "id": 1,
            "name": "FLUX-ON Platform Selector",
            "description": "Seletor principal de plataformas FLUX-ON",
            "path": os.path.join("scripts", "seletor.py"),
            "created_at": datetime.now().isoformat()
        }

    def _validate_database_structure(self):
        """Garante que todas as seções necessárias existam no banco de dados"""
        data = self._read()  # Adicione esta linha para ler os dados
        
        required = {
            'users': list,
            'scripts': list,
            'permissions': list,
            'access_logs': list,
            'execution_logs': list,
            'blocked_ips': list
        }
        
        for key, type_ in required.items():
            if key not in data or not isinstance(data[key], type_):
                raise ValueError(f"Estrutura inválida: {key} faltando ou tipo errado")
            
    def fix_admin_user(self):
        """Corrige o usuário admin com as credenciais corretas"""
        data = self._read()
        admin_email = SECURITY_CONFIG['ADMIN_EMAIL']
        admin_password = SECURITY_CONFIG['ADMIN_PASSWORD']
        
        for user in data["users"]:
            if user["email"].lower() == admin_email.lower():
                user.update({
                    "password": generate_password_hash(admin_password),
                    "is_admin": True,
                    "status": "Ativo",
                    "license_expiry": "2030-12-31"
                })
                self._write(data)
                return True
        return False

    def _read(self):
        """Lê todo o conteúdo do arquivo JSON com thread lock"""
        with self.LOCK:
            # Garante que o arquivo não esteja vazio antes de tentar ler
            if os.path.getsize(self.DB_FILE) == 0:
                self._create_initial_database() # Recria se estiver vazio

            with open(self.DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write(self, data):
        """Escreve no arquivo JSON com thread lock e validação"""
        with self.LOCK:
            try:
                start_time = time.time()
                # Garante que o diretório existe
                os.makedirs(os.path.dirname(self.DB_FILE), exist_ok=True)
                
                # Escreve em arquivo temporário primeiro
                temp_file = f"{self.DB_FILE}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                # Substitui o arquivo original
                if os.path.exists(self.DB_FILE):
                    os.replace(temp_file, self.DB_FILE)
                else:
                    os.rename(temp_file, self.DB_FILE)
                    
                duration = time.time() - start_time
                self.logger.debug(f"Dados persistidos em {self.DB_FILE} em {duration:.3f}s")
            except Exception as e:
                self.logger.critical(f"Falha ao escrever no banco de dados: {str(e)}")
                raise

    def _cleanup_duplicate_admins(self):
        """Remove duplicate admin users"""
        data = self._read()
        admin_email = SECURITY_CONFIG['ADMIN_EMAIL'].lower()
        
        # Find all admins with the admin email
        admins = [u for u in data['users'] if u['email'].lower() == admin_email]
        
        if len(admins) > 1:
            logger.warning(f"Found {len(admins)} admin users with email {admin_email}, cleaning up duplicates")
            # Keep the first admin and remove duplicates
            data['users'] = [u for u in data['users'] 
                            if u['email'].lower() != admin_email or u['id'] == admins[0]['id']]
            self._write(data)
            logger.info(f"Kept admin user ID {admins[0]['id']}, removed {len(admins)-1} duplicates")
            return True
        return False
    
    def add_user(self, **user_data):
        """Adiciona um novo usuário ao sistema com validações completas"""
        data = self._read()
        
        # Validações
        if not all(k in user_data for k in ['name', 'email', 'password']):
            raise ValueError("Missing required fields: name, email, password")
        
        if any(u['email'].lower() == user_data['email'].lower() for u in data["users"]):
            raise ValueError("Email already exists")
        
        # Gera ID
        new_id = max((u.get("id", 0) for u in data["users"]), default=0) + 1
        
        # Cria usuário com campos padrão
        user = {
            "id": new_id,
            "name": user_data['name'],
            "email": user_data['email'],
            "password": user_data['password'],
            "is_admin": user_data.get('is_admin', False),
            "status": user_data.get('status', 'Ativo'),
            "license_expiry": user_data.get('license_expiry', '2030-12-31'),
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        data["users"].append(user)
        self._write(data)
        
        # Retorna cópia sem a senha
        return {k: v for k, v in user.items() if k != 'password'}
    
    def get_user_by_email(self, email):
        data = self._read()
        return next((u for u in data["users"] if u["email"].lower() == email.lower()), None)

    def get_user_by_id(self, user_id):
        data = self._read()
        return next((u for u in data["users"] if u["id"] == int(user_id)), None)

    def is_user_admin(self, user_id):
        """Verifica se um usuário é admin pelo seu ID."""
        user = self.get_user_by_id(user_id)
        return user and user.get('is_admin') is True

    def get_all_users(self):
        data = self._read()
        users_copy = []
        for user in data.get('users', []):
            uc = user.copy()
            uc.pop('password', None)
            users_copy.append(uc)
        return users_copy

    def get_all_access_logs(self):
        data = self._read()
        # Retorna os logs em ordem decrescente (mais recentes primeiro)
        return sorted(data.get('access_logs', []), key=lambda x: x.get('timestamp', ''), reverse=True)

    def get_all_scripts(self):
        """Retorna todos os scripts do sistema"""
        data = self._read()
        return data.get('scripts', [])

    def get_script_permissions(self, script_id):
        """Retorna IDs de usuários com permissão para um script"""
        data = self._read()
        return [p['user_id'] for p in data['permissions'] 
            if p['script_id'] == script_id]

    def update_script_permissions(self, script_id, allowed_users):
        """Atualiza as permissões de um script"""
        data = self._read()
        
        # Remove todas as permissões existentes para este script
        data['permissions'] = [p for p in data['permissions'] 
                            if p['script_id'] != script_id]
        
        # Adiciona as novas permissões
        for user_id in allowed_users:
            data['permissions'].append({
                'user_id': user_id,
                'script_id': script_id
            })
        
        self._write(data)
        return True

    def block_ip(self, ip):
        """Bloqueia um endereço IP"""
        data = self._read()
        if ip not in data['blocked_ips']:
            data['blocked_ips'].append(ip)
            self._write(data)
        return True

    def log_execution(self, user_id, script_id, return_code):
        """Registra uma execução de script"""
        data = self._read()
        data['execution_logs'].append({
            "user_id": user_id,
            "script_id": script_id,
            "return_code": return_code,
            "timestamp": datetime.now().isoformat()
        })
        self._write(data)
        return True

    def update_user(self, user_id, update_data):
        with self.LOCK:
            try:
                data = self._read()

                user_index, user = next(
                    ((i, u) for i, u in enumerate(data["users"]) if u["id"] == user_id),
                    (None, None)
                )

                if user_index is None:
                    self.logger.warning(f"Usuário {user_id} não encontrado para atualização")
                    return None

                original_user = user.copy()

                try:
                    data["users"][user_index].update(update_data)
                    data["users"][user_index]['last_updated'] = datetime.now().isoformat()

                    # Testa se serializa
                    json.dumps(data["users"][user_index])

                    self._write(data)

                    updated_user = data["users"][user_index].copy()
                    updated_user.pop('password', None)
                    return updated_user

                except Exception as e:
                    data["users"][user_index] = original_user
                    self._write(data)
                    self.logger.error(f"Erro durante atualização: {str(e)}")
                    raise

            except Exception as e:
                self.logger.error(f"Erro geral ao atualizar usuário: {str(e)}")
                raise
        
    # --- Métodos de Scripts ---
    def add_script(self, name, description, path):
        """Adiciona um novo script à plataforma"""
        data = self._read()
        new_id = max((s.get("id", 0) for s in data["scripts"]), default=0) + 1
        
        script = {
            "id": new_id,
            "name": name,
            "description": description,
            "path": path,
            "created_at": datetime.now().isoformat()
        }
        
        data["scripts"].append(script)
        self._write(data)
        return script

    def get_script_by_id(self, script_id):
        return {
            "id": 1,
            "name": "Seletor de Ativos",
            "path": "scripts/seletor/seletor.py",
            "description": "Filtra ativos por liquidez, volume e tendência"
        }

    # --- Métodos de Permissões ---
    def add_permission(self, user_id, script_id):
        """Concede permissão para um usuário executar um script"""
        data = self._read()
        
        # Verifica se já existe
        if any(p for p in data["permissions"] 
              if p["user_id"] == user_id and p["script_id"] == script_id):
            return False
        
        data["permissions"].append({
            "user_id": user_id,
            "script_id": script_id
        })
        self._write(data)
        return True
    
    def delete_user(self, user_id):
        """Remove um usuário do sistema pelo ID"""
        data = self._read()
        
        # Encontra e remove o usuário
        users = data['users']
        original_count = len(users)
        data['users'] = [user for user in users if user['id'] != user_id]
        
        # Remove todas as permissões associadas a este usuário
        data['permissions'] = [p for p in data['permissions'] 
                            if p['user_id'] != user_id]
        
        # Verifica se o usuário foi realmente removido
        if len(data['users']) < original_count:
            self._write(data)
            return True
        return False

    def is_script_allowed(self, user_id, script_id):
        """
        Verifica se um usuário tem permissão para executar um script.
        Admins podem executar tudo.
        """
        if self.is_user_admin(user_id):
            return True

        data = self._read()
        script_id = int(script_id) # Garante que a comparação seja entre números
        
        for p in data.get("permissions", []):
            if p.get("user_id") == user_id and p.get("script_id") == script_id:
                return True
        return False
        
    def get_allowed_scripts_for_user(self, user_id):
        """Retorna todos os scripts que um usuário pode executar"""
        data = self._read()
        
        # Admins têm acesso a todos scripts
        user = self.get_user_by_id(user_id)
        if user and user.get('is_admin'):
            return data.get("scripts", [])
        
        # Usuários normais só têm acesso aos permitidos
        allowed_ids = {p["script_id"] for p in data["permissions"] if p["user_id"] == user_id}
        return [s for s in data["scripts"] if s["id"] in allowed_ids]

    def log_access(self, access_data):
        """Registra um acesso ao sistema com um dicionário de dados"""
        try:
            data = self._read()
            new_id = max((l.get("id", 0) for l in data["access_logs"]), default=0) + 1
            
            # Garante que todos os campos necessários estão presentes
            required_fields = ['ip', 'endpoint', 'method', 'browser', 'os', 'device']
            if not all(field in access_data for field in required_fields):
                missing = [field for field in required_fields if field not in access_data]
                self.logger.error(f"Campos faltando no log de acesso: {missing}")
                return None
            
            # Cria o registro de log
            log = {
                "id": new_id,
                "user_id": access_data.get('user_id'),
                "ip": access_data['ip'],
                "endpoint": access_data['endpoint'],
                "method": access_data['method'],
                "timestamp": access_data.get('timestamp', datetime.now().isoformat()),
                "browser": access_data['browser'],
                "os": access_data['os'],
                "device": access_data['device'],
                "is_mobile": access_data.get('is_mobile', False),
                "is_tablet": access_data.get('is_tablet', False),
                "is_pc": access_data.get('is_pc', False),
                "is_bot": access_data.get('is_bot', False)
            }
            
            data["access_logs"].append(log)
            self._write(data)
            return log
        except Exception as e:
            self.logger.error(f"Erro ao registrar acesso: {str(e)}")
            return None

    # --- Métodos Administrativos ---
    def backup_database(self, backup_path):
        """Cria uma cópia de segurança do banco de dados"""
        data = self._read()
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True

    def restore_database(self, backup_path):
        """Restaura o banco de dados a partir de um backup"""
        if not os.path.exists(backup_path):
            return False
            
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)
        
        self._write(backup_data)
        return True

    # --- Métodos de Diagnóstico ---
    def get_database_status(self):
        """Retorna estatísticas do banco de dados"""
        data = self._read()
        return {
            "users": len(data["users"]),
            "scripts": len(data["scripts"]),
            "permissions": len(data["permissions"]),
            "access_logs": len(data["access_logs"]),
            "execution_logs": len(data["execution_logs"]),
            "blocked_ips": len(data["blocked_ips"])
        }

    def verify_data_integrity(self):
        """Verifica a integridade dos relacionamentos no banco de dados"""
        data = self._read()
        issues = []
        
        # Verifica usuários referenciados em permissões
        user_ids = {u["id"] for u in data["users"]}
        for perm in data["permissions"]:
            if perm["user_id"] not in user_ids:
                issues.append(f"Permissão referencia usuário inexistente: {perm}")
        
        # Verifica scripts referenciados em permissões
        script_ids = {s["id"] for s in data["scripts"]}
        for perm in data["permissions"]:
            if perm["script_id"] not in script_ids:
                issues.append(f"Permissão referencia script inexistente: {perm}")
        
        return issues if issues else "Integridade do banco de dados verificada com sucesso"
