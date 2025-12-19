"""
Simple token server for LiveKit room access.
Provides JWT tokens for frontend clients to connect to LiveKit rooms.
"""

import os
from datetime import datetime
from aiohttp import web
from livekit import api
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")


async def handle_token(request: web.Request) -> web.Response:
    """Generate a LiveKit access token for a room."""
    try:
        data = await request.json()
        room_name = data.get("room", f"codecoach-{datetime.now().timestamp()}")
        identity = data.get("identity", f"user-{datetime.now().timestamp()}")
        
        # Create access token
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(identity)
        token.with_name(identity)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        ))
        
        jwt_token = token.to_jwt()
        
        return web.json_response({
            "token": jwt_token,
            "room": room_name,
            "identity": identity,
        })
        
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_health(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "ok"})


def create_app() -> web.Application:
    """Create the aiohttp application."""
    app = web.Application()
    
    # CORS middleware
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "OPTIONS":
                response = web.Response()
            else:
                response = await handler(request)
            
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response
        return middleware_handler
    
    app.middlewares.append(cors_middleware)
    
    # Routes
    app.router.add_post("/token", handle_token)
    app.router.add_get("/health", handle_health)
    
    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("TOKEN_SERVER_PORT", 8080))
    print(f"Token server running on http://localhost:{port}")
    web.run_app(app, host="0.0.0.0", port=port)

