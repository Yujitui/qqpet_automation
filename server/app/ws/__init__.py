from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.ws.manager import manager
from app.ws.auth import verify_ws_token
from app.ws.handler import handle_message

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    auth_result = await verify_ws_token(ws)

    if not auth_result.success:
        await ws.accept()
        await ws.send_json({
            "router": "system.error",
            "action": "response",
            "data": {"error": auth_result.error},
            "from": 0,
            "to": None,
        })
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = auth_result.user_id
    await manager.connect(ws, user_id)

    await ws.send_json({
        "router": "system.connected",
        "action": "notify",
        "data": {"user_id": user_id, "message": "连接成功"},
        "from": 0,
        "to": user_id,
    })

    try:
        while True:
            raw = await ws.receive_text()
            await handle_message(ws, user_id, raw)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass
    finally:
        manager.disconnect(ws, user_id)
