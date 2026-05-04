from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.security import verify_token
from app.ws_manager import manager


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    identifier = verify_token(token)
    if identifier is None:
        await websocket.close(code=1008)
        return

    user_id = identifier # identifier is the sub/id from token
    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception:
        manager.disconnect(websocket, user_id)

