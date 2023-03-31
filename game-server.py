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
game['game-0000000000'] = {'game_id': None, 'activePlayer': '0', 'winner': None, 'p0': None, 'p1': None, 'player_count': 0,
                           'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
                           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}

## Constant for # of players required to start a tictactoe game. We can later refactor to use
## a variable number of required players if we add in new games at a later date
REQUIRED_PLAYERS = 2

# stores player defined usernames with player's uuid as the key
## NOTE: based on updates discussed 3/28, not clear if we will still be using player uuids
## if not, we may not need this dict anymore
## I'm leaving for now  in case we come back to using player UUIDs since that seems like
## possibly better implementation to me
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
        print("message received by websocket:", message)
        # game_id = websocket.request_headers['game-id']
        json_message = json.loads(message)

        # if 'op' in json_message[0]:
        #     if json_message[0]['op'] == 'replace':
        #         await play_move(json_message)
        if 'action' in json_message[0]:
            if json_message[0]['action'] == 'game_move':
                await play_move(websocket, json_message)
            if json_message[0]['action'] == 'set_player_name':
                await set_player_name(websocket, json_message)
            if json_message[0]['action'] == 'create_game':
                await create_game(websocket, json_message)
            if json_message[0]['action'] == 'join_game':
                await join_game(websocket, json_message)
            if json_message[0]['action'] == 'spectate_game':
                await spectate_game(websocket, json_message)
            if json_message[0]['action'] == 'get_game_state':
                await get_game_state(websocket, json_message)


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


async def play_move(websocket, message):
    # print("message received in play_move:", operation)
    global game

    ## new message format [{'action': 'game_move', 'game_id': 'gameuuid', 'player_id': 'UserName', 'piece': 'piece-5'}]

    try:
        game_id = message[0]['game_id']
        ## take off the 'game-' part of game_id
        # game_id = game_id[5:]
        player_name = message[0]['player_id']
        piece = message[0]['piece']

        p0 = game['game-{}'.format(game_id)]['p0']
        p1 = game['game-{}'.format(game_id)]['p1']
        player_no = '-1'

        if player_name == p0:
            player_no = '0'
        elif player_name == p1:
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



        check_winner(game_id)
        websockets.broadcast(connection, json.dumps(game['game-{}'.format(game_id)]))
        try:
            patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/winner'.format(game_id), 'value': None}])
            patch.apply(game)
        except:
            reset_game(game_id)

        print(game['game-{}'.format(game_id)])

    except Exception as e:
        ## send message to the client that attempted move if it is illegal
        msg = json.dumps({'action': 'game_move', 'description': 'Illegal move'})
        await websocket.send(msg)
        print('illegal move')


'''
Creates a game for the player that requested to create a game. Assigns the game a unique identifer
which can be used for other players (or spectators) to join it. Sends a message via the websocket
containing the initial state of the game including the game id and the player id for p0 (the player
that requested). If game is successfully created, this function returns the game's UUID.

Inputs: 
websocket, the socket used by this player
operation, the message from the websocket in string form
(Note the following format is expected: [{'action': 'create_game', 'player_id': String player_name}])

Outputs:
returns UUID of the game that was created
Also sends a message via the websocket containing the initial game state

'''


