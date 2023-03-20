import unittest
# import game_server
import asyncio
import websockets
import json
import time


class TestGameServer(unittest.IsolatedAsyncioTestCase):
    client = None

    def setUp(self):
        self.client = DummyClient()

    async def test_set_player_name(self):
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': 'TestUser1'}]))
        # time.sleep(.5)
        msg = await self.client.receive()
        dictMsg = json.loads(msg)


        expected = {'action': 'set_player_name', 'description': 'success', 'username': 'TestUser1', 'player_id': dictMsg['player_id']}
        self.assertEqual(dictMsg, expected)



    if __name__ == '__main__':
        unittest.main()


class DummyClient:

    def __init__(self):
        # ip = "127.0.0.1"
        self.URL = "ws://localhost:8000"
        self.websocket = None

    async def send(self, message):
        self.websocket = await websockets.connect(self.URL)
        await self.websocket.send(message)

    async def receive(self):
        return await self.websocket.recv()

    



        

