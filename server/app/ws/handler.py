import asyncio
import json
import logging
import uuid
from typing import Any, Callable, Dict, Optional
from sqlalchemy import or_, and_

from app.database import SessionLocal
from app.models import PetData, PetInventory
from app.ws.manager import manager

logger = logging.getLogger(__name__)

HandlerFunc = Callable[[int, Dict[str, Any]], Optional[Dict[str, Any]]]


def safe_set_value(obj, attr_name, value, expected_type=None):
    if value is None:
        return

    if value == "" and expected_type in (int, float):
        value = 0 if expected_type == int else 0.0

    if expected_type == int and isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            value = 0
    elif expected_type == float and isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            value = 0.0

    setattr(obj, attr_name, value)


def _persist_pet(user_id: int, data: dict) -> None:
    db = SessionLocal()
    try:
        pet_data = db.query(PetData).filter(PetData.user_id == user_id).first()
        if not pet_data:
            logger.warning(f"WS sync: pet not found for user {user_id}")
            return

        if "info" in data:
            info_updates = data["info"]
            for key, value in info_updates.items():
                field_name = f"info_{key}"
                if hasattr(pet_data, field_name):
                    if key in ["growth", "online_time", "online_data_time"]:
                        safe_set_value(pet_data, field_name, value, float)
                    elif key in ["hunger", "clean", "health", "mood", "yb", "intel", "charm", "strong", "last_login_time"]:
                        safe_set_value(pet_data, field_name, value, int)
                    else:
                        safe_set_value(pet_data, field_name, value, str)

        if "max_info" in data:
            max_updates = data["max_info"]
            for key, value in max_updates.items():
                field_name = f"max_{key}"
                if hasattr(pet_data, field_name):
                    if key == "stop_growth":
                        safe_set_value(pet_data, field_name, value, bool)
                    else:
                        safe_set_value(pet_data, field_name, value, int)

        if "active_option" in data:
            pet_data.active_option = data["active_option"] or {}
        if "active_value" in data:
            pet_data.active_value = data["active_value"] or {}
        if "other_options" in data:
            pet_data.other_options = data["other_options"] or {}
        if "fishing" in data:
            pet_data.fishing = data["fishing"] or {}

        db.commit()
        logger.info(f"WS sync: pet persisted for user {user_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"WS sync: pet persist failed for user {user_id}: {e}")
        raise
    finally:
        db.close()


def _persist_inventory(user_id: int, data: dict) -> None:
    db = SessionLocal()
    try:
        inventory = db.query(PetInventory).filter(PetInventory.user_id == user_id).first()
        if not inventory:
            logger.warning(f"WS sync: inventory not found for user {user_id}")
            return

        items = dict(inventory.items or {})
        for key in ("food", "commodity", "medicine", "background"):
            if key in data and data[key] is not None:
                items[key] = data[key]

        inventory.items = items
        db.commit()
        logger.info(f"WS sync: inventory persisted for user {user_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"WS sync: inventory persist failed for user {user_id}: {e}")
        raise
    finally:
        db.close()


class MessageRouter:
    def __init__(self):
        self._handlers: Dict[str, HandlerFunc] = {}

    def register(self, router_prefix: str, handler: HandlerFunc):
        self._handlers[router_prefix] = handler

    async def dispatch(self, user_id: int, message: dict) -> Optional[dict]:
        router = message.get("router", "")
        for prefix, handler in self._handlers.items():
            if router.startswith(prefix):
                return await handler(user_id, message)
        return None

    async def handle_system(self, user_id: int, msg: dict) -> Optional[dict]:
        action = msg.get("action", "")
        data = msg.get("data", {})

        if action == "ping":
            return {
                "router": "system.pong",
                "action": "response",
                "data": {"echo": data},
                "id": msg.get("id"),
                "from": 0,
                "to": user_id,
            }

        if action == "echo":
            return {
                "router": "system.echo",
                "action": "response",
                "data": data,
                "id": msg.get("id"),
                "from": 0,
                "to": user_id,
            }

        return {
            "router": "system.error",
            "action": "response",
            "data": {"error": f"unknown system action: {action}"},
            "id": msg.get("id"),
            "from": 0,
            "to": user_id,
        }

    async def handle_sync(self, user_id: int, msg: dict) -> Optional[dict]:
        action = msg.get("action", "")
        data = msg.get("data", {})
        router = msg.get("router", "")

        if action == "update":
            try:
                if router == "sync.pet":
                    _persist_pet(user_id, data)
                elif router == "sync.inventory":
                    _persist_inventory(user_id, data)
                else:
                    logger.warning(f"WS sync: unknown router {router}")

                return {
                    "router": router + ".ack",
                    "action": "response",
                    "data": {"ok": True},
                    "id": msg.get("id"),
                    "from": 0,
                    "to": user_id,
                }
            except Exception as e:
                logger.error(f"WS sync failed for user {user_id}: {e}")
                return {
                    "router": router + ".error",
                    "action": "response",
                    "data": {"error": str(e)},
                    "id": msg.get("id"),
                    "from": 0,
                    "to": user_id,
                }

        return {
            "router": "sync.error",
            "action": "response",
            "data": {"error": f"unknown sync action: {action}"},
            "id": msg.get("id"),
            "from": 0,
            "to": user_id,
        }

    async def handle_social(self, user_id: int, msg: dict) -> Optional[dict]:
        action = msg.get("action", "")
        data = msg.get("data", {})

        if action == "status_broadcast":
            online = manager.is_online(user_id)
            return {
                "router": "social.status_broadcast",
                "action": "response",
                "data": {"online": online},
                "id": msg.get("id"),
                "from": 0,
                "to": user_id,
            }

        if action == "friend_online":
            from app.models import Friend
            db = SessionLocal()
            try:
                from sqlalchemy import or_, and_
                friend_rels = db.query(Friend).filter(
                    or_(
                        and_(Friend.user_id == user_id, Friend.status == "accepted"),
                        and_(Friend.friend_user_id == user_id, Friend.status == "accepted"),
                    )
                ).all()
                friend_ids = set()
                for f in friend_rels:
                    friend_ids.add(f.friend_user_id if f.user_id == user_id else f.user_id)
                for fid in friend_ids:
                    await manager.send_to_user(fid, {
                        "router": "social.friend_online",
                        "action": "update",
                        "data": {"user_id": user_id, "online": True},
                        "from": user_id,
                        "to": fid,
                    })
                return {
                    "router": "social.friend_online",
                    "action": "response",
                    "data": {"ok": True, "notified": list(friend_ids)},
                    "id": msg.get("id"),
                    "from": 0,
                    "to": user_id,
                }
            finally:
                db.close()

        return {
            "router": "social.error",
            "action": "response",
            "data": {"error": f"unknown social action: {action}"},
            "id": msg.get("id"),
            "from": 0,
            "to": user_id,
        }


router = MessageRouter()
router.register("system.", router.handle_system)
router.register("sync.", router.handle_sync)
router.register("social.", router.handle_social)


async def handle_message(ws, user_id: int, raw: str):
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        await ws.send_json({
            "router": "system.error",
            "action": "response",
            "data": {"error": "invalid JSON"},
            "id": None,
            "from": 0,
            "to": user_id,
        })
        return

    msg_id = msg.get("id") or str(uuid.uuid4())
    msg["from"] = user_id
    msg["id"] = msg_id

    response = await router.dispatch(user_id, msg)

    if response is not None:
        response.setdefault("id", msg_id)
        response.setdefault("from", 0)
        response.setdefault("to", user_id)
        await ws.send_json(response)

    # Broadcast sync updates to all other connections of this user (multi-device)
    router_name = msg.get("router", "")
    if router_name.startswith("sync.") and msg.get("action") == "update":
        asyncio.create_task(
            manager.send_to_user(user_id, {
                "router": router_name,
                "action": "update",
                "data": msg.get("data", {}),
                "id": msg_id,
                "from": user_id,
                "to": 0,
            })
        )
