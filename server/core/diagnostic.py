import requests
import json
import socket
from datetime import datetime

def check_service(url, name):
    try:
        response = requests.get(url, timeout=3)
        
        # ✅ VERIFICAÇÃO MELHORADA PARA REDIRECT SERVER
        if name == "Redirect Server":
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Aceita qualquer resposta 200 com JSON válido
                    return {
                        "service": name,
                        "status": "online",
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    }
                except:
                    # Se não for JSON, mas respondeu 200, considera online
                    return {
                        "service": name,
                        "status": "online", 
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    }
            else:
                return {
                    "service": name,
                    "status": "offline",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
        
        # Para outros serviços, mantém a lógica original
        return {
            "service": name,
            "status": "online" if response.status_code == 200 else "offline",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
        
    except Exception as e:
        return {
            "service": name,
            "status": "error",
            "error": str(e)
        }

def main():
    services = [
        ("http://localhost:5000/health", "Flask Server"),
        ("http://localhost:8501/_stcore/health", "Streamlit"),
        ("http://localhost:5500/health", "Quantum Proxy"),
        ("http://localhost:5001", "Redirect Server")
    ]
    
    results = []
    for url, name in services:
        results.append(check_service(url, name))
    
    print("=== DIAGNÓSTICO DO SISTEMA ===")
    for result in results:
        status_icon = "✅" if result["status"] == "online" else "❌"
        print(f"{status_icon} {result['service']}: {result['status']}")
        if "error" in result:
            print(f"   Erro: {result['error']}")
    
    # Save to file
    with open("system_diagnostic.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)

if __name__ == "__main__":
    main()