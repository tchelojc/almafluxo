from flask_cors import CORS
from flask import request
import re

def configure_cors(app, bridge_config=None):
    """
    Configuração CORS ROBUSTA - Versão híbrida com fallbacks inteligentes
    Combina segurança com tolerância máxima para desenvolvimento
    """
    
    # ==================== CONFIGURAÇÃO PRINCIPAL ====================
    
    # 1. LISTA EXPLÍCITA de origens permitidas (para produção)
    ALLOWED_ORIGINS_LIST = [
        "https://almafluxo.uk",
        "https://fluxon.almafluxo.uk", 
        "http://almafluxo.uk",
        "http://fluxon.almafluxo.uk",
        "http://localhost:5001",
        "http://localhost:5000",
        "http://127.0.0.1:5001",
        "http://127.0.0.1:5000"
    ]
    
    # 2. PADRÕES REGEX para desenvolvimento (mais permissivos)
    ALLOWED_ORIGIN_PATTERNS = [
        r"https?://([a-z0-9-]+\.)?almafluxo\.uk",
        r"https?://localhost(:[0-9]+)?",
        r"https?://127.0.0.1(:[0-9]+)?",
        r"https?://192\.168\.([0-9]{1,3})\.([0-9]{1,3})(:[0-9]+)?",
        r"https?://10\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})(:[0-9]+)?",
    ]
    
    # 3. Headers permitidos (balanceando segurança e funcionalidade)
    ALLOWED_HEADERS = [
        "Content-Type",
        "Authorization", 
        "X-Requested-With",
        "X-Forwarded-For",
        "X-Client-Timestamp",
        "X-System-Fingerprint",
        "Origin",
        "Accept",
        "Access-Control-Request-Headers",
        "Access-Control-Request-Method"
    ]
    
    # 4. Headers expostos
    EXPOSED_HEADERS = [
        "Authorization", 
        "X-Token-Expiry",
        "Content-Type",
        "X-Request-ID"
    ]

    # ==================== DETECÇÃO DE AMBIENTE ====================
    
    # Verifica se estamos em modo de desenvolvimento
    IS_DEVELOPMENT = app.config.get('DEBUG', False) or app.config.get('ENV') == 'development'
    
    if IS_DEVELOPMENT:
        print("🚀 Modo DESENVOLVIMENTO - CORS super permissivo")
        # Configuração EXTREMAMENTE permissiva para desenvolvimento
        CORS(app,
            origins=ALLOWED_ORIGIN_PATTERNS,  # Regex patterns
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            allow_headers=ALLOWED_HEADERS + ["*"],  # Permite todos + específicos
            expose_headers=EXPOSED_HEADERS + ["*"],
            supports_credentials=True,
            max_age=3600,
            always_send=True
        )
    else:
        print("🔒 Modo PRODUÇÃO - CORS seguro")
        # Configuração SEGURA para produção
        CORS(app,
            origins=ALLOWED_ORIGINS_LIST,  # Lista explícita
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=ALLOWED_HEADERS,
            expose_headers=EXPOSED_HEADERS,
            supports_credentials=True,
            max_age=600
        )

    # ==================== MIDDLEWARE DE FALLBACK ====================
    
    # Middleware adicional para garantir CORS mesmo em casos extremos
    @app.after_request
    def add_cors_headers(response):
        """Adiciona headers CORS em todas as respostas (fallback)"""
        
        origin = request.headers.get('Origin', '')
        
        # Verifica se a origem é permitida via patterns (desenvolvimento)
        if IS_DEVELOPMENT and origin:
            for pattern in ALLOWED_ORIGIN_PATTERNS:
                if re.match(pattern, origin):
                    response.headers['Access-Control-Allow-Origin'] = origin
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
                    break
        
        # Verifica se a origem está na lista explícita (produção)
        elif origin in ALLOWED_ORIGINS_LIST:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Headers de segurança adicionais
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response

    # ==================== HANDLER PARA OPTIONS ====================
    
    @app.before_request
    def handle_options():
        """Manipula requisições OPTIONS de forma robusta"""
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            
            # Adiciona headers CORS para OPTIONS
            origin = request.headers.get('Origin', '')
            if origin and (origin in ALLOWED_ORIGINS_LIST or 
                          any(re.match(pattern, origin) for pattern in ALLOWED_ORIGIN_PATTERNS)):
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
                response.headers['Access-Control-Allow-Headers'] = ', '.join(ALLOWED_HEADERS)
                response.headers['Access-Control-Max-Age'] = '3600' if IS_DEVELOPMENT else '600'
            
            return response

    print("✅ CORS Configurado ROBUSTAMENTE!")
    print(f"   Modo: {'DESENVOLVIMENTO' if IS_DEVELOPMENT else 'PRODUÇÃO'}")
    print(f"   Origens permitidas: {len(ALLOWED_ORIGINS_LIST)} explícitas + {len(ALLOWED_ORIGIN_PATTERNS)} patterns")

