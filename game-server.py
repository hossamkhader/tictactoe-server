#!/usr/bin/python3


import asyncio
import websockets
import json
import jsonpatch
import re
import uuid


game = dict()
game['game-0000000000'] = {'activePlayer': '0', 'winner': None,
                           'piece-0': None, 'piece-1': None, 'piece-2': None, 'piece-3': None,
                           'piece-4': None, 'piece-5': None, 'piece-6': None, 'piece-7': None, 'piece-8': None}


async def echo(websocket, path):
    global game
    game_uuid = uuid.uuid4()
    async for message in websocket:
        # game_id = websocket.request_headers['game-id']
        operation = json.loads(message)
        if operation[0]['op'] == 'replace':
            try:
                game_id = re.findall('/game-(.*)/', operation[0]['path'])[0]

                x = [{'op': 'test', 'path': operation[0]['path'], 'value': None}]
                patch = jsonpatch.JsonPatch(x)
                patch.apply(game)
                x = [{'op': 'test', 'path': '/game-{}/activePlayer'.format(game_id), 'value': operation[0]['value']}]
                patch = jsonpatch.JsonPatch(x)
                patch.apply(game)

                patch = jsonpatch.JsonPatch(operation)
                game = patch.apply(game)

                if game['game-{}'.format(game_id)]['activePlayer'] == '0':
                    game['game-{}'.format(game_id)]['activePlayer'] = '1'
                elif game['game-{}'.format(game_id)]['activePlayer'] == '1':
                    game['game-{}'.format(game_id)]['activePlayer'] = '0'
                check_winner(game_id)
                print(json.dumps(game))
                await websocket.send(json.dumps(game))
                if game['game-{}'.format(game_id)]['winner'] is not None:
                    reset_game(game_id)
            except Exception as e:
                print('illegal move')


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
    game_id = 'game-{}'.format(game_id)
    game[game_id]['winner'] = None
    game[game_id]['activePlayer'] = '0'
    game[game_id]['piece-0'] = None
    game[game_id]['piece-1'] = None
    game[game_id]['piece-2'] = None
    game[game_id]['piece-3'] = None
    game[game_id]['piece-4'] = None
    game[game_id]['piece-5'] = None
    game[game_id]['piece-6'] = None
    game[game_id]['piece-7'] = None
    game[game_id]['piece-8'] = None


async def main():
    async with websockets.serve(echo, "0.0.0.0", 8000):
        print("WebSocket server started")
        await asyncio.Future()  # Run forever

asyncio.run(main())
