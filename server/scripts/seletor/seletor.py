# seletor.py (VERSÃO COM ABERTURA EM NOVA ABA)
import streamlit as st
import time
from pathlib import Path
import sys

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
    </style>
    """, unsafe_allow_html=True)

# ==================== PLATAFORMAS CONFIGURADAS ====================
PLATFORMS = {
    "Trading Financeiro": {"id": "daytrade", "port": 8502, "icon": "📈", "color": "#4CAF50", "description": "Plataforma avançada para operações de day trade"},
    "Apostas Esportivas": {"id": "sports", "port": 8503, "icon": "⚽", "color": "#2196F3", "description": "Sistema profissional para gestão de apostas"},
    "Operações Quânticas": {"id": "quantum", "port": 8504, "icon": "🎯", "color": "#9C27B0", "description": "Ferramentas premium"}
}

def check_service_health(port):
    """Verifica se o serviço está online tentando conexão direta"""
    import socket
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

# No seletor.py, substitua a validação de token por:
def main():
    st.set_page_config(page_title="🚀 Alma Hub", page_icon="🚀", layout="wide")
    apply_custom_styles()
    
    st.markdown("<div class='alma-header'><h1>🚀 ALMA</h1></div>", unsafe_allow_html=True)
    st.markdown("### Selecione a plataforma que deseja acessar.")

    # ✅ Acesso já autorizado pelo proxy - apenas exibe as opções
    # O token é passado via query string e validado pelo proxy
    
    # Layout em colunas
    cols = st.columns(len(PLATFORMS))
    
    for i, (name, data) in enumerate(PLATFORMS.items()):
        with cols[i]:
            service_id = data["id"]
            port = data["port"]
            is_online = check_service_health(port)
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
                target_url = f"http://localhost:{port}/"
                js_code = open_in_new_tab(target_url)
                st.components.v1.html(js_code, height=0)
                st.success(f"✅ {name} aberto em nova aba!")
                time.sleep(1)

if __name__ == "__main__":
    main()