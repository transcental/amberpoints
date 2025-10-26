from slack_bolt.async_app import AsyncAck, AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.tables import Person, AuditLog


async def ban_handler(ack: AsyncAck, client: AsyncWebClient, respond: AsyncRespond, performer: str, user: str, reason: str = "No reason provided"):
    await ack()

    # Check if the user exists
    person = await Person.objects().where(Person.slack_id == user).first()

    if not person:
        # Create the user as banned
        await Person.insert(Person(slack_id=user, banned=True, ban_reason=reason, points=0, admin=False))
        # DM the user
        try:
            await client.chat_postMessage(channel=user, text=f"You have been banned from Amber Points. Reason: {reason}")
        except Exception as e:
            # If DM fails, maybe log, but continue
            pass
        await respond(f"User {user} has been banned (new user created). Reason: {reason}")
        # Audit log
        await AuditLog.insert(AuditLog(user_id=performer, action="ban", target_user=user, reason=reason))
        return

    # Check if already banned
    if person.banned:
        await respond(f"User {user} is already banned.")
        return

    # Ban the user
    await Person.update({Person.banned: True, Person.ban_reason: reason}).where(Person.slack_id == user)

    # DM the user
    try:
        await client.chat_postMessage(channel=user, text=f"You have been banned from Amber Points. Reason: {reason}")
    except Exception as e:
        pass

    await respond(f"User {user} has been banned. Reason: {reason}")

    # Audit log
    await AuditLog.insert(AuditLog(user_id=performer, action="ban", target_user=user, reason=reason))
