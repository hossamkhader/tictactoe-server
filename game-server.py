#!/usr/bin/python3

import asyncio
import json
import re
import uuid
import jsonpatch
import websockets
from datetime import datetime

# dictionary that stores all the games' gamestate
game = dict()

# keeping this in for now since it allows the current client to test games
# once client is set up to create/join games, this test game should be removed
# NOTE: This formatting is slightly different from the formatting I used in create_game(),
# which has added fields
game['game-0000000000'] = {'activePlayer': '0', 'winner': None, 'p0': None, 'p1': None, 'last_move': None,
                           'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
                           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

# stores player defined usernames with player's uuid as the key
player_names = dict()

# stores connections for a game (set of the websockets it should broadcast to for updates)
# note: I think this can allow for easily adding spectators if we decide to, since spectators
# can simply be added to the set of websockets, and prevented from making moves
connections = dict()


async def echo(websocket, path):
    """
    2 lines below only for the test game-0000000000 to prevent this from breaking
    can be removed once we actually are making games
    """
    global connections
    connections['game-0000000000'] = {websocket}

    async for message in websocket:
        # game_id = websocket.request_headers['game-id']
        operation = json.loads(message)
        if 'op' in operation[0]:
            if operation[0]['op'] == 'replace':
                await play_move(operation)
        if 'action' in operation[0]:
            if operation[0]['action'] == 'set_player_name':
                await set_player_name(websocket, operation)
            if operation[0]['action'] == 'create_game':
                await create_game(websocket, operation)
            if operation[0]['action'] == 'join_game':
                await join_game(websocket, operation)


def check_winner(game_id):
    game_id = 'game-{}'.format(game_id)
    if game[game_id]['piece-0'] == game[game_id]['piece-1'] == game[game_id]['piece-2']:
        game[game_id]['winner'] = game[game_id]['piece-0']
    if game[game_id]['piece-3'] == game[game_id]['piece-4'] == game[game_id]['piece-5']:
        game[game_id]['winner'] = game[game_id]['piece-3']
    if game[game_id]['piece-6'] == game[game_id]['piece-7'] == game[game_id]['piece-8']:
        game[game_id]['winner'] = game[game_id]['piece-6']
    if game[game_id]['piece-0'] == game[game_id]['piece-3'] == game[game_id]['piece-6']:
        game[game_id]['winner'] = game[game_id]['piece-0']
    if game[game_id]['piece-1'] == game[game_id]['piece-4'] == game[game_id]['piece-7']:
        game[game_id]['winner'] = game[game_id]['piece-1']
    if game[game_id]['piece-2'] == game[game_id]['piece-5'] == game[game_id]['piece-8']:
        game[game_id]['winner'] = game[game_id]['piece-2']
    if game[game_id]['piece-0'] == game[game_id]['piece-4'] == game[game_id]['piece-8']:
        game[game_id]['winner'] = game[game_id]['piece-0']
    if game[game_id]['piece-2'] == game[game_id]['piece-4'] == game[game_id]['piece-6']:
        game[game_id]['winner'] = game[game_id]['piece-2']


def reset_game(game_id):
    global game
    tmp = {'activePlayer': '0', 'winner': None,
           'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
    patch = jsonpatch.JsonPatch([{'op': 'add', 'path': '/game-{}'.format(game_id), 'value': tmp}])
    game = patch.apply(game)


'''
Code for handling an operation that plays a move was moved here. This takes the operation
that was received by the websocket and applies a JSONpatch to the relevant game to make
the update to the game state.
Input: operation string from the websocket, represents the JSONpatch to apply.

Throws an Exception if the move was illegal (this could include move was for wrong player,
wrong game, incorrect grid space) 
'''


async def play_move(operation):
    global game

    try:
        game_id = re.findall('/game-(.*)/', operation[0]['path'])[0]

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
            ...

        try:
            patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/activePlayer'.format(game_id), 'value': '1'}])
            patch.apply(game)
            patch = jsonpatch.JsonPatch([{'op': 'replace', 'path': '/game-{}/activePlayer'.format(game_id), 'value': '0'}])
            game = patch.apply(game)
        except:
            ...

        check_winner(game_id)
        websockets.broadcast(connection, json.dumps(game['game-{}'.format(game_id)]))
        try:
            patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/winner'.format(game_id), 'value': None}])
            patch.apply(game)
        except:
            reset_game(game_id)

    except Exception as e:
        print('illegal move')


'''
Creates a game for the player that requested to create a game. Assigns the game a unique identifer
which can be used for other players (or spectators) to join it. Sends a message via the websocket
containing the initial state of the game including the game id and the player id for p0 (the player
that requested). If game is successfully created, this function returns the game's UUID.

Inputs: 
websocket, the socket used by this player
operation, the message from the websocket in string form
(Note the following format is expected: {'action': 'create_game', 'player_id': String player_uuid})

Outputs:
returns UUID of the game that was created
Also sends a message via the websocket containing the initial game state

'''


async def create_game(websocket, operation):
    global game
    global connections
    # EXPECTS MESSAGE IN FORMAT:
    # {'action': 'create_game', 'player_id': player_uuid}

    player_id = operation[0]['player_id']

    # get game id for the game in string form
    game_uuid = uuid.uuid4().hex
    # set the initial board state of the game
    tmp = {'p0': player_names[player_id], 'p1': None, 'activePlayer': '0', 'winner': None,
                 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
                 'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
    
    try:
        patch = jsonpatch.JsonPatch([{'op': 'add', 'path': '/game-{}'.format(game_uuid), 'value': tmp}])
        game = patch.apply(game)
        # print(json.dumps(game['game-{}'.format(game_uuid)]))
        # send the game via websocket
        await websocket.send(json.dumps(game['game-{}'.format(game_uuid)]))
    except Exception as e:
        raise Exception("Failed to create game.")

    connections['game-{}'.format(game_uuid)] = {websocket}
    return game_uuid


'''
Allows the requesting player to join a game with specified uuid. Assigns the player to the game and adds
the player's websocket to the connected websockets for that game. Sends a message via the connection
containing the initial state of the game including any info from the first player's actions, plus the id for
the 2nd player). If game is successfully created, this function returns the game's UUID.

Inputs: 
websocket, the socket used by this player
operation, the message from the websocket in string form
(Note the following format is expected: {'action': 'join_game', 'player_id': String player_uuid, 'game_id': String game_uuid}
also note that game_uuid expected is just the id string, don't need to include "game-" in the value.)

Outputs:
returns UUID of the game that was created
Also sends a message via the websocket containing the initial game state

'''


async def join_game(websocket, operation):
    global game
    global connections
    # expect join game message in format:
    # {'action': 'join_game', 'player_id': player_uuid, 'game_id': game_uuid}
    
    # get new player id and game id from the received message
    new_player = operation[0]['player_id']
    game_uuid = operation[0]['game_id']

    try:
        # check if game has an empty slot for p1
        patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/p1', 'value': None}])
        patch.apply(game)

        # add the new player id into p1 for that game
        patch = jsonpatch.JsonPatch([{'op': 'replace', 'path': '/game-{}/p1'.format(game_uuid), 'value': player_names[new_player]}])
        game = patch.apply(game)

        # add the new player's websocket to the set of connected websockets for that game
        connection = connections['game-{}'.format(game_uuid)]
        connection.add(websocket)

        # send the game state to the new player
        # NOTE: maybe we should think about adding something to prevent this from happening
        # at same time that player 1 makes a move? Maybe a dict with a semaphore for each game
        # that gets locked during play_move function and released when it returns?
        websockets.broadcast(connection, json.dumps(game['game-{}'.format(game_uuid)]))

    except Exception as e:
        # if exception maybe this means game id didn't exist?
        raise Exception("Failed to join game.")
    
    return game_uuid
    

'''
Takes a websocket message containing the username of a player requesting to set their username,
and assigns this user with a UUID and stores the username on the server with the corresponding
UUID, in the player_names dictionary. Sends a success message back via websocket to let the client
know if the name change was successful or not (success message also contains the player_id if needed
by the client). Function also returns the player uuid if successful.

Inputs:
websocket, the websocket used by this player
operation, the message containing the username
(Note the following format is expected: {'action': 'set_player_name', 'username': String username})

Outputs:
the player's uuid if successful
also a success/failure message is sent via websocket to the client
'''


async def set_player_name(websocket, operation):
    global player_names

    try:
        # get an id for the player (.hex converts so this can be used like string)
        player_uuid = uuid.uuid4().hex
        
        # get username from the operation that was loaded from json
        username = operation[0]['username']
        # add the username to the dict of player_names, with the new id as key
        player_names[player_uuid] = username

        # send back a success message in case client wants to let player know their name change was successful
        msg = {'action': 'set_player_name', 'description': 'success', 'username': username, 'player_id': player_uuid}
        await websocket.send(json.dumps(msg))
    except Exception as e:
        msg = {'action': 'set_player_name', 'description': 'fail'}
        await websocket.send(json.dumps(msg))
        raise Exception("Failed to set username.")

    return player_uuid


async def main():
    async with websockets.serve(echo, "0.0.0.0", 8000):
        print("WebSocket server started")
        await asyncio.Future()  # Run forever

asyncio.run(main())
