import json
import logging
import os
import traceback

import httpx
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DiscordBot:
    commands = {}

    def __init__(self):
        self.BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
        self.PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")

        assert self.BOT_TOKEN is not None
        assert self.PUBLIC_KEY is not None

    def authenticate_discord(self, event):
        signature = event['headers']['x-signature-ed25519']
        timestamp = event['headers']['x-signature-timestamp']

        # validate the interaction
        verify_key = VerifyKey(bytes.fromhex(self.PUBLIC_KEY))
        message = timestamp + event['body']
        verify_key.verify(message.encode(), signature=bytes.fromhex(signature))

    async def handle_message(self, event):
        body = json.loads(event['body'])
        try:
            self.authenticate_discord(event)
        except BadSignatureError as e:
            return self._response(401, 'invalid request signature')

        t = body['type']

        if t == 1:
            return self._response(200, {'type': 1})
        elif t == 2:
            logger.info("received interaction")
            logger.info(json.dumps(body, indent=4))
            command = body['data']['name']
            options = {o["name"]:o["value"] for o in body['data'].get('options', [])}
            if command not in self.commands:
                return self._response(400, 'unknown command')
            try:
                message = await self.commands[command](body=body, **options)
                return self._response(200, {'type': 4, 'data': {'content': message}})
            except Exception as e:
                traceback.print_exc()
                return self._response(500, str(e))
        else:
            return self._response(400, 'unhandled request type')

    @classmethod
    def command(cls, route_command: str):
        if route_command.startswith('/'):
            route_command = route_command[1:]

        def func_wrapper(func):
            # register the function in the routes dict
            cls.commands[route_command] = func
            return func

        return func_wrapper

    async def send_message(self, message: str, channel_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"https://discord.com/api/v10/channels/{channel_id}/messages",
                                         headers={"Authorization": f"Bot {self.BOT_TOKEN}"},
                                         json={"content": message})
            if response.status_code != 200:
                logger.error(f"failed to send message: {response.status_code} {response.text}")

    @staticmethod
    def _response(status: int, message):
        return {'statusCode': status, 'body': json.dumps(message)}
