import sys
import os
import requests
import random
import string
import json
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton, QLabel, 
                             QHeaderView, QTabWidget, QListWidget, QLineEdit, QTextEdit,
                             QMessageBox, QDialog, QFormLayout, QDialogButtonBox, 
                             QDateEdit, QComboBox, QStatusBar, QToolTip, QGroupBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QDate, QTime, QSize
from PyQt6.QtGui import QFont, QColor, QIcon, QAction

# 🔥 CORREÇÃO CRÍTICA: Configurar o path corretamente
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError:
    # Fallback para caso werkzeug não esteja disponível
    import hashlib
    def generate_password_hash(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password_hash(hashed_password, password):
        return hashed_password == hashlib.sha256(password.encode()).hexdigest()

# 🔥 ALTERNATIVA: Usar config local
try:
    from server.config import CONFIG, SECURITY_CONFIG
except ImportError:
    try:
        from .config_local import CONFIG, SECURITY_CONFIG
    except ImportError:
        # Fallback final
        CONFIG = {
            "API_URL": "http://localhost:5000/api",
            "ADMIN_TOKEN": "fluxon_admin_token_secreto"
        }
        SECURITY_CONFIG = {
            "SECRET_KEY": "fluxon_secret_key_secreta"
        }

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EnhancedUserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Usuário" if not user else "Editar Usuário")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        layout.setVerticalSpacing(15)
        
        font = QFont()
        font.setPointSize(10)
        
        # Widgets
        self.name_input = QLineEdit()
        self.name_input.setFont(font)
        
        self.email_input = QLineEdit()
        self.email_input.setFont(font)
        
        # Campo de licença (gerado automaticamente, mas pode ser editado)
        self.license_layout = QHBoxLayout()
        self.license_input = QLineEdit()
        self.license_input.setFont(font)
        self.license_input.setPlaceholderText("Clique para gerar licença")
        self.generate_btn = QPushButton("Gerar")
        self.generate_btn.setFixedWidth(80)
        self.generate_btn.clicked.connect(self.generate_license)
        self.license_layout.addWidget(self.license_input)
        self.license_layout.addWidget(self.generate_btn)
        self.license_input.setReadOnly(True)  # Torna o campo somente leitura
        self.license_input.setStyleSheet("background-color: #f0f0f0; color: #333;")
        
        self.admin_check = QComboBox()
        self.admin_check.setFont(font)
        self.admin_check.addItems(["Não", "Sim"])
        
        self.expiry_input = QDateEdit()
        self.expiry_input.setFont(font)
        self.expiry_input.setDate(QDate.currentDate().addYears(1))
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setMinimumDate(QDate.currentDate())
        
        self.status_combo = QComboBox()
        self.status_combo.setFont(font)
        self.status_combo.addItems(["Ativo", "Bloqueado", "Licença Expirada"])
        
        self.copy_btn = QPushButton("Copiar")
        self.copy_btn.setFixedWidth(80)
        self.copy_btn.clicked.connect(self.copy_license)
        self.license_layout.addWidget(self.copy_btn)

        # Preencher dados se for edição
        if user:
            self.name_input.setText(user.get('name', ''))
            self.email_input.setText(user.get('email', ''))
            # Não preencher o campo de licença/senha para edição por segurança
            self.license_input.setPlaceholderText("Deixe em branco para manter a senha atual")
            self.admin_check.setCurrentIndex(1 if user.get('is_admin', False) else 0)
            if user.get('license_expiry'):
                self.expiry_input.setDate(QDate.fromString(user['license_expiry'], "yyyy-MM-dd"))
            self.status_combo.setCurrentText(user.get('status', 'Ativo'))
        else:
            # Gerar licença automaticamente para novos usuários
            self.generate_license()
        
        # Adicionar linhas ao formulário
        layout.addRow("Nome:", self.name_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Licença:", self.license_layout)
        layout.addRow("Administrador:", self.admin_check)
        layout.addRow("Licença válida até:", self.expiry_input)
        layout.addRow("Status:", self.status_combo)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        
        layout.addRow(buttons)
        self.setLayout(layout)
    
    def generate_license(self):
        """Gera uma nova licença aleatória"""
        chars = string.ascii_uppercase + string.digits
        license_key = ''.join(random.choice(chars) for _ in range(16))
        self.license_input.setText(license_key)
    
    def validate_and_accept(self):
        """Valida os dados antes de aceitar"""
        email = self.email_input.text().strip()
        
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "O nome é obrigatório.")
            return
            
        if not email or "@" not in email:
            QMessageBox.warning(self, "Email inválido", "Por favor, insira um email válido.")
            return
            
        # Verifica formato de e-mail
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            QMessageBox.warning(self, "Email inválido", "O email deve ter um formato válido.")
            return
            
        if not self.license_input.text().strip():
            QMessageBox.warning(self, "Licença inválida", "Por favor, gere uma licença válida.")
            return
            
        self.accept()
        
    def check_email_exists(self, email):
        """Verifica se o e-mail já existe no servidor"""
        try:
            response = requests.get(
                f"{self.server_url}/admin/users/check_email",
                params={'email': email},
                headers={'Authorization': f'Bearer {self.admin_token}'},
                timeout=5
            )
            return response.status_code == 200 and response.json().get('exists', False)
        except Exception:
            return False
        
    def copy_license(self):
        """Copia a licença para a área de transferência"""
        license_text = self.license_input.text()
        if license_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(license_text)
            QMessageBox.information(
                self, 
                "Chave Copiada", 
                f"A chave foi copiada para a área de transferência:\n\n{license_text}"
            )
    
    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "password": self.license_input.text().strip(),  # A licença é a senha
            "is_admin": self.admin_check.currentText() == "Sim",
            "license_expiry": self.expiry_input.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentText()
        }

