import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# ==============================
# Carrega variáveis de ambiente
# ==============================
env_path = Path(__file__).parent.parent.parent / 'flux_on' / '.env'
print(f"📁 Procurando .env em: {env_path}")
load_dotenv(dotenv_path=env_path)

# ==============================
# Determina caminhos base
# ==============================
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = DATA_DIR / 'logs'
BACKUP_DIR = BASE_DIR / 'FLUXON_BACKUPS'
SCRIPTS_DIR = BASE_DIR / 'flux_on' / 'scripts'

# ==============================
# Cria diretórios se não existirem
# ==============================
for directory in [DATA_DIR, LOGS_DIR, BACKUP_DIR, SCRIPTS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# ==============================
# Configurações gerais
# ==============================
CONFIG = {
    'DATABASE': str(DATA_DIR / 'fluxon.db'),
    'SCRIPTS_DIR': str(SCRIPTS_DIR),
    'LOGS_DIR': str(LOGS_DIR),
    'BACKUP_DIR': str(BACKUP_DIR),
    'MAX_LOG_SIZE': 10 * 1024 * 1024,  # 10MB
    'LOG_BACKUP_COUNT': 5,
    'ALLOWED_EXTENSIONS': ['.py', '.json', '.txt'],
    
    # 🔒 NOVAS CONFIGURAÇÕES DE REDE
    'LOCAL_NETWORK_ONLY': True,  # Ativa modo rede local apenas
    'ALLOWED_HOSTS': ['127.0.0.1', 'localhost', '::1'],  # Hosts permitidos
    'BLOCK_EXTERNAL_ACCESS': True  # Bloqueia acesso externo
}

# ==============================
# Configurações de segurança
# ==============================
# Carrega a chave fixa do .env, remove espaços e aspas
SECRET_KEY = os.getenv('SECRET_KEY')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')

if not SECRET_KEY or not ADMIN_TOKEN:
    raise ValueError("⚠️  SECRET_KEY ou ADMIN_TOKEN não configurados no .env")

# 🔒 CONFIGURAÇÕES DE REDE LOCAL ADICIONADAS AQUI
SECURITY_CONFIG = {
    'SECRET_KEY': SECRET_KEY,              # Deve ser igual no servidor e painel
    'ADMIN_TOKEN': ADMIN_TOKEN,            # Mesmo no servidor e painel
    'TOKEN_EXPIRATION': int(os.getenv('TOKEN_EXPIRATION', 3600)),  # 1 hora por padrão
    'ADMIN_EMAIL': os.getenv('ADMIN_EMAIL', 'admin@fluxon.com'),
    'ADMIN_PASSWORD': os.getenv('ADMIN_PASSWORD', 'senha_admin_segura'),  # Será hasheada
    
    # 🔒 NOVAS CONFIGURAÇÕES DE REDE LOCAL
    'NETWORK': {
        'local_only': True,  # Modo apenas rede local
        'allowed_ips': ['127.0.0.1', 'localhost', '::1', '192.168.1.0/24'],  # Rede local permitida
        'block_external': True,  # Bloqueia acesso externo
        'local_ports': [5000, 5001, 8501, 8502, 8503, 8504]  # Portas para modo local
    }
}

# ==============================
# Validação de diretórios e arquivos
# ==============================
for key, path in CONFIG.items():
    if 'DIR' in key and not Path(path).exists():
        raise FileNotFoundError(f"Diretório {path} não encontrado ou não foi criado corretamente")

print("✅ Configurações carregadas com sucesso")
print(f"SECRET_KEY: {SECURITY_CONFIG['SECRET_KEY'][:8]}... (não compartilhe publicamente)")
print(f"ADMIN_TOKEN: {SECURITY_CONFIG['ADMIN_TOKEN'][:8]}...")
print(f"🔒 MODO LOCAL ATIVADO: {SECURITY_CONFIG['NETWORK']['local_only']}")
print(f"🌐 IPS PERMITIDOS: {SECURITY_CONFIG['NETWORK']['allowed_ips']}")