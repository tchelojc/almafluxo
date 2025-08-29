#!/usr/bin/env python3
"""Teste específico para o Streamlit"""

import requests
import httpx
import asyncio

async def test_streamlit_endpoints():
    print("🔍 Testando endpoints do Streamlit na porta 8501...")
    
    endpoints = [
        "http://localhost:8501",
        "http://localhost:8501/health",
        "http://localhost:8501/_stcore/health", 
        "http://localhost:8501/seletor",
        "http://localhost:8501/seletor/health",
        "http://localhost:8501/seletor/_stcore/health"
    ]
    
    for endpoint in endpoints:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=3)
                print(f"✅ {endpoint} -> {response.status_code}")
                if response.status_code == 200:
                    print(f"   Content: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {endpoint} -> Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_streamlit_endpoints())