#!/usr/bin/env python3
"""
Teste de Conexão para Fluxon Quantum Proxy
Este script testa cada componente individualmente para identificar o problema.
"""

import requests
import httpx
import asyncio
import websockets
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConnectionTester:
    def __init__(self):
        self.proxy_url = "http://localhost:5500"
        self.tunnel_url = "http://localhost:5501"
        self.streamlit_url = "http://localhost:8501"
        
    async def test_all_connections(self):
        """Testa todas as conexões sequencialmente"""
        print("="*60)
        print("🔍 TESTE DE CONEXÃO - FLUXON QUANTUM PROXY")
        print("="*60)
        
        # Teste 1: Proxy Server
        print("\n1. 🚀 Testando Proxy Server (5500)...")
        proxy_ok = await self.test_proxy()
        
        # Teste 2: Tunnel Server
        print("\n2. 🔌 Testando Tunnel Server (5501)...")
        tunnel_ok = await self.test_tunnel()
        
        # Teste 3: Streamlit Service
        print("\n3. 📊 Testando Streamlit Service (8501)...")
        streamlit_ok = await self.test_streamlit()
        
        # Teste 4: Conexão Completa
        print("\n4. 🔗 Testando Conexão Completa...")
        full_connection_ok = await self.test_full_connection()
        
        # Resultado Final
        print("\n" + "="*60)
        print("📊 RESULTADO DOS TESTES")
        print("="*60)
        print(f"Proxy Server (5500):    {'✅' if proxy_ok else '❌'}")
        print(f"Tunnel Server (5501):   {'✅' if tunnel_ok else '❌'}")
        print(f"Streamlit Service (8501): {'✅' if streamlit_ok else '❌'}")
        print(f"Conexão Completa:       {'✅' if full_connection_ok else '❌'}")
        
        if not full_connection_ok:
            print("\n🔧 DIAGNÓSTICO DO PROBLEMA:")
            if not proxy_ok:
                print("  - Proxy Server não está respondendo")
            elif not tunnel_ok:
                print("  - Tunnel Server não está respondendo")
            elif not streamlit_ok:
                print("  - Streamlit Service não está respondendo")
            else:
                print("  - Todos os serviços respondem, mas há loop de redirecionamento")
                
        return all([proxy_ok, tunnel_ok, streamlit_ok, full_connection_ok])
    
    async def test_proxy(self):
        """Testa se o proxy está respondendo"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.proxy_url}/health", timeout=5)
                if response.status_code == 200:
                    print("   ✅ Proxy Server respondendo")
                    return True
                else:
                    print(f"   ❌ Proxy Server retornou status: {response.status_code}")
                    return False
        except Exception as e:
            print(f"   ❌ Erro no Proxy Server: {e}")
            return False
    
    async def test_tunnel(self):
        """Testa se o tunnel está respondendo"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.tunnel_url}/health", timeout=5)
                if response.status_code == 200:
                    print("   ✅ Tunnel Server respondendo")
                    return True
                else:
                    print(f"   ❌ Tunnel Server retornou status: {response.status_code}")
                    return False
        except Exception as e:
            print(f"   ❌ Erro no Tunnel Server: {e}")
            return False
    
    # No método test_streamlit(), substitua:
    async def test_streamlit(self):
        """Testa se o streamlit está respondendo"""
        try:
            async with httpx.AsyncClient() as client:
                # ✅ TESTE O ENDPOINT CORRETO!
                response = await client.get("http://localhost:8501/seletor/_stcore/health", timeout=5)
                if response.status_code == 200:
                    print("   ✅ Streamlit Service respondendo")
                    return True
                else:
                    print(f"   ❌ Streamlit Service retornou status: {response.status_code}")
                    return False
        except Exception as e:
            print(f"   ❌ Erro no Streamlit Service: {e}")
            return False
    
    async def test_full_connection(self):
        """Testa a conexão completa proxy → tunnel → streamlit"""
        try:
            async with httpx.AsyncClient() as client:
                # Testa sem redirecionamento automático
                response = await client.get(
                    f"{self.proxy_url}/seletor/_stcore/health",
                    timeout=10,
                    follow_redirects=False  # 🔥 Importante: não seguir redirecionamentos
                )
                
                print(f"   Status: {response.status_code}")
                print(f"   Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print("   ✅ Conexão completa funcionando")
                    return True
                elif response.status_code in [301, 302, 307, 308]:
                    location = response.headers.get('location', '')
                    print(f"   ⚠️  Redirecionamento detectado para: {location}")
                    
                    # Testa o redirecionamento
                    if location:
                        redirect_response = await client.get(location, timeout=5, follow_redirects=False)
                        print(f"   Redirecionamento status: {redirect_response.status_code}")
                        
                        if redirect_response.status_code == 200:
                            print("   ✅ Redirecionamento funcionando")
                            return True
                        else:
                            print("   ❌ Redirecionamento falhou")
                            return False
                    return False
                else:
                    print(f"   ❌ Status inesperado: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Erro na conexão completa: {e}")
            return False
    
    async def trace_redirects(self, url):
        """Rastreia todos os redirecionamentos de uma URL"""
        print(f"\n🔍 Rastreando redirecionamentos para: {url}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, follow_redirects=True)
                print(f"   URL final: {response.url}")
                print(f"   Status final: {response.status_code}")
                print(f"   Número de redirecionamentos: {len(response.history)}")
                
                for i, resp in enumerate(response.history):
                    print(f"   Redirecionamento {i+1}: {resp.status_code} -> {resp.headers.get('location')}")
                    
                return response.url, response.status_code
                
            except Exception as e:
                print(f"   ❌ Erro no rastreamento: {e}")
                return None, None

async def main():
    tester = ConnectionTester()
    
    print("Iniciando teste de conexão...")
    success = await tester.test_all_connections()
    
    if not success:
        print("\n🧪 Teste adicional: Rastreamento de redirecionamentos...")
        test_url = "http://localhost:5500/seletor/_stcore/health"
        final_url, status = await tester.trace_redirects(test_url)
        
        print(f"\n📋 Recomendações:")
        print("1. Verifique se todos os serviços estão rodando:")
        print("   - Proxy: python proxy_server.py")
        print("   - Tunnel: python tunnel_server.py") 
        print("   - Streamlit: streamlit run seletor.py --server.port=8501 --server.baseUrlPath=seletor")
        print("2. Verifique as portas não estão conflitando")
        print("3. Execute 'netstat -ano | findstr :5500' para verificar portas ocupadas")

if __name__ == "__main__":
    asyncio.run(main())