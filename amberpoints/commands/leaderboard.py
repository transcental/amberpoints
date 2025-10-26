from slack_bolt.async_app import AsyncAck
from slack_bolt.async_app import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient

from amberpoints.tables import Person


async def leaderboard_handler(
    ack: AsyncAck, client: AsyncWebClient, respond: AsyncRespond, performer: str
):
    await ack()

    # Get top 10 users by points
    top_users = (
        await Person.objects().order_by(Person.points, ascending=False).limit(10)
    )

    if not top_users:
        await respond("No users found.")
        return

    leaderboard = "🏆 Amber Points Leaderboard 🏆\n"
    for i, person in enumerate(top_users, 1):
        status = f" (banned - {person.ban_reason})" if person.banned else ""
        status += " (admin)" if person.admin else ""
        status += " (you)" if person.slack_id == performer else ""
        leaderboard += f"{i}. *<@{person.slack_id}>*: {person.points} point{'s' if person.points != 1 else ''}{status}\n"

    await respond(leaderboard)
