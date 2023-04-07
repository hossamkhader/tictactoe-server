import json
import uuid
import string


class Game():

    def __init__(self, game_type, player_id):
        # self.game_state = {}
        if self.is_valid_game_type(game_type):
            # self.game_state['game_type'] = game_type
            self.initialize_game_state(player_id)
        else:
            raise Exception("Invalid Game Type")  

    
    def is_valid_game_type(self, game_type):
        if game_type == "TicTacToe":
            return True

        ## add more game types as needed
        
        return False
    
    ## override this in the child class
    def initialize_game_state(self, player):
        return None
    
    ## override this in the child class
    def add_player(self, player):
        return None
    
    ## override this in the child class
    def game_move(self, player, move):
        return None
    
    def get_game_uuid(self):
        # get game id for the game in string form
        game_uuid = uuid.uuid4().hex

        ###################################################################################
        ###################################################################################
        ## CODE TO REDUCE SIZE OF GAME UUID FOR TESTING PURPOSES. CONSIDER REMOVING AT END:
        ###################################################################################
        game_uuid = game_uuid[:8]

        return game_uuid




class TicTacToeGame(Game):
    def __init__(self, player_id):
        super().__init__("TicTacToe", player_id)

    def initialize_game_state(self, player):
        player_id = player.player_id
        player_name = player.player_name
        game_id = self.get_game_uuid()
        self.game_id = game_id
        self.p0 = player
        self.p0.player_piece = '0'
        self.p1 = None
        self.player_count = 1
        self.active_player = '0'
        self.winner = None
        self.last_move = None
        self.board = {'piece-0': None, 'piece-1': None, 'piece-2': None, 
                      'piece-3': None, 'piece-4': None, 'piece-5': None, 
                      'piece-6': None, 'piece-7': None, 'piece-8': None}

        # self.game_state = {'game_id': game_id, 'p0': player_id, 'p1': None, 'activePlayer': '0',
        #     'player_count': 1, 'p0_name': player_name, 'p1_name': None,
        #     'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
        #     'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
    def to_json(self):
        game_state = {'game_id': self.game_id, 'p0': self.p0.player_id, 'p1': self.p1.player_id, 'p0_name': self.p0.player_name, 'p1_name': self.p1.player_name,
            'player_count': self.player_count, 'winner': self.winner, 'activePlayer': self.active_player, 'last_move': self.last_move,
            'piece-0': self.board['piece-0'], 'piece-1': self.board['piece-1'], 'piece-2': self.board['piece-2'],
            'piece-3': self.board['piece-3'], 'piece-4': self.board['piece-4'], 'piece-5': self.board['piece-5'],
            'piece-6': self.board['piece-6'], 'piece-7': self.board['piece-7'], 'piece-8': self.board['piece-8']}
        
        return game_state


        
    def add_player(self, player):
        ## if we want to add single player version just remove the following check
        if player.player_id == self.p0.player_id:
            raise ValueError("Cannot have same player for both player 1 and player 2.")
        
        self.p1 = player
        self.player_count = self.player_count + 1


    def game_move(self, player, move):
        ## not implemented yet
        pass
            



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
        if self.is_valid_player_name(player_name):
            self.player_name = player_name
    
    ## will have to handle duplicate player names in the server code
    def is_valid_player_name(self, player_name):
        if len(player_name) > self.MAX_NAME_LEN:
            raise ValueError("Greater than max name length ({} characters)".format(self.MAX_NAME_LEN))
        elif not (set(player_name) <= set(self.ALLOWED_CHARS)):
            raise ValueError("Only lowercase and uppercase letters and underscores are allowed for username.")
        
        return True
        



        


    


