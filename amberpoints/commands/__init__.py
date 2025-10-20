import logging
from slack_bolt.async_app import AsyncAck, AsyncApp, AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.commands.ban import ban_handler
from amberpoints.commands.shop import shop_handler

COMMANDS = [
    {
        "name": "ban",
        "admin": True,
        "description": "Ban a user from earning or using Amber Points",
        "function": ban_handler,
        "parameters": [
            {
                "name": "user",
                "type": "user",
                "description": "The user to ban",
                "required": True
            },
            {
                "name": "reason",
                "type": "string",
                "description": "The reason for the ban",
                "default": "No reason provided"
            }
        ]
    },
    {
        "name": "donate",
        "admin": False,
        "description": "Donate Amber Points to another user",
        "function": None,
        "parameters": [
            {
                "name": "user",
                "type": "user",
                "description": "The user to donate points to",
                "required": True
            },
            {
                "name": "amount",
                "type": "integer",
                "description": "The amount of points to donate",
                "default": 1
            }
        ]
    },
    {
        "name": "give",
        "admin": True,
        "description": "Give out Amber Points",
        "function": None,
        "parameters": [
            {
                "name": "user",
                "type": "user",
                "description": "The user to give points to",
                "required": True
            },
            {
                "name": "amount",
                "type": "integer",
                "description": "The amount of points to give",
                "default": 1
            }
        ]
    },
    {
        "name": "subtract",
        "admin": True,
        "description": "Subtract Amber Points from a user",
        "function": None,
        "parameters": [
            {
                "name": "user",
                "type": "user",
                "description": "The user to subtract points from",
                "required": True
            },
            {
                "name": "amount",
                "type": "integer",
                "description": "The amount of points to subtract",
                "default": 1
            }
        ]
    },
    {
        "name": "leaderboard",
        "admin": False,
        "description": "Show the Amber Points leaderboard",
        "function": None,
        "parameters": []
    },
    {
        "name": "shop",
        "admin": False,
        "description": "Access the Amber Points shop",
        "function": shop_handler,
        "parameters": []
    },
]

def register_commands(app: AsyncApp):
    help = "Available commands:\n"
    for cmd in COMMANDS:
        params = " ".join(
            [
                f"<{param['name']}>" if param.get("required", False) else f"[{param['name']}]"
                for param in cmd["parameters"]
            ]
        )
        help += f"- `/amberpoint {cmd['name']}{f" {params}" if params else ""}`: {cmd['description']}\n"
        
    @app.command("/amberpoint")
    async def amberpoint_command(ack: AsyncAck, client: AsyncWebClient, respond: AsyncRespond, command: dict):
        await ack()
        text = command.get("text", "")
        
        command = text.split()[0] if text else "" # type: ignore (text is always... text)
        for cmd in COMMANDS:
            if cmd["name"] == command:
                if cmd["function"]:
                    # check the parameters
                    if cmd["parameters"]:
                        args = text.split()[1:]
                        if len(args) < len([p for p in cmd["parameters"] if p.get("required", False)]):
                            await respond(f"Missing required parameters for `{command}` command.")
                            return
                    await cmd["function"](ack=ack, client=client, respond=respond, text=text)
                else:
                    await respond(f"The `{command}` command is not yet implemented.")
                return
        await respond(help)
