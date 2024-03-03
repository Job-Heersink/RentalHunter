import json
import os

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from app.sites import site_list

PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")


def authenticate_discord(event):
    signature = event['headers']['x-signature-ed25519']
    timestamp = event['headers']['x-signature-timestamp']

    # validate the interaction

    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    message = timestamp + event['body']
    verify_key.verify(message.encode(), signature=bytes.fromhex(signature))


def handle_discord(event):
    body = json.loads(event['body'])
    try:
        authenticate_discord(event)
    except BadSignatureError as e:
        return {
            'statusCode': 401,
            'body': json.dumps('invalid request signature')
        }

    t = body['type']

    if t == 1:
        return {
            'statusCode': 200,
            'body': json.dumps({'type': 1})
        }
    elif t == 2:
        return command_handler(body)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('unhandled request type')
        }


def command_handler(body):
    command = body['data']['name']

    if command == 'bleb':
        return {
            'statusCode': 200,
            'body': json.dumps({
                'type': 4,
                'data': {
                    'content': '\n'.join([s.name for s in site_list]),
                }
            })
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('unhandled command')
        }
