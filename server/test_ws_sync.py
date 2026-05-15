#!/usr/bin/env python3
"""Test WS sync persistence end-to-end

Usage:  python test_ws_sync.py
"""

import asyncio
import json
import http.client
import random
import sys

BASE = "localhost:8000"


class Client:
    def __init__(self, token=None):
        self.token = token

    def req(self, method, path, data=None, auth=True):
        c = http.client.HTTPConnection(BASE)
        h = {"Content-Type": "application/json"}
        if auth and self.token:
            h["Authorization"] = f"Bearer {self.token}"
        c.request(method, path, json.dumps(data) if data else None, h)
        r = c.getresponse()
        return r.status, json.loads(r.read())


async def run_test():
    c = Client()

    suffix = random.randint(10000, 99999)
    username = f"wstest_{suffix}"

    status, data = c.req("POST", "/api/auth/register",
                         {"username": username, "password": "test123"}, auth=False)
    assert status == 200, f"Register failed: {data}"

    status, data = c.req("POST", "/api/auth/login",
                         {"username": username, "password": "test123"}, auth=False)
    assert status == 200, f"Login failed: {data}"
    token = data["access_token"]
    c.token = token

    status, data = c.req("POST", "/api/pet/init")
    assert status == 200

    import websockets
    uri = f"ws://{BASE}/ws?token={token}"

    async with websockets.connect(uri) as ws:
        await ws.recv()  # system.connected

        # === sync.pet ===
        await ws.send(json.dumps({
            "router": "sync.pet", "action": "update",
            "data": {"info": {"name": "WSPet", "hunger": 500},
                     "max_info": {"level": 5}},
            "id": "t1", "timestamp": 1,
        }))
        ack = json.loads(await ws.recv())
        assert ack["router"] == "sync.pet.ack", f"Expected sync.pet.ack, got {ack}"
        json.loads(await ws.recv())  # broadcast

        # === sync.inventory ===
        await ws.send(json.dumps({
            "router": "sync.inventory", "action": "update",
            "data": {"food": ["_ws_item-3"], "commodity": ["_ws_comm-1"]},
            "id": "t2", "timestamp": 1,
        }))
        ack2 = json.loads(await ws.recv())
        assert ack2["router"] == "sync.inventory.ack", f"Expected sync.inventory.ack, got {ack2}"
        json.loads(await ws.recv())  # broadcast

    # === Verify HTTP persistence ===
    _, pet = c.req("GET", "/api/pet")
    assert pet["info"]["name"] == "WSPet", f"Name: {pet['info']['name']}"
    assert pet["info"]["hunger"] == 500, f"Hunger: {pet['info']['hunger']}"
    assert pet["max_info"]["level"] == 5, f"Level: {pet['max_info']['level']}"
    print("Pet persistence: OK")

    _, inv = c.req("GET", "/api/pet/inventory")
    assert "_ws_item-3" in inv["food"], f"Food: {inv['food']}"
    assert "_ws_comm-1" in inv["commodity"], f"Commodity: {inv['commodity']}"
    print("Inventory persistence: OK")

    print("=== ALL WS SYNC TESTS PASSED ===")


def main():
    asyncio.run(run_test())


if __name__ == "__main__":
    main()
