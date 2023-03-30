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
        P0 = 'TestUser1'
        await self.client.connect()
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]))
        # time.sleep(.5)
        msg = await self.client.receive()
        dictMsg = json.loads(msg)


        expected = {'action': 'set_player_name', 'description': 'success', 'username': P0, 'player_id': dictMsg['player_id']}
        self.assertEqual(dictMsg, expected)

    async def test_create_game(self):
        P0 = 'TestUser1'
        P1 = 'TestUser2'
        await self.client.connect()
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]))
        # time.sleep(.5)
        msg = await self.client.receive()
        dictMsg = json.loads(msg)
        # player_id = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': P0}]))
        msg = await self.client.receive()
        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': None, 'activePlayer': '0',
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        self.assertEqual(dictMsg, expected)

    async def test_join_game(self):
        P0 = 'TestUser1'
        P1 = 'TestUser2'
        P2 = 'TestUser3'

        await self.client.connect()
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]))
        msg = await self.client.receive()
        dictMsg = json.loads(msg)
        # P0 = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': P0}]))
        msg = await self.client.receive()
        dictMsg = json.loads(msg)
        game_id = dictMsg['game_id']


        await self.client.close()
        await self.client.connect()

        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P1}]))
        msg = await self.client.receive()
        dictMsg = json.loads(msg)
        # P1 = dictMsg['player_id']

        ## remove "game-" from game_id since input is just the uuid # as a string
        game_id = game_id[5:]

        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': P1, 'game_id': game_id}]))
        msg = await self.client.receive()
        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '0',
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        self.assertEqual(dictMsg, expected)

        await self.client.close()
        await self.client.connect()

        ## test that you can't add a 3rd player to same game

        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P2}]))
        msg = await self.client.receive()
        dictMsg = json.loads(msg)
        player3_id = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': P2, 'game_id': game_id}]))
        try:
            msg = await self.client.receive()
            self.fail()
        except:
            pass

    
    async def asyncTearDown(self):
        await self.client.close()



    if __name__ == '__main__':
        unittest.main()


class DummyClient:

    def __init__(self):
        # ip = "127.0.0.1"
        self.URL = "ws://localhost:8000"
        self.websocket = None
        

    async def connect(self):
        self.websocket = await websockets.connect(self.URL)

    async def send(self, message):
        # self.websocket = await websockets.connect(self.URL)
        await self.websocket.send(message)

    async def receive(self):
        return await self.websocket.recv()
    
    async def close(self):
        await self.websocket.close()

    



        