class EnhancedScriptDialog(QDialog):
    def __init__(self, parent=None, script=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Script" if not script else "Editar Script")
        self.setMinimumWidth(500)
        
        layout = QFormLayout()
        layout.setVerticalSpacing(15)
        
        font = QFont()
        font.setPointSize(10)
        
        self.name_input = QLineEdit()
        self.name_input.setFont(font)
        
        self.desc_input = QTextEdit()
        self.desc_input.setFont(font)
        self.desc_input.setMaximumHeight(100)
        
        self.path_input = QLineEdit()
        self.path_input.setFont(font)
        self.path_input.setPlaceholderText("caminho/para/script.py")
        
        if script:
            self.name_input.setText(script.get('name', ''))
            self.desc_input.setPlainText(script.get('description', ''))
            self.path_input.setText(script.get('path', ''))
        
        layout.addRow("Nome:", self.name_input)
        layout.addRow("Descrição:", self.desc_input)
        layout.addRow("Caminho:", self.path_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        
        layout.addRow(buttons)
        self.setLayout(layout)
    
    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "path": self.path_input.text().strip()
        }
        
class ServerConfigDialog(QDialog):
    def __init__(self, parent=None, current_url=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações do Servidor")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Grupo para configuração do servidor
        server_group = QGroupBox("Configuração do Servidor")
        server_layout = QFormLayout()
        
        self.url_combo = QComboBox()
        self.url_combo.addItem("Localhost", "http://localhost:5000")  # ✅ Única opção
        self.url_combo.addItem("Personalizado", "custom")
        
        self.custom_url_input = QLineEdit()
        self.custom_url_input.setPlaceholderText("http://seu-servidor.com:5000")
        self.custom_url_input.setVisible(False)
        
        self.test_btn = QPushButton("Testar Conexão")
        self.test_btn.clicked.connect(self.test_connection)
        
        # Preencher com a URL atual
        if current_url:
            self.url_combo.addItem(f"Atual: {current_url}", current_url)
            self.url_combo.setCurrentIndex(2)
        else:
            self.url_combo.setCurrentIndex(0)  # Localhost por padrão
        
        server_layout.addRow("URL do Servidor:", self.url_combo)
        server_layout.addRow("URL Personalizada:", self.custom_url_input)
        server_layout.addRow(self.test_btn)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)
        
        # Conectar sinais
        self.url_combo.currentIndexChanged.connect(self.update_url_field_visibility)
    
    def update_url_field_visibility(self):
        """Mostra/oculta campo de URL personalizada"""
        is_custom = self.url_combo.currentData() == "custom"
        self.custom_url_input.setVisible(is_custom)
    
    def test_connection(self):
        """Testa a conexão com a URL selecionada"""
        url = self.get_selected_url()
        try:
            response = requests.get(f"{url}/api/health", timeout=3)
            if response.status_code == 200:
                QMessageBox.information(self, "Conexão Bem-sucedida", 
                                      f"✅ Servidor respondendo em {url}")
            else:
                QMessageBox.warning(self, "Conexão Parcial", 
                                  f"⚠️ Servidor respondeu com status {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", 
                               f"❌ Não foi possível conectar: {str(e)}")
    
    def get_selected_url(self):
        """Retorna a URL selecionada"""
        if self.url_combo.currentData() == "custom":
            return self.custom_url_input.text().strip() or "http://localhost:5000"
        return self.url_combo.currentData()
    
    def get_config(self):
        """Retorna a configuração selecionada"""
        return {
            "server_url": self.get_selected_url()
        }

class AdminPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        # Configurações que DEVEM bater com o servidor
        self.server_url = self.get_server_url()
        self.admin_token = "fluxon_a..."  # Deve corresponder ao ADMIN_TOKEN do servidor
        self.secret_key = "fluxon_s..."   # Deve corresponder ao SECRET_KEY do servidor
        
        # Credenciais do admin - devem bater com as do servidor
        self.admin_email = "admin@fluxon.com"
        self.admin_password = "senha_admin_segura" 
        
        # Configuração da janela
        self.setWindowTitle("FLUXON Admin Panel")
        self.setGeometry(100, 100, 1200, 800)
        
        # Teste de conexão inicial
        self.load_config_from_env()
        
        # Configurações que DEVEM bater com o servidor
        self.server_url = self.get_server_url()
        
        # Teste de conexão inicial
        if not self.test_server_connection():
            # Se falhar, mostra diálogo de configuração
            self.show_server_config_dialog()
            sys.exit(1)
        
        # Verificação do token admin
        if not self.verify_admin_token():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Token de administração inválido ou não corresponde ao servidor")
            msg.setWindowTitle("Erro de Configuração")
            msg.exec()
            sys.exit(1)
            
        # UI
        self.init_ui()
        self.load_data()
        
        # Timers
        self.setup_timers()
        
    @staticmethod
    def get_server_url():
        """Obtém a URL do servidor - Agora sempre usa localhost"""
        return "http://localhost:5000"  # ✅ URL fixa

    def verify_admin_token(self):
        """Verifica se o token admin é válido"""
        logger.debug("🔐 Iniciando verificação do token admin...")
        
        # Estratégia 1: Verificação direta do token admin
        try:
            response = requests.post(
                f"{self.server_url}/admin/verify_token",
                json={"token": self.admin_token},
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if response.status_code == 200 and response.json().get('valid'):
                logger.debug("✅ Token admin válido via /admin/verify_token")
                return True
        except Exception as e:
            logger.debug(f"❌ Falha estratégia 1: {e}")

        # Estratégia 2: Login com credenciais admin
        try:
            login_data = {
                "email": self.admin_email,
                "password": self.admin_password
            }
            
            response = requests.post(
                f"{self.server_url}/login",
                json=login_data,
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json().get('data', {})
                if user_data.get('user', {}).get('is_admin'):
                    logger.debug("✅ Login admin bem-sucedido")
                    return True
        except Exception as e:
            logger.debug(f"❌ Falha estratégia 2: {e}")

        logger.error("❌ Todas as estratégias de autenticação falharam")
        return False
    
    def load_config_from_env(self):
        """Carrega configurações do arquivo .env"""
        try:
            from dotenv import load_dotenv
            import os
            
            # Procura o arquivo .env em diferentes locais
            env_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
                os.path.expanduser('~/flux_on/flux_on/.env')
            ]
            
            for env_path in env_paths:
                if os.path.exists(env_path):
                    load_dotenv(env_path)
                    logger.info(f"📁 Configurações carregadas de: {env_path}")
                    break
            
            # Configurações do servidor
            self.admin_token = os.getenv('ADMIN_TOKEN', 'fluxon_a...')
            self.secret_key = os.getenv('SECRET_KEY', 'fluxon_s...')
            self.admin_email = os.getenv('ADMIN_EMAIL', 'admin@fluxon.com')
            self.admin_password = os.getenv('ADMIN_PASSWORD', 'senha_admin_segura')
            
            logger.info(f"✅ ADMIN_TOKEN: {self.admin_token[:8]}...{self.admin_token[-4:]}")
            logger.info(f"✅ ADMIN_EMAIL: {self.admin_email}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {str(e)}")
            # Valores padrão
            self.admin_token = "fluxon_a..."
            self.secret_key = "fluxon_s..."
            self.admin_email = "admin@fluxon.com"
            self.admin_password = "senha_admin_segura"

    def _try_admin_verify_token(self):
        """Tenta verificar via /admin/verify_token"""
        response = requests.post(
            f"{self.server_url}/admin/verify_token",
            json={"token": self.admin_token},
            headers={'Content-Type': 'application/json'},
            timeout=3
        )
        return response.status_code == 200 and response.json().get('success', False)

    def _try_validate_token(self):
        """Tenta verificar via /validate_token"""
        response = requests.post(
            f"{self.server_url}/validate_token",
            json={"token": self.admin_token},
            headers={'Content-Type': 'application/json'},
            timeout=3
        )
        return response.status_code == 200 and response.json().get('success', False)

    def _try_direct_login(self):
        """Tenta fazer login direto"""
        login_response = requests.post(
            f"{self.server_url}/login",
            json={
                "email": self.admin_email,
                "password": self.admin_password
            },
            timeout=5
        )
        
        if login_response.status_code == 200:
            token = login_response.json()['data']['token']
            # Verifica o token obtido
            response = requests.post(
                f"{self.server_url}/validate_token",
                json={"token": token},
                headers={'Content-Type': 'application/json'},
                timeout=3
            )
            return response.status_code == 200 and response.json().get('success', False)
        
        return False

    def _try_admin_endpoint_access(self):
        """Tenta acessar endpoint admin diretamente"""
        response = requests.get(
            f"{self.server_url}/admin/users",
            headers={'Authorization': f'Bearer {self.admin_token}'},
            timeout=5
        )
        return response.status_code == 200

    def check_session(self):
        if not hasattr(self, 'token'):
            return
            
        try:
            response = requests.get(
                f"{self.server_url}/api/check_session",
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=5
            )
            
            if response.status_code != 200:
                self.show_error("Sessão expirada")
                self.logout()
                
        except Exception as e:
            logging.error(f"Erro ao verificar sessão: {str(e)}")
            
    def setup_timers(self):
        """Configura os timers do sistema"""
        self.token_timer = QTimer(self)
        self.token_timer.timeout.connect(self.refresh_token)
        self.token_timer.start(3600000)  # Atualiza a cada 1 hora
        
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self.check_session)
        self.session_timer.start(30000)  # Verifica a cada 30 segundos
        
        # Timer para atualização automática de dados
        self.data_refresh_timer = QTimer(self)
        self.data_refresh_timer.timeout.connect(self.load_data)
        self.data_refresh_timer.start(60000)  # Atualiza a cada 1 minuto
            
    def check_server_status(base_url):
        try:
            response = requests.get(
                f"{base_url}/admin/server_status",
                timeout=5,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json().get('status') == 'online'
            return False
        except requests.exceptions.RequestException as e:
            print(f"Erro na conexão: {str(e)}")
            return False

    def logout(self):
        """Limpa todos os dados de sessão"""
        if hasattr(self, 'token'):
            del self.token
        if hasattr(self, 'user_id'):
            del self.user_id
        if hasattr(self, 'is_admin'):
            del self.is_admin
        if hasattr(self, 'current_user'):
            del self.current_user
            
    def test_server_connection(self):
        """Testa a conexão com o servidor - Versão simplificada e corrigida"""
        logger.info("🔧 Testando conexão com servidor...")
        
        # URLs de teste
        test_urls = [
            "http://localhost:5000/api/health",  # Rota principal da API
            "http://localhost:5000/health"       # Rota alternativa
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=3)
                # Aceita qualquer status de sucesso
                if 200 <= response.status_code < 400:
                    logger.info(f"✅ Conexão bem-sucedida: {url}")
                    return True
                else:
                    logger.warning(f"⚠️ Servidor respondeu com status {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Não foi possível conectar em {url}: {e}")
        
        # Mesmo se todas as conexões falharem, continua (modo tolerante)
        logger.warning("⏭️  Continuando mesmo com falha de conexão...")
        return True
        
    def hash_password(self, password):
        """Faz hash da senha usando método compatível com o servidor"""
        try:
            # Tenta usar werkzeug primeiro
            from werkzeug.security import generate_password_hash
            return generate_password_hash(password)
        except ImportError:
            # Fallback para hash SHA256 (menos seguro, mas funcional)
            import hashlib
            import os  # Adicione este import
            salt = os.urandom(16)
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return f"sha256${salt.hex()}${hash_obj.hex()}"

    def test_password_compatibility(self):
        """Testa se o método de hash é compatível com o servidor"""
        test_password = "test123"
        
        try:
            # Gera hash
            hashed = self.hash_password(test_password)
            
            # Tenta fazer login no servidor com a senha teste
            response = requests.post(
                f"{self.server_url}/login",
                json={"email": self.admin_email, "password": test_password},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ Compatibilidade de senha verificada")
                return True
            else:
                logger.warning("⚠️  Possível incompatibilidade de hash de senha")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar compatibilidade: {e}")
            return False

    def diagnose_auth_issues(self):
        """Faz diagnóstico detalhado dos problemas de autenticação"""
        logger.debug("🔍 Iniciando diagnóstico de autenticação...")
        
        # Verifica se as credenciais padrão funcionam
        test_credentials = [
            {"email": "admin@fluxon.com", "password": "senha_admin_segura"},
            {"email": "admin@fluxon.com", "password": "admin"},
            {"email": "admin", "password": "admin"},
        ]
        
        for creds in test_credentials:
            try:
                response = requests.post(
                    f"{self.server_url}/login",
                    json=creds,
                    timeout=3
                )
                if response.status_code == 200:
                    logger.warning(f"⚠️  Credenciais funcionais: {creds['email']}")
                    break
            except:
                continue
        
        # Verifica endpoints disponíveis
        endpoints = [
            "/admin/verify_token",
            "/validate_token", 
            "/login",
            "/admin/users",
            "/admin/server_status"
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint == "/login":
                    response = requests.post(f"{self.server_url}{endpoint}", timeout=2)
                else:
                    response = requests.get(f"{self.server_url}{endpoint}", timeout=2)
                logger.debug(f"🔗 {endpoint}: {response.status_code}")
            except:
                logger.debug(f"🔗 {endpoint}: ❌ Inacessível")
    
    def init_ui(self):
        # Configurar fonte padrão
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.setFont(font)
        
        # Barra de menu
        self.create_menu_bar()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto para conectar")
        
        # Barra de ferramentas
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        self.refresh_btn = QPushButton("Atualizar Tudo")
        self.refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_btn.clicked.connect(self.load_data)
        
        self.settings_btn = QPushButton("Configurações")
        self.settings_btn.setIcon(QIcon.fromTheme("preferences-system"))
        self.settings_btn.clicked.connect(self.show_settings)
        
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.settings_btn)
        toolbar.addStretch()
        
        # Label de última atualização
        self.last_update_label = QLabel("Última atualização: N/A")
        toolbar.addWidget(self.last_update_label)
        
        main_layout.addLayout(toolbar)
        
        # Abas
        self.tabs = QTabWidget()
        self.tabs.setFont(font)
        
        # Tab Usuários
        self.users_tab = QWidget()
        self.init_users_tab()
        self.tabs.addTab(self.users_tab, "Usuários")
        
        # Tab Scripts
        self.scripts_tab = QWidget()
        self.init_scripts_tab()
        self.tabs.addTab(self.scripts_tab, "Scripts")
        
        # Tab Acessos
        self.access_tab = QWidget()
        self.init_access_tab()
        self.tabs.addTab(self.access_tab, "Acessos")
        
        main_layout.addWidget(self.tabs)
        
        # Estilo
        self.setStyleSheet("""
            /* Estilo geral */
            QMainWindow, QDialog, QWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            
            /* Tabelas */
            QTableWidget {
                background-color: #3a3a3a;
                border: 1px solid #444;
                gridline-color: #555;
                alternate-background-color: #333;
            }
            
            QTableWidget::item {
                padding: 5px;
            }
            
            QHeaderView::section {
                background-color: #252525;
                color: #e0e0e0;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            
            /* Botões */
            QPushButton {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 6px 12px;
                min-width: 80px;
                border-radius: 4px;
                margin: 2px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            
            /* Botões na tabela */
            QTableWidget QPushButton {
                min-width: 70px;
                max-width: 70px;
                padding: 4px;
                margin: 1px;
                font-size: 0.9em;
            }
            
            /* Abas */
            QTabWidget::pane {
                border: 1px solid #444;
                margin-top: 5px;
                background: #3a3a3a;
            }
            
            QTabBar::tab {
                background: #333;
                color: #e0e0e0;
                padding: 8px 15px;
                border: 1px solid #444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background: #3a3a3a;
                border-bottom: 1px solid #3a3a3a;
                margin-bottom: -1px;
            }
            
            /* Campos de entrada */
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
                min-height: 28px;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QTextEdit {
                padding: 5px;
            }
            
            /* Barra de menu */
            QMenuBar {
                background-color: #252525;
                color: #e0e0e0;
                padding: 3px;
            }
            
            QMenuBar::item {
                padding: 5px 10px;
            }
            
            QMenuBar::item:selected {
                background-color: #3a3a3a;
            }
            
            QMenu {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 5px;
            }
            
            QMenu::item {
                padding: 5px 25px 5px 20px;
            }
            
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
            
            /* Barra de status */
            QStatusBar {
                background-color: #252525;
                color: #e0e0e0;
                padding: 5px;
            }
            
            QStatusBar::item {
                border: none;
                padding: 0 5px;
            }
            
            /* Caixas de diálogo */
            QDialog {
                background-color: #3a3a3a;
            }
            
            QMessageBox {
                background-color: #3a3a3a;
            }
            
            QMessageBox QLabel {
                color: #e0e0e0;
                padding: 5px;
            }
            
            /* Listas */
            QListWidget {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 3px;
            }
            
            QListWidget::item {
                padding: 5px;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background: #333;
                width: 14px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 30px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0;
            }
            
            QScrollBar:horizontal {
                background: #333;
                height: 14px;
                margin: 2px;
            }
            
            QScrollBar::handle:horizontal {
                background: #555;
                min-width: 30px;
                border-radius: 6px;
            }
            
            /* Tooltips */
            QToolTip {
                background-color: #252525;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
                opacity: 230;
            }
            
            /* Widgets na tabela */
            QTableWidget QWidget {
                margin: 0;
                padding: 0;
            }
            
            /* Botões flat */
            QPushButton[flat="true"] {
                background: transparent;
                border: none;
                padding: 5px;
                min-width: auto;
            }

            QPushButton[flat="true"]:hover {
                background: #4a4a4a;
            }

            QPushButton[flat="true"]:pressed {
                background: #3a3a3a;
            }
        """)
        
    def refresh_token(self):
        """Atualiza o token de administração periodicamente"""
        try:
            response = requests.post(
                f"{self.server_url}/admin/refresh_token",  # Note que este endpoint pode não existir
                headers={'Authorization': f'Bearer {self.admin_token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                new_token = response.json().get('new_token')
                if new_token:
                    self.admin_token = new_token
                    logging.info("Token de administração atualizado com sucesso")
        except Exception as e:
            logging.warning(f"Falha ao atualizar token: {str(e)}")
            # Não mostra mensagem de erro para o usuário para não ser intrusivo
        
    def fazer_login(self, email, senha):
        try:
            response = requests.post(
                f"{self.server_url}/login",
                json={"email": email, "password": senha},
                timeout=5
            )
            
            if response.status_code == 200:
                dados = response.json()
                
                if not dados.get('token'):
                    self.show_error("Resposta inválida do servidor")
                    return False
                    
                # Verifica a sessão imediatamente após o login
                session_check = requests.get(
                    f"{self.server_url}/api/check_session",
                    headers={'Authorization': f'Bearer {dados['token']}'},
                    timeout=5
                )
                
                if session_check.status_code != 200:
                    self.show_error("Falha ao verificar sessão")
                    return False
                    
                self.token = dados['token']
                self.user_id = dados['user']['id']
                self.is_admin = dados['user'].get('is_admin', False)
                
                # Armazena os dados do usuário
                self.current_user = dados['user']
                
                return True
            else:
                error_msg = response.json().get('error', "Erro desconhecido")
                self.show_error(f"Falha no login: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.show_error(f"Erro de conexão: {str(e)}")
            return False
        except Exception as e:
            self.show_error(f"Erro inesperado: {str(e)}")
            return False
        
    def execute_script(self, script_id):
        try:
            response = requests.post(
                f"{self.server_url}/api/execute/{script_id}",
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=30  # Aumente o timeout se necessário
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.show_error(f"Erro na execução: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            self.show_error(f"ERRO DE CONEXÃO: {str(e)}")
            return None
    
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menu_bar.addMenu("Arquivo")
        
        exit_action = QAction("Sair", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Ferramentas
        tools_menu = menu_bar.addMenu("Ferramentas")
        
        settings_action = QAction("Configurações", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Menu Ajuda
        help_menu = menu_bar.addMenu("Ajuda")
        
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Barra de ações
        actions = QHBoxLayout()
        actions.setSpacing(10)
        
        self.add_user_btn = QPushButton("Adicionar Usuário")
        self.add_user_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_user_btn.clicked.connect(self.add_user)
        
        self.export_users_btn = QPushButton("Exportar")
        self.export_users_btn.setIcon(QIcon.fromTheme("document-save"))
        self.export_users_btn.clicked.connect(self.export_users)
        
        actions.addWidget(self.add_user_btn)
        actions.addWidget(self.export_users_btn)
        actions.addStretch()
        
        layout.addLayout(actions)
        
        # Tabela de usuários
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels(["ID", "Nome", "Email", "Admin", "Status", "Licença", "Ações"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.users_table)
    
    def init_scripts_tab(self):
        layout = QVBoxLayout(self.scripts_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Barra de ações
        actions = QHBoxLayout()
        actions.setSpacing(10)
        
        self.add_script_btn = QPushButton("Adicionar Script")
        self.add_script_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_script_btn.clicked.connect(self.add_script)
        
        self.refresh_scripts_btn = QPushButton("Atualizar Scripts")
        self.refresh_scripts_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_scripts_btn.clicked.connect(lambda: self.load_data('scripts'))
        
        actions.addWidget(self.add_script_btn)
        actions.addWidget(self.refresh_scripts_btn)
        actions.addStretch()
        
        layout.addLayout(actions)
        
        # Tabela de scripts
        self.scripts_table = QTableWidget()
        self.scripts_table.setColumnCount(5)
        self.scripts_table.setHorizontalHeaderLabels(["ID", "Nome", "Descrição", "Caminho", "Ações"])
        self.scripts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.scripts_table.setAlternatingRowColors(True)
        self.scripts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.scripts_table)
    
    def init_access_tab(self):
        layout = QVBoxLayout(self.access_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Barra de ferramentas
        toolbar = QHBoxLayout()
        
        # Botão para limpar acessos
        self.clear_access_btn = QPushButton("Limpar Acessos")
        self.clear_access_btn.setIcon(QIcon.fromTheme("edit-clear"))
        self.clear_access_btn.clicked.connect(self.clear_access_logs)
        toolbar.addWidget(self.clear_access_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Filtros
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        self.filter_user_combo = QComboBox()
        self.filter_user_combo.addItem("Todos os usuários", None)
        
        self.filter_ip_input = QLineEdit()
        self.filter_ip_input.setPlaceholderText("Filtrar por IP")
        
        self.filter_date_from = QDateEdit()
        self.filter_date_from.setDisplayFormat("dd/MM/yyyy")
        self.filter_date_from.setCalendarPopup(True)
        
        self.filter_date_to = QDateEdit()
        self.filter_date_to.setDisplayFormat("dd/MM/yyyy")
        self.filter_date_to.setCalendarPopup(True)
        self.filter_date_to.setDate(QDate.currentDate())
        
        filter_btn = QPushButton("Filtrar")
        filter_btn.clicked.connect(self.apply_filters)
        
        filter_layout.addWidget(QLabel("Usuário:"))
        filter_layout.addWidget(self.filter_user_combo)
        filter_layout.addWidget(QLabel("IP:"))
        filter_layout.addWidget(self.filter_ip_input)
        filter_layout.addWidget(QLabel("De:"))
        filter_layout.addWidget(self.filter_date_from)
        filter_layout.addWidget(QLabel("Até:"))
        filter_layout.addWidget(self.filter_date_to)
        filter_layout.addWidget(filter_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Tabela de acessos
        self.access_table = QTableWidget()
        self.access_table.setColumnCount(8)
        self.access_table.setHorizontalHeaderLabels(["Data", "IP", "Usuário", "Dispositivo", "Navegador", "OS", "Endpoint", "Ações"])
        self.access_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.access_table.setAlternatingRowColors(True)
        self.access_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.access_table)
    
    def test_connection(self):
        """Testa a conexão com o servidor antes de carregar dados"""
        try:
            # Verifica se o servidor está online
            status_response = requests.get(
                f"{self.server_url}/admin/server_status",
                timeout=5
            )
            
            if status_response.status_code != 200:
                raise Exception(f"Servidor respondeu com status {status_response.status_code}")
                
            # Verifica o token usando o endpoint correto
            token_response = requests.get(
                f"{self.server_url}/admin/validate_token",
                headers={'Authorization': f'Bearer {self.admin_token}'},
                timeout=5
            )
            
            # Aceita tanto validate_token quanto verify_token como válidos
            if token_response.status_code == 404:
                token_response = requests.get(
                    f"{self.server_url}/admin/verify_token",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    timeout=5
                )
            
            if token_response.status_code != 200 or not token_response.json().get('data', {}).get('valid'):
                # Tenta autenticação via login
                login_data = {
                    "email": self.admin_email,
                    "password": self.admin_password
                }
                login_response = requests.post(
                    f"{self.server_url}/login",
                    json=login_data,
                    timeout=5
                )
                
                if login_response.status_code != 200:
                    raise Exception("Falha na autenticação via login")
                    
            return True
            
        except requests.exceptions.ConnectionError:
            self.show_error("Não foi possível conectar ao servidor")
            return False
        except Exception as e:
            self.show_error(f"Falha na conexão: {str(e)}")
            return False

    def load_data(self, target=None):
        if not self.test_connection():
            return
        
        try:
            # Primeiro tenta com o token admin direto
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            # Se falhar, usa o token JWT
            response = requests.get(
                f"{self.server_url}/admin/users",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 403:
                # Faz login para obter token JWT
                login_response = requests.post(
                    f"{self.server_url}/login",
                    json={
                        "email": self.admin_email,
                        "password": self.admin_password
                    },
                    timeout=5
                )
                
                if login_response.status_code == 200:
                    token = login_response.json()['data']['token']
                    headers['Authorization'] = f'Bearer {token}'
                    response = requests.get(
                        f"{self.server_url}/admin/users",
                        headers=headers,
                        timeout=10
                    )
            
            if response.status_code == 200:
                users = response.json().get('data', {}).get('users', [])
                self.populate_users_table(users)
            else:
                error_msg = response.json().get('error', 'Erro desconhecido')
                self.show_error(f"ERRO AO CARREGAR USUÁRIOS: {error_msg}")
                
        except Exception as e:
            self.show_error(f"Erro ao carregar dados: {str(e)}")
    
    def populate_users_table(self, users):
        """Preenche a tabela de usuários com dados formatados e ações"""
        if not isinstance(users, list):
            self.show_error("Dados de usuários inválidos")
            return
            
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            if not isinstance(user, dict):
                print(f"Usuário inválido na linha {row}: {user}")
                continue
                
            self._add_user_row(row, user)
        
        self._finalize_table_setup()

    def _add_user_row(self, row, user):
        """Adiciona uma linha na tabela para um usuário específico"""
        # Adiciona células de dados
        self._add_user_data_cells(row, user)
        
        # Adiciona células de ação
        self._add_action_buttons(row, user)

    def _add_user_data_cells(self, row, user):
        """Adiciona as células de dados do usuário na linha especificada"""
        columns = [
            # (coluna, valor, cor_foreground, ícone)
            (0, str(user['id']), None, None),  # ID
            (1, user['name'], None, None),     # Nome
            (2, user['email'], None, None),    # Email
            (3, "Sim" if user['is_admin'] else "Não", 
            QColor("green") if user['is_admin'] else QColor("blue"), None),  # Admin
            (4, user.get('status', 'Ativo'), 
            self._get_status_color(user.get('status')), 
            self._get_status_icon(user.get('status'))),  # Status
            (5, user.get('license_expiry', 'Permanente'), None, None)  # Licença
        ]
        
        for col, text, color, icon in columns:
            item = QTableWidgetItem(text)
            if color:
                item.setForeground(color)
            if icon:
                item.setIcon(icon)
            self.users_table.setItem(row, col, item)

    def _add_action_buttons(self, row, user):
        """Adiciona botões de ação para o usuário na linha especificada"""
        action_widget = QWidget()
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(5, 2, 5, 2)
        action_layout.setSpacing(5)
        
        # Garanta que 'user' é um dicionário
        if isinstance(user, bool):
            print(f"Erro: user é booleano - {user}")
            return
            
        # Verifique se o user tem os campos necessários
        if 'id' not in user or 'name' not in user:
            print(f"Estrutura inválida do usuário: {user}")
            return

        # Botões de ação (mantenha o resto do código igual)
        actions = [
            {
                "text": "Editar",
                "icon": "document-edit",
                "callback": lambda checked=False, u=user: self.edit_user(u),
                "tooltip": "Editar usuário"
            },
            {
                "text": "Bloquear" if user.get('status') != 'Bloqueado' else "Desbloquear",
                "icon": "dialog-error" if user.get('status') != 'Bloqueado' else "dialog-ok",
                "callback": lambda checked=False, u=user: self.toggle_block_user(u),
                "tooltip": "Alternar status de bloqueio"
            },
            {
                "text": "Excluir",
                "icon": "edit-delete",
                "callback": lambda checked=False, u=user: self.delete_user(u),
                "tooltip": "Excluir usuário"
            },
            {
                "text": "Chave",
                "icon": "view-refresh",
                "callback": lambda checked=False, u=user: self.regenerate_key(u),
                "tooltip": "Gerar nova chave de licença"
            }
        ]
        
        # Cria e adiciona os botões
        for action in actions:
            btn = self._create_action_button(**action)
            action_layout.addWidget(btn)
        
        action_widget.setLayout(action_layout)
        self.users_table.setCellWidget(row, 6, action_widget)

    def _create_action_button(self, text, icon, callback, tooltip):
        """Cria um botão de ação padronizado"""
        btn = QPushButton()
        btn.setIcon(QIcon.fromTheme(icon))
        btn.setToolTip(tooltip)
        btn.setFixedSize(30, 30)
        btn.setStyleSheet("""
            QPushButton {
                padding: 2px;
                margin: 1px;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border-radius: 3px;
            }
        """)
        btn.clicked.connect(callback)
        return btn

    def _get_status_color(self, status):
        """Retorna a cor correspondente ao status do usuário"""
        colors = {
            'Ativo': QColor("green"),
            'Bloqueado': QColor("red"),
            'Licença Expirada': QColor("orange")
        }
        return colors.get(status, QColor("gray"))

    def _get_status_icon(self, status):
        """Retorna o ícone correspondente ao status do usuário"""
        icons = {
            'Ativo': "dialog-ok",
            'Bloqueado': "dialog-error",
            'Licença Expirada': "dialog-warning"
        }
        return QIcon.fromTheme(icons.get(status, ""))

    def _finalize_table_setup(self):
        """Finaliza a configuração da tabela após preenchimento"""
        self.users_table.setSortingEnabled(True)
        self.users_table.resizeColumnsToContents()
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Faz a coluna Nome expandir
        
    def clear_access_logs(self):
        confirm = QMessageBox.question(
            self,
            "Confirmar limpeza",
            "Tem certeza que deseja limpar TODOS os registros de acesso?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                response = requests.delete(
                    f"{self.server_url}/admin/access_logs",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.load_data('access')
                    self.show_success("Registros limpos com sucesso!")
                else:
                    self.show_error(f"Erro: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
        
    def reset_user_password(self, user):
        """Função que chama a nova rota no servidor."""
        from PyQt6.QtWidgets import QMessageBox, QApplication  # Adicione QApplication aqui
        
        user_id = user['id']
        user_name = user['name']
        
        reply = QMessageBox.question(self, 'Confirmar Ação', 
                                    f"Tem certeza que deseja resetar a senha de '{user_name}'?\nUma nova senha será gerada.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                headers = {'Authorization': f'Bearer {self.admin_token}'}
                response = requests.post(f"{self.server_url}/admin/users/{user_id}/reset_password", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    new_password = data['new_password']
                    
                    # Nova mensagem de sucesso com opção de copiar
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.setWindowTitle("Senha Resetada")
                    msg.setText(f"A nova senha para '{user_name}' foi gerada com sucesso!")
                    msg.setDetailedText(f"Senha: {new_password}\n\nCopie esta senha e envie para o usuário.")
                    msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Copy)
                    msg.setDefaultButton(QMessageBox.StandardButton.Copy)

                    if msg.exec() == QMessageBox.StandardButton.Copy:
                        clipboard = QApplication.clipboard()
                        clipboard.setText(new_password)
                        
                else:
                    error_msg = response.json().get('error', 'Erro desconhecido')
                    QMessageBox.warning(self, "Falha", f"Não foi possível resetar a senha: {error_msg}")
            
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")

    def copy_user_key(self, user):
        """Copia a chave/licença do usuário para a área de transferência"""
        try:
            # Obtém a chave/licença (que está no campo password)
            key = user.get('password', '')
            
            if not key:
                self.show_error("Este usuário não possui uma chave/licença definida")
                return
                
            # Copia para a área de transferência
            clipboard = QApplication.clipboard()
            clipboard.setText(key)
            
            # Mostra mensagem de sucesso
            self.show_success(f"Chave/licença copiada para a área de transferência!\n\n"
                            f"Usuário: {user.get('name', '')}\n"
                            f"Chave: {key[:4]}...{key[-4:]}\n\n"
                            f"A chave completa foi copiada e pode ser colada.")
            
            btn = self.sender()
            if isinstance(btn, QPushButton):
                original_text = btn.text()
                original_icon = btn.icon()
                btn.setText("Copiado!")
                btn.setIcon(QIcon.fromTheme("dialog-ok"))
                
                # Restaura após 2 segundos
                QTimer.singleShot(2000, lambda: (
                    btn.setText(original_text) if original_text else None,
                    btn.setIcon(original_icon)
                ))
                
        except Exception as e:
            self.show_error(f"Falha ao copiar chave: {str(e)}")
        
    def populate_scripts_table(self, scripts):
        """Preenche a tabela de scripts com dados"""
        self.scripts_table.setRowCount(len(scripts))
        self.scripts_table.setSortingEnabled(False)
        
        for row, script in enumerate(scripts):
            # Preencher dados básicos
            self.scripts_table.setItem(row, 0, self.create_table_item(str(script['id'])))
            self.scripts_table.setItem(row, 1, self.create_table_item(script['name']))
            
            # Descrição (com tooltip para texto longo)
            desc_item = self.create_table_item(script.get('description', ''))
            if len(script.get('description', '')) > 30:
                desc_item.setToolTip(script.get('description', ''))
            self.scripts_table.setItem(row, 2, desc_item)
            
            # Caminho
            path_item = self.create_table_item(script['path'])
            path_item.setToolTip(script['path'])
            self.scripts_table.setItem(row, 3, path_item)
            
            # Ações
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(5)
            
            # Botão Editar
            edit_btn = QPushButton()
            edit_btn.setIcon(QIcon.fromTheme("document-edit"))
            edit_btn.setToolTip("Editar script")
            edit_btn.setFixedSize(30, 30)
            edit_btn.clicked.connect(lambda _, s=script: self.edit_script(s))
            
            # Botão Excluir
            delete_btn = QPushButton()
            delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
            delete_btn.setToolTip("Excluir script")
            delete_btn.setFixedSize(30, 30)
            delete_btn.clicked.connect(lambda _, s=script: self.delete_script(s))
            
            # Botão Permissões
            perm_btn = QPushButton()
            perm_btn.setIcon(QIcon.fromTheme("document-properties"))
            perm_btn.setToolTip("Gerenciar permissões")
            perm_btn.setFixedSize(30, 30)
            perm_btn.clicked.connect(lambda _, s=script: self.manage_permissions(s))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addWidget(perm_btn)
            
            action_widget.setLayout(action_layout)
            self.scripts_table.setCellWidget(row, 4, action_widget)
        
        self.scripts_table.setSortingEnabled(True)
        self.scripts_table.resizeColumnsToContents()
    
    def populate_access_table(self, access_logs):
        """Preenche a tabela de acessos com dados"""
        self.access_table.setRowCount(len(access_logs))
        self.access_table.setSortingEnabled(False)
        
        for row, log in enumerate(access_logs):
            # Data/Hora
            timestamp_item = self.create_table_item(log['timestamp'])
            self.access_table.setItem(row, 0, timestamp_item)
            
            # IP (com cor condicional para IPs suspeitos)
            ip_item = self.create_table_item(log['ip'])
            if log.get('suspicious', False):
                ip_item.setForeground(QColor("red"))
            self.access_table.setItem(row, 1, ip_item)
            
            # Usuário
            user_item = self.create_table_item(str(log.get('user_id', 'Anônimo')))
            self.access_table.setItem(row, 2, user_item)
            
            # Dispositivo
            device_item = self.create_table_item(log['device'])
            self.access_table.setItem(row, 3, device_item)
            
            # Navegador
            browser_item = self.create_table_item(log['browser'])
            self.access_table.setItem(row, 4, browser_item)
            
            # Sistema Operacional
            os_item = self.create_table_item(log['os'])
            self.access_table.setItem(row, 5, os_item)
            
            # Endpoint
            endpoint_item = self.create_table_item(log['endpoint'])
            self.access_table.setItem(row, 6, endpoint_item)
            
            # Ações
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(5)
            
            # Botão Bloquear IP
            block_btn = QPushButton()
            block_btn.setIcon(QIcon.fromTheme("network-error"))
            block_btn.setToolTip("Bloquear este IP")
            block_btn.setFixedSize(30, 30)
            block_btn.clicked.connect(lambda _, ip=log['ip']: self.block_ip(ip))
            
            # Botão Detalhes
            details_btn = QPushButton()
            details_btn.setIcon(QIcon.fromTheme("help-about"))
            details_btn.setToolTip("Ver detalhes")
            details_btn.setFixedSize(30, 30)
            details_btn.clicked.connect(lambda _, l=log: self.show_access_details(l))
            
            action_layout.addWidget(block_btn)
            action_layout.addWidget(details_btn)
            
            action_widget.setLayout(action_layout)
            self.access_table.setCellWidget(row, 7, action_widget)
        
        self.access_table.setSortingEnabled(True)
        self.access_table.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        self.access_table.resizeColumnsToContents()
    
    def create_table_item(self, text):
        """Cria um QTableWidgetItem com texto formatado"""
        item = QTableWidgetItem(str(text))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setForeground(QColor("#e0e0e0"))  # Texto claro
        return item
    
    def update_user_filter(self):
        """Atualiza o combobox de filtro de usuários na aba de acessos"""
        current_data = self.filter_user_combo.currentData()
        self.filter_user_combo.clear()
        self.filter_user_combo.addItem("Todos os usuários", None)
        
        for row in range(self.users_table.rowCount()):
            user_id = self.users_table.item(row, 0).text()
            user_name = self.users_table.item(row, 1).text()
            self.filter_user_combo.addItem(f"{user_name} ({user_id})", user_id)
        
        # Restaurar seleção anterior se ainda existir
        index = self.filter_user_combo.findData(current_data)
        if index >= 0:
            self.filter_user_combo.setCurrentIndex(index)
    
    def apply_filters(self):
        """Aplica os filtros na tabela de acessos"""
        user_id = self.filter_user_combo.currentData()
        ip_filter = self.filter_ip_input.text().strip()
        date_from = self.filter_date_from.date()
        date_to = self.filter_date_to.date()
        
        for row in range(self.access_table.rowCount()):
            show_row = True
            
            # Filtrar por usuário
            if user_id:
                row_user = self.access_table.item(row, 2).text()
                show_row = show_row and (row_user == user_id)
            
            # Filtrar por IP
            if ip_filter:
                row_ip = self.access_table.item(row, 1).text()
                show_row = show_row and (ip_filter in row_ip)
            
            # Filtrar por data
            row_date = QDate.fromString(self.access_table.item(row, 0).text().split()[0], "yyyy-MM-dd")
            show_row = show_row and (not date_from.isValid() or row_date >= date_from)
            show_row = show_row and (not date_to.isValid() or row_date <= date_to)
            
            self.access_table.setRowHidden(row, not show_row)
    
    def add_user(self):
        """Mostra diálogo para adicionar novo usuário"""
        dialog = EnhancedUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_data()
            
            # Verifica se a senha foi fornecida
            if not user_data['password']:
                self.show_error("A senha/licença é obrigatória")
                return
                
            # Faz hash da senha antes de enviar
            try:
                user_data['password'] = self.hash_password(user_data['password'])
            except Exception as e:
                self.show_error(f"Erro ao processar senha: {str(e)}")
                return
            
            try:
                response = requests.post(
                    f"{self.server_url}/admin/users",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code == 201:
                    self.load_data('users')
                    self.show_success("Usuário adicionado com sucesso!")
                    
                    # Mostra a senha original para o administrador
                    QMessageBox.information(
                        self,
                        "Senha do Usuário",
                        f"Usuário criado com sucesso!\n\n"
                        f"Email: {user_data['email']}\n"
                        f"Senha: {dialog.get_data()['password']}\n\n"
                        f"Copie esta senha e envie para o usuário."
                    )
                    
                elif response.status_code == 400:
                    error_data = response.json()
                    if error_data.get('code') == 'email_exists':
                        self.show_error("Este e-mail já está cadastrado no sistema")
                    else:
                        self.show_error(f"Erro: {error_data.get('error', 'Erro desconhecido')}")
                else:
                    self.show_error(f"Falha ao adicionar usuário: {response.text}")
                            
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")

    def edit_user(self, user):
        """Mostra diálogo para editar usuário existente"""
        dialog = EnhancedUserDialog(self, user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_data()
            
            # Se a senha foi alterada, fazer hash
            if 'password' in user_data and user_data['password'] != user.get('password', ''):
                try:
                    from werkzeug.security import generate_password_hash
                    user_data['password'] = generate_password_hash(user_data['password'])
                except ImportError:
                    import hashlib
                    user_data['password'] = hashlib.sha256(user_data['password'].encode()).hexdigest()
            
            try:
                response = requests.put(
                    f"{self.server_url}/admin/users/{user['id']}",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.load_data('users')
                    self.show_success("Usuário atualizado com sucesso!")
                else:
                    self.show_error(f"Falha ao editar usuário: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
    
    def toggle_block_user(self, user):
        """Alterna status de bloqueio do usuário"""
        new_status = 'Ativo' if user.get('status') == 'Bloqueado' else 'Bloqueado'
        confirm = QMessageBox.question(
            self,
            "Confirmar ação",
            f"Tem certeza que deseja {new_status.lower()} o usuário {user['name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                response = requests.patch(
                    f"{self.server_url}/admin/users/{user['id']}/status",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    json={'status': new_status},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.load_data('users')
                    self.show_success(f"Status do usuário alterado para {new_status}")
                else:
                    self.show_error(f"Falha ao alterar status: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
    
    def delete_user(self, user):
        """Exclui um usuário"""
        if isinstance(user, bool):
            self.show_error("Dados inválidos do usuário")
            return
            
        if not isinstance(user, dict) or 'id' not in user or 'name' not in user:
            self.show_error("Estrutura de dados do usuário inválida")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja excluir o usuário {user['name']}? Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                response = requests.delete(
                    f"{self.server_url}/admin/users/{user['id']}",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.load_data('users')
                    self.show_success("Usuário excluído com sucesso!")
                else:
                    self.show_error(f"Falha ao excluir usuário: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
    
    def regenerate_key(self, user):
        """Regenera a chave de acesso do usuário"""
        confirm = QMessageBox.question(
            self,
            "Confirmar regeneração",
            f"Tem certeza que deseja gerar uma nova chave para {user['name']}? A chave atual será invalidada.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                response = requests.post(
                    f"{self.server_url}/admin/users/{user['id']}/regenerate_key",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.load_data('users')
                    self.show_success("Nova chave gerada com sucesso!")
                else:
                    self.show_error(f"Falha ao gerar chave: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
    
    def add_script(self):
        """Mostra diálogo para adicionar novo script"""
        dialog = EnhancedScriptDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            script_data = dialog.get_data()
            try:
                response = requests.post(
                    f"{self.server_url}/admin/scripts",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    json=script_data,
                    timeout=10
                )
                
                if response.status_code == 201:
                    self.load_data('scripts')
                    self.show_success("Script adicionado com sucesso!")
                else:
                    self.show_error(f"Falha ao adicionar script: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
    
    def edit_script(self, script):
        """Mostra diálogo para editar script existente"""
        dialog = EnhancedScriptDialog(self, script)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            script_data = dialog.get_data()
            try:
                response = requests.put(
                    f"{self.server_url}/admin/scripts/{script['id']}",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    json=script_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.load_data('scripts')
                    self.show_success("Script atualizado com sucesso!")
                else:
                    self.show_error(f"Falha ao editar script: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
    
    def delete_script(self, script):
        """Exclui um script"""
        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja excluir o script {script['name']}? Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                response = requests.delete(
                    f"{self.server_url}/admin/scripts/{script['id']}",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.load_data('scripts')
                    self.show_success("Script excluído com sucesso!")
                else:
                    self.show_error(f"Falha ao excluir script: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
    
    def manage_permissions(self, script):
        """Gerencia permissões de acesso ao script"""
        try:
            # Obter lista de usuários
            users_response = requests.get(
                f"{self.server_url}/admin/users",
                headers={'Authorization': f'Bearer {self.admin_token}'},
                timeout=10
            )
            
            if users_response.status_code != 200:
                raise Exception(users_response.text)
            
            users = users_response.json().get('users', [])
            
            # Obter permissões atuais
            perm_response = requests.get(
                f"{self.server_url}/admin/scripts/{script['id']}/permissions",
                headers={'Authorization': f'Bearer {self.admin_token}'},
                timeout=10
            )
            
            if perm_response.status_code != 200:
                raise Exception(perm_response.text)
            
            current_perms = perm_response.json().get('allowed_users', [])
            
            # Criar diálogo de permissões
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Permissões para {script['name']}")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout()
            
            # Lista de usuários com checkboxes
            user_list = QListWidget()
            for user in users:
                item = QListWidgetItem(f"{user['name']} ({user['email']})")
                item.setData(Qt.ItemDataRole.UserRole, user['id'])
                item.setCheckState(Qt.CheckState.Checked if user['id'] in current_perms else Qt.CheckState.Unchecked)
                user_list.addItem(item)
            
            layout.addWidget(QLabel("Selecione os usuários com acesso:"))
            layout.addWidget(user_list)
            
            # Botões
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                Qt.Orientation.Horizontal, dialog
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            
            layout.addWidget(buttons)
            dialog.setLayout(layout)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Coletar usuários selecionados
                allowed_users = []
                for i in range(user_list.count()):
                    item = user_list.item(i)
                    if item.checkState() == Qt.CheckState.Checked:
                        allowed_users.append(item.data(Qt.ItemDataRole.UserRole))
                
                # Enviar atualização
                update_response = requests.put(
                    f"{self.server_url}/admin/scripts/{script['id']}/permissions",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    json={'allowed_users': allowed_users},
                    timeout=10
                )
                
                if update_response.status_code == 200:
                    self.show_success("Permissões atualizadas com sucesso!")
                else:
                    self.show_error(f"Falha ao atualizar permissões: {update_response.text}")
        
        except Exception as e:
            self.show_error(f"Falha ao gerenciar permissões: {str(e)}")
    
    def block_ip(self, ip):
        """Bloqueia um endereço IP"""
        confirm = QMessageBox.question(
            self,
            "Confirmar bloqueio",
            f"Tem certeza que deseja bloquear o IP {ip}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                response = requests.post(
                    f"{self.server_url}/admin/block_ip",
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    json={'ip': ip},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.show_success(f"IP {ip} bloqueado com sucesso!")
                    self.load_data('access')
                else:
                    self.show_error(f"Falha ao bloquear IP: {response.text}")
            except Exception as e:
                self.show_error(f"Falha na comunicação: {str(e)}")
    
    def show_access_details(self, log):
        """Mostra detalhes de um registro de acesso"""
        details = f"""
        <b>Data/Hora:</b> {log['timestamp']}<br>
        <b>IP:</b> {log['ip']}<br>
        <b>Usuário:</b> {log.get('user_id', 'Anônimo')}<br>
        <b>Dispositivo:</b> {log['device']}<br>
        <b>Navegador:</b> {log['browser']}<br>
        <b>Sistema Operacional:</b> {log['os']}<br>
        <b>Endpoint:</b> {log['endpoint']}<br>
        <b>User Agent:</b> {log.get('user_agent', 'N/A')}<br>
        <b>Suspicious:</b> {'Sim' if log.get('suspicious', False) else 'Não'}
        """
        
        QMessageBox.information(
            self,
            "Detalhes do Acesso",
            details,
            QMessageBox.StandardButton.Ok
        )
    
    def export_users(self):
        """Exporta lista de usuários para CSV"""
        # Implementação simplificada - na prática, seria mais completo
        from datetime import datetime
        import csv
        from pathlib import Path
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Usuários",
            f"usuarios_fluxon_{datetime.now().strftime('%Y%m%d')}.csv",
            "Arquivos CSV (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['ID', 'Nome', 'Email', 'Admin', 'Status', 'Licença'])
                    
                    for row in range(self.users_table.rowCount()):
                        row_data = [
                            self.users_table.item(row, col).text()
                            for col in range(self.users_table.columnCount() - 1)  # Excluir coluna de ações
                        ]
                        writer.writerow(row_data)
                
                self.show_success(f"Usuários exportados com sucesso para {Path(file_path).name}")
            except Exception as e:
                self.show_error(f"Falha ao exportar usuários: {str(e)}")
    
    def show_settings(self):
        """Mostra diálogo de configurações do servidor"""
        dialog = ServerConfigDialog(self, self.server_url)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_url = dialog.get_selected_url()
            
            # Verificar se a URL mudou
            if new_url and new_url != self.server_url:
                # Testar a nova conexão
                if dialog.test_connection():
                    self.server_url = new_url
                    self.status_bar.showMessage(f"URL do servidor atualizada para: {new_url}", 5000)
                    
                    # Salvar a configuração (opcional - pode implementar persistência)
                    try:
                        with open('server_config.json', 'w') as f:
                            json.dump({'server_url': new_url}, f)
                    except Exception as e:
                        logger.error(f"Erro ao salvar configuração: {str(e)}")
                    
                    # Recarregar dados com a nova URL
                    self.load_data()
                    
    def show_server_config_dialog(self):
        """Mostra diálogo para configurar manualmente o servidor"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuração do Servidor")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Não foi possível conectar automaticamente ao servidor."))
        layout.addWidget(QLabel("Por favor, configure manualmente:"))
        
        url_input = QLineEdit(self.server_url)
        url_input.setPlaceholderText("URL do servidor (ex: https://seu-servidor.ngrok.io)")
        layout.addWidget(QLabel("URL do Servidor:"))
        layout.addWidget(url_input)
        
        token_input = QLineEdit(self.admin_token)
        token_input.setPlaceholderText("Token de administração")
        layout.addWidget(QLabel("Token Admin:"))
        layout.addWidget(token_input)
        
        email_input = QLineEdit(self.admin_email)
        email_input.setPlaceholderText("Email admin")
        layout.addWidget(QLabel("Email Admin:"))
        layout.addWidget(email_input)
        
        password_input = QLineEdit(self.admin_password)
        password_input.setPlaceholderText("Senha admin")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Senha Admin:"))
        layout.addWidget(password_input)
        
        test_btn = QPushButton("Testar Conexão")
        test_btn.clicked.connect(lambda: self.test_manual_config(
            url_input.text(), token_input.text(), email_input.text(), password_input.text()
        ))
        layout.addWidget(test_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(lambda: self.save_manual_config(
            url_input.text(), token_input.text(), email_input.text(), password_input.text(), dialog
        ))
        layout.addWidget(ok_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

    def test_manual_config(self, url, token, email, password):
        """Testa configuração manual"""
        original_url = self.server_url
        original_token = self.admin_token
        original_email = self.admin_email
        original_password = self.admin_password
        
        try:
            self.server_url = url
            self.admin_token = token
            self.admin_email = email
            self.admin_password = password
            
            if self.test_server_connection():
                QMessageBox.information(self, "Sucesso", "Conexão bem-sucedida!")
            else:
                QMessageBox.warning(self, "Falha", "Não foi possível conectar.")
                
        finally:
            self.server_url = original_url
            self.admin_token = original_token
            self.admin_email = original_email
            self.admin_password = original_password

    def save_manual_config(self, url, token, email, password, dialog):
        """Salva configuração manual"""
        self.server_url = url
        self.admin_token = token
        self.admin_email = email
        self.admin_password = password
        dialog.accept()
        
    def show_about(self):
        """Mostra diálogo 'Sobre'"""
        about_text = """
        <b>FLUXON Admin Panel</b><br>
        Versão 2.0.0<br><br>
        Sistema de gerenciamento de usuários e scripts<br>
        Desenvolvido por [Sua Empresa]<br><br>
        © 2023 Todos os direitos reservados
        """
        
        QMessageBox.about(
            self,
            "Sobre o FLUXON Admin",
            about_text
        )
    
    def show_success(self, message):
        """Mostra mensagem de sucesso"""
        QMessageBox.information(
            self,
            "Sucesso",
            message,
            QMessageBox.StandardButton.Ok
        )
    
    def show_error(self, message):
        """Mostra mensagem de erro"""
        QMessageBox.critical(
            self,
            "Erro",
            message,
            QMessageBox.StandardButton.Ok
        )

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        
        # Configurar estilo e fonte
        app.setStyle('Fusion')
        
        # Configurar paleta de cores para tema escuro
        dark_palette = app.palette()
        dark_palette.setColor(dark_palette.ColorRole.Window, QColor(45, 45, 45))
        dark_palette.setColor(dark_palette.ColorRole.WindowText, QColor(224, 224, 224))
        dark_palette.setColor(dark_palette.ColorRole.Base, QColor(58, 58, 58))
        dark_palette.setColor(dark_palette.ColorRole.AlternateBase, QColor(51, 51, 51))
        dark_palette.setColor(dark_palette.ColorRole.ToolTipBase, QColor(37, 37, 37))
        dark_palette.setColor(dark_palette.ColorRole.ToolTipText, QColor(224, 224, 224))
        dark_palette.setColor(dark_palette.ColorRole.Text, QColor(224, 224, 224))
        dark_palette.setColor(dark_palette.ColorRole.Button, QColor(58, 58, 58))
        dark_palette.setColor(dark_palette.ColorRole.ButtonText, QColor(224, 224, 224))
        dark_palette.setColor(dark_palette.ColorRole.BrightText, QColor(255, 255, 255))
        dark_palette.setColor(dark_palette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(dark_palette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(dark_palette)
        
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        app.setFont(font)
        
        # Criar e mostrar janela principal
        window = AdminPanel()
        
        # Verificar se a conexão foi bem-sucedida
        if hasattr(window, 'connection_successful') and window.connection_successful:
            window.show()
        else:
            # Se não conseguiu conectar, mostrar diálogo de configuração
            window.show_server_config_dialog()
            if window.test_server_connection():
                window.show()
            else:
                QMessageBox.critical(None, "Erro", "Não foi possível conectar ao servidor.")
                sys.exit(1)
                
        sys.exit(app.exec())
        
    except Exception as e:
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setText(f"Erro ao iniciar o painel:\n{str(e)}")
        error_msg.setWindowTitle("Erro Crítico")
        error_msg.exec()
        sys.exit(1)