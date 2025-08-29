#!/usr/bin/env python3
"""
Teste de conectividade WebSocket para o sistema ALMA
"""

import asyncio
import websockets
import json
import sys
import time

# No arquivo mobile_test.py, corrija o teste WebSocket:
async def test_websocket_connection(url, description):
    """Testa a conexão WebSocket"""
    try:
        print(f"🧪 Testando {description} ({url})...")
        
        # Use wait_for para timeout em vez do parâmetro
        try:
            async with websockets.connect(url) as ws:
                # Teste de ping com timeout separado
                await ws.send(json.dumps({"type": "ping", "data": "test"}))
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"✅ {description}: CONECTADO - Resposta: {response[:100]}...")
                return "SUCCESS"
        except asyncio.TimeoutError:
            print(f"⏰ {description}: TIMEOUT")
            return "TIMEOUT"
            
    except ConnectionRefusedError:
        print(f"❌ {description}: CONEXÃO RECUSADA")
        return "CONNECTION_REFUSED"
    except Exception as e:
        print(f"❌ {description}: ERRO - {e}")
        return f"ERROR: {e}"

async def test_http_connections():
    """Testa conexões HTTP"""
    import requests
    
    endpoints = [
        ("http://localhost:5000/api/health", "Flask API"),
        ("http://localhost:5001/health", "FastAPI Proxy"),
        ("http://localhost:8501/_stcore/health", "Streamlit Hub")
    ]
    
    results = {}
    
    for url, description in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: ONLINE (Status {response.status_code})")
                results[url] = "SUCCESS"
            else:
                print(f"⚠️ {description}: OFFLINE (Status {response.status_code})")
                results[url] = f"HTTP_{response.status_code}"
        except Exception as e:
            print(f"❌ {description}: ERRO - {e}")
            results[url] = f"ERROR: {e}"
    
    return results

async def test_websocket_cors():
    """Testa especificamente a conectividade WebSocket com CORS"""
    test_cases = [
        {
            "origin": "http://localhost:5001",
            "expected": "should_connect",
            "description": "Origem localhost permitida"
        },
        {
            "origin": "https://almafluxo.uk", 
            "expected": "should_connect",
            "description": "Origem de produção permitida"
        },
        {
            "origin": "http://evil.com",
            "expected": "should_reject", 
            "description": "Origem maliciosa deve ser rejeitada"
        }
    ]
    
    for test_case in test_cases:
        print(f"🧪 Testando: {test_case['description']}")
        
        try:
            # Tentar conectar com origem específica
            async with websockets.connect(
                "ws://localhost:5001/_stcore/stream",
                extra_headers={"Origin": test_case["origin"]},
                timeout=5
            ) as ws:
                # Se conectou, verificar se era esperado
                if test_case["expected"] == "should_connect":
                    print(f"✅ PASS: Conexão permitida corretamente")
                    await ws.close()
                else:
                    print(f"❌ FAIL: Conexão foi permitida mas deveria ser rejeitada")
                    
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 403 and test_case["expected"] == "should_reject":
                print(f"✅ PASS: Conexão rejeitada corretamente")
            else:
                print(f"❌ FAIL: Código de status inesperado: {e.status_code}")
                
        except Exception as e:
            if "Origin not allowed" in str(e) and test_case["expected"] == "should_reject":
                print(f"✅ PASS: Conexão rejeitada corretamente")
            elif test_case["expected"] == "should_connect":
                print(f"❌ FAIL: Conexão falhou mas deveria ter sido permitida: {e}")
            else:
                print(f"⚠️  UNKNOWN: Erro inesperado: {e}")

async def comprehensive_test():
    """Executa teste completo"""
    print("🚀 Iniciando teste completo de conectividade ALMA")
    
    # Testar HTTP primeiro
    print("\n🌐 Testando conexões HTTP:")
    http_results = await test_http_connections()
    
    print("\n🔗 Testando conexões WebSocket:")
    # CORREÇÃO: Passe os parâmetros necessários
    ws_results = {}
    ws_results["ws://localhost:8501/_stcore/stream"] = await test_websocket_connection(
        "ws://localhost:8501/_stcore/stream", "Streamlit direto"
    )
    ws_results["ws://localhost:5001/_stcore/stream"] = await test_websocket_connection(
        "ws://localhost:5001/_stcore/stream", "FastAPI Proxy" 
    )
    
    print("\n" + "=" * 60)
    print("📊 RESULTADOS DO TESTE:")
    print("=" * 60)
    
    all_success = all("SUCCESS" in result for result in http_results.values())
    all_success = all_success and all("SUCCESS" in result for result in ws_results.values())
    
    if all_success:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema está funcionando corretamente.")
    else:
        print("❌ ALGUNS TESTES FALHARAM. Verifique os serviços:")
        
        for url, result in http_results.items():
            if "SUCCESS" not in result:
                print(f"   - HTTP {url}: {result}")
        
        for url, result in ws_results.items():
            if "SUCCESS" not in result:
                print(f"   - WebSocket {url}: {result}")
    
    return all_success

if __name__ == "__main__":
    try:
        success = asyncio.run(comprehensive_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
        sys.exit(1)