from slack_bolt.async_app import AsyncAck, AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient


async def ban_handler(ack: AsyncAck, client: AsyncWebClient, text: str, respond: AsyncRespond):
    await ack()
    await respond(f"Ban command received with text: {text}")
