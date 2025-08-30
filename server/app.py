import sys
import os
import logging
from datetime import datetime, timezone, timedelta

from flask import Flask, request, jsonify, send_from_directory, redirect
from werkzeug.security import check_password_hash
import jwt as pyjwt

# 🔥 CORREÇÃO: Adiciona o caminho correto para importar database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ✅ Agora aponta para flux_on/
sys.path.insert(0, BASE_DIR)

from core.database import JSONDatabase
from server.cors_config import configure_cors
from server.config import SECURITY_CONFIG

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# 🔥 CORREÇÃO: Caminho absoluto para client/static
CLIENT_DIR = os.path.join(BASE_DIR, 'client', 'static')  # ✅ Agora correto

def create_app():
    # Configura Flask
    app = Flask(__name__)
    
    # Configuração básica
    app.config['SECRET_KEY'] = SECURITY_CONFIG['SECRET_KEY']
    app.config['ADMIN_EMAIL'] = SECURITY_CONFIG['ADMIN_EMAIL']
    app.config['ADMIN_PASSWORD'] = SECURITY_CONFIG['ADMIN_PASSWORD']
    
    # URL do servidor externo
    app.config['EXTERNAL_SERVER_URL'] = 'https://almafluxo.uk'

    # Banco de dados
    app.db = JSONDatabase()

    # Configura CORS
    configure_cors(app)

    # ===== ROTAS API =====
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "service": "flask_api"}), 200

    @app.route('/api/login', methods=['POST'])
    def login():
        try:
            data = request.get_json() or {}
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return jsonify({"success": False, "error": "Email e senha são obrigatórios"}), 400

            user = app.db.get_user_by_email(email)
            if not user or not check_password_hash(user['password'], password):
                return jsonify({"success": False, "error": "Credenciais inválidas"}), 401

            if user.get('status') != 'Ativo':
                return jsonify({"success": False, "error": "Conta desativada"}), 403

            token = pyjwt.encode({
                'user_id': user['id'],
                'email': user['email'],
                'is_admin': user.get('is_admin', False),
                'exp': datetime.now(timezone.utc) + timedelta(hours=2)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            # 🔥 REDIRECIONAMENTO CORRETO para Streamlit Cloud
            hub_url = f"https://almafluxo-7magbvhbc7xk7zhjnlazq7.streamlit.app/?token={token}"

            return jsonify({
                "success": True,
                "data": {
                    "token": token,
                    "hub_url": hub_url,  # ✅ URL do Streamlit Cloud com token
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "name": user.get('name'),
                        "is_admin": user.get('is_admin', False)
                    }
                }
            }), 200

        except Exception:
            logger.exception("Erro no login")
            return jsonify({"success": False, "error": "Erro interno no servidor"}), 500
        
    @app.route('/api/validate_token', methods=['POST'])
    def validate_token():
        try:
            data = request.get_json() or {}
            token = data.get('token')
            if not token:
                return jsonify({"success": False, "error": "Token não fornecido"}), 400

            payload = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = app.db.get_user_by_id(payload.get('user_id'))
            if not user or user.get('status') != 'Ativo':
                return jsonify({"success": False, "error": "Usuário não autorizado"}), 401

            return jsonify({
                "success": True,
                "data": {
                    "valid": True,
                    "user_id": payload.get('user_id'),
                    "email": payload.get('email'),
                    "is_admin": payload.get('is_admin', False)
                }
            }), 200

        except pyjwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token expirado"}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Token inválido"}), 401
        except Exception:
            logger.exception("Erro na validação de token")
            return jsonify({"success": False, "error": "Erro interno no servidor"}), 500

    # 🔥 NOVA ROTA: Redirecionamento para o frontend externo
    @app.route('/')
    def redirect_to_external():
        """Redireciona para o servidor externo"""
        return redirect(app.config['EXTERNAL_SERVER_URL'])

    # 🔥 CORREÇÃO: Agora serve arquivos de client/static/
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(CLIENT_DIR, filename)

    # Rota para health check do load balancer externo
    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "service": "flask_backend"})

    @app.route('/admin/server_status')
    def admin_server_status():
        """Retorna status do servidor para o painel admin"""
        return jsonify({
            "status": "online",
            "services": {
                "flask_api": "running",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }
        })

    # ===== ROTAS ADMINISTRATIVAS =====
    @app.route('/admin/users', methods=['GET'])
    def admin_get_users():
        """Retorna todos os usuários para o painel admin"""
        try:
            # Verificar token admin primeiro
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"success": False, "error": "Token de administração requerido"}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verificar se é token admin
            if token != SECURITY_CONFIG.get('ADMIN_TOKEN'):
                return jsonify({"success": False, "error": "Token de administração inválido"}), 403
            
            users = app.db.get_all_users()
            return jsonify({"success": True, "data": {"users": users}})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/admin/verify_token', methods=['POST'])
    def admin_verify_token():
        """Verifica se um token é válido para administração"""
        try:
            data = request.get_json() or {}
            token = data.get('token')
            
            if not token:
                return jsonify({"success": False, "error": "Token não fornecido"}), 400
            
            # Verificar se é o token admin correto
            if token == SECURITY_CONFIG.get('ADMIN_TOKEN'):
                return jsonify({"success": True, "valid": True, "is_admin": True})
            else:
                return jsonify({"success": True, "valid": False, "is_admin": False})
                
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/login', methods=['POST'])
    def legacy_login():
        """Endpoint de login legado (para compatibilidade com o painel)"""
        return login()  # Chama a função de login existente

    @app.route('/validate_token', methods=['POST'])
    def legacy_validate_token():
        """Endpoint de validação de token legado"""
        return validate_token()  # Chama a função de validação existente
        @app.route('/admin/stats')
        def admin_get_stats():
            """Retorna estatísticas para o painel admin"""
            stats = app.db.get_database_status()
            return jsonify({"success": True, "stats": stats})

    # 🔥 ADICIONAR: Debug route para verificar caminhos
    @app.route('/debug/paths')
    def debug_paths():
        return jsonify({
            "base_dir": BASE_DIR,
            "client_dir": CLIENT_DIR,
            "client_dir_exists": os.path.exists(CLIENT_DIR),
            "files_in_client_dir": os.listdir(CLIENT_DIR) if os.path.exists(CLIENT_DIR) else "Directory not found"
        })
        
    @app.route('/daytrade')
    def day_trade_platform():
        """Redireciona para a plataforma de Day Trade"""
        # Verificar autenticação primeiro
        token = request.args.get('token')
        if not token or not validate_token(token):
            return redirect('/login')
        
        # Redirecionar para o arquivo main.py do day_trade
        return redirect('http://localhost:8502/')

    @app.route('/sports')  
    def sports_platform():
        """Redireciona para a plataforma de Apostas Esportivas"""
        token = request.args.get('token')
        if not token or not validate_token(token):
            return redirect('/login')
        
        return redirect('http://localhost:8503/')

    @app.route('/quantum')
    def quantum_platform():
        """Redireciona para a plataforma de Operações Quânticas"""
        token = request.args.get('token')
        if not token or not validate_token(token):
            return redirect('/login')
        
        return redirect('http://localhost:8504/')

    return app

if __name__ == "__main__":
    app = create_app()
    
    # 🔥 DEBUG: Verificar caminhos antes de iniciar
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"CLIENT_DIR: {CLIENT_DIR}")
    print(f"CLIENT_DIR existe: {os.path.exists(CLIENT_DIR)}")
    
    if os.path.exists(CLIENT_DIR):
        print(f"Arquivos em CLIENT_DIR: {os.listdir(CLIENT_DIR)}")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
