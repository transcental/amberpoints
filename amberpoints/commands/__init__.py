import logging
import re
import shlex

from slack_bolt.async_app import AsyncAck
from slack_bolt.async_app import AsyncApp
from slack_bolt.async_app import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.commands.ban import ban_handler
from amberpoints.commands.donate import donate_handler
from amberpoints.commands.give import give_handler
from amberpoints.commands.leaderboard import leaderboard_handler
from amberpoints.commands.shop import shop_handler
from amberpoints.commands.subtract import subtract_handler
from amberpoints.config import config
from amberpoints.tables import Person


def _normalize_user_token(token: str) -> str | None:
    """Extract a Slack user id from common mention forms or accept raw ids.

    Supported forms:
    - <@U123ABC|username>
    - <@U123ABC>
    - U123ABC

    Returns the extracted user id (e.g. 'U123ABC') or None if not recognized.
    """
    if not isinstance(token, str):
        return None

    # Match <@U123ABC|name> or <@U123ABC>
    m = re.match(r"^<@([UW][A-Z0-9]+)(?:\|[^>]+)?>$", token)
    if m:
        return m.group(1)

    # Plain id like U123ABC or W123ABC
    if re.match(r"^[UW][A-Z0-9]+$", token):
        return token

    return None


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
                "required": True,
            },
            {
                "name": "reason",
                "type": "string",
                "description": "The reason for the ban",
                "default": "No reason provided",
            },
        ],
    },
    {
        "name": "donate",
        "admin": False,
        "description": "Donate Amber Points to another user",
        "function": donate_handler,
        "parameters": [
            {
                "name": "sender",
                "type": "current_user",
                "description": "The user sending the donation",
                "required": True,
            },
            {
                "name": "user",
                "type": "user",
                "description": "The user to donate points to",
                "required": True,
            },
            {
                "name": "amount",
                "type": "integer",
                "description": "The amount of points to donate",
                "default": 1,
            },
            {
                "name": "reason",
                "type": "string",
                "description": "The reason for the donation",
                "default": "",
            },
        ],
    },
    {
        "name": "give",
        "admin": True,
        "description": "Give out Amber Points",
        "function": give_handler,
        "parameters": [
            {
                "name": "user",
                "type": "user",
                "description": "The user to give points to",
                "required": True,
            },
            {
                "name": "amount",
                "type": "integer",
                "description": "The amount of points to give",
                "default": 1,
            },
            {
                "name": "reason",
                "type": "string",
                "description": "The reason for giving points",
                "default": "",
            },
        ],
    },
    {
        "name": "subtract",
        "admin": True,
        "description": "Subtract Amber Points from a user",
        "function": subtract_handler,
        "parameters": [
            {
                "name": "user",
                "type": "user",
                "description": "The user to subtract points from",
                "required": True,
            },
            {
                "name": "amount",
                "type": "integer",
                "description": "The amount of points to subtract",
                "default": 1,
            },
            {
                "name": "reason",
                "type": "string",
                "description": "The reason for subtracting points",
                "default": "",
            },
        ],
    },
    {
        "name": "leaderboard",
        "admin": False,
        "description": "Show the Amber Points leaderboard",
        "function": leaderboard_handler,
        "parameters": [],
    },
    {
        "name": "shop",
        "admin": False,
        "description": "Access the Amber Points shop",
        "function": shop_handler,
        "parameters": [],
    },
]


