#!/usr/bin/python3

import asyncio
import json
import re
import uuid
import jsonpatch
import websockets
from datetime import datetime
import random
from game import Player
from game import TicTacToeGame



# dictionary that stores all the game objects
games = dict()
# dictionary that stores all the player objects
players = dict()

## Constant for # of players required to start a tictactoe game. We can later refactor to use
## a variable number of required players if we add in new games at a later date
REQUIRED_PLAYERS = 2




async def client_message_handler(websocket, path):


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
            elif json_message[0]['action'] == 'set_player_name':
                await set_player_name(websocket, json_message)
            elif json_message[0]['action'] == 'create_game':
                await create_game(websocket, json_message)
            elif json_message[0]['action'] == 'join_game':
                await join_game(websocket, json_message)
            elif json_message[0]['action'] == 'spectate_game':
                await spectate_game(websocket, json_message)
            elif json_message[0]['action'] == 'get_game_state':
                await get_game_state(websocket, json_message)
            elif json_message[0]['action'] == 'rematch':
                await rematch(websocket, json_message) 
            elif json_message[0]['action'] == 'exit_game':
                await exit_game(websocket, json_message)





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

    ## new message format [{'action': 'game_move', 'game_id': 'gameuuid', 'player_id': 'UserName', 'piece': 'piece-5'}]

    try:

        game_id = message[0]['game_id']
        

        # if game['game-{}'.format(game_id)]['winner'] is not None:
        #     ## this exception will be caught, preventing the move
        #     raise Exception('Game is over.')

        ## take off the 'game-' part of game_id
        # game_id = game_id[5:]
        player_id = message[0]['player_id']
        piece = message[0]['piece']

        game = games[game_id]
        player = players[player_id]
        
        await game.game_move(player, piece)
        print(game.to_json())

    except Exception as e:
        ## send message to the client that attempted move is illegal
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

    global games


    player_id = message[0]['player_id']

    
    try:
        
        player = players[player_id]
        game = TicTacToeGame(player)
        games[game.game_id] = game

        await websocket.send(json.dumps(game.to_json()))
    except Exception as e:
        msg = json.dumps({'action': 'create_game', 'description': 'fail'})
        await websocket.send(msg)
        raise Exception("Failed to create game.")



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
    
    # get new player id and game id from the received message
    new_player = message[0]['player_id']
    # p1_name = player_names[new_player]
    game_uuid = message[0]['game_id']


    ## NOTE: as of now player_id here will really be the username

    try:

        game = games[game_uuid]
        player = players[new_player]
        game.add_player(player)

        connection = game.sockets

        if game.player_count == game.required_players:
            websockets.broadcast(connection, json.dumps(game.to_json()))
        else:
            websockets.broadcast(connection, 'player_joined')



    except Exception as e:
        msg = json.dumps({'action': 'join_game', 'description': 'fail'})
        await websocket.send(msg)
        # if exception maybe this means game id didn't exist?
        raise Exception("Failed to join game.")

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

    game_uuid = message[0]['game_id']

    try:
        game = games[game_uuid]
        game.add_spectator(websocket)
        # connection = connections['game-{}'.format(game_uuid)]
        # connection.add(websocket)

        await websocket.send(json.dumps(game.to_json()))
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

    # print("message received in set_player_name:", message)

    try:

        
        # get username from the operation that was loaded from json
        username = message[0]['username']


        player = Player(username, websocket)
        players[player.get_player_id()] = player

        stored_player = players[player.get_player_id()] 

        # send back a success message in case client wants to let player know their name change was successful
        msg = {'action': 'set_player_name', 'description': 'success', 'username': username, 'player_id': stored_player.get_player_id()}
        await websocket.send(json.dumps(msg))
    except Exception as e:
        msg = {'action': 'set_player_name', 'description': 'fail'}
        await websocket.send(json.dumps(msg))
        raise Exception("Failed to set username.")


'''
Client can request the gamestate from the server, and server will send the gamestate
back to just that client.

Input: expects message as [{'action': 'get_game_state', 'game_id': game_uuuid}]
Output: sends the gamestate back to the client, or a failure message if failed
'''
async def get_game_state(websocket, message):
    game_uuid = message[0]['game_id']

    try:
        # await websocket.send(json.dumps(game['game-{}'.format(game_uuid)]))
        await websocket.send(json.dumps(games[game_uuid].to_json()))
    except Exception as e:
        msg = {'action': 'get_game_state', 'description': 'fail'}
        await websocket.send(json.dumps(msg))
        raise Exception("Failed to get gamestate.")
    
    return True

async def rematch(websocket, message):

    game_id = message[0]['game_id']
    game = games[game_id]

    await game.rematch(websocket)

async def exit_game(websocket, message):
    game_id = message[0]['game_id']

    try:
        game = games[game_id]

        msg = {'action': 'exit_game', 'description': 'success'}

        ## send exit message to all clients so they can transition to correct screen
        websockets.broadcast(game.sockets, json.dumps(msg))

        ## remove the game from the dictionary as it is no longer in use
        games.pop(game_id)

    except Exception as e:

        fail_msg = {'action': 'exit_game', 'description': 'fail'}
        ## send a message to the requesting client if exit game failed
        await websocket.send(json.dumps(fail_msg))










async def main():
    async with websockets.serve(client_message_handler, "0.0.0.0", 8000):
        print("WebSocket server started")
        await asyncio.Future()  # Run forever

asyncio.run(main())