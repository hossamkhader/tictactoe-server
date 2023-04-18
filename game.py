import json
import uuid
import string
import jsonpatch
from datetime import datetime
import websockets
import asyncio
import random




class Game():

    def __init__(self, game_type, player):
        self.sockets = set()
        # self.game_state = {}
        if self.is_valid_game_type(game_type):
            # self.game_state['game_type'] = game_type
            self.initialize_game_state(player)
        else:
            raise Exception("Invalid Game Type")  

    
    def is_valid_game_type(self, game_type):
        if game_type == "TicTacToe":
            return True

        ## add more game types as needed
        
        return False
    
    def add_spectator(self, websocket):
        self.sockets.add(websocket)

    
    ## override this in the child class
    def initialize_game_state(self, player):
        raise NotImplementedError
    
    ## override this in the child class
    def add_player(self, player):
        raise NotImplementedError
    
    ## override this in the child class
    def game_move(self, player, move):
        raise NotImplementedError
    
    def set_game_uuid(self):
        # get game id for the game in string form
        game_uuid = uuid.uuid4().hex

        ###################################################################################
        ###################################################################################
        ## CODE TO REDUCE SIZE OF GAME UUID FOR TESTING PURPOSES. CONSIDER REMOVING AT END:
        ###################################################################################
        game_uuid = game_uuid[:8]

        return game_uuid




