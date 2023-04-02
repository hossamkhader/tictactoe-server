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

    ## Test setting player name
    async def test_set_player_name(self):
        await self.client.connect(WEBSOCKET_1)
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)


        expected = {'action': 'set_player_name', 'description': 'success', 'username': P0, 'player_id': dictMsg['player_id']}
        self.assertEqual(dictMsg, expected)


    ## Test creating a game
    async def test_create_game(self):
        await self.client.connect(WEBSOCKET_1)
        ## code for setting player name not necessary as of now since we aren't using player uuid anymore
        ## but I'm leaving here since it seems like it could be useful to go back to this later
        # await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]), WEBSOCKET_1)
        # msg = await self.client.receive(WEBSOCKET_1)
        # dictMsg = json.loads(msg)
        # player_id = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': None, 'activePlayer': '0', 'player_count': 1,
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        self.assertEqual(dictMsg, expected)

    ## Test joining a game that another player created
    async def test_join_game(self):

        await self.client.connect(WEBSOCKET_1)
        # await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P0}]), WEBSOCKET_1)
        # msg = await self.client.receive(WEBSOCKET_1)
        # dictMsg = json.loads(msg)
        # P0 = dictMsg['player_id']

        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)
        game_id = dictMsg['game_id']

        await self.client.connect(WEBSOCKET_2)

        # await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P1}]), WEBSOCKET_2)
        # msg = await self.client.receive(WEBSOCKET_2)
        # dictMsg = json.loads(msg)
        # P1 = dictMsg['player_id']

        ## remove "game-" from game_id since input is just the uuid # as a string
        game_id = game_id[5:]

        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': P1, 'game_id': game_id}]), WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)

        ## TEST: check that both websockets got the game_ready message
        self.assertEqual(msg, msg2)

        # dictMsg = json.loads(msg)        

        # expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '0',
        #    'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
        #    'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        expected = 'game_ready'

        self.assertEqual(msg, expected)

         ## TEST: check that both websockets got the updated game-state
        
        request = json.dumps([{'action': 'get_game_state', 'game_id': game_id}])
        await self.client.send(request, WEBSOCKET_1)
        await self.client.send(request, WEBSOCKET_2)

        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)


        dictMsg = json.loads(msg)        

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '0', 'player_count': 2,
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)

        # await self.client.close()
        await self.client.connect(WEBSOCKET_3)

        ## TEST: you can't add a 3rd player to same game

        # await self.client.send(json.dumps([{'action': 'set_player_name', 'username': P2}]), WEBSOCKET_3)
        # msg = await self.client.receive(WEBSOCKET_3)
        # dictMsg = json.loads(msg)
        # player3_id = dictMsg['player_id']

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

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': None, 'activePlayer': '0', 'player_count': 1,
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


        # dictMsg = json.loads(msg)

        # expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '0',
        #    'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
        #    'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        expected = 'game_ready'
        
        self.assertEqual(msg, expected)

        ## add the 'game-' back in here because game_move expects it
        # game_id = 'game-' + game_id

        ## TEST: spectator receives update from player 1 making a move
        move = json.dumps([{'action': 'game_move', 'game_id': game_id, 'player_id': P0, 'piece': 'piece-5'}])
        await self.client.send(move, WEBSOCKET_1)

        ## NOTE that WEBSOCKET_2 is spectator's websocket
        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '1', 'player_count': 2,
           'winner': None, 'last_move': dictMsg['last_move'], 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': '0', 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)
        
        ## TEST: spectator receives update from player 2 making a move
        move = json.dumps([{'action': 'game_move', 'game_id': game_id, 'player_id': P1, 'piece': 'piece-3'}])
        await self.client.send(move, WEBSOCKET_3)

        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '0', 'player_count': 2,
            'winner': None, 'last_move': dictMsg['last_move'], 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': '1',
            'piece-4': None, 'piece-5': '0', 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)
        

    async def test_game_move(self):
        
        await self.client.connect(WEBSOCKET_1)

        ## create game and get game_id
        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': P0}]), WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        dictMsg = json.loads(msg)
        game_id = dictMsg['game_id']

        await self.client.connect(WEBSOCKET_2)

        ## remove "game-" from game_id since input is just the uuid # as a string
        game_id = game_id[5:]

        ## join game and receive game_ready response from server (don't need that for unit test though)
        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': P1, 'game_id': game_id}]), WEBSOCKET_2)
        ## discard incoming messages 
        await self.client.receive(WEBSOCKET_1)
        await self.client.receive(WEBSOCKET_2)
        
        # request = json.dumps([{'action': 'get_game_state', 'game_id': game_id}])
        # await self.client.send(request, WEBSOCKET_1)
        # await self.client.send(request, WEBSOCKET_2)

        # msg = await self.client.receive(WEBSOCKET_1)
        # msg2 = await self.client.receive(WEBSOCKET_2)

        ## here ready to receive gamestate updates from moves

        ## move order to test every piece

        move_1 = [{'action': 'game_move', 'player_id': P0, 'game_id': game_id, 'piece': 'piece-0'}]
        move_2 = [{'action': 'game_move', 'player_id': P1, 'game_id': game_id, 'piece': 'piece-1'}]
        move_3 = [{'action': 'game_move', 'player_id': P0, 'game_id': game_id, 'piece': 'piece-2'}]
        move_4 = [{'action': 'game_move', 'player_id': P1, 'game_id': game_id, 'piece': 'piece-3'}]
        move_5 = [{'action': 'game_move', 'player_id': P0, 'game_id': game_id, 'piece': 'piece-4'}]
        move_6 = [{'action': 'game_move', 'player_id': P1, 'game_id': game_id, 'piece': 'piece-5'}]
        move_7 = [{'action': 'game_move', 'player_id': P0, 'game_id': game_id, 'piece': 'piece-7'}]
        move_8 = [{'action': 'game_move', 'player_id': P1, 'game_id': game_id, 'piece': 'piece-6'}]
        move_9 = [{'action': 'game_move', 'player_id': P0, 'game_id': game_id, 'piece': 'piece-8'}]

        await self.client.send(json.dumps(move_1),WEBSOCKET_1)

        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)

        ## check that both websockets receive the updated game-state
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        
        ## check the updated game-state
        expected = {'game_id': dictMsg['game_id'], 'p0': P0, 'p1': P1, 'activePlayer': '1', 'player_count': 2,
            'winner': None, 'last_move': dictMsg['last_move'], 'piece-0': '0', 'piece-1': None, 'piece-2': None, 'piece-3': None,
            'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}    
        self.assertEqual(expected, dictMsg)

        ## test remaining moves
        await self.client.send(json.dumps(move_2),WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-1'] = '1'
        expected['activePlayer'] = '0'
        self.assertEqual(expected, dictMsg)

        await self.client.send(json.dumps(move_3),WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-2'] = '0'
        expected['activePlayer'] = '1'
        self.assertEqual(expected, dictMsg)

        await self.client.send(json.dumps(move_4),WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-3'] = '1'
        expected['activePlayer'] = '0'
        self.assertEqual(expected, dictMsg)

        await self.client.send(json.dumps(move_5),WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-4'] = '0'
        expected['activePlayer'] = '1'
        self.assertEqual(expected, dictMsg)

        await self.client.send(json.dumps(move_6),WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-5'] = '1'
        expected['activePlayer'] = '0'
        self.assertEqual(expected, dictMsg)

        await self.client.send(json.dumps(move_7),WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-7'] = '0'
        expected['activePlayer'] = '1'
        self.assertEqual(expected, dictMsg)

        await self.client.send(json.dumps(move_8),WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-6'] = '1'
        expected['activePlayer'] = '0'
        self.assertEqual(expected, dictMsg)

        await self.client.send(json.dumps(move_9),WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-8'] = '0'
        expected['activePlayer'] = '1'
        ## winner changes to 0 here as well
        expected['winner'] = '0'
        self.assertEqual(expected, dictMsg)


    
    async def asyncTearDown(self):
        await self.client.close()



    if __name__ == '__main__':
        unittest.main()


## Class for clients to use for testing
## NOTE: I realized I should have just used 1 websocket
## and made separate instances of clients but only after I had already set up a lot of tests
## I'd like to go back and refactor this but it will take some time to do.
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