# seletor.py (VERSÃO COMPLETAMENTE INTEGRADA)
import streamlit as st
import requests
import jwt
from datetime import datetime
import time
import json
import socket
import os

# ==================== CONFIGURAÇÃO ====================
# URLs das suas APIs (usando seu domínio almafluxo.uk)
BASE_API_URL = "https://almafluxo.uk/api"
STREAMLIT_HUB_URL = "https://almafluxo-7magbvhbc7xk7zhjnlazq7.streamlit.app"

# ==================== CONFIGURAÇÃO DE ESTILOS ====================
def apply_custom_styles():
    st.markdown("""
    <style>
    :root {
        --primary-color: #4a6fa5; --primary-hover: #166088;
        --error-color: #e74c3c; --success-color: #2ecc71;
        --text-light: #ffffff; --text-muted: #dddddd;
        --bg-transparent: rgba(0, 0, 0, 0.65);
    }
    body, .stApp {
        background: url('https://images.unsplash.com/photo-1639762681057-408e52192e55?q=80&w=2232&auto=format&fit=crop') no-repeat center center fixed;
        background-size: cover;
    }
    .alma-header h1 { font-size: 2.8rem; margin: 0; color: var(--text-light); text-shadow: 0 3px 6px rgba(0,0,0,0.6); }
    .platform-card { background: var(--bg-transparent); border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem; border-left: 6px solid; backdrop-filter: blur(8px); transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
    .platform-card:hover { transform: translateY(-5px) scale(1.02); box-shadow: 0 8px 30px rgba(0,0,0,0.6); }
    .platform-card h2 { margin: 0 0 10px; font-size: 1.5rem; }
    .stButton > button { width: 100%; padding: 14px; background: var(--primary-color); border: none; border-radius: 10px; color: white; font-size: 16px; font-weight: bold; }
    .stButton > button:hover { background: var(--primary-hover); }
    .status-online, .status-offline { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 0.9rem; font-weight: bold; }
    .status-online { background: rgba(46, 204, 113, 0.2); color: var(--success-color); border: 1px solid rgba(46,204,113,0.5); }
    .status-offline { background: rgba(231, 76, 60, 0.2); color: var(--error-color); border: 1px solid rgba(231,76,60,0.5); }
    
    /* Estilos adicionais da versão integrada */
    .integrated-footer { 
        background: rgba(26, 26, 26, 0.9); 
        padding: 15px; 
        border-radius: 10px; 
        margin-top: 20px;
        border: 1px solid #34495e;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== PLATAFORMAS CONFIGURADAS ====================
PLATFORMS = {
    "Trading Financeiro": {"id": "trading", "port": 8502, "icon": "📈", "color": "#4CAF50", "description": "Plataforma avançada para operações de day trade"},
    "Apostas Esportivas": {"id": "sports", "port": 8503, "icon": "⚽", "color": "#2196F3", "description": "Sistema profissional para gestão de apostas"},
    "Operações Quânticas": {"id": "quantum", "port": 8504, "icon": "🎯", "color": "#9C27B0", "description": "Ferramentas premium"}
}

# ==================== FUNÇÕES DE AUTENTICAÇÃO ====================
def get_auth_token():
    """Obtém token JWT dos query parameters - VERSÃO STREAMLIT 1.28+"""
    try:
        # Para versões mais recentes do Streamlit
        query_params = st.query_params
        return query_params.get("token", [None])[0]
    except:
        # Fallback para versões mais antigas
        query_params = st.experimental_get_query_params()
        return query_params.get("token", [None])[0]

def validate_token(token):
    """Valida token JWT - Tenta primeiro localmente, depois via API"""
    # 1. Primeiro tenta validar localmente (mais rápido)
    try:
        # Use a mesma chave secreta do seu servidor Flask
        secret_key = os.environ.get('JWT_SECRET_KEY', 'fluxon_secret_key_secreta')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return True
    except jwt.ExpiredSignatureError:
        st.error("Token expirado. Faça login novamente.")
        return False
    except jwt.InvalidTokenError:
        # 2. Se validação local falhar, tenta via API
        try:
            response = requests.post(
                f"{BASE_API_URL}/validate_token",
                json={"token": token},
                timeout=5
            )
            return response.status_code == 200 and response.json().get("valid", False)
        except:
            return False

def show_login_redirect():
    """Mostra mensagem e botão para redirecionar ao login"""
    st.warning("🔒 Autenticação necessária para acessar o ALMA Fluxo")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("""
        **Para acessar as plataformas premium:**
        1. Clique no botão abaixo para fazer login
        2. Use suas credenciais do ALMA Fluxo
        3. Você será redirecionado automaticamente
        """)
    
    with col2:
        if st.button("📝 Fazer Login no ALMA Fluxo", use_container_width=True):
            # Redireciona para a página de login
            js_redirect = """
            <script>
                window.location.href = "https://almafluxo.uk/login";
            </script>
            """
            st.components.v1.html(js_redirect, height=0)

# ==================== FUNÇÕES DE SERVIÇO ====================
def check_service_health(service_id, port):
    """Verifica se o serviço está online - Tenta múltiplas formas"""
    # 1. Primeiro tenta verificar via API externa
    try:
        response = requests.get(f"{BASE_API_URL}/{service_id}/health", timeout=3)
        if response.status_code == 200:
            return True
    except:
        pass
    
    # 2. Se API externa falhar, tenta conexão local
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except:
        return False

def open_in_new_tab(url):
    """JavaScript para abrir URL em nova aba"""
    js_code = f"""
    <script>
        window.open('{url}', '_blank');
    </script>
    """
    return js_code

# ==================== FUNÇÕES DE PLATAFORMA ====================
def render_platform_card(name, data, token):
    """Renderiza card individual da plataforma"""
    service_id = data["id"]
    port = data["port"]
    is_online = check_service_health(service_id, port)
    status_text = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
    status_class = "status-online" if is_online else "status-offline"
    
    st.markdown(f"""
    <div class="platform-card" style="border-left-color: {data['color']}">
        <h2 style='color: {data["color"]};'>{data["icon"]} {name}</h2>
        <p><strong>Status:</strong> <span class="{status_class}">{status_text}</span></p>
        <p>{data['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(f"🚀 Acessar {name}", key=service_id, use_container_width=True, disabled=not is_online):
        # Abre a plataforma CORRETA com autenticação
        target_url = f"https://almafluxo.uk/{service_id}?token={token}"
        js_code = open_in_new_tab(target_url)
        st.components.v1.html(js_code, height=0)
        st.success(f"✅ {name} aberto em nova aba!")
        time.sleep(1)

# ==================== FUNÇÃO PRINCIPAL ====================
def main():
    st.set_page_config(page_title="🚀 ALMA Fluxo", page_icon="🚀", layout="wide")
    apply_custom_styles()
    
    # Verificar autenticação - NOVA LÓGICA INTEGRADA
    token = get_auth_token()
    
    if not token or not validate_token(token):
        show_login_redirect()
        return
    
    # Usuário autenticado - mostrar dashboard
    st.markdown("<div class='alma-header'><h1>🚀 ALMA Fluxo</h1></div>", unsafe_allow_html=True)
    st.markdown("### Selecione a plataforma que deseja acessar.")
    
    # Layout em colunas
    cols = st.columns(len(PLATFORMS))
    
    for i, (name, data) in enumerate(PLATFORMS.items()):
        with cols[i]:
            render_platform_card(name, data, token)
    
    # Footer com informações de integração
    st.markdown("""
    <div class="integrated-footer">
        <h4>🌐 Sistema Integrado</h4>
        <p><strong>Frontend:</strong> Streamlit Cloud | <strong>Backend:</strong> almafluxo.uk</p>
        <p><strong>Autenticação:</strong> JWT Token | <strong>Segurança:</strong> HTTPS/SSL</p>
        <p><strong>Usuário Conectado:</strong> ✅ Autenticado via JWT</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão de logout na sidebar
    st.sidebar.success("✅ Conectado ao ALMA Fluxo UK")
    if st.sidebar.button("🚪 Sair do Sistema"):
        js_logout = """
        <script>
            window.location.href = "https://almafluxo.uk/logout";
        </script>
        """
        st.components.v1.html(js_logout, height=0)

if __name__ == "__main__":
    main()