import asyncio
import aiohttp
from aiohttp import web, WSMsgType
import logging
import httpx

# Configuração
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mapeamento para os serviços Streamlit
# Mapeamento CORRIGIDO para os serviços Streamlit
SERVICES = {
    'seletor': {
        'url': 'http://localhost:8501', 
        'path': '/seletor',
        'health_endpoint': '/seletor/_stcore/health'
    },
    'daytrade': {  # ✅ Nome único
        'url': 'http://localhost:8502',
        'path': '/daytrade',  # ✅ Path único
        'health_endpoint': '/daytrade/_stcore/health'
    },
    'sports': {  # ✅ Nome único  
        'url': 'http://localhost:8503',
        'path': '/sports',  # ✅ Path único
        'health_endpoint': '/sports/_stcore/health'
    },
    'quantum': {  # ✅ Nome único
        'url': 'http://localhost:8504', 
        'path': '/quantum',  # ✅ Path único
        'health_endpoint': '/quantum/_stcore/health'
    },
}

class TunnelServer:
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        self.session = None
        
    async def startup(self, app):
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self, app):
        if self.session:
            await self.session.close()
            
    def setup_routes(self):
        # WebSocket tunnel para serviços Streamlit
        self.app.router.add_route('*', '/{service}/_stcore/stream', self.websocket_tunnel)
        
        # Proxy HTTP para serviços Streamlit
        self.app.router.add_route('*', '/{service}/{path:.*}', self.http_proxy)
        self.app.router.add_route('*', '/{path:.*}', self.http_proxy_root)
        
    async def websocket_tunnel(self, request):
        service = request.match_info['service']
        if service not in SERVICES:
            return web.Response(text='Service not found', status=404)
            
        service_config = SERVICES[service]
        target_ws_url = f"{service_config['url'].replace('http', 'ws')}{service_config['path']}/_stcore/stream"
        
        logger.info(f"🔌 Conectando WebSocket para serviço: {service} -> {target_ws_url}")
        
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        try:
            async with self.session.ws_connect(
                target_ws_url,
                headers={
                    'Origin': 'http://localhost:5500',
                    'Sec-WebSocket-Protocol': 'v4.streamlit.connection'
                }
            ) as target_ws:
                logger.info(f"✅ Conexão WebSocket estabelecida com {service}")
                
                async def forward_to_service():
                    async for msg in ws:
                        if msg.type == WSMsgType.TEXT:
                            await target_ws.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await target_ws.send_bytes(msg.data)
                
                async def forward_from_service():
                    async for msg in target_ws:
                        if msg.type == WSMsgType.TEXT:
                            await ws.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws.send_bytes(msg.data)
                
                await asyncio.gather(forward_to_service(), forward_from_service())
                
        except Exception as e:
            logger.error(f"❌ Erro no tunnel para {service}: {e}")
        finally:
            await ws.close()
            
        return ws
        
    # No método http_proxy, substitua esta parte:
    async def http_proxy(self, request):
        service = request.match_info['service']
        path = request.match_info.get('path', '')
        
        if service not in SERVICES:
            return web.Response(text='Service not found', status=404)
            
        service_config = SERVICES[service]
        target_url = f"{service_config['url']}{service_config['path']}/{path}"
        
        if request.query_string:
            target_url += f"?{request.query_string}"
            
        logger.info(f"🔁 HTTP para serviço: {request.path} -> {target_url}")
        
        headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
        
        try:
            async with self.session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=await request.read() if request.can_read_body else None,
                allow_redirects=False  # 🔥 IMPORTANTE: Não seguir redirecionamentos automaticamente
            ) as response:
                
                # 🔥 TRATAR REDIRECIONAMENTOS MANUALMENTE
                if response.status in [301, 302, 307, 308]:
                    location = response.headers.get('location', '')
                    if location and location.startswith('/'):
                        # Redirecionamento relativo - ajustar para URL completa
                        location = f"{service_config['url']}{service_config['path']}{location}"
                    return web.Response(
                        status=response.status,
                        headers=dict(response.headers),
                        body=await response.read()
                    )
                
                return web.Response(
                    status=response.status,
                    headers=dict(response.headers),
                    body=await response.read()
                )
                
        except aiohttp.ClientConnectorError:
            logger.error(f"❌ Serviço {service} offline na porta {service_config['url'].split(':')[-1]}")
            return web.Response(
                text=f"Serviço {service} indisponível. Execute: streamlit run {service}.py --server.port={service_config['url'].split(':')[-1]} --server.baseUrlPath={service}",
                status=503
            )
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão: {e}")
            return web.Response(text=f"Service {service} unavailable", status=503)
        
    async def http_proxy_root(self, request):
        # Para requisições na raiz, redireciona para seletor
        if 'token' in request.query:
            token = request.query['token']
            return web.HTTPFound(f'/seletor?token={token}')
            
        return web.Response(text="Fluxon Tunnel Server - Use /seletor, /trading, etc.")

    async def health_check(self, request):
        # Health check para todos os serviços
        services_status = {}
        
        for service_name, service_config in SERVICES.items():
            try:
                # Testa vários endpoints possíveis
                endpoints = [
                    f"{service_config['url']}{service_config['path']}/_stcore/health",
                    f"{service_config['url']}{service_config['path']}/health", 
                    f"{service_config['url']}/_stcore/health",
                    f"{service_config['url']}/health",
                    service_config['url']  # Apenas a URL base
                ]
                
                for endpoint in endpoints:
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.get(endpoint, timeout=2.0)
                            if response.status_code == 200:
                                services_status[service_name] = "healthy"
                                break
                    except:
                        continue
                else:
                    services_status[service_name] = "unhealthy"
                    
            except Exception as e:
                services_status[service_name] = f"error: {str(e)}"
        
        return web.json_response({
            "status": "healthy",
            "tunnel": "running",
            "services": services_status
        })

async def main():
    server = TunnelServer()
    
    # Adicionar health check
    server.app.router.add_get('/health', server.health_check)
    
    server.app.on_startup.append(server.startup)
    server.app.on_cleanup.append(server.cleanup)
    
    print("="*60)
    print("🚀 FLUXON TUNNEL SERVER - COMUNICAÇÃO INTERNA")
    print("="*60)
    print("📡 Porta: 5501")
    print("🔌 Conectando aos serviços Streamlit:")
    for service, config in SERVICES.items():
        print(f"   • {service}: {config['url']}{config['path']}")
    print("="*60)
    print("🌐 Acesse através do Proxy: http://localhost:5500")
    print("="*60)
    
    runner = web.AppRunner(server.app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 5501)
    await site.start()
    
    print("✅ Tunnel Server iniciado!")
    print("⏹️  Pressione Ctrl+C para parar")
    
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("\n🛑 Parando servidor...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())