def register_commands(app: AsyncApp):
    help = "Available commands:\n"
    for cmd in COMMANDS:
        parameters = cmd.get("parameters", [])
        if "current_user" in [p.get("type") for p in parameters]:
            # Exclude current_user from help display
            cmd["parameters"] = [
                p for p in parameters if p.get("type") != "current_user"
            ]
        params = " ".join(
            [
                f"<{param['name']}>"
                if param.get("required", False)
                else f"[{param['name']}]"
                for param in parameters
            ]
        )

        help += (
            f"- `/amberpoint {cmd['name']}{f' {params}' if params else ''}`: {cmd['description']}\n"
            if not cmd.get("admin")
            else f"- `/amberpoint {cmd['name']}{f' {params}' if params else ''}`: {cmd['description']} (admin only)\n"
        )

    @app.command(
        "/amberpoint" if config.environment == "production" else "/dev-amberpoint"
    )
    async def amberpoint_command(
        ack: AsyncAck, client: AsyncWebClient, respond: AsyncRespond, command: dict
    ):
        await ack()
        user_id = command.get("user_id")
        raw_text = command.get("text", "")

        # Check if user is banned
        person = await Person.objects().where(Person.slack_id == user_id).first()
        if person and person.banned:
            await respond(
                f"You are banned from using Amber Points. Reason: {person.ban_reason}"
            )
            return

        # Parse the incoming text with shlex so quoted arguments are preserved and escape sequences are allowed.
        try:
            tokens = shlex.split(raw_text, posix=True) if raw_text else []
        except ValueError as e:
            await respond(f"Could not parse command text: {e}")
            return

        command_name = tokens[0] if tokens else ""  # type: ignore (text is always... text)
        for cmd in COMMANDS:
            if cmd["name"] == command_name:
                if cmd.get("admin") and not user_id == "U054VC2KM9P":
                    await respond("You do not have permission to use this command.")
                    return
                if cmd["function"]:
                    parsed = tokens[1:]
                    params = cmd.get("parameters", [])
                    args_tokens = parsed
                    logging.debug(
                        f"Command '{command_name}' invoked by user '{user_id}' with raw text: {raw_text}"
                    )
                    logging.debug(f"Parsed tokens: {tokens}")

                    # If the last declared parameter is a 'string', join the remainder into one argument.
                    if params and params[-1].get("type") == "string":
                        num_non_string = max(0, len(params) - 1)
                        first_parts = args_tokens[:num_non_string]
                        remaining = args_tokens[num_non_string:]
                        last_string = (
                            " ".join(remaining)
                            if remaining
                            else params[-1].get("default", "")
                        )
                        # Decode escape sequences like \n, \t inside the joined string
                        try:
                            import codecs

                            last_string = codecs.decode(last_string, "unicode_escape")
                        except Exception:
                            # If decode fails, fall back to the raw joined string
                            pass
                        args_tokens = first_parts + [last_string]
                        logging.debug(
                            f"Adjusted args tokens for trailing string parameter: {args_tokens}"
                        )

                    # Build kwargs mapping parameter names to typed/validated values
                    import inspect
                    import re
                    import codecs

                    kwargs_for_params = {}
                    errors = []

                    if "current_user" in [p.get("type") for p in params]:
                        pname = next(
                            p.get("name")
                            for p in params
                            if p.get("type") == "current_user"
                        )
                        kwargs_for_params[pname] = user_id
                        params.remove(
                            next(p for p in params if p.get("type") == "current_user")
                        )

                    # Special handling for commands with required user, optional int, optional string
                    if (
                        len(params) >= 3
                        and params[0].get("required", False)
                        and not params[1].get("required", False)
                        and params[1].get("type") == "integer"
                        and not params[2].get("required", False)
                        and params[2].get("type") == "string"
                    ):
                        if len(parsed) > 0:
                            user_str = parsed[0]
                            if len(parsed) > 1:
                                try:
                                    int(parsed[1])
                                    amount_str = parsed[1]
                                    reason_str = " ".join(parsed[2:])
                                except ValueError:
                                    amount_str = ""
                                    reason_str = " ".join(parsed[1:])
                            else:
                                amount_str = ""
                                reason_str = ""
                            args_tokens = [user_str, amount_str, reason_str]
                        else:
                            args_tokens = []
                    # Special handling for commands with optional user, optional int
                    elif (
                        len(params) >= 2
                        and not params[0].get("required", False)
                        and params[0].get("type") == "user"
                        and not params[1].get("required", False)
                        and params[1].get("type") == "integer"
                    ):
                        if len(parsed) > 0:
                            try:
                                int(parsed[0])
                                # First arg is int, assign to amount, second to user if present
                                amount_str = parsed[0]
                                user_str = parsed[1] if len(parsed) > 1 else ""
                            except ValueError:
                                # First arg not int, assign to user, second to amount if int
                                user_str = parsed[0]
                                if len(parsed) > 1:
                                    try:
                                        int(parsed[1])
                                        amount_str = parsed[1]
                                    except ValueError:
                                        amount_str = ""
                                else:
                                    amount_str = ""
                        else:
                            user_str = ""
                            amount_str = ""
                        args_tokens = [user_str, amount_str]

                    for idx, param in enumerate(params):
                        pname = param.get("name")
                        ptype = param.get("type", "string")
                        default = param.get("default", None)

                        logging.debug(
                            f"Processing parameter '{pname}' of type '{ptype}' at position {idx}"
                        )

                        if idx < len(args_tokens):
                            raw_val = args_tokens[idx]
                        else:
                            raw_val = default

                        logging.debug(f"Raw value for parameter '{pname}': {raw_val}")

                        # Normalize missing values
                        if raw_val is None or raw_val == "":
                            value = None
                        else:
                            # Type validation & coercion
                            if ptype == "integer":
                                try:
                                    value = int(raw_val)
                                except Exception:
                                    errors.append(
                                        f"Parameter '{pname}' must be an integer."
                                    )
                                    continue
                            elif ptype == "user":
                                # Normalize Slack mention formats like <@U123ABC|name> to the user id and validate.
                                if not isinstance(raw_val, str):
                                    errors.append(
                                        f"Parameter '{pname}' must be a user mention or ID (e.g. <@U123ABC|name>)."
                                    )
                                    continue
                                norm = _normalize_user_token(raw_val)
                                logging.debug(
                                    f"Normalized user token '{raw_val}' to '{norm}'"
                                )
                                # After normalization, ensure we have a Slack-style user id (starts with U or W)
                                if re.match(r"^[UW][A-Z0-9]+$", norm):
                                    value = norm
                                else:
                                    errors.append(
                                        f"Parameter '{pname}' must be a user mention or ID (e.g. <@U123ABC|name>)."
                                    )
                                    continue
                            else:
                                # string or unknown types => treat as string and decode escape sequences
                                if isinstance(raw_val, str):
                                    try:
                                        value = codecs.decode(raw_val, "unicode_escape")
                                    except Exception:
                                        value = raw_val
                                else:
                                    value = str(raw_val)

                        if value is None:
                            value = param.get("default")
                        kwargs_for_params[pname] = value

                    if errors:
                        await respond("; ".join(errors))
                        return

                    # Prepare the invocation kwargs for the handler.
                    handler = cmd["function"]
                    sig = inspect.signature(handler)
                    handler_kwargs = {
                        "ack": ack,
                        "client": client,
                        "respond": respond,
                        "performer": user_id,
                    }

                    # Backwards compatibility:
                    # If the handler accepts a parameter named 'text', pass the original raw_text.
                    # Otherwise, pass only the named parameters that the handler declares.
                    if "text" in sig.parameters:
                        handler_kwargs["text"] = raw_text
                    else:
                        for pname, pvalue in kwargs_for_params.items():
                            if pname in sig.parameters:
                                handler_kwargs[pname] = pvalue

                    await handler(**handler_kwargs)
                else:
                    await respond(
                        f"The `{command_name}` command is not yet implemented."
                    )
                return
        await respond(help)