class TicTacToeGame(Game):
    def __init__(self, player):
        super().__init__("TicTacToe", player)

    def initialize_game_state(self, player):
        player_id = player.player_id
        player_name = player.player_name
        game_id = self.set_game_uuid()
        self.game_id = game_id
        self.p0 = player
        self.p0.player_piece = '0'
        self.p1 = None
        self.player_count = 1
        self.required_players = 2
        self.active_player = '0'
        self.winner = None
        self.last_move = None
        self.board = {'piece-0': None, 'piece-1': None, 'piece-2': None, 
                      'piece-3': None, 'piece-4': None, 'piece-5': None, 
                      'piece-6': None, 'piece-7': None, 'piece-8': None}
        self.sockets.add(self.p0.get_ws())
        self.timer = None

        # self.game_state = {'game_id': game_id, 'p0': player_id, 'p1': None, 'activePlayer': '0',
        #     'player_count': 1, 'p0_name': player_name, 'p1_name': None,
        #     'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
        #     'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
    def to_json(self):
        p0 = None
        p1 = None
        p0_name = None
        p1_name = None
        if self.p0 != None:
            p0 = self.p0.player_id
            p0_name = self.p0.player_name
        if self.p1 != None:
            p1 = self.p1.player_id
            p1_name = self.p1.player_name

        game_state = {'game_id': self.game_id, 'p0': p0, 'p1': p1, 'p0_name': p0_name, 'p1_name': p1_name,
            'player_count': self.player_count, 'winner': self.winner, 'activePlayer': self.active_player, 'last_move': self.last_move,
            'piece-0': self.board['piece-0'], 'piece-1': self.board['piece-1'], 'piece-2': self.board['piece-2'],
            'piece-3': self.board['piece-3'], 'piece-4': self.board['piece-4'], 'piece-5': self.board['piece-5'],
            'piece-6': self.board['piece-6'], 'piece-7': self.board['piece-7'], 'piece-8': self.board['piece-8']}
        
        return game_state
    
    def from_json(self, game_state):
        
        self.winner = game_state['winner']
        self.active_player = game_state['activePlayer']
        self.last_move = game_state['last_move']
        self.board['piece-0'] = game_state['piece-0']
        self.board['piece-1'] = game_state['piece-1']
        self.board['piece-2'] = game_state['piece-2']
        self.board['piece-3'] = game_state['piece-3']
        self.board['piece-4'] = game_state['piece-4']
        self.board['piece-5'] = game_state['piece-5']
        self.board['piece-6'] = game_state['piece-6']
        self.board['piece-7'] = game_state['piece-7']
        self.board['piece-8'] = game_state['piece-8']



        
    def add_player(self, player):
        if self.p1 is not None:
            raise ValueError("Game already has two players.")
        ## if we want to add single player version just remove the following check
        if player.player_id == self.p0.player_id:
            raise ValueError("Cannot have same player for both player 1 and player 2.")
        
        self.p1 = player
        self.player_count = self.player_count + 1

        self.sockets.add(self.p1.get_ws())


    async def game_move(self, player, move):

        ## note mismatch in naming here
        player_id = player.get_player_id()
        game_id = self.game_id
        piece = move

        game = dict()
        connections = dict()
        timers = dict()

        game['game-{}'.format(game_id)] = self.to_json()
        
        connections['game-{}'.format(game_id)] = self.sockets

        timers['game-{}'.format(game_id)] = self.timer

        websocket = player.get_ws()




        # game_id = message[0]['game_id']

        if game['game-{}'.format(game_id)]['winner'] is not None:
            ## this exception will be caught, preventing the move
            raise Exception('Game is over.')
        if game['game-{}'.format(game_id)]['player_count'] != 2:
            raise Exception('Waiting for 2nd player.')

        ## take off the 'game-' part of game_id
        # game_id = game_id[5:]
        # player_id = message[0]['player_id']
        # piece = message[0]['piece']

        p0 = game['game-{}'.format(game_id)]['p0']
        p1 = game['game-{}'.format(game_id)]['p1']
        player_no = '-1'

        if player_id == p0:
            player_no = '0'
        elif player_id == p1:
            player_no = '1'
        

        # game_id = re.findall('/game-(.*)/', operation[0]['path'])[0]

        operation = []
        operation.append({'op': 'replace', 'path': '/game-{}/{}'.format(game_id, piece), 'value': player_no})

        # added this code to get the set of websockets for this game
        connection = connections['game-{}'.format(game_id)]

        x = [{'op': 'test', 'path': operation[0]['path'], 'value': None}]
        patch = jsonpatch.JsonPatch(x)
        patch.apply(game)
        x = [{'op': 'test', 'path': '/game-{}/activePlayer'.format(game_id), 'value': operation[0]['value']}]
        patch = jsonpatch.JsonPatch(x)
        patch.apply(game)

        patch = jsonpatch.JsonPatch(operation)
        game = patch.apply(game)

        ts = datetime.now().timestamp()
        patch = jsonpatch.JsonPatch([{'op': 'replace', 'path': '/game-{}/last_move'.format(game_id), 'value': str(ts)}])
        game = patch.apply(game)

        try:
            patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/activePlayer'.format(game_id), 'value': '0'}])
            patch.apply(game)
            patch = jsonpatch.JsonPatch([{'op': 'replace', 'path': '/game-{}/activePlayer'.format(game_id), 'value': '1'}])
            game = patch.apply(game)
        except:
            ## this was just switching it back to 0 so did not work, so putting it inside the except block of the
            ## previous patch instead
            try:
                patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/activePlayer'.format(game_id), 'value': '1'}])
                patch.apply(game)
                patch = jsonpatch.JsonPatch([{'op': 'replace', 'path': '/game-{}/activePlayer'.format(game_id), 'value': '0'}])
                game = patch.apply(game)
            except:
                ...

        ## check if a timer exists for this game
        # if 'game-{}'.format(game_id) in timers.keys():
        #     ## if the timer was not set to None, then cancel it
        #     ## since a move was received in time
        #     if timers['game-{}'.format(game_id)] is not None:
        #         (timers['game-{}'.format(game_id)]).cancel()

        if self.timer is not None:
            self.timer.cancel()
        
        
        self.from_json(game['game-{}'.format(game_id)])
        self.check_winner()
        game['game-{}'.format(game_id)] = self.to_json()
        ## start a timer for the next move if no winner yet
        try:
            patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/winner'.format(game_id), 'value': None}])
            patch.apply(game)
            # timers['game-{}'.format(game_id)] = asyncio.create_task(timer(game_id, player_id))
            self.timer = asyncio.create_task(self.set_timer(player_id))
        except:
            ...

        websockets.broadcast(connection, json.dumps(game['game-{}'.format(game_id)]))

        ## moved reset game logic to rematch function



        print(game['game-{}'.format(game_id)])
        return 

        # except Exception as e:
        #     ## send message to the client that attempted move is illegal
        #     msg = json.dumps({'action': 'game_move', 'description': 'Illegal move'})
        #     await websocket.send(msg)
        #     print('illegal move')

    def check_winner(self):
        game_id = self.game_id
        game = dict()
        
        game_id = self.game_id

        game[game_id] = self.to_json()

        
        if game[game_id]['piece-0'] != None and (game[game_id]['piece-0'] == game[game_id]['piece-1'] == game[game_id]['piece-2']):
            game[game_id]['winner'] = game[game_id]['piece-0']
        elif game[game_id]['piece-3'] != None and (game[game_id]['piece-3'] == game[game_id]['piece-4'] == game[game_id]['piece-5']):
            game[game_id]['winner'] = game[game_id]['piece-3']
        elif game[game_id]['piece-6'] != None and (game[game_id]['piece-6'] == game[game_id]['piece-7'] == game[game_id]['piece-8']):
            game[game_id]['winner'] = game[game_id]['piece-6']
        elif game[game_id]['piece-0'] != None and (game[game_id]['piece-0'] == game[game_id]['piece-3'] == game[game_id]['piece-6']):
            game[game_id]['winner'] = game[game_id]['piece-0']
        elif game[game_id]['piece-1'] != None and (game[game_id]['piece-1'] == game[game_id]['piece-4'] == game[game_id]['piece-7']):
            game[game_id]['winner'] = game[game_id]['piece-1']
        elif  game[game_id]['piece-2'] != None and (game[game_id]['piece-2'] == game[game_id]['piece-5'] == game[game_id]['piece-8']):
            game[game_id]['winner'] = game[game_id]['piece-2']
        elif game[game_id]['piece-0'] != None and (game[game_id]['piece-0'] == game[game_id]['piece-4'] == game[game_id]['piece-8']):
            game[game_id]['winner'] = game[game_id]['piece-0']
        elif game[game_id]['piece-2'] != None and (game[game_id]['piece-2'] == game[game_id]['piece-4'] == game[game_id]['piece-6']):
            game[game_id]['winner'] = game[game_id]['piece-2']

        if game[game_id]['winner'] is None:
            draw = True
            for i in range(0, 9):
                if game[game_id]['piece-{}'.format(i)] is None:
                    draw = False
            
            if draw:
                game[game_id]['winner'] = 'draw'

        self.from_json(game[game_id])

    '''
    Timer task to use by play move. Picks a move at random if the timer expires.
    This task will be cancelled if a legal move is selected before the timer expires.
    The calling method has to handle cancellation of the task.
    '''
    async def set_timer(self, player_id):
            ## sleep for 15 seconds
        try:
            for i in range(1, 16):
                await asyncio.sleep(1)
                print("game-{}".format(self.game_id), "timer:", i)

            print("timer expired")

            if self.p0.get_player_id() == player_id:
                opponent = self.p1
            else:
                opponent = self.p0

            random_idx = random.randrange(9)
            while(self.board['piece-{}'.format(random_idx)] is not None):
                random_idx = random.randrange(9)
            
            # message = [{'action': 'game_move', 'game_id': game_id, 'player_id': opponent_id, 'piece': 'piece-{}'.format(random_idx)}]
            move = random_idx
            await self.game_move(opponent, 'piece-{}'.format(move))
            

            # timers['game-{}'.format(game_id)] = None
        except asyncio.CancelledError:
            print("timer canceled")

    async def rematch(self, websocket):
        # game_id = message[0]['game_id']

        ## if count is 2 then first player to request rematch
        if self.player_count == 2:
            await self.reset_game()
            await websocket.send(json.dumps(self.to_json()))
        ## if count is 1 then second player to request rematch
        elif self.player_count == 1:
            self.player_count = self.player_count + 1
            websockets.broadcast(self.sockets, json.dumps(self.to_json()))
        else:
            ## some issue with rematch occurred if here
            await websocket.send(json.dumps({'action': 'rematch', 'description': 'fail'}))  

        # if game['game-{}'.format(game_id)]['player_count'] == 2:
        #     ## if count is 2 then this is first player to request rematch
        #     reset_game(game_id)
        #     await websocket.send(json.dumps(game['game-{}'.format(game_id)]))
        # elif game['game-{}'.format(game_id)]['player_count'] == 1:
        #     ## if count is 1 then this is second player to request rematch
        #     game['game-{}'.format(game_id)]['player_count'] = 2
        #     connection = connections['game-{}'.format(game_id)]
        #     websockets.broadcast(connection, json.dumps(game['game-{}'.format(game_id)]))
        # else:
        #     ## some issue with rematch occurred if here
        #     await websocket.send(json.dumps({'action': 'rematch', 'description': 'fail'}))  

    async def reset_game(self):
        self.player_count = 1
        self.active_player = '0'
        self.winner = None
        self.last_move = None
        self.board = {'piece-0': None, 'piece-1': None, 'piece-2': None, 
                      'piece-3': None, 'piece-4': None, 'piece-5': None, 
                      'piece-6': None, 'piece-7': None, 'piece-8': None}
        self.sockets.add(self.p0.get_ws())
        self.timer = None
    


                



class Player():

    MAX_NAME_LEN = 20

    ALLOWED_CHARS = set(string.ascii_letters + string.digits + '_')

    ## raises ValueError if player_name is invalid
    def __init__(self, player_name, websocket):
        self.player_name = None
        self.set_player_name(player_name)
        self.player_id = uuid.uuid4().hex
        self.ws = websocket
        self.player_piece = None

    def set_player_name(self, player_name):
        # taking this out for now since we had not specified any name requirements
        # if self.is_valid_player_name(player_name):
        #     self.player_name = player_name

        self.player_name = player_name
    
    ## will have to handle duplicate player names in the server code
    def is_valid_player_name(self, player_name):
        if len(player_name) > self.MAX_NAME_LEN:
            raise ValueError("Greater than max name length ({} characters)".format(self.MAX_NAME_LEN))
        elif not (set(player_name) <= set(self.ALLOWED_CHARS)):
            raise ValueError("Only lowercase and uppercase letters and underscores are allowed for username.")
        
        return True
    
    def get_player_name(self):
        return self.player_name
    
    def get_player_id(self):
        return self.player_id
    
    def get_ws(self):
        return self.ws
        



        


    


