# seletor.py (VERSÃO FINAL - Portal de Acesso)
import streamlit as st
import requests

# ==================== CONFIGURAÇÃO ====================
# URL para onde o botão "ALMA" irá redirecionar
LOGIN_URL = "https://almafluxo.uk/login"

# URL da sua API para validar o token.
# O app Streamlit precisa conseguir acessar esta URL publicamente.
API_VALIDATION_URL = "https://almafluxo.uk/api/validate_token"

# ==================== PLATAFORMAS CONFIGURADAS ====================
PLATFORMS = {
    "Trading Financeiro": {
        "id": "daytrade", 
        "icon": "📈", 
        "color": "#4CAF50", 
        "description": "Plataforma avançada para operações de day trade e análise de mercado.",
        "url": "https://almafluxo.uk/daytrade"
    },
    "Apostas Esportivas": {
        "id": "sports", 
        "icon": "⚽", 
        "color": "#2196F3", 
        "description": "Sistema profissional para gestão de apostas e análises esportivas.",
        "url": "https://almafluxo.uk/sports"
    },
    "Operações Quânticas": {
        "id": "quantum", 
        "icon": "🎯", 
        "color": "#9C27B0", 
        "description": "Ferramentas premium para operações avançadas e estratégias complexas.",
        "url": "https://almafluxo.uk/quantum"
    }
}

# ==================== FUNÇÕES PRINCIPAIS ====================

def verify_token(token):
    """Verifica se o token JWT é válido fazendo uma chamada à sua API Flask."""
    if not token:
        return False
    try:
        response = requests.post(API_VALIDATION_URL, json={"token": token}, timeout=7)
        # Verifica se a resposta foi bem-sucedida e se o JSON confirma a validade
        return response.status_code == 200 and response.json().get("data", {}).get("valid", False)
    except requests.exceptions.RequestException:
        # Se a API de validação estiver offline, consideramos o token inválido.
        st.error("Não foi possível conectar ao servidor de autenticação.")
        return False

