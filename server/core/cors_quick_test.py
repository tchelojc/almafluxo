#!/usr/bin/env python3
"""
TESTE RÁPIDO DE CORS - Para verificação instantânea
"""

import requests

def quick_cors_test():
    print("🚀 Teste Rápido de CORS")
    
    # Testar acesso direto ao Streamlit
    try:
        response = requests.get('http://localhost:8501/_stcore/health', timeout=3)
        print(f"✅ Streamlit Direct: {response.status_code}")
    except:
        print("❌ Streamlit Direct: Connection failed")
    
    # Testar via proxy
    try:
        response = requests.get('http://localhost:5000/proxy/streamlit/_stcore/health', timeout=3)
        print(f"✅ Streamlit via Proxy: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ Streamlit via Proxy: {str(e)}")
    
    # Testar preflight
    try:
        headers = {
            'Origin': 'https://1ac41472cd64.ngrok-free.app',
            'Access-Control-Request-Method': 'GET'
        }
        response = requests.options('http://localhost:5000/health', headers=headers, timeout=3)
        print(f"✅ Preflight Test: {response.status_code}")
        print(f"   Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
    except Exception as e:
        print(f"❌ Preflight Test: {str(e)}")

if __name__ == "__main__":
    quick_cors_test()