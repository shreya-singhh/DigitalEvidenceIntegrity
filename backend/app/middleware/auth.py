from fastapi import Request
from starlette.responses import Response

async def auth_middleware(request: Request, call_next):
    response = await call_next(request)
    return response
