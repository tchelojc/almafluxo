import httpx
import uvicorn
import asyncio
from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.websockets import WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import logging
import websockets
from urllib.parse import urlencode, urlparse
from contextlib import asynccontextmanager

# Configuração do Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
TUNNEL_URL = "http://localhost:5501"
CLIENT_DIR = Path(__file__).parent

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(timeout=30.0, follow_redirects=False)  # 🔥 NÃO seguir redirects automaticamente
    yield
    await app.state.client.aclose()

app = FastAPI(title="Fluxon Quantum Proxy - Porta de Entrada", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Tunnel - TUDO VAI PARA O TUNNEL
@app.websocket("/{service}/_stcore/stream")
async def websocket_proxy(websocket: WebSocket, service: str):
    await websocket.accept()
    
    target_ws_url = f"ws://localhost:5501/{service}/_stcore/stream"
    
    logger.info(f"🔌 Encaminhando WebSocket para tunnel: {service} -> {target_ws_url}")
    
    try:
        async with websockets.connect(
            target_ws_url, 
            ping_interval=None,
            ping_timeout=60,
            extra_headers={
                'Origin': 'http://localhost:5500',
                'Sec-WebSocket-Protocol': 'v4.streamlit.connection'
            }
        ) as target_ws:
            logger.info(f"✅ Conexão estabelecida com tunnel para {service}")
            
            async def forward_to_tunnel():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await target_ws.send(data)
                except WebSocketDisconnect:
                    logger.info(f"🔌 Cliente desconectado: {service}")
                except Exception as e:
                    logger.error(f"Erro no forward para tunnel ({service}): {e}")

            async def forward_from_tunnel():
                try:
                    async for message in target_ws:
                        await websocket.send_text(message)
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"🔌 Tunnel desconectado: {service}")
                except Exception as e:
                    logger.error(f"Erro no forward do tunnel ({service}): {e}")
            
            await asyncio.gather(forward_to_tunnel(), forward_from_tunnel())
            
    except Exception as e:
        logger.error(f"❌ Falha na conexão com tunnel para {service}: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# 🔥 CORREÇÃO CRÍTICA: Evitar loop de redirecionamento
def should_handle_locally(path: str) -> bool:
    """Determina se a requisição deve ser tratada localmente"""
    local_paths = ['', 'health', 'index_external.html', 'favicon.ico']
    return path in local_paths or path.endswith(('.js', '.css', '.png', '.jpg', '.ico'))

# 🔥 NOVO: Servir arquivos estáticos localmente
@app.get("/{filename:path}")
async def serve_static(filename: str):
    static_file = CLIENT_DIR / filename
    if static_file.exists() and static_file.is_file():
        return FileResponse(static_file)
    raise HTTPException(status_code=404)

# Health check simples
@app.get("/health")
async def health_check():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TUNNEL_URL}/health", timeout=2.0)
            return {"status": "healthy", "tunnel": response.status_code == 200}
    except:
        return {"status": "healthy", "tunnel": False}

# 🔥 CORREÇÃO: Proxy HTTP com tratamento inteligente de redirecionamentos
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def reverse_proxy(request: Request, path: str):
    # 🔥 Tratamento local primeiro
    if should_handle_locally(path):
        if path == "" or path == "index_external.html":
            index_file = CLIENT_DIR / "index_external.html"
            if index_file.exists():
                return FileResponse(index_file)
        elif path == "health":
            return await health_check()
        return await serve_static(path)
    
    # 🔥 Construir URL do tunnel CORRETAMENTE
    target_url = f"{TUNNEL_URL}/{path}"
    
    # Adicionar query parameters
    if request.query_params:
        target_url += f"?{urlencode(request.query_params)}"
    
    logger.info(f"🔁 Encaminhando para tunnel: {request.method} {path} -> {target_url}")
    
    try:
        headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
        
        req = app.state.client.build_request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=await request.body(),
        )
        
        response = await app.state.client.send(req, stream=True)
        
        # 🔥 TRATAMENTO ESPECIAL PARA REDIRECIONAMENTOS DO STREAMLIT
        if response.status_code in [301, 302, 307, 308]:
            location = response.headers.get('location', '')
            if location:
                # Se o redirecionamento é para o mesmo tunnel, ajustar para o proxy
                if 'localhost:5501' in location:
                    location = location.replace('localhost:5501', 'localhost:5500')
                elif ':5501' in location:
                    location = location.replace(':5501', ':5500')
                
                logger.info(f"🔄 Redirecionamento ajustado: {location}")
                return RedirectResponse(url=location)
        
        # Para respostas normais, streaming
        return StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=dict(response.headers),
        )
        
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Tunnel indisponível - Execute tunnel_server.py primeiro!")
    except Exception as e:
        logger.error(f"Erro no proxy: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do proxy")

if __name__ == "__main__":
    print("="*60)
    print("🚀 FLUXON QUANTUM PROXY - PORTA DE ENTRADA (CORRIGIDO)")
    print("="*60)
    print("📡 Porta: 5500")
    print("🔌 Encaminhando tudo para Tunnel: 5501")
    print("🔥 Correção: Prevenção de loops de redirecionamento")
    print("="*60)
    
    uvicorn.run(app, host="0.0.0.0", port=5500, log_level="info")