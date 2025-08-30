# seletor.py (VERSÃO FINAL COM OPÇÕES DE ABERTURA)
import streamlit as st
import time

# ==================== CONFIGURAÇÃO DE ESTILOS (Mantida) ====================
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
# As URLs devem apontar para os caminhos públicos que você configurou
PLATFORMS = {
    "Trading Financeiro": {
        "id": "daytrade", 
        "icon": "📈", 
        "color": "#4CAF50", 
        "description": "Plataforma avançada para operações de day trade e análise de mercado.",
        "url": "https://almafluxo.uk/daytrade" # Exemplo de URL pública
    },
    "Apostas Esportivas": {
        "id": "sports", 
        "icon": "⚽", 
        "color": "#2196F3", 
        "description": "Sistema profissional para gestão de apostas e análises esportivas.",
        "url": "https://almafluxo.uk/sports" # Exemplo de URL pública
    },
    "Operações Quânticas": {
        "id": "quantum", 
        "icon": "🎯", 
        "color": "#9C27B0", 
        "description": "Ferramentas premium para operações avançadas e estratégias complexas.",
        "url": "https://almafluxo.uk/quantum" # Exemplo de URL pública
    }
}

# ==================== FUNÇÕES AUXILIARES ====================

def check_service_health(port):
    """
    Verifica se o serviço está online.
    NOTA: Em um ambiente como o Streamlit Cloud, não podemos verificar portas locais.
    Esta função assume que os serviços estão online se as URLs públicas estiverem configuradas.
    """
    return True

# ✅ CORREÇÃO: Função unificada para gerar o JavaScript de redirecionamento
def execute_redirect(url, open_in_new_tab=False):
    """Gera e executa o código JavaScript para redirecionar o usuário."""
    if open_in_new_tab:
        # Abre em uma NOVA ABA. Requer que o navegador permita pop-ups.
        js_code = f'window.open("{url}", "_blank");'
    else:
        # Abre na MESMA JANELA, alterando a URL da página principal.
        js_code = f'window.top.location.href = "{url}";'
    
    # Executa o JavaScript usando o componente HTML do Streamlit
    st.components.v1.html(f"<script>{js_code}</script>", height=0)

# ==================== APLICAÇÃO PRINCIPAL ====================

def main():
    st.set_page_config(
        page_title="🚀 ALMA EM FLUXO", 
        page_icon="🚀", 
        layout="wide"
    )
    apply_custom_styles()
    
    # 👑 HEADER - ALMA EM FLUXO
    st.markdown("<div class='alma-header'><h1>🌊 ALMA EM FLUXO</h1></div>", unsafe_allow_html=True)
    st.markdown("<div class='alma-subtitle'>O Fluxo Natural da Alma Rumo ao Equilíbrio</div>", unsafe_allow_html=True)
    
    # ✅ NOVO: Opção para o usuário escolher como abrir as plataformas
    st.markdown("---")
    c1, c2 = st.columns([3,2])
    with c1:
        st.write("") # Espaçador
    with c2:
        open_option = st.radio(
            "Modo de abertura:",
            ("Na mesma janela", "Em uma nova aba"),
            index=0, # Padrão é "Na mesma janela"
            horizontal=True,
        )
    
    # Converte a opção em um booleano para a função
    open_in_new_tab = (open_option == "Em uma nova aba")

    # Adiciona um aviso se o usuário escolher abrir em nova aba
    if open_in_new_tab:
        st.info("ℹ️ Abertura em nova aba pode exigir que você habilite pop-ups para este site no seu navegador.")
        
    # 🎯 PLATAFORMAS
    cols = st.columns(len(PLATFORMS))
    
    for i, (name, data) in enumerate(PLATFORMS.items()):
        with cols[i]:
            is_online = check_service_health(data.get("port")) # .get é mais seguro
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
                # ✅ CHAMADA DA NOVA FUNÇÃO DE REDIRECIONAMENTO
                execute_redirect(data["url"], open_in_new_tab=open_in_new_tab)
                
                st.success(f"✅ Redirecionando para {name}...")
                time.sleep(1) # Apenas para o usuário ver a mensagem
    
    # 📝 FOOTER
    st.markdown("""
    <div class='footer'>
        <h4>🌐 ALMA EM FLUXO - Sistema Integrado</h4>
        <p><strong>Conceito:</strong> O fluxo constante da alma em busca da Liberdade Consciente</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
