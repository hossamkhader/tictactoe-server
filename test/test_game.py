from game import TicTacToeGame
from game import Player
from game import Game

import unittest

class TestGame(unittest.TestCase):

    def setup(self):
        pass

    def test_create_player(self):
        P0 = 'TestName'
        p0 = Player(P0, "ws")
        self.assertIsNotNone(p0.player_id)
        self.assertEqual(P0, p0.player_name)
        self.assertIsNone(p0.player_piece)
        self.assertEqual('ws', p0.ws)

    def test_tictactoe(self):
        P0 = 'Tester1'
        p0 = Player(P0, "ws1")

        game = TicTacToeGame(p0)
        
        self.assertEqual(p0, game.p0)
        self.assertEqual(P0, game.p0.player_name)
        self.assertEqual(p0.player_id, game.p0.player_id)
        self.assertEqual('0', game.active_player)
        self.assertEqual(1, game.player_count)
        self.assertIsNotNone(game.game_id)
        self.assertIsNone(game.p1)
        self.assertIsNone(game.winner)
        self.assertIsNone(game.last_move)

        expected = {'piece-0': None, 'piece-1': None, 'piece-2': None, 
                      'piece-3': None, 'piece-4': None, 'piece-5': None, 
                      'piece-6': None, 'piece-7': None, 'piece-8': None}

        self.assertEqual(expected ,game.board)


    def test_add_player_tictactoe(self):
        P0 = 'Tester1'
        P1 = 'Tester2'
        p0 = Player(P0, "ws1")
        p1 = Player(P1, "ws2")

        game = TicTacToeGame(p0)
        game.add_player(p1)

        self.assertEqual(p0, game.p0)
        self.assertEqual(P0, game.p0.player_name)
        self.assertEqual(p0.player_id, game.p0.player_id)
        self.assertEqual(p1, game.p1)
        self.assertEqual(p1.player_id, game.p1.player_id)
        self.assertEqual(p1.player_name, game.p1.player_name)
        self.assertEqual('0', game.active_player)
        self.assertEqual(2, game.player_count)
        self.assertIsNotNone(game.game_id)
        self.assertIsNone(game.winner)
        self.assertIsNone(game.last_move)

        expected = {'piece-0': None, 'piece-1': None, 'piece-2': None, 
                      'piece-3': None, 'piece-4': None, 'piece-5': None, 
                      'piece-6': None, 'piece-7': None, 'piece-8': None}

        self.assertEqual(expected ,game.board)

    def test_to_json(self):
        P0 = 'Tester1'
        P1 = 'Tester2'
        p0 = Player(P0, "ws1")
        p1 = Player(P1, "ws2")

        game = TicTacToeGame(p0)
        game.add_player(p1)

        expected = {'game_id': game.game_id, 'p0': p0.player_id, 'p1': p1.player_id,
            'p0_name': p0.player_name, 'p1_name': p1.player_name, 'activePlayer': '0', 'player_count': 2,
            'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
            'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
        
        self.assertEqual(expected, game.to_json())


