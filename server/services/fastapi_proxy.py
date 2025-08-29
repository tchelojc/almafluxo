#!/usr/bin/env python3
"""
Proxy reverso com suporte a WebSocket - Substitui o Redirect Server
"""
import asyncio
import websockets
import httpx
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, Response
import uvicorn

app = FastAPI(title="ALMA Proxy")

# CORS amplo para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente HTTP assíncrono
client = httpx.AsyncClient(base_url="http://localhost:5000")

@app.get("/")
async def home():
    """Redireciona para login"""
    return RedirectResponse("/login")

@app.get("/login")
async def login_page():
    """Serve página de login"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:5001/login")
    return Response(content=response.content, media_type="text/html")

@app.post("/login")
async def login(request: Request):
    """Proxy para login"""
    data = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:5000/login", json=data)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "alma_proxy"}

@app.websocket("/hub/_stcore/stream")
async def websocket_proxy(websocket: WebSocket):
    """Proxy WebSocket para Streamlit"""
    await websocket.accept()
    
    try:
        # Conecta ao WebSocket do Streamlit
        async with websockets.connect("ws://localhost:8501/_stcore/stream") as streamlit_ws:
            # Task para receber do Streamlit e enviar para cliente
            async def forward_to_client():
                try:
                    async for message in streamlit_ws:
                        await websocket.send_text(message)
                except:
                    pass
            
            # Task para receber do cliente e enviar para Streamlit
            async def forward_to_streamlit():
                try:
                    async for message in websocket.iter_text():
                        await streamlit_ws.send(message)
                except:
                    pass
            
            # Executa ambas as direções simultaneamente
            await asyncio.gather(
                forward_to_client(),
                forward_to_streamlit()
            )
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_all(path: str, request: Request):
    """Proxy para todas as outras rotas"""
    target_url = f"http://localhost:5000/{path}"
    
    # Headers
    headers = {key: value for key, value in request.headers.items() 
               if key.lower() not in ['host', 'content-length']}
    
    # Body
    body = await request.body() if request.method in ['POST', 'PUT'] else None
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params
        )
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")