def show_login_gateway():
    """
    Exibe uma página de portal limpa, sem elementos do Streamlit,
    com um único botão que redireciona para a página de login.
    """
    st.set_page_config(layout="centered")

    # CSS para limpar a interface do Streamlit e estilizar o portal
    st.markdown(f"""
    <style>
        /* Remove todos os elementos da interface do Streamlit */
        .stApp > header, .st-emotion-cache-16txtl3, div[data-testid="stToolbar"], 
        div[data-testid="stDecoration"], div[data-testid="stStatusWidget"] {{
            display: none !important;
        }}

        /* Aplica a imagem de fundo em toda a tela */
        .stApp {{
            background: url('https://images.unsplash.com/photo-1639762681057-408e52192e55?q=80&w=2232&auto=format&fit=crop') no-repeat center center fixed;
            background-size: cover;
        }}

        /* Centraliza o conteúdo verticalmente e horizontalmente */
        .main {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }}

        /* Container central para o botão e texto */
        .center-container {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
        }}

        /* Estiliza o botão "ALMA" */
        .alma-btn {{
            width: 200px;
            height: 200px;
            background: rgba(74, 111, 165, 0.5);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-size: 2.5rem;
            font-weight: bold;
            text-decoration: none;
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.2), inset 0 0 30px rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.4);
            cursor: pointer;
            transition: all 0.4s ease;
            animation: pulse 3s infinite;
            backdrop-filter: blur(10px);
            margin-bottom: 25px;
        }}

        .alma-btn:hover {{
            transform: scale(1.1);
            box-shadow: 0 0 50px rgba(255, 255, 255, 0.4), inset 0 0 40px rgba(255, 255, 255, 0.2);
            animation-play-state: paused;
        }}

        @keyframes pulse {{
            0% {{ box-shadow: 0 0 20px rgba(255, 255, 255, 0.2), inset 0 0 20px rgba(255, 255, 255, 0.1); }}
            50% {{ box-shadow: 0 0 40px rgba(255, 255, 255, 0.3), inset 0 0 30px rgba(255, 255, 255, 0.15); }}
            100% {{ box-shadow: 0 0 20px rgba(255, 255, 255, 0.2), inset 0 0 20px rgba(255, 255, 255, 0.1); }}
        }}

        /* Textos de suporte */
        .support-text {{
            text-align: center;
            color: rgba(255, 255, 255, 0.9);
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}
        .support-text .title {{ 
            font-size: 1.2rem; 
            margin-bottom: 5px;
        }}
        .support-text .subtitle {{ 
            font-size: 0.9rem; 
            opacity: 0.8; 
        }}
    </style>
    
    <div class="main">
        <div class="center-container">
            <a href="{LOGIN_URL}" target="_top" class="alma-btn">ALMA</a>
            <div class="support-text">
                <div class="title">Sistema ALMA</div>
                <div class="subtitle">Clique para acessar o portal</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Impede que o restante do script Streamlit seja executado
    st.stop()

# ==================== CONFIGURAÇÃO DE ESTILOS (Mantida - para quando estiver logado) ====================
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
    .alma-header h1 { 
        font-size: 3.5rem; 
        margin: 0; 
        color: white; 
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8),
                     0 0 10px rgba(74, 111, 165, 0.8),
                     0 0 20px rgba(74, 111, 165, 0.6);
        text-align: center;
        font-family: 'Arial Black', sans-serif;
        letter-spacing: 2px;
        padding: 20px 0;
    }
    .alma-subtitle {
        font-size: 1.4rem;
        color: white;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
        margin-bottom: 30px;
        font-weight: 300;
    }
    .platform-card { 
        background: var(--bg-transparent); 
        border-radius: 14px; 
        padding: 1.5rem; 
        margin-bottom: 1.5rem; 
        border-left: 6px solid; 
        backdrop-filter: blur(8px); 
        transition: all 0.3s ease; 
        box-shadow: 0 4px 16px rgba(0,0,0,0.4); 
    }
    .platform-card:hover { 
        transform: translateY(-5px) scale(1.02); 
        box-shadow: 0 8px 30px rgba(0,0,0,0.6); 
    }
    .platform-card h2 { 
        margin: 0 0 10px; 
        font-size: 1.5rem;
        display: flex;
        align-items: center;
        gap: 10px;
        color: white;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
    }
    .stButton > button { 
        width: 100%; 
        padding: 14px; 
        background: var(--primary-color); 
        border: none; 
        border-radius: 10px; 
        color: white; 
        font-size: 16px; 
        font-weight: bold;
        transition: all 0.3s ease;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    .stButton > button:hover { 
        background: var(--primary-hover);
        transform: scale(1.02);
    }
    .stButton > button:disabled {
        background: #666;
        cursor: not-allowed;
    }
    .status-online, .status-offline { 
        display: inline-block; 
        padding: 6px 12px; 
        border-radius: 20px; 
        font-size: 0.9rem; 
        font-weight: bold; 
    }
    .status-online { 
        background: rgba(46, 204, 113, 0.2); 
        color: var(--success-color); 
        border: 1px solid rgba(46,204,113,0.5); 
    }
    .status-offline { 
        background: rgba(231, 76, 60, 0.2); 
        color: var(--error-color); 
        border: 1px solid rgba(231,76,60,0.5); 
    }
    .footer { 
        background: rgba(26, 26, 26, 0.8); 
        padding: 15px; 
        border-radius: 10px; 
        margin-top: 30px;
        border: 1px solid #34495e;
        text-align: center;
        color: white;
    }
    .info-box {
        background: rgba(74, 111, 165, 0.2);
        border: 1px solid rgba(74, 111, 165, 0.5);
        border-radius: 10px;
        padding: 15px;
        margin: 20px 0;
        color: white;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== FUNÇÕES AUXILIARES ====================
def check_service_health(port):
    return True

def execute_redirect(url, open_in_new_tab=False):
    if open_in_new_tab:
        js_code = f'window.open("{url}", "_blank");'
    else:
        js_code = f'window.top.location.href = "{url}";'
    st.components.v1.html(f"<script>{js_code}</script>", height=0)

def show_platforms_hub():
    """
    Mostra o hub com a seleção de plataformas para usuários autenticados.
    """
    st.set_page_config(
        page_title="🚀 ALMA EM FLUXO", 
        page_icon="🚀", 
        layout="wide"
    )
    apply_custom_styles()
    
    # 👑 HEADER - ALMA EM FLUXO
    st.markdown("<div class='alma-header'><h1>🌊 ALMA EM FLUXO</h1></div>", unsafe_allow_html=True)
    st.markdown("<div class='alma-subtitle'>O Fluxo Natural da Alma Rumo ao Equilíbrio</div>", unsafe_allow_html=True)
    
    # ✅ Opção de abertura
    st.markdown("---")
    c1, c2 = st.columns([3,2])
    with c1:
        st.write("")
    with c2:
        open_option = st.radio(
            "Modo de abertura:",
            ("Na mesma janela", "Em uma nova aba"),
            index=0,
            horizontal=True,
        )
    
    open_in_new_tab = (open_option == "Em uma nova aba")

    if open_in_new_tab:
        st.info("ℹ️ Abertura em nova aba pode exigir que você habilite pop-ups para este site no seu navegador.")
        
    # 🎯 PLATAFORMAS
    cols = st.columns(len(PLATFORMS))
    
    for i, (name, data) in enumerate(PLATFORMS.items()):
        with cols[i]:
            is_online = check_service_health(data.get("port"))
            status_text = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
            status_class = "status-online" if is_online else "status-offline"
            
            st.markdown(f"""
            <div class="platform-card" style="border-left-color: {data['color']}">
                <h2>{data["icon"]} {name}</h2>
                <p><strong>Status:</strong> <span class="{status_class}">{status_text}</span></p>
                <p>{data['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🚀 Acessar {name}", key=data["id"], use_container_width=True, disabled=not is_online):
                execute_redirect(data["url"], open_in_new_tab=open_in_new_tab)
                st.success(f"✅ Redirecionando para {name}...")
    
    # 📝 FOOTER
    st.markdown("""
    <div class='footer'>
        <h4>🌐 ALMA EM FLUXO - Sistema Integrado</h4>
        <p><strong>Conceito:</strong> O fluxo constante da alma em busca da Liberdade Consciente</p>
    </div>
    """, unsafe_allow_html=True)

# ==================== LÓGICA PRINCIPAL ====================
def main():
    """
    Ponto de entrada do aplicativo.
    Verifica o token; se for válido, mostra o hub, senão, mostra o portal de login.
    """
    token = st.query_params.get("token")

    if verify_token(token):
        # Se o token na URL for válido, mostra o hub de plataformas.
        show_platforms_hub()
    else:
        # Se não houver token ou ele for inválido, mostra o portal de acesso.
        show_login_gateway()

if __name__ == "__main__":
    main()
