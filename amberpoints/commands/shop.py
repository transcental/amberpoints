

import logging

from slack_bolt.async_app import AsyncAck, AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.utils.logging import send_heartbeat


async def shop_handler(ack: AsyncAck, client: AsyncWebClient, text: str, respond: AsyncRespond):
    logging.info('hi')
    await ack()
    await send_heartbeat(str(text))
    await respond(f'The Amber Points shop is not yet open, sorry!')