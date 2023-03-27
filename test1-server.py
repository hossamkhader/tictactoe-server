#!/usr/bin/python3

import asyncio
import json
import re
import uuid
import jsonpatch
import websockets 
import copy

JOIN ={}
game = dict()
game = {'game_id': None, 'mode': 'new', 'activePlayer': '0', 'winner': None, 'p0': None, 'p1': None,
                           'last_move': None, 'piece-0': '2', 'piece-1': '2', 'piece-2': '2', 'piece-3': '2',
                           'piece-4': '2', 'piece-5': '2', 'piece-6': '2', 'piece-7': '2', 'piece-8': '2'}


connected = set()

async def echo(websocket, path):
    # global game
    game_uuid = uuid.uuid4()
    connected.add(websocket)
    try:
        async for message in websocket:
            for conn in connected:
                game = json.loads(message)
                check_winner(game)
                if game['winner'] != None:
                    await conn.send(json.dumps(game))
                else:
                    if game['activePlayer'] == '0':
                        game['activePlayer'] = '1'
                    elif game['activePlayer'] == '1' :
                        game['activePlayer'] = '0'
                            
                print(json.dumps(game))
                # await websocket.send(json.dumps(game))
                await conn.send(json.dumps(game))
    finally:
        # Unregister.
        connected.remove(websocket)


def check_winner(game):
    if (game['piece-0'] != "2" and game['piece-1'] != "2" and game['piece-2'] != "2") and (game['piece-0'] == game['piece-1'] == game['piece-2']):
        game['winner'] = game['piece-0']
    if (game['piece-3'] != "2" and game['piece-4'] != "2" and game['piece-5'] != "2") and (game['piece-3'] == game['piece-4'] == game['piece-5']):
        game['winner'] = game['piece-3']
    if (game['piece-6'] != "2" and game['piece-7'] != "2" and game['piece-8'] != "2") and game['piece-6'] == game['piece-7'] == game['piece-8']:
        game['winner'] = game['piece-6']
    if (game['piece-0'] != "2" and game['piece-3'] != "2" and game['piece-6'] != "2") and game['piece-0'] == game['piece-3'] == game['piece-6']:
        game['winner'] = game['piece-0']
    if (game['piece-1'] != "2" and game['piece-4'] != "2" and game['piece-7'] != "2") and game['piece-1'] == game['piece-4'] == game['piece-7']:
        game['winner'] = game['piece-1']
    if(game['piece-2'] != "2" and game['piece-5'] != "2" and game['piece-8'] != "2") and game['piece-2'] == game['piece-5'] == game['piece-8']:
        game['winner'] = game['piece-2']
    if (game['piece-0'] != "2" and game['piece-4'] != "2" and game['piece-8'] != "2") and game['piece-0'] == game['piece-4'] == game['piece-8']:
        game['winner'] = game['piece-0']
    if (game['piece-2'] != "2" and game['piece-4'] != "2" and game['piece-6'] != "2") and game['piece-2'] == game['piece-4'] == game['piece-6']:
        game['winner'] = game['piece-2']


def reset_game(game_id):
    game_id = 'game-{}'.format(game_id)
    game['winner'] = None
    game['activePlayer'] = '0'
    game['piece-0'] = None
    game['piece-1'] = None
    game['piece-2'] = None
    game['piece-3'] = None
    game['piece-4'] = None
    game['piece-5'] = None
    game['piece-6'] = None
    game['piece-7'] = None
    game['piece-8'] = None

#start_server = websockets.serve(echo, "0.0.0.0", 8000)
#print("WebSocket server started")
#asyncio.get_event_loop().run_until_complete(start_server)
#asyncio.get_event_loop().run_forever()

async def main():
     async with websockets.serve(echo, "0.0.0.0", 8000):
         print("WebSocket server started")
         await asyncio.Future()  # Run forever

asyncio.run(main())