async def create_game(websocket, message):
    # print("message received in create_game:", operation)

    global game
    global connections

    player_id = message[0]['player_id']
    ## NOTE: changing player_id to be the player name based on discussion from 3/28

    # get game id for the game in string form
    game_uuid = uuid.uuid4().hex
    # set the initial board state of the game

    ## old version using player UUID
    # tmp = {'game_id': 'game-{}'.format(game_uuid), 'p0': player_names[player_id], 'p1': None, 'activePlayer': '0',
    #        'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
    #        'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
    
    tmp = {'game_id': 'game-{}'.format(game_uuid), 'p0': player_id, 'p1': None, 'activePlayer': '0', 'player_count': 1,
           'winner': None, 'last_move': None, 'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}
    
    try:
        patch = jsonpatch.JsonPatch([{'op': 'add', 'path': '/game-{}'.format(game_uuid), 'value': tmp}])
        game = patch.apply(game)
        # print(json.dumps(game['game-{}'.format(game_uuid)]))
        # send the game via websocket
        await websocket.send(json.dumps(game['game-{}'.format(game_uuid)]))
    except Exception as e:
        msg = json.dumps({'action': 'create_game', 'description': 'fail'})
        await websocket.send(msg)
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
(Note the following format is expected: [{'action': 'join_game', 'player_id': String player_name, 'game_id': String game_uuid}]
also note that game_uuid expected is just the id string, don't need to include "game-" in the value.)

Outputs:
returns UUID of the game that was created
Also sends a message via the websocket containing the initial game state

'''


async def join_game(websocket, message):
    # print("message received in join_game:", message)

    global game
    global connections
    
    # get new player id and game id from the received message
    new_player = message[0]['player_id']
    game_uuid = message[0]['game_id']
    ## NOTE: as of now player_id here will really be the username

    try:
        # check if game has an empty slot for p1
        patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/p1'.format(game_uuid), 'value': None}])
        patch.apply(game)

        # add the new player id into p1 for that game
        # patch = jsonpatch.JsonPatch([{'op': 'replace', 'path': '/game-{}/p1'.format(game_uuid), 'value': player_names[new_player]}])
        patch = jsonpatch.JsonPatch([{'op': 'replace', 'path': '/game-{}/p1'.format(game_uuid), 'value': new_player}])
        game = patch.apply(game)

        player_count = game['game-{}'.format(game_uuid)]['player_count']
        player_count = player_count + 1
        patch = jsonpatch.JsonPatch([{'op': 'replace', 'path': '/game-{}/player_count'.format(game_uuid), 'value': player_count}])
        game = patch.apply(game)

        # add the new player's websocket to the set of connected websockets for that game
        connection = connections['game-{}'.format(game_uuid)]
        connection.add(websocket)

        # send the game state to the new player
        # NOTE: maybe we should think about adding something to prevent this from happening
        # at same time that player 1 makes a move? Maybe a dict with a semaphore for each game
        # that gets locked during play_move function and released when it returns?

        # websockets.broadcast(connection, json.dumps(game['game-{}'.format(game_uuid)]))
        try:
            patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/game-{}/player_count'.format(game_uuid), 'value': REQUIRED_PLAYERS}])
            patch.apply(game)
            websockets.broadcast(connection, 'game_ready')
        except:
            ## here the number of players is not at the required number yet, so don't send game_ready
            websockets.broadcast(connection, 'player_joined')


    except Exception as e:
        msg = json.dumps({'action': 'join_game', 'description': 'fail'})
        await websocket.send(msg)
        # if exception maybe this means game id didn't exist?
        raise Exception("Failed to join game.")
    
    return game_uuid

'''
Used when a player requests to spectate a game with the specified game UUID.
Adds the player's websocket to the connected websockets for that game, then
sends the spectator the current game-state. They should receive updates any
time the game-state is updated further by other functions.

Input: expected as [{'action': 'spectate_game', 'game_id', game_uuid}]
Output: websocket message with game state to spectator if successful
        or websocket message that joining game failed otherwise
'''
async def spectate_game(websocket, message):
    # print("message received in spectate_game:", message)

    global game
    global connections

    game_uuid = message[0]['game_id']

    try:
        connection = connections['game-{}'.format(game_uuid)]
        connection.add(websocket)

        await websocket.send(json.dumps(game['game-{}'.format(game_uuid)]))
    except Exception as e:
        msg = {'action': 'spectate_game', 'description': 'fail'}
        await websocket.send(json.dumps(msg))
        raise Exception("Failed to join game as spectator.")
    
    return True
    

'''
Takes a websocket message containing the username of a player requesting to set their username,
and assigns this user with a UUID and stores the username on the server with the corresponding
UUID, in the player_names dictionary. Sends a success message back via websocket to let the client
know if the name change was successful or not (success message also contains the player_id if needed
by the client). Function also returns the player uuid if successful.

Inputs:
websocket, the websocket used by this player
operation, the message containing the username
(Note the following format is expected: [{'action': 'set_player_name', 'username': String username}])

Outputs:
the player's uuid if successful
also a success/failure message is sent via websocket to the client
'''


async def set_player_name(websocket, message):
    global player_names

    # print("message received in set_player_name:", message)

    try:
        # get an id for the player (.hex converts so this can be used like string)
        player_uuid = uuid.uuid4().hex
        
        # get username from the operation that was loaded from json
        username = message[0]['username']
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


'''
Client can request the gamestate from the server, and server will send the gamestate
back to just that client.

Input: expects message as [{'action': 'get_game_state', 'game_id': game_uuuid}]
Output: sends the gamestate back to the client, or a failure message if failed
'''
async def get_game_state(websocket, message):
    game_uuid = message[0]['game_id']

    try:
        await websocket.send(json.dumps(game['game-{}'.format(game_uuid)]))
    except Exception as e:
        msg = {'action': 'get_game_state', 'description': 'fail'}
        await websocket.send(json.dumps(msg))
        raise Exception("Failed to get gamestate.")
    
    return True



async def main():
    async with websockets.serve(echo, "0.0.0.0", 8000):
        print("WebSocket server started")
        await asyncio.Future()  # Run forever

asyncio.run(main())