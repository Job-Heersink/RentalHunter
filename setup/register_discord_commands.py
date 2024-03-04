import asyncio
import json
import os
from inspect import signature, Signature

import httpx

from app.discord.commands import discord_bot
from app.utils.doc_parser import parse_docstring

APP_ID = os.getenv("DISCORD_APP_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
assert APP_ID is not None
assert BOT_TOKEN is not None

URL = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}


discord_type_map = {
    str: 3,
    int: 4,
    bool: 5,
    float: 10
}





async def register_discord_commands():
    """
    Register all commands in the discord bot
    """
    async with httpx.AsyncClient() as client:
        for c_label, c_func in discord_bot.commands.items():
            doc = parse_docstring(c_func.__doc__)
            param_doc = {p["name"]: p['doc'] for p in doc["params"]}
            options = []
            sig = signature(c_func)
            params = sig.parameters
            for k, p in params.items():
                if k == "body":
                    continue

                if p.annotation == Signature.empty:
                    raise Exception(f"parameter '{k}' in command '{c_label}' has no type annotation")

                options.append({
                    "name": k,
                    "type": discord_type_map.get(p.annotation, 3),
                    "description": param_doc[k],
                    "required": p.default == Signature.empty
                })

            request = {"name": c_label,
                       "type": 1,
                       "description": f"{doc['short_description']}",
                       "options": options}
            print(f"adding {c_label}")
            print(json.dumps(request, indent=4))
            # response = await client.post(URL, headers=HEADERS, json=request)
            # print(response.status_code)
            # print(json.dumps(response.json(),indent=4))
            # assert response.status_code == 200 or response.status_code == 201


async def get_discord_commands():
    """
    Get all commands in the discord bot
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(URL, headers=HEADERS)
        print(response.status_code)
        print(json.dumps(response.json(),indent=4))


if __name__ == '__main__':
    asyncio.run(register_discord_commands())
