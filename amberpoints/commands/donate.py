from slack_bolt.async_app import AsyncAck, AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.tables import Person, AuditLog


async def donate_handler(ack: AsyncAck, client: AsyncWebClient, respond: AsyncRespond, performer: str, sender: str, user: str, amount: int = 1):
    await ack()

    if sender == user:
        await respond("You cannot donate to yourself.")
        return
    if not user:
        await respond("You must specify a user to donate to.")
        return

    # Get sender
    sender_person = await Person.objects().where(Person.slack_id == sender).first()
    if not sender_person:
        await respond("You don't have an account yet. Earn some points first!")
        return

    if sender_person.points < amount:
        await respond(f"You don't have enough points. You have {sender_person.points}.")
        return

    # Get or create recipient
    recipient = await Person.objects().where(Person.slack_id == user).first()
    if not recipient:
        recipient = Person(slack_id=user, points=amount, admin=False, banned=False)
        await Person.insert(recipient)
        new_sender_points = sender_person.points - amount
        await Person.update({Person.points: new_sender_points}).where(Person.slack_id == sender)
        await respond(f"Donated {amount} points to <@{user}>. You now have {new_sender_points} points. They now have {amount} points.")
        # Audit log
        await AuditLog.insert(AuditLog(user_id=sender, action="donate", target_user=user, amount=amount))
    else:
        new_sender_points = sender_person.points - amount
        new_recipient_points = recipient.points + amount
        await Person.update({Person.points: new_sender_points}).where(Person.slack_id == sender)
        await Person.update({Person.points: new_recipient_points}).where(Person.slack_id == user)
        await respond(f"Donated {amount} points to <@{user}>. You now have {new_sender_points} points. They now have {new_recipient_points} points.")
        # Audit log
        await AuditLog.insert(AuditLog(user_id=sender, action="donate", target_user=user, amount=amount))
    await client.chat_postMessage(channel=user, text=f"You have received {amount} points from <@{sender}>!")
    await client.chat_postMessage(channel=sender, text=f"You have donated {amount} points to <@{user}>.")
