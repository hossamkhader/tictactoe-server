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


    async def test_get_game_state(self):
        await self.client.connect(WEBSOCKET_1)
        await self.client.connect(WEBSOCKET_2)

        game = await self.game_for_testing(WEBSOCKET_1, WEBSOCKET_2)
        p0_id = game['p0']
        p1_id = game['p1']
        game_id = game['game_id']

        ## test requesting game state from websocket_1
        await self.client.send(json.dumps([{'action': 'get_game_state', 'game_id': game_id}]), WEBSOCKET_1)

        msg = await self.client.receive(WEBSOCKET_1)

        dictMsg = json.loads(msg)

        expected = {'game_id': dictMsg['game_id'], 'p0': p0_id, 'p1': p1_id, 'activePlayer': '0', 'player_count': 2,
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(expected, dictMsg)




    ## Test joining a game that another player created
    async def test_join_game(self):

        await self.client.connect(WEBSOCKET_1)
        await self.client.connect(WEBSOCKET_2)

        p0_id = await self.get_player_id(P0, WEBSOCKET_1)
        game_id = await self.create_game(p0_id, WEBSOCKET_1)
        p1_id = await self.get_player_id(P1, WEBSOCKET_2)

        ## remove "game-" from game_id since input is just the uuid # as a string
        # game_id = game_id[5:]

        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': p1_id, 'game_id': game_id}]), WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)

        ## TEST: check that both websockets got the initial game state
        self.assertEqual(msg, msg2)

        dictMsg = json.loads(msg)        

        expected = {'game_id': dictMsg['game_id'], 'p0': p0_id, 'p1': p1_id, 'activePlayer': '0', 'player_count': 2,
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        # expected = 'game_ready'

        self.assertEqual(dictMsg, expected)

         ## TEST: check that both websockets got the updated game-state
        
        request = json.dumps([{'action': 'get_game_state', 'game_id': game_id}])
        await self.client.send(request, WEBSOCKET_1)
        await self.client.send(request, WEBSOCKET_2)

        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)


        dictMsg = json.loads(msg)        

        expected = {'game_id': dictMsg['game_id'], 'p0': p0_id, 'p1': p1_id, 'activePlayer': '0', 'player_count': 2,
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)



        ## TEST: you can't add a 3rd player to same game

        await self.client.connect(WEBSOCKET_3)
        p2_id = await self.get_player_id(P2, WEBSOCKET_3)

        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': p2_id, 'game_id': game_id}]), WEBSOCKET_3)
        try:
            msg = await self.client.receive(WEBSOCKET_3)
            self.fail("Should not be able to join a game with 3 players.")
        except:
            pass

    
    '''
    As of now this just tests joining a spectated game, receiving update when 2nd player joins
    Need to find a way to test that moves sent to the game are also received by the spectator.
    '''
    async def test_spectate_game(self):

        await self.client.connect(WEBSOCKET_1)
        await self.client.connect(WEBSOCKET_2)
        await self.client.connect(WEBSOCKET_3)

        p0_id = await self.get_player_id(P0, WEBSOCKET_1)
        p1_id = await self.get_player_id(P1, WEBSOCKET_3)

        game_id = await self.create_game(p0_id, WEBSOCKET_1)        

        ## TEST: you can add a 3rd player as a spectator (add before 2nd player 
        ## and test you receive initial game-state)

        await self.client.send(json.dumps([{'action': 'spectate_game', 'game_id': game_id}]), WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)

        expected = {'game_id': game_id, 'p0': p0_id, 'p1': None, 'activePlayer': '0', 'player_count': 1,
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)
        

        ## TEST: when 2nd player joins, the spectator also gets the updated game-state

        await self.join_game(p1_id, game_id, WEBSOCKET_3)

        ## note that websocket 2 is the spectator's websocket
        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)

        expected = {'game_id': game_id, 'p0': p0_id, 'p1': p1_id, 'activePlayer': '0', 'player_count': 2,
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

        self.assertEqual(expected, dictMsg)


        ## TEST: spectator receives update from player 1 making a move
        move = self.get_move_json(p0_id, game_id, 5)
        await self.client.send(move, WEBSOCKET_1)

        ## note that WEBSOCKET_2 is spectator's websocket
        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)

        expected = {'game_id': game_id, 'p0': p0_id, 'p1': p1_id, 'activePlayer': '1', 'player_count': 2,
           'winner': None, 'last_move': dictMsg['last_move'], 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': '0', 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)
        
        ## TEST: spectator receives update from player 2 making a move
        move = self.get_move_json(p1_id, game_id, 3)
        await self.client.send(move, WEBSOCKET_3)

        ## note that WEBSOCKET_2 is spectator's websocket
        msg = await self.client.receive(WEBSOCKET_2)
        dictMsg = json.loads(msg)

        expected = {'game_id': game_id, 'p0': p0_id, 'p1': p1_id, 'activePlayer': '0', 'player_count': 2,
            'winner': None, 'last_move': dictMsg['last_move'], 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': '1',
            'piece-4': None, 'piece-5': '0', 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(dictMsg, expected)
        

    async def test_game_move(self):
        
        await self.client.connect(WEBSOCKET_1)
        await self.client.connect(WEBSOCKET_2)

        game = await self.game_for_testing(WEBSOCKET_1, WEBSOCKET_2)
        game_id = game['game_id']
        p0_id = game['p0']
        p1_id = game['p1']
        ## here ready to receive gamestate updates from moves    
    
        ## first player chooses piece-0
        move_1 = self.get_move_json(p0_id, game_id, 0)
        await self.client.send(move_1, WEBSOCKET_1)

        msg = await self.client.receive(WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)

        ## check that both websockets receive the updated game-state
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        
        ## check the updated game-state
        expected = {'game_id': game_id, 'p0': p0_id, 'p1': p1_id, 'activePlayer': '1', 'player_count': 2,
            'winner': None, 'last_move': dictMsg['last_move'], 'piece-0': '0', 'piece-1': None, 'piece-2': None, 'piece-3': None,
            'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}    
        self.assertEqual(expected, dictMsg)

        ## test remaining moves
        move_2 = self.get_move_json(p1_id, game_id, 1)

        await self.client.send(move_2, WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-1'] = '1'
        expected['activePlayer'] = '0'
        self.assertEqual(expected, dictMsg)

        move_3 = self.get_move_json(p0_id, game_id, 2)

        await self.client.send(move_3, WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-2'] = '0'
        expected['activePlayer'] = '1'
        self.assertEqual(expected, dictMsg)


        move_4 = self.get_move_json(p1_id, game_id, 3)

        await self.client.send(move_4, WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-3'] = '1'
        expected['activePlayer'] = '0'
        self.assertEqual(expected, dictMsg)


        move_5 = self.get_move_json(p0_id, game_id, 4)

        await self.client.send(move_5, WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-4'] = '0'
        expected['activePlayer'] = '1'
        self.assertEqual(expected, dictMsg)


        move_6 = self.get_move_json(p1_id, game_id, 5)

        await self.client.send(move_6, WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-5'] = '1'
        expected['activePlayer'] = '0'
        self.assertEqual(expected, dictMsg)


        move_7 = self.get_move_json(p0_id, game_id, 7)

        await self.client.send(move_7, WEBSOCKET_1)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-7'] = '0'
        expected['activePlayer'] = '1'
        self.assertEqual(expected, dictMsg)


        move_8 = self.get_move_json(p1_id, game_id, 6)

        await self.client.send(move_8, WEBSOCKET_2)
        msg = await self.client.receive(WEBSOCKET_1)
        msg2 = await self.client.receive(WEBSOCKET_2)
        self.assertEqual(msg, msg2)
        dictMsg = json.loads(msg)
        expected['last_move'] = dictMsg['last_move']
        expected['piece-6'] = '1'
        expected['activePlayer'] = '0'
        self.assertEqual(expected, dictMsg)


        move_9 = self.get_move_json(p0_id, game_id, 8)
        await self.client.send(move_9, WEBSOCKET_1)
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


###############################################################
####### End of test functions, helper functions below: ########
###############################################################

    async def get_player_id(self, username, socket):
        await self.client.send(json.dumps([{'action': 'set_player_name', 'username': username}]), socket)
        msg = await self.client.receive(socket)
        dictMsg = json.loads(msg)
        return dictMsg['player_id']
    
    async def create_game(self, player_id, socket):
        await self.client.send(json.dumps([{'action': 'create_game', 'player_id': player_id}]), socket)
        msg = await self.client.receive(socket)
        dictMsg = json.loads(msg)
        return dictMsg['game_id']
    
    ## note that joining game will receive messages on all connected sockets
    ## only handling receipt of the original socket, any others may need to be accounted for as well
    async def join_game(self, player_id, game_id, socket):
        await self.client.send(json.dumps([{'action': 'join_game', 'player_id': player_id, 'game_id': game_id}]), socket)
        msg = await self.client.receive(socket)
        return json.loads(msg)
    
    async def game_for_testing(self, socket1, socket2):
        p0_id = await self.get_player_id(P0, socket1)
        p1_id = await self.get_player_id(P1, socket2)

        game_id = await self.create_game(p0_id, socket1)
        game = await self.join_game(p1_id, game_id, socket2)
        # msg = await self.client.receive(socket2)
        # game = json.loads(msg)

        return game
    
    def get_move_json(self, player_id, game_id, piece_num):
        return json.dumps([{'action': 'game_move', 'game_id': game_id, 'player_id': player_id, 'piece': 'piece-{}'.format(piece_num)}])

    
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
            # async with asyncio.timeout(5):
            return await asyncio.wait_for(self.websocket.recv(), 2)
        
        if socket == WEBSOCKET_2:
            # async with asyncio.timeout(5):
            return await asyncio.wait_for(self.websocket2.recv(), 2)
        
        if socket == WEBSOCKET_3:
            # async with asyncio.timeout(5):
            return await asyncio.wait_for(self.websocket3.recv(), 2)
    
    ## close all the websockets
    async def close(self):
        if self.websocket is not None:
            await self.websocket.close()

        if self.websocket2 is not None:
            await self.websocket2.close()

        if self.websocket3 is not None:
            await self.websocket3.close()