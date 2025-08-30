# seletor.py (VERSÃO COM IDENTIDADE VISUAL APRIMORADA)
import streamlit as st
import time

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

# ==================== PLATAFORMAS CONFIGURADAS ====================
PLATFORMS = {
    "Trading Financeiro": {
        "id": "daytrade", 
        "port": 8502, 
        "icon": "📈", 
        "color": "#4CAF50", 
        "description": "Plataforma avançada para operações de day trade e análise de mercado",
        "url": "https://almafluxo.uk/daytrade"
    },
    "Apostas Esportivas": {
        "id": "sports", 
        "port": 8503, 
        "icon": "⚽", 
        "color": "#2196F3", 
        "description": "Sistema profissional para gestão de apostas e análises esportivas",
        "url": "https://almafluxo.uk/sports"
    },
    "Operações Quânticas": {
        "id": "quantum", 
        "port": 8504, 
        "icon": "🎯", 
        "color": "#9C27B0", 
        "description": "Ferramentas premium para operações avançadas e estratégias complexas",
        "url": "https://almafluxo.uk/quantum"
    }
}

def check_service_health(port):
    """Verifica se o serviço está online - Versão para Streamlit Cloud"""
    try:
        return True
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

def main():
    st.set_page_config(
        page_title="🚀 ALMA EM FLUXO", 
        page_icon="🚀", 
        layout="wide"
    )
    apply_custom_styles()
    
    # 👑 HEADER - ALMA EM FLUXO
    st.markdown("<div class='alma-header'><h1>🌊 ALMA EM FLUXO</h1></div>", unsafe_allow_html=True)
    st.markdown("<div class='alma-subtitle'>O Fluxo Natural da Alma Rumo ao Equlíbrio</div>", unsafe_allow_html=True)
    
    # 📊 STATUS INFO
    st.markdown("""
    <div class='info-box'>
        <strong>💡 Como Funciona:</strong><br>
        • Clique em qualquer plataforma para abrir em nova aba<br>
        • Todas as plataformas são acessadas através do domínio <strong>almafluxo.uk</strong><br>
        • Conecte-se ao fluxo natural da evolução tecnológica
    </div>
    """, unsafe_allow_html=True)
    
    # 🎯 PLATAFORMAS
    cols = st.columns(len(PLATFORMS))
    
    for i, (name, data) in enumerate(PLATFORMS.items()):
        with cols[i]:
            is_online = check_service_health(data["port"])
            status_text = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
            status_class = "status-online" if is_online else "status-offline"
            
            st.markdown(f"""
            <div class="platform-card" style="border-left-color: {data['color']}">
                <h2>{data["icon"]} {name}</h2>
                <p><strong>Status:</strong> <span class="{status_class}">{status_text}</span></p>
                <p>{data['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🚀 Acessar {name}", key=data["id"], use_container_width=True):
                js_code = open_in_new_tab(data["url"])
                st.components.v1.html(js_code, height=0)
                st.success(f"✅ {name} aberto em nova aba!")
                time.sleep(1)
    
    # 📝 FOOTER
    st.markdown("""
    <div class='footer'>
        <h4>🌐 ALMA EM FLUXO - Sistema Integrado</h4>
        <p><strong>Portal:</strong> Streamlit Cloud | <strong>Backend:</strong> AlmaFluxo UK</p>
        <p><strong>Conceito:</strong> O fluxo constante da alma em busca da Liberdade Consciente</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
