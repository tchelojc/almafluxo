import sys
import os
import logging
from datetime import datetime, timezone, timedelta

from flask import Flask, request, jsonify, send_from_directory, redirect
from werkzeug.security import check_password_hash
import jwt as pyjwt

# Adiciona o diretório pai ao path para encontrar database.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import JSONDatabase
from cors_config import configure_cors
from config import SECURITY_CONFIG

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Caminho absoluto da pasta client
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(BASE_DIR, '..', 'client')

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

            # 🔥 CORREÇÃO CRÍTICA: Redirecionar para o servidor externo
            hub_url = f"{app.config['EXTERNAL_SERVER_URL']}/redirect-confirmation?token={token}"

            return jsonify({
                "success": True,
                "data": {
                    "token": token,
                    "hub_url": hub_url,  # URL externa
                    "user": {
                        "id": user['id'],
                        "email": user['email'],  # <-- usar 'user', não 'payload'
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

    # 🔥 NOVA ROTA: Servir arquivos estáticos localmente se necessário
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(CLIENT_DIR, filename)

    # Rota para health check do load balancer externo
    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "service": "flask_backend"})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)  # ⬅️ Mudar para 5000