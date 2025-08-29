# test_proxy.py
import requests
import json
import time
from urllib.parse import urljoin

def test_proxy_connections():
    """Testa todas as conexões do proxy"""
    print("=" * 60)
    print("🔍 TESTE DE DIAGNÓSTICO DO PROXY SERVER")
    print("=" * 60)
    
    base_url = "http://localhost:5500"
    test_urls = [
        "/",  # Página principal
        "/health",  # Health check do Flask
        "/streamlit",  # Redirecionamento para Streamlit
        "/api/status",  # API do Flask
        "/_stcore/health"  # Health check do Streamlit
    ]
    
    results = {}
    
    for test_path in test_urls:
        test_url = urljoin(base_url, test_path)
        print(f"\n🧪 Testando: {test_url}")
        
        try:
            start_time = time.time()
            
            if test_path == "/streamlit":
                # Teste especial para redirecionamento
                response = requests.get(test_url, allow_redirects=False, timeout=5)
                elapsed = time.time() - start_time
                
                if response.status_code in [301, 302, 307, 308]:
                    print(f"   ✅ REDIRECT {response.status_code} → {response.headers.get('Location', 'N/A')}")
                    results[test_path] = {
                        "status": "success", 
                        "code": response.status_code,
                        "redirect": response.headers.get('Location'),
                        "time": f"{elapsed:.2f}s"
                    }
                else:
                    print(f"   ❌ Esperado redirect, mas recebeu: {response.status_code}")
                    results[test_path] = {
                        "status": "error", 
                        "code": response.status_code,
                        "time": f"{elapsed:.2f}s"
                    }
                    
            else:
                # Teste normal
                response = requests.get(test_url, timeout=5)
                elapsed = time.time() - start_time
                
                print(f"   ✅ {response.status_code} ({elapsed:.2f}s)")
                if response.status_code == 200:
                    print(f"   📦 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                
                results[test_path] = {
                    "status": "success" if response.status_code < 400 else "error",
                    "code": response.status_code,
                    "content_type": response.headers.get('Content-Type'),
                    "time": f"{elapsed:.2f}s"
                }
                
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            print(f"   ❌ ERRO: {e}")
            results[test_path] = {
                "status": "error",
                "error": str(e),
                "time": f"{elapsed:.2f}s"
            }
    
    # Teste WebSocket (simplificado)
    print(f"\n🔌 Testando WebSocket (conectividade básica)...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('localhost', 8501))
        if result == 0:
            print("   ✅ Porta 8501 (Streamlit) está aberta")
            results['websocket_port'] = {"status": "success", "port": 8501}
        else:
            print("   ❌ Porta 8501 não está respondendo")
            results['websocket_port'] = {"status": "error", "port": 8501}
        sock.close()
    except Exception as e:
        print(f"   ❌ Erro no teste de porta: {e}")
        results['websocket_port'] = {"status": "error", "error": str(e)}
    
    # Resultados finais
    print("\n" + "=" * 60)
    print("📊 RESULTADOS DO DIAGNÓSTICO")
    print("=" * 60)
    
    success_count = sum(1 for r in results.values() if r.get('status') == 'success')
    total_count = len(results)
    
    print(f"✅ Sucessos: {success_count}/{total_count}")
    
    for path, result in results.items():
        status_icon = "✅" if result.get('status') == 'success' else "❌"
        print(f"{status_icon} {path}: {json.dumps(result, indent=2)}")
    
    # Recomendações
    print("\n💡 RECOMENDAÇÕES:")
    if results.get('/streamlit', {}).get('status') != 'success':
        print("   • Verifique a rota /streamlit no proxy_server.py")
        print("   • Confirme se o Streamlit está rodando na porta 8501")
    
    if results.get('websocket_port', {}).get('status') != 'success':
        print("   • O Streamlit não está rodando ou não está na porta 8501")
        print("   • Execute: streamlit run seletor.py --server.port=8501")
    
    if results.get('/health', {}).get('status') != 'success':
        print("   • O Flask app não está respondendo")
        print("   • Verifique se python app.py está rodando")
    
    return results

if __name__ == "__main__":
    test_proxy_connections()