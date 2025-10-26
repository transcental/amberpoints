

import logging

from slack_bolt.async_app import AsyncAck, AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.utils.logging import send_heartbeat


async def shop_handler(ack: AsyncAck, client: AsyncWebClient, respond: AsyncRespond, performer: str):
    logging.info('hi')
    await ack()
    # Fire a heartbeat without relying on a `text` positional argument;
    # this handler now uses keyword args and does not expect `text`.
    await send_heartbeat('shop accessed')
    await respond('The Amber Points shop is not yet open, sorry!')
