from slack_bolt.async_app import AsyncAck
from slack_bolt.async_app import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.tables import Person
from amberpoints.utils.ledger import create_ledger_entry


async def subtract_handler(
    ack: AsyncAck,
    client: AsyncWebClient,
    respond: AsyncRespond,
    performer: str,
    user: str,
    amount: int = 1,
    reason: str = "",
):
    await ack()

    # Get or create the person
    person = await Person.objects().where(Person.slack_id == user).first()

    if not person:
        # Create new person with negative points
        await Person.insert(
            Person(slack_id=user, points=-amount, admin=False, banned=False)
        )
        await respond(
            f"Subtracted {amount} points from <@{user}>. They now have {-amount} points."
        )
        # Audit log
        await create_ledger_entry(
            performer=performer,
            target_user=user,
            action="subtract",
            amount=amount,
            reason=reason,
        )
    else:
        # Subtract from existing
        new_points = person.points - amount
        await Person.update({Person.points: new_points}).where(Person.slack_id == user)
        await respond(
            f"Subtracted {amount} points from <@{user}>. They now have {new_points} points."
        )
        # Audit log
        await create_ledger_entry(
            performer=performer,
            target_user=user,
            action="subtract",
            amount=amount,
            reason=reason,
        )
    dm_text = (
        f"{amount} points have been subtracted from your account by <@{performer}>!"
    )
    if reason:
        dm_text += f" Reason: {reason}"
    await client.chat_postMessage(channel=user, text=dm_text)
