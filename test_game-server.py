import unittest
# import game_server
import asyncio
import websockets
import json
import time

## constants used for indicating which websocket to use
WEBSOCKET_1 = 1
WEBSOCKET_2 = 2
WEBSOCKET_3 = 3
## constants to represent the usernames
P0 = 'TestUser1'
P1 = 'TestUser2'
P2 = 'TestUser3'

class TestGameServer(unittest.IsolatedAsyncioTestCase):



    client = None

    def setUp(self):
        self.client = DummyClient()

    async def test_set_player_name(self):
        await self.client.connect(WEBSOCKET_1)
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)


        expected = {'action': 'set_player_name', 'description': 'success', 'username': P0, 'player_id': dictMsg['player_id']}
        self.assertEqual(dictMsg, expected)

    async def test_create_game(self):
        await self.client.connect(WEBSOCKET_1)
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)
        # player_id = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': None, 'activePlayer': '0',
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        self.assertEqual(dictMsg, expected)

    async def test_join_game(self):

        await self.client.connect(WEBSOCKET_1)
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)
        # P0 = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)
        game_id = dictMsg['game_id']

        await self.client.connect(WEBSOCKET_2)

        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P1}]), WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)
        # P1 = dictMsg['player_id']

        ## remove "game-" from game_id since input is just the uuid # as a string
        game_id = game_id[5:]

        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': P1, 'game_id': game_id}]), WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)

        ## TEST: check that both websockets got the updated game-state
        self.assertEqual(msg, msg2)

        dictMsg = json.loads(msg)        

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '0',
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        self.assertEqual(dictMsg, expected)

        # await self.client.close()
        await self.client.connect(WEBSOCKET_3)

        ## TEST: you can't add a 3rd player to same game

        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P2}]), WEBSOCKET_3)
        msg = await self.client.receive(WEBSOCKET_3)
        dictMsg = json.loads(msg)
        player3_id = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': P2, 'game_id': game_id}]), WEBSOCKET_3)
        try:
            msg = await self.client.receive(WEBSOCKET_3)
            self.fail()
        except:
            pass

    
    '''
    As of now this just tests joining a spectated game, receiving update when 2nd player joins
    Need to find a way to test that moves sent to the game are also received by the spectator.
    '''
    async def test_spectate_game(self):
        # P0 = 'TestUser1'
        # P1 = 'TestUser2'

        await self.client.connect(WEBSOCKET_1)
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)
        # P0 = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)
        game_id = dictMsg['game_id']

        ## remove "game-" from game_id since input is just the uuid # as a string
        game_id = game_id[5:]


        # await self.client.close()
        await self.client.connect(WEBSOCKET_2)

        ## TEST: you can add a 3rd player as a spectator (add before 2nd player 
        ## and test you receive initial game-state)

        await self.client.send(json.dumps([{'action': 'spectate_game', 'game_id': game_id}]), WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': None, 'activePlayer': '0',
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)

        # await self.client.close()
        await self.client.connect(WEBSOCKET_3)

        ## TEST: when 2nd player joins, the spectator also gets the updated game-state

        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P1}]), WEBSOCKET_3)
        msg = await self.client.receive(WEBSOCKET_3)
        dictMsg = json.loads(msg)
        # P1 = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': P1, 'game_id': game_id}]), WEBSOCKET_3)
        ## note that WEBSOCKET_2 is spectator's websocket
        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '0',
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)

    
    async def asyncTearDown(self):
        await self.client.close()



    if __name__ == '__main__':
        unittest.main()


class DummyClient:

    def __init__(self):
        # ip = "127.0.0.1"
        self.URL = "ws://localhost:8000"
        self.websocket = None
        self.websocket2 = None
        self.websocket3 = None

    ## connnect the specified websocket
    async def connect(self, socket):
        if socket == WEBSOCKET_1:
            self.websocket = await websockets.connect(self.URL)

        if socket == WEBSOCKET_2:
            self.websocket2 = await websockets.connect(self.URL)

        if socket == WEBSOCKET_3:
            self.websocket3 = await websockets.connect(self.URL)

    ## send message via the specified websocket
    async def send(self, message, socket):
        if socket == WEBSOCKET_1:
            await self.websocket.send(message)

        if socket == WEBSOCKET_2:
            await self.websocket2.send(message)

        if socket == WEBSOCKET_3:
            await self.websocket3.send(message)
    
    ## receive message on the specified websocket
    async def receive(self, socket):
        if socket == WEBSOCKET_1:
            return await self.websocket.recv()
        
        if socket == WEBSOCKET_2:
            return await self.websocket2.recv()
        
        if socket == WEBSOCKET_3:
            return await self.websocket3.recv()
    
    ## close all the websockets
    async def close(self):
        if self.websocket is not None:
            await self.websocket.close()

        if self.websocket2 is not None:
            await self.websocket2.close()

        if self.websocket3 is not None:
            await self.websocket3.close()