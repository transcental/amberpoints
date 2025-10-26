from slack_bolt.async_app import AsyncAck
from slack_bolt.async_app import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.tables import AuditLog
from amberpoints.tables import Person


async def donate_handler(
    ack: AsyncAck,
    client: AsyncWebClient,
    respond: AsyncRespond,
    performer: str,
    user: str,
    amount: int = 1,
):
    await ack()

    if performer == user:
        await respond("You cannot donate to yourself.")
        return
    if not user:
        await respond("You must specify a user to donate to.")
        return
    if amount <= 0:
        await respond("You must donate a positive amount of points.")
        return

    # Get performer
    performer_person = (
        await Person.objects().where(Person.slack_id == performer).first()
    )
    if not performer_person:
        await respond("You don't have an account yet. Earn some points first!")
        return

    if performer_person.points < amount:
        await respond(
            f"You don't have enough points. You have {performer_person.points}."
        )
        return

    # Get or create recipient
    recipient = await Person.objects().where(Person.slack_id == user).first()
    if not recipient:
        recipient = Person(slack_id=user, points=amount, admin=False, banned=False)
        await Person.insert(recipient)
        new_performer_points = performer_person.points - amount
        await Person.update({Person.points: new_performer_points}).where(
            Person.slack_id == performer
        )
        await respond(
            f"Donated {amount} points to <@{user}>. You now have {new_performer_points} points. They now have {amount} points."
        )
        # Audit log
        await AuditLog.insert(
            AuditLog(
                user_id=performer, action="donate", target_user=user, amount=amount
            )
        )
    else:
        new_performer_points = performer_person.points - amount
        new_recipient_points = recipient.points + amount
        await Person.update({Person.points: new_performer_points}).where(
            Person.slack_id == performer
        )
        await Person.update({Person.points: new_recipient_points}).where(
            Person.slack_id == user
        )
        await respond(
            f"Donated {amount} points to <@{user}>. You now have {new_performer_points} points. They now have {new_recipient_points} points."
        )
        # Audit log
        await AuditLog.insert(
            AuditLog(
                user_id=performer, action="donate", target_user=user, amount=amount
            )
        )
    await client.chat_postMessage(
        channel=user, text=f"You have received {amount} points from <@{performer}>!"
    )
    await client.chat_postMessage(
        channel=performer, text=f"You have donated {amount} points to <@{user}>."
    )
