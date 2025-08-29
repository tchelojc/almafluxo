import streamlit as st
from licensing_manager import LicenseManager

def show_license_ui():
    st.title("Validação de Licença")
    license_key = st.text_input("Digite sua chave de licença:")
    
    if st.button("Validar"):
        manager = LicenseManager()
        result = manager.verify(license_key, strict_check=True)
        
        if result['valid']:
            st.success("Licença ativada com sucesso!")
            st.session_state.license_valid = True
            st.experimental_rerun()
        else:
            st.error(f"Erro: {result.get('message')}")