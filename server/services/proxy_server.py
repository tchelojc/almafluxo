"""
🚀 SERVIDOR PROXY FASTAPI
Apenas para proxy reverso - sem gerenciamento de serviços
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, Response
from flask import render_template_string
import httpx
import logging
import urllib.parse
import os
from pathlib import Path

# Adicione no início do arquivo, após os imports
BASE_DIR = Path(__file__).parent.parent
CLIENT_DIR = BASE_DIR / "client"

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="ALMA Proxy")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://almafluxo.uk",
        "http://localhost:5001",
        "http://127.0.0.1:5001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_ROUTES = {
    "api": "http://localhost:5000",
    "hub": "http://localhost:8501",
    "daytrade": "http://localhost:8502",
    "_stcore": "http://localhost:8501",  # Streamlit internals
    "static": "http://localhost:8501",   # Streamlit static files
}

async def route_request(path: str, request: Request):
    """Roteia requisições para o serviço apropriado"""
    # Determinar o serviço de destino baseado no caminho
    first_segment = path.split('/')[0] if path else ""
    target_base = SERVICE_ROUTES.get(first_segment, "http://localhost:5000")
    
    target_url = f"{target_base}/{path}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers={k: v for k, v in request.headers.items() 
                        if k.lower() not in ['host', 'content-length']},
                content=await request.body(),
                params=request.query_params
            )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items() 
                    if k.lower() not in ['content-encoding', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Erro no roteamento para {target_url}: {e}")
        return JSONResponse({"error": "Serviço indisponível"}, status_code=503)

@app.get("/")
async def home():
    """Serve a página inicial (index_external.html)"""
    return await serve_frontend("")

@app.get("/{path:path}")
async def serve_frontend(path: str, request: Request):  # ⬅️ ADICIONAR Request como parâmetro
    """Serve arquivos estáticos do frontend com roteamento inteligente"""
    try:
        # ⬇️⬇️⬇️ CORREÇÃO CRÍTICA: Roteamento específico ⬇️⬇️⬇️
        if path == "redirect-confirmation":
            # Esta rota será tratada pela função redirect_confirmation
            return await redirect_confirmation(request)  # ⬅️ Agora request está definido
        
        if path == "login" or path == "":
            # Serve a página de login
            return await serve_index()
        
        # Serve arquivos estáticos (CSS, JS, imagens)
        file_path = CLIENT_DIR / path
        if file_path.exists() and file_path.is_file():
            return Response(
                content=file_path.read_bytes(),
                media_type="text/html" if path.endswith(".html") else 
                          "text/css" if path.endswith(".css") else
                          "application/javascript" if path.endswith(".js") else
                          "image/png" if path.endswith(".png") else
                          "image/jpeg" if path.endswith((".jpg", ".jpeg")) else
                          "text/plain"
            )
        
        # Para qualquer outra rota, servir a página de login
        return await serve_index()
            
    except Exception as e:
        logger.error(f"Erro ao servir frontend: {e}")
        return JSONResponse({"error": "Erro ao carregar página"}, status_code=500)
    
async def serve_index():
    """Serve o index_external.html"""
    index_path = CLIENT_DIR / "index_external.html"
    if index_path.exists():
        return Response(
            content=index_path.read_bytes(),
            media_type="text/html"
        )
    return Response(content="<h1>Página não encontrada</h1>", media_type="text/html")

@app.post("/login")
async def login(request: Request):
    """Proxy para login na API Flask"""
    try:
        data = await request.json()
        logger.info(f"Login attempt for email: {data.get('email')}")
        
        async with httpx.AsyncClient() as client:
            # ⬇️⬇️⬇️ CORREÇÃO CRÍTICA: Mudar para /api/login ⬇️⬇️⬇️
            resp = await client.post(
                "http://localhost:5000/api/login",  # ✅ CORRIGIDO
                json=data, 
                timeout=10.0
            )
            
            logger.info(f"API response status: {resp.status_code}")
            
        return JSONResponse(
            content=resp.json(),
            status_code=resp.status_code
        )
        
    except httpx.RequestError as e:
        logger.error(f"Erro de conexão com API: {e}")
        return JSONResponse({
            "success": False, 
            "error": "Não foi possível conectar ao servidor"
        }, status_code=503)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return JSONResponse({
            "success": False, 
            "error": "Erro interno do servidor"
        }, status_code=500)
        
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "alma_proxy"}

# Adicione esta rota ao proxy_server.py
# ⬇️ SUBSTITUA a função redirect_confirmation por esta versão correta ⬇️

@app.get("/redirect-confirmation")
async def redirect_confirmation(request: Request):
    """Serve a página completa de redirecionamento COM DEBUG"""
    token = request.query_params.get("token")
    
    logger.info(f"Redirect confirmation request received, token: {token}")
    
    if not token:
        logger.warning("Token não fornecido")
        return RedirectResponse("/login")
    
    try:
        # Validar token com a API Flask primeiro
        async with httpx.AsyncClient() as client:
            validation_response = await client.post(
                "http://localhost:5000/api/validate_token",
                json={"token": token},
                timeout=5.0
            )
            
            logger.info(f"Token validation response: {validation_response.status_code}")
            
            if validation_response.status_code != 200:
                logger.warning("Token validation failed")
                return RedirectResponse("/login")
                
            validation_data = validation_response.json()
            if not validation_data.get("success") or not validation_data.get("data", {}).get("valid"):
                logger.warning("Token inválido ou expirado")
                return RedirectResponse("/login")
                
    except Exception as e:
        logger.error(f"Erro na validação do token: {e}")
        return RedirectResponse("/login")
    
    # Servir o arquivo HTML completo de redirecionamento
    file_path = CLIENT_DIR / "redirect_confirmation.html"
    
    logger.info(f"Procurando arquivo em: {file_path}")
    logger.info(f"Arquivo existe: {file_path.exists()}")
    
    if not file_path.exists():
        logger.error("Arquivo redirect_confirmation.html não encontrado")
        # Listar arquivos no diretório para debug
        try:
            files = os.listdir(CLIENT_DIR)
            logger.info(f"Arquivos em {CLIENT_DIR}: {files}")
        except Exception as e:
            logger.error(f"Erro ao listar arquivos: {e}")
        
        return await serve_redirect_confirmation_fallback(token)
    
    try:
        # Ler o arquivo HTML
        html_content = file_path.read_text(encoding="utf-8")
        logger.info("Arquivo HTML lido com sucesso")
        return Response(content=html_content, media_type="text/html")
        
    except Exception as e:
        logger.error(f"Erro ao ler arquivo HTML: {e}")
        return await serve_redirect_confirmation_fallback(token)

async def serve_redirect_confirmation_fallback(token: str):
    """Fallback se o arquivo HTML não for encontrado"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ALMA - Conectando...</title>
        <script>
            window.addEventListener('load', function() {{
                console.log('Redirecionando para o ALMA Hub...');
                window.location.href = 'http://localhost:8501?token={token}';
            }});
        </script>
    </head>
    <body>
        <div style="text-align: center; margin-top: 50px;">
            <h2>ALMA - Conectando...</h2>
            <p>Por favor, aguarde enquanto redirecionamos para a plataforma.</p>
            <p>Se não for redirecionado automaticamente, <a href="http://localhost:8501?token={token}">clique aqui</a>.</p>
        </div>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

async def serve_redirect_confirmation(token: str):
    """Serve a página de confirmação de redirecionamento"""
    # Você pode criar um template HTML ou servir um arquivo estático
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ALMA - Conectando...</title>
        <meta http-equiv="refresh" content="0; url=http://localhost:8501?token={token}">
    </head>
    <body>
        <p>Conectando ao ALMA Hub... <a href="http://localhost:8501?token={token}">Clique aqui</a> se não for redirecionado.</p>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_all(path: str, request: Request):
    """Proxy reverso para todos os serviços usando roteamento inteligente"""
    return await route_request(path, request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5001, log_level="